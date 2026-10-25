"""Optional FastAPI checks: no dummy success and no unauthenticated scoring."""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from nohack.api.app import create_app


def test_unconnected_and_read_only(tmp_path: object) -> None:
    from pathlib import Path

    db = Path(str(tmp_path)) / "missing.db"
    client = TestClient(create_app(database=db))
    assert client.get("/health").json()["model_connected"] is False
    assert client.get("/model/status").json()["status"] == "model_not_connected"
    assert client.get("/assessments").json()["items"] == []
    assert client.post("/predict", json={"features": {}}).status_code == 401


def test_invalid_limit_and_untrusted_model(tmp_path: object) -> None:
    from pathlib import Path

    client = TestClient(create_app(model_dir=Path(str(tmp_path))))
    assert client.get("/model/status").json()["model_connected"] is False
    assert client.get("/assessments?limit=21").status_code == 422
