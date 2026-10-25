"""Classical baselines train on group-disjoint partitions only."""

# ruff: noqa: E402
from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("sklearn")

from nohack.models.baselines import run_baselines
from scripts.demo_model_pipeline import make_fixture


def test_two_baselines_with_group_isolation() -> None:
    all_rows = make_fixture(16)
    train = all_rows[all_rows.group_id.str.endswith(tuple(f"{i:03}" for i in range(8)))]
    val = all_rows[
        all_rows.group_id.str.endswith(tuple(f"{i:03}" for i in range(8, 16)))
    ]
    results = run_baselines(train, val)
    assert set(results) == {"logistic_regression", "random_forest"}
    assert all(0 <= m["f1"] <= 1 for m in results.values())
    with pytest.raises(ValueError, match="Group leakage"):
        run_baselines(train, train)
