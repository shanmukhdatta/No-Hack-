"""Optional SHAP attribution for the XGBoost *component*, not the hybrid stack.

Do not describe component explanations as causal or as the full ensemble's SHAP.
"""
from __future__ import annotations

from typing import Any

from nohack.features import FEATURE_NAMES
from nohack.models.hybrid import NUMERICAL, PROTOCOL_ORDER, encode_flow


def explain_xgb_component(
    trusted_bundle: dict[str, Any],
    verified_features: dict[str, Any],
    *,
    top_k: int = 10,
) -> dict[str, Any]:
    if not 1 <= top_k <= 36:
        raise ValueError("top_k must be 1..36")
    import numpy as np
    import pandas as pd
    import shap

    from nohack.features import validate_features

    values = validate_features(verified_features)
    frame = pd.DataFrame([values], columns=FEATURE_NAMES)
    encoded = encode_flow(frame)
    xgb = trusted_bundle["base"].supervised["xgb"]
    explainer = shap.TreeExplainer(xgb)
    results = np.asarray(explainer.shap_values(encoded))
    if results.ndim == 3:
        results = results[:, :, -1]
    scores = np.asarray(results[0], dtype=float)
    names = [*NUMERICAL, *(f"protocol_{p.lower()}" for p in PROTOCOL_ORDER)]
    if scores.shape != (len(names),) or not np.isfinite(scores).all():
        raise ValueError("Unexpected SHAP explanation shape")
    ranks = np.argsort(np.abs(scores))[::-1][:top_k]
    return {
        "scope": "xgboost_base_component_only",
        "not_causal": True,
        "not_full_stack_explanation": True,
        "contributions": [
            {"feature": names[int(i)], "shap_value": float(scores[i])}
            for i in ranks
        ],
    }
