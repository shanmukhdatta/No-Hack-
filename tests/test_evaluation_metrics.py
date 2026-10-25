"""Tests exercise pure metrics with no synthetic metrics advertised as results."""
from __future__ import annotations

import pytest

pytest.importorskip("numpy")
pytest.importorskip("sklearn")
from nohack.evaluation.report import evaluate_binary, group_slice_metrics


def test_confusion_and_single_class_safety() -> None:
    result = evaluate_binary([0, 0, 1, 1], [0.1, 0.9, 0.8, 0.9])
    assert result["confusion_matrix"] == [[1, 1], [0, 2]]
    assert result["false_positive_rate"] == 0.5
    solo = evaluate_binary([0, 0], [0.1, 0.2])
    assert solo["roc_auc"] is None
    assert solo["average_precision"] is None


def test_groups_and_bad_scores() -> None:
    result = group_slice_metrics([0, 1], [0.2, 0.8], ["first", "second"])
    assert set(result) == {"first", "second"}
    with pytest.raises(ValueError):
        evaluate_binary([0, 1], [0.2, float("nan")])
