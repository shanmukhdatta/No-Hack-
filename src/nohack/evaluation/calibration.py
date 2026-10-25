"""Post-hoc calibration diagnostics for independent binary heldout labels."""
from __future__ import annotations

import numpy as np


def calibration_bins(
    truth: list[int] | np.ndarray,
    probabilities: list[float] | np.ndarray,
    *,
    bins: int = 10,
) -> dict[str, object]:
    if not 2 <= bins <= 100:
        raise ValueError("bins must be 2..100")
    y = np.asarray(truth)
    p = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or y.size == 0 or y.size != p.size:
        raise ValueError("Need equal nonempty one-dimensional arrays")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all():
        raise ValueError("Binary labels and finite scores required")
    if (p < 0).any() or (p > 1).any():
        raise ValueError("Probability must be within [0,1]")
    indices = np.minimum(np.floor(p * bins).astype(int), bins - 1)
    result = []
    ece = 0.0
    for i in range(bins):
        selected = indices == i
        count = int(selected.sum())
        if count:
            observed = float(y[selected].mean())
            confidence = float(p[selected].mean())
            ece += count * abs(observed - confidence) / len(y)
            result.append(
                {"bin": i, "count": count, "mean_predicted": confidence, "observed_frequency": observed}
            )
    return {
        "kind": "independent_label_calibration_diagnostic",
        "n": int(y.size),
        "expected_calibration_error": float(ece),
        "nonempty_bins": result,
        "not_a_causal_security_explanation": True,
    }
