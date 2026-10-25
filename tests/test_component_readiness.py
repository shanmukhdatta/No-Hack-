"""Code inventory cannot certify production readiness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nohack.engineering.readiness import (
    project_inventory,
    self_attested_acceptance,
)


def test_inventory_matches_repo_without_faking_release() -> None:
    root = Path(__file__).resolve().parents[1]
    report = project_inventory(root)
    assert report["total"] >= 20
    assert report["present"] == report["total"]
    assert report["production_ready"] is False
    assert all(not x["acceptance_verified_by_inventory"] for x in report["components"])


def test_release_requires_all_external_evidence(tmp_path: Path) -> None:
    file = tmp_path / "approval.json"
    file.write_text(json.dumps({"fake": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="external acceptance"):
        self_attested_acceptance(file)
