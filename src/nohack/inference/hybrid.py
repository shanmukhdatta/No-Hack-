"""Versioned, fail-closed hybrid inference; trusted local model bundles only."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nohack.features import FEATURE_NAMES, validate_features, schema_fingerprint
from nohack.models.hybrid import summarize_reasons
from nohack.datasets.prepare import _digest


def load_bundle(folder: Path, *, trust_local_artifact: bool = False) -> dict[str, Any]:
    """Reject untrusted pickle artifacts even if the manifest has matching hashes."""
    if not trust_local_artifact:
        raise PermissionError(
            "Loading joblib can execute code. Explicitly trust this locally trained bundle."
        )
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    model_path = folder / "hybrid.joblib"
    if (manifest.get("bundle_format") != 1
            or manifest.get("bundle_filename") != "hybrid.joblib"
            or manifest.get("feature_schema_sha256") != schema_fingerprint()
            or _digest(model_path) != manifest.get("bundle_sha256")):
        raise ValueError("Model manifest/hash/schema verification failed")
    import joblib

    bundle: dict[str, Any] = joblib.load(model_path)
    if (tuple(bundle["feature_names"]) != FEATURE_NAMES
            or bundle["feature_schema_sha256"] != schema_fingerprint()):
        raise ValueError("Loaded model feature contract mismatch")
    return bundle


def predict_features(bundle: dict[str, Any], values: dict[str, Any]
                     ) -> dict[str, Any]:
    """Produce a flow assessment, not an assertion of website safety."""
    import numpy as np
    import pandas as pd

    ordered = validate_features(values)
    frame = pd.DataFrame([ordered], columns=FEATURE_NAMES)
    meta_features = bundle["base"].meta_features(frame)
    raw = bundle["meta"].predict_proba(meta_features)[:, 1]
    known = float(bundle["calibrator"].predict_proba(raw.reshape(-1, 1))[0, 1])
    anomaly = float(meta_features[0, 7])
    disagreement = float(meta_features[0, 6])
    threshold = float(bundle["known_threshold"])
    novel_threshold = float(bundle["anomaly_threshold"])
    if not np.isfinite([known, anomaly, disagreement]).all():
        raise ValueError("Model returned nonfinite signals")
    near = abs(known - threshold) < 0.04
    if disagreement > 0.23 or near:
        state = "UNCERTAIN"
    elif known >= threshold:
        state = "KNOWN_THREAT"
    elif anomaly >= novel_threshold:
        state = "NOVEL_ANOMALY"
    else:
        state = "NORMAL"
    signals = summarize_reasons(ordered) if state != "NORMAL" else []
    return {
        "state": state,
        "known_threat_probability": round(known, 6),
        "anomaly_percentile": round(anomaly, 6),
        "risk_score": int(round(100 * max(known, anomaly))),
        "risk_score_is_probability": False,
        "attack_family": None,
        "model_disagreement": round(disagreement, 6),
        "top_reasons": signals,
        "feature_schema_version": "nohackflow-v1",
        "assessment_scope": "network_flow_not_browser_tab",
    }
