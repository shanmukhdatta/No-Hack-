"""Fixed-loopback model-availability probe tests; no network requests are made."""

from __future__ import annotations

import io
import json
from typing import Any

import pytest

from nohack.native_host import local_model_status


class FakeResponse:
    status = 200

    def __init__(self, payload: dict[str, Any]) -> None:
        self.stream = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        self.stream.close()

    def read(self, size: int) -> bytes:
        return self.stream.read(size)


def test_verified_local_model_status(monkeypatch: pytest.MonkeyPatch) -> None:
    import nohack.native_host as host

    urls: list[str] = []

    def fake_urlopen(url: str, timeout: float) -> FakeResponse:
        urls.append(url)
        assert timeout < 1
        return FakeResponse(
            {
                "service": "nohack-local-api",
                "scope": "network_flow_only",
                "model_connected": True,
                "model_sha256": "a" * 64,
            }
        )

    monkeypatch.setattr(host, "urlopen", fake_urlopen)
    assert local_model_status() == {
        "model_loaded": True,
        "model_sha256": "a" * 64,
        "synthetic_demo_only": False,
    }
    assert urls == ["http://127.0.0.1:8787/model/status"]


def test_refuse_unverified_status(monkeypatch: pytest.MonkeyPatch) -> None:
    import nohack.native_host as host

    monkeypatch.setattr(
        host,
        "urlopen",
        lambda url, timeout: FakeResponse(
            {
                "service": "another-app",
                "scope": "network_flow_only",
                "model_connected": True,
                "model_sha256": "not-a-valid-digest",
            }
        ),
    )
    assert local_model_status()["model_loaded"] is False

    def not_running(url: str, timeout: float) -> FakeResponse:
        raise OSError("local service not started")

    monkeypatch.setattr(host, "urlopen", not_running)
    assert local_model_status() == {"model_loaded": False}
