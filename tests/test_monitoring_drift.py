"""Known-distribution drift tests; not an intrusion-detection accuracy test."""
from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
from nohack.monitoring.drift import numeric_drift_report, population_stability_index


def test_psi_identical_and_shift() -> None:
    ref = np.linspace(0.01, 2, 500).tolist()
    assert population_stability_index(ref, ref) == pytest.approx(0)
    shifted = np.linspace(4, 6, 500).tolist()
    assert population_stability_index(ref, shifted) > 0.2
    result = numeric_drift_report({"count": ref}, {"count": shifted})
    assert result["warning_count"] == 1
    assert result["not_accuracy_or_security_verdict"] is True


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        population_stability_index([0], [0])
    with pytest.raises(ValueError):
        numeric_drift_report({"a": [0] * 20}, {"b": [1] * 20})
