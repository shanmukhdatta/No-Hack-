"""Binary-protocol and safety tests. Does not access a real Chrome installation."""

from __future__ import annotations

import io
import json
import struct
from pathlib import Path

import pytest

from nohack.native_host import handle_message, read_message, serve_one, write_message


def test_read_write_roundtrip() -> None:
    buffer = io.BytesIO()
    write_message(buffer, {"type": "ping"})
    buffer.seek(0)
    assert read_message(buffer) == {"type": "ping"}


def test_serve_read_only_ping() -> None:
    incoming = io.BytesIO()
    write_message(incoming, {"type": "ping"})
    incoming.seek(0)
    outgoing = io.BytesIO()
    assert serve_one(incoming, outgoing)
    outgoing.seek(0)
    assert read_message(outgoing) == {
        "ok": True,
        "protocol_version": 1,
        "name": "No Hack companion",
    }


def test_reject_invalid_length_and_json() -> None:
    with pytest.raises(ValueError, match="length"):
        read_message(io.BytesIO(struct.pack("<I", 100_000)))
    with pytest.raises(ValueError, match="Incomplete"):
        read_message(io.BytesIO(struct.pack("<I", 7) + b"{}"))
    with pytest.raises(ValueError, match="Invalid JSON"):
        read_message(io.BytesIO(struct.pack("<I", 4) + b"nope"))
    with pytest.raises(ValueError, match="Incomplete"):
        read_message(io.BytesIO(b"\x01"))


def test_no_unsafe_commands() -> None:
    assert handle_message({"type": "start_capture"}) == {
        "ok": False,
        "error": "Unsupported read-only command",
    }
    assert handle_message("status") == {
        "ok": False,
        "error": "Expected JSON object",
    }
    assert handle_message({"type": "status"})["model_loaded"] is False


def test_eof_and_response_size(monkeypatch: pytest.MonkeyPatch) -> None:
    assert serve_one(io.BytesIO(), io.BytesIO()) is False
    import nohack.native_host as module

    monkeypatch.setattr(module, "MAX_RESPONSE_BYTES", 8)
    with pytest.raises(ValueError, match="size limit"):
        write_message(io.BytesIO(), {"hello": "world"})


def test_manifest_allowlist(tmp_path: Path) -> None:
    # Load the lightweight installer script without Windows Registry APIs.
    from importlib.util import module_from_spec, spec_from_file_location

    path = Path(__file__).resolve().parents[1] / "scripts" / "install_native_host.py"
    spec = spec_from_file_location("install_native_host", path)
    assert spec is not None and spec.loader is not None
    installer = module_from_spec(spec)
    spec.loader.exec_module(installer)
    exe = tmp_path / "host.exe"
    exe.write_bytes(b"fixture")
    result = installer.host_manifest("a" * 32, exe)
    assert result["allowed_origins"] == ["chrome-extension://" + "a" * 32 + "/"]
    assert json.loads(json.dumps(result))["type"] == "stdio"
    with pytest.raises(ValueError, match="Extension ID"):
        installer.host_manifest("*" * 32, exe)
    with pytest.raises(ValueError, match="built"):
        installer.host_manifest("a" * 32, tmp_path / "missing.exe")
