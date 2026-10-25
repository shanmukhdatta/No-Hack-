"""The API must identify a synthetic demo model without claiming validation."""

# ruff: noqa: E402
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from nohack.api.app import create_app


def test_synthetic_model_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import nohack.inference.hybrid as inference

    monkeypatch.setattr(
        inference,
        "load_bundle",
        lambda folder, trust_local_artifact: {"test_stub": True},
    )
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "bundle_sha256": "a" * 64,
                "synthetic_demo_only": True,
                "model_status": "synthetic_demo_not_security_validated",
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(model_dir=tmp_path, trust_local_model=True))
    status = client.get("/model/status").json()
    assert status["model_connected"] is True
    assert status["synthetic_demo_only"] is True
    assert status["model_validation_status"] == "synthetic_demo_not_security_validated"
