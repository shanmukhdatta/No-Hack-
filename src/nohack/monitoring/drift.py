"""Reference-vs-current covariate drift without requiring test labels.

PSI is a heuristic, not a statistical proof of compromise or model error.
We never store source IPs or packet payloads here.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


def population_stability_index(
    reference: Sequence[float], current: Sequence[float], *, bins: int = 10
) -> float:
    """Population Stability Index with training-only cutpoints and smoothing."""
    import numpy as np

    if not 2 <= bins <= 100:
        raise ValueError("bins must be 2..100")
    r = np.asarray(reference, dtype=float)
    c = np.asarray(current, dtype=float)
    if r.size < 20 or c.size < 20:
        raise ValueError("At least 20 values per population required")
    if not np.isfinite(r).all() or not np.isfinite(c).all():
        raise ValueError("Drift data must contain only finite values")
    boundaries = np.unique(np.quantile(r, np.linspace(0, 1, bins + 1))[1:-1])
    ref_counts = np.bincount(np.searchsorted(boundaries, r), minlength=len(boundaries) + 1)
    cur_counts = np.bincount(np.searchsorted(boundaries, c), minlength=len(boundaries) + 1)
    n = len(ref_counts)
    ref_rates = (ref_counts + 0.5) / (ref_counts.sum() + 0.5 * n)
    cur_rates = (cur_counts + 0.5) / (cur_counts.sum() + 0.5 * n)
    return float(np.sum((cur_rates - ref_rates) * np.log(cur_rates / ref_rates)))


def numeric_drift_report(
    reference: Mapping[str, Sequence[float]],
    current: Mapping[str, Sequence[float]],
    *,
    bins: int = 10,
    warning_psi: float = 0.2,
) -> dict[str, Any]:
    """Only supplied comparable numeric fields are checked."""
    if set(reference) != set(current) or not reference:
        raise ValueError("Reference and current numeric feature schemas must match")
    if not math.isfinite(warning_psi) or warning_psi <= 0:
        raise ValueError("warning_psi must be positive")
    metrics: dict[str, dict[str, float | bool]] = {}
    for key in sorted(reference):
        psi = population_stability_index(reference[key], current[key], bins=bins)
        metrics[key] = {"psi": round(psi, 6), "warning": psi >= warning_psi}
    return {
        "kind": "unlabeled_covariate_drift",
        "not_accuracy_or_security_verdict": True,
        "reference_is_baseline_only": True,
        "warning_psi": warning_psi,
        "features": metrics,
        "warning_count": sum(int(v["warning"]) for v in metrics.values()),
    }
