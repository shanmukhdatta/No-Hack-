"""Pure deterministic contract checks; timing numbers are not precomputed."""

from __future__ import annotations

import pytest

from nohack.evaluation.latency import benchmark
from nohack.monitoring.assessment_metrics import summarize_assessments


def test_real_timing_shape() -> None:
    result = benchmark(lambda x: x["value"], [{"value": 1}], warmups=0, repetitions=2)
    assert result["samples"] == 2
    assert result["p95_ms"] >= 0
    assert "not_production_sla" in result["kind"]


def test_unlabeled_assessments_are_not_accuracy() -> None:
    result = summarize_assessments(
        [
            {"state": "NORMAL", "risk_score": 15},
            {"state": "UNCERTAIN", "risk_score": 70},
        ]
    )
    assert result["rows"] == 2
    assert result["detection_accuracy_not_measured"] is True
    with pytest.raises(ValueError):
        summarize_assessments([{"state": "NORMAL", "risk_score": 200}])
