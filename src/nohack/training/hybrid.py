"""Train and package a real, group-aware OOF NoHackFlow hybrid detector.

Only use verified canonical flow records; public CICFlowMeter CSVs are NOT
directly compatible with the 33-field NoHackFlow v1 schema.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, brier_score_loss, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from nohack.datasets.prepare import _digest, validate_canonical_table
from nohack.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, schema_fingerprint
from nohack.models.hybrid import META_COLUMNS, HybridBase, train_hybrid_base


def _binary(df: pd.DataFrame) -> np.ndarray:
    return df["label"].str.strip().str.upper().ne("BENIGN").astype(int).to_numpy()


def _frame(df: pd.DataFrame) -> pd.DataFrame:
    return df[list(FEATURE_NAMES)]


def _safe_metrics(y: np.ndarray, prob: np.ndarray, threshold: float) -> dict[str, Any]:
    hard = (prob >= threshold).astype(int)
    fpr_den = max(1, int((y == 0).sum()))
    return {
        "rows": int(len(y)),
        "precision": float(precision_score(y, hard, zero_division=0)),
        "recall": float(recall_score(y, hard, zero_division=0)),
        "f1": float(f1_score(y, hard, zero_division=0)),
        "average_precision": float(average_precision_score(y, prob)),
        "roc_auc": float(roc_auc_score(y, prob)) if len(np.unique(y)) == 2 else None,
        "brier": float(brier_score_loss(y, prob)),
        "false_positive_rate": float(((hard == 1) & (y == 0)).sum() / fpr_den),
        "confusion_matrix": confusion_matrix(y, hard, labels=[0, 1]).tolist(),
    }


def _choose_threshold(y: np.ndarray, prob: np.ndarray, max_fpr: float) -> float:
    """Tune known-threat threshold on the policy-validation partition only."""
    choices = np.unique(np.concatenate(([0.5, 1.0], prob)))
    feasible = []
    for threshold in choices:
        predictions = prob >= threshold
        fpr = np.mean(predictions[y == 0]) if (y == 0).any() else 1.0
        if fpr <= max_fpr:
            recall = np.mean(predictions[y == 1]) if (y == 1).any() else 0.0
            feasible.append((recall, threshold))
    if not feasible:
        return 1.0
    best_recall = max(r for r, _ in feasible)
    return float(max(t for r, t in feasible if r == best_recall))


def _dataset_parts(folder: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest["feature_schema"] != FEATURE_SCHEMA_VERSION:
        raise ValueError("Dataset feature version mismatch")
    if manifest["feature_schema_sha256"] != schema_fingerprint():
        raise ValueError("Dataset feature fingerprint mismatch")
    parts = []
    for name in ("train", "val", "test"):
        p = folder / f"{name}.parquet"
        if _digest(p) != manifest["splits"][name]["sha256"]:
            raise ValueError(f"{name} file SHA256 mismatch")
        parts.append(validate_canonical_table(pd.read_parquet(p)))
    groups = [set(df["group_id"]) for df in parts]
    if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
        raise ValueError("Dataset split group leakage")
    return parts[0], parts[1], parts[2]


def _meta_probability(
    base: HybridBase, meta: LogisticRegression, cal: LogisticRegression,
    frame: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    features = base.meta_features(frame)
    raw = meta.predict_proba(features)[:, 1]
    probabilities = cal.predict_proba(raw.reshape(-1, 1))[:, 1]
    return probabilities, features


def train_from_splits(
    data_dir: Path, output_dir: Path, *, seed: int = 42, folds: int = 4,
    max_false_positive_rate: float = 0.02,
) -> dict[str, Any]:
    """Train only on train folds, calibrate and tune on separate validation groups."""
    if not 0 < max_false_positive_rate < 1:
        raise ValueError("max_false_positive_rate must be between 0 and 1")
    train, validation, test = _dataset_parts(data_dir)
    y = _binary(train)
    groups = train["group_id"].to_numpy()
    if len(set(groups)) < folds or folds < 2:
        raise ValueError("Need enough independent training groups for OOF folds")
    oof = np.full((len(train), len(META_COLUMNS)), np.nan)
    splitter = GroupKFold(n_splits=folds)
    for fold, (fit_idx, predict_idx) in enumerate(splitter.split(train, y, groups)):
        fitted = train_hybrid_base(_frame(train.iloc[fit_idx]), y[fit_idx],
                                   seed=seed + fold)
        oof[predict_idx] = fitted.meta_features(_frame(train.iloc[predict_idx]))
    if not np.isfinite(oof).all():
        raise RuntimeError("Missing OOF predictions")
    meta = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)
    meta.fit(oof, y)
    base = train_hybrid_base(_frame(train), y, seed=seed)
    # Keep calibration and threshold-selection groups disjoint.
    validator = GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=seed+3)
    calibration_idx, policy_idx = next(
        validator.split(validation, groups=validation["group_id"])
    )
    calibration_frame = validation.iloc[calibration_idx]
    policy_frame = validation.iloc[policy_idx]
    y_cal = _binary(calibration_frame)
    y_policy = _binary(policy_frame)
    if len(np.unique(y_cal)) != 2 or len(np.unique(y_policy)) != 2:
        raise ValueError("Validation needs both labels in calibration/policy groups")
    cal_raw = meta.predict_proba(base.meta_features(_frame(calibration_frame)))[:, 1]
    calibrator = LogisticRegression(max_iter=1000, random_state=seed)
    calibrator.fit(cal_raw.reshape(-1, 1), y_cal)
    policy_prob, policy_features = _meta_probability(
        base, meta, calibrator, _frame(policy_frame)
    )
    known_threshold = _choose_threshold(
        y_policy, policy_prob, max_false_positive_rate
    )
    # Anomaly threshold from benign training references (not test labels).
    # Mean of two independently normalized novelty signals; conservative.
    anomaly_threshold = 0.99
    test_prob, test_features = _meta_probability(base, meta, calibrator, _frame(test))
    y_test = _binary(test)
    metrics = _safe_metrics(y_test, test_prob, known_threshold)
    metrics["n_test_groups"] = int(test["group_id"].nunique())
    metrics["known_threshold"] = known_threshold
    metrics["anomaly_threshold"] = anomaly_threshold
    metrics["max_policy_validation_fpr"] = max_false_positive_rate
    metrics["policy_validation"] = _safe_metrics(
        y_policy, policy_prob, known_threshold
    )
    metrics["anomaly_alerts_test"] = int(
        ((test_features[:, 7] >= anomaly_threshold) &
         (test_prob < known_threshold)).sum()
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = {
        "base": base, "meta": meta, "calibrator": calibrator,
        "known_threshold": known_threshold,
        "anomaly_threshold": anomaly_threshold,
        "meta_columns": META_COLUMNS,
        "feature_names": FEATURE_NAMES,
        "feature_schema_sha256": schema_fingerprint(),
    }
    bundle_path = output_dir / "hybrid.joblib"
    joblib.dump(bundle, bundle_path, compress=3)
    manifest = {
        "product": "No Hack", "bundle_format": 1,
        "model_type": "hybrid_oof_binary_with_anomaly",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_schema_sha256": schema_fingerprint(),
        "bundle_filename": "hybrid.joblib",
        "bundle_sha256": _digest(bundle_path),
        "training_data_manifest_sha256": _digest(data_dir / "manifest.json"),
        "seed": seed, "n_folds": folds, "metrics": metrics,
        "attack_family_model": "not_trained",
        "model_status": "trained_not_windows_validated",
        "artifact_warning": (
            "joblib contains executable pickle data. Only load bundles you "
            "personally trained or authenticated from a trusted source."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
