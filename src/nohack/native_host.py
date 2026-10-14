"""Restricted, read-only Chrome Native Messaging host for No Hack.

Chrome launches the installed executable for an extension with an exact
allowlisted origin. This module does not capture traffic, start services,
or fabricate ML threat results.
"""

from __future__ import annotations

import json
import struct
import sys
from typing import BinaryIO

from nohack.capture.capabilities import capture_capabilities

MAX_REQUEST_BYTES = 65_536
MAX_RESPONSE_BYTES = 1_048_576


def read_message(stream: BinaryIO) -> object | None:
    """Read a little-endian length-prefixed JSON message."""
    prefix = stream.read(4)
    if not prefix:
        return None
    if len(prefix) != 4:
        raise ValueError("Incomplete native message header")
    (length,) = struct.unpack("<I", prefix)
    if length == 0 or length > MAX_REQUEST_BYTES:
        raise ValueError("Invalid native message length")
    payload = stream.read(length)
    if len(payload) != length:
        raise ValueError("Incomplete native message body")
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid JSON native message") from exc


def write_message(stream: BinaryIO, message: dict[str, object]) -> None:
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("Native response exceeds size limit")
    stream.write(struct.pack("<I", len(payload)))
    stream.write(payload)
    stream.flush()


def handle_message(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {"ok": False, "error": "Expected JSON object"}
    request_type = value.get("type")
    if request_type == "ping":
        return {"ok": True, "protocol_version": 1, "name": "No Hack companion"}
    if request_type == "status":
        return {
            "ok": True,
            "protocol_version": 1,
            "capture": capture_capabilities(),
            "monitoring_active": False,
            "model_loaded": False,
            "note": "Read-only companion handshake; does not start capture or ML",
        }
    return {"ok": False, "error": "Unsupported read-only command"}


def serve_one(input_stream: BinaryIO, output_stream: BinaryIO) -> bool:
    request = read_message(input_stream)
    if request is None:
        return False
    write_message(output_stream, handle_message(request))
    return True


def main() -> int:
    """Run one request for chrome.runtime.sendNativeMessage."""
    if sys.platform == "win32":
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), 0x8000)  # O_BINARY
        msvcrt.setmode(sys.stdout.fileno(), 0x8000)
    try:
        serve_one(sys.stdin.buffer, sys.stdout.buffer)
    except (ValueError, OSError) as exc:
        print(f"No Hack native host protocol error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
