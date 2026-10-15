"""Reusable hybrid network-flow stacking components (no private packet data)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler

from nohack.features import FEATURE_NAMES

NUMERICAL = [name for name in FEATURE_NAMES if name != "protocol"]
PROTOCOL_ORDER = ("TCP", "UDP", "ICMP", "ICMPV6")
META_COLUMNS = (
    "xgb_attack", "lightgbm_attack", "catboost_attack",
    "iforest_percentile", "gmm_percentile", "supervised_mean",
    "supervised_std", "anomaly_mean", "evidence_gap", "supervised_votes",
)


def encode_flow(frame: pd.DataFrame) -> np.ndarray:
    """Stable numerical encoding for all supported model families."""
    if tuple(frame.columns[:len(FEATURE_NAMES)]) != FEATURE_NAMES:
        raise ValueError("NoHackFlow order mismatch")
    if not frame["protocol"].isin(PROTOCOL_ORDER).all():
        raise ValueError("Unsupported protocol")
    numeric = frame[NUMERICAL].to_numpy(dtype=np.float64)
    if not np.isfinite(numeric).all() or (numeric < 0).any():
        raise ValueError("Nonfinite/negative features")
    protocol = frame["protocol"].to_numpy()
    categories = np.column_stack([protocol == p for p in PROTOCOL_ORDER])
    return np.column_stack([numeric, categories.astype(np.float64)])


def anomaly_matrix(encoded: np.ndarray, scaler: RobustScaler | None = None
                   ) -> tuple[np.ndarray, RobustScaler]:
    """Log1p-scale numerical flow magnitudes; train-fitted RobustScaler only."""
    n = len(NUMERICAL)
    values = np.concatenate((np.log1p(encoded[:, :n]), encoded[:, n:]), axis=1)
    if scaler is None:
        scaler = RobustScaler(quantile_range=(10.0, 90.0))
        values = scaler.fit_transform(values)
    else:
        values = scaler.transform(values)
    return np.clip(values, -100.0, 100.0), scaler


@dataclass
class HybridBase:
    supervised: dict[str, Any]
    anomaly_scaler: RobustScaler
    isolation_forest: IsolationForest
    gaussian_mixture: GaussianMixture
    iso_reference: np.ndarray
    gmm_reference: np.ndarray

    def meta_features(self, frame: pd.DataFrame) -> np.ndarray:
        x = encode_flow(frame)
        numeric, _ = anomaly_matrix(x, self.anomaly_scaler)
        supervised = np.column_stack([
            self.supervised[name].predict_proba(x)[:, 1]
            for name in ("xgb", "lightgbm", "catboost")
        ])
        # Greater values mean more anomalous, unlike sklearn score_samples().
        iso = -self.isolation_forest.score_samples(numeric)
        gmm = -self.gaussian_mixture.score_samples(numeric)
        a = np.searchsorted(self.iso_reference, iso, side="right") / len(self.iso_reference)
        b = np.searchsorted(self.gmm_reference, gmm, side="right") / len(self.gmm_reference)
        anomaly = (a + b) / 2
        mean = supervised.mean(axis=1)
        std = supervised.std(axis=1)
        gap = np.abs(mean - anomaly)
        votes = (supervised >= 0.5).sum(axis=1)
        return np.column_stack([supervised, a, b, mean, std, anomaly, gap, votes])


def train_hybrid_base(frame: pd.DataFrame, labels: np.ndarray, *, seed: int
                      ) -> HybridBase:
    """Fit three supervised classifiers and benign-reference anomaly models."""
    from catboost import CatBoostClassifier
    from lightgbm import LGBMClassifier
    from xgboost import XGBClassifier

    x = encode_flow(frame)
    if len(np.unique(labels)) != 2:
        raise ValueError("A training fold must contain benign and attack classes")
    models: dict[str, Any] = {
        "xgb": XGBClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.07,
            subsample=0.85, colsample_bytree=0.9, n_jobs=2,
            tree_method="hist", random_state=seed, eval_metric="logloss",
        ),
        "lightgbm": LGBMClassifier(
            n_estimators=120, num_leaves=24, learning_rate=0.06,
            class_weight="balanced", verbosity=-1, n_jobs=2,
            random_state=seed,
        ),
        "catboost": CatBoostClassifier(
            iterations=120, depth=5, learning_rate=0.07,
            verbose=False, thread_count=2, random_seed=seed,
            auto_class_weights="Balanced", allow_writing_files=False,
        ),
    }
    for model in models.values():
        model.fit(x, labels)
    benign = x[labels == 0]
    if len(benign) < 20:
        raise ValueError("At least 20 benign flows required per training fold")
    # Robust preprocessing is fitted ONLY to benign examples within the fold.
    scaled, scaler = anomaly_matrix(benign)
    iforest = IsolationForest(n_estimators=120, max_samples=min(512, len(benign)),
                               contamination="auto", n_jobs=2, random_state=seed)
    iforest.fit(scaled)
    components = min(3, max(1, len(benign) // 30))
    gmm = GaussianMixture(n_components=components, covariance_type="diag",
                          reg_covar=1e-3, max_iter=120, random_state=seed)
    gmm.fit(scaled)
    iso_reference = np.sort(-iforest.score_samples(scaled))
    gmm_reference = np.sort(-gmm.score_samples(scaled))
    return HybridBase(models, scaler, iforest, gmm, iso_reference, gmm_reference)


def summarize_reasons(features: dict[str, Any]) -> list[str]:
    """Fact-based feature descriptions, not causal malware explanations."""
    reasons = []
    if float(features["packets_per_second"]) > 500:
        reasons.append("High observed packet rate")
    if int(features["rst_count"]) >= 3:
        reasons.append("Multiple TCP reset flags")
    if float(features["forward_backward_packet_ratio"]) >= 10:
        reasons.append("Strongly asymmetric packet counts")
    if int(features["total_packet_count"]) <= 2:
        reasons.append("Very short observed flow")
    return reasons[:3] or ["Anomalous combination of flow statistics"]
