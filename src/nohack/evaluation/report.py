"""Group-aware evaluation of independent held-out network-flow labels."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_binary(
    truth: list[int] | np.ndarray,
    probabilities: list[float] | np.ndarray,
    *,
    threshold: float = 0.5,
) -> dict[str, Any]:
    y = np.asarray(truth)
    p = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or len(y) != len(p) or len(y) == 0:
        raise ValueError("One-dimensional matched nonempty arrays required")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all():
        raise ValueError("Binary labels and finite scores required")
    if not (0 <= p).all() or not (p <= 1).all() or not 0 < threshold <= 1:
        raise ValueError("Probability or threshold outside valid bounds")
    decision = (p >= threshold).astype(int)
    neg = y == 0
    return {
        "rows": int(len(y)),
        "n_attack": int((y == 1).sum()),
        "n_benign": int(neg.sum()),
        "threshold": threshold,
        "precision": float(precision_score(y, decision, zero_division=0)),
        "recall": float(recall_score(y, decision, zero_division=0)),
        "f1": float(f1_score(y, decision, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, p)) if np.unique(y).size == 2 else None,
        "average_precision": (
            float(average_precision_score(y, p)) if np.any(y == 1) else None
        ),
        "false_positive_rate": (
            float(np.mean(decision[neg] == 1)) if neg.any() else None
        ),
        "brier": float(brier_score_loss(y, p)),
        "confusion_matrix": confusion_matrix(y, decision, labels=[0, 1]).tolist(),
    }


def group_slice_metrics(
    truth: list[int] | np.ndarray,
    probabilities: list[float] | np.ndarray,
    groups: list[str] | np.ndarray,
    *,
    threshold: float = 0.5,
) -> dict[str, dict[str, Any]]:
    y, p, g = np.asarray(truth), np.asarray(probabilities), np.asarray(groups)
    if len(g) != len(y) or len(g) != len(p):
        raise ValueError("Group length mismatch")
    return {
        str(group): evaluate_binary(y[g == group], p[g == group], threshold=threshold)
        for group in np.unique(g)
    }
