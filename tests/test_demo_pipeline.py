"""Synthetic samples validate the software contract; not real detection scores."""

# ruff: noqa: E402
from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")

from nohack.datasets.prepare import validate_canonical_table
from scripts.demo_model_pipeline import DEMO_WARNING, make_demo_flow, make_fixture


def test_demo_fixture_has_canonical_features_and_group_labels() -> None:
    data = make_fixture(groups=24)
    validated = validate_canonical_table(data)
    assert len(validated) == 24 * 12
    assert validated.group_id.nunique() == 24
    assert all(str(group).startswith("synthetic-demo-group-") for group in validated.group_id)
    assert "NOT validated security detection" in DEMO_WARNING
    assert validated.label.eq("BENIGN").sum() > 0
    assert validated.label.ne("BENIGN").sum() > 0


def test_demo_not_a_realistic_traffic_generator() -> None:
    a, b = make_demo_flow(1, 0), make_demo_flow(2, 0)
    assert a["duration_ms"] != b["duration_ms"]
    assert a["forward_packet_count"] + a["backward_packet_count"] == a["total_packet_count"]
    with pytest.raises(ValueError):
        make_demo_flow(1000, 0)
