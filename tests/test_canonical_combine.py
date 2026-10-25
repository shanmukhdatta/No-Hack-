"""Validated multi-dataset joining never fabricates features or labels."""

# ruff: noqa: E402

from __future__ import annotations

import json
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
from nohack.features.flow_schema import FEATURE_SPECS


def row(label: str, group: str) -> dict[str, object]:
    data = {
        name: 0 if kind == "int" else 0.0
        for name, kind in FEATURE_SPECS
        if kind != "category"
    }
    data.update({"protocol": "TCP", "label": label, "group_id": group})
    return data


def test_group_prefix_and_provenance(tmp_path: Path) -> None:
    from scripts.combine_canonical_datasets import combine_sources

    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    pd.DataFrame([row("BENIGN", "session"), row("Probe", "attack")]).to_csv(
        first, index=False
    )
    pd.DataFrame([row("BENIGN", "session"), row("DoS", "attack")]).to_csv(
        second, index=False
    )
    out = tmp_path / "combined.csv"
    report = combine_sources([("datasetA", first), ("datasetB", second)], out)
    assert report["rows"] == 4
    assert report["groups"] == 4
    values = pd.read_csv(out)
    assert set(values["group_id"]) == {
        "datasetA::session",
        "datasetA::attack",
        "datasetB::session",
        "datasetB::attack",
    }
    assert json.loads((tmp_path / "combined.provenance.json").read_text())["rows"] == 4


def test_combine_requires_independent_sources(tmp_path: Path) -> None:
    from scripts.combine_canonical_datasets import combine_sources

    with pytest.raises(ValueError, match="At least two"):
        combine_sources([("only", tmp_path / "missing.csv")], tmp_path / "out.csv")
