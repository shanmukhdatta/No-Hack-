"""Structured logging emits only allowlisted metadata."""

import json
import logging

from pytest import CaptureFixture

from nohack.config.logging import configure_logging
from nohack.config.settings import Settings


def test_json_logging_and_no_sensitive_extras(capsys: CaptureFixture[str]) -> None:
    logger = configure_logging(Settings())
    logger.info(
        "collector idle",
        extra={"event": "collector.idle", "packet_payload": "SECRET_PAYLOAD"},
    )
    captured = capsys.readouterr()
    parsed = json.loads(captured.err)
    assert parsed["level"] == "INFO"
    assert parsed["event"] == "collector.idle"
    assert parsed["message"] == "collector idle"
    assert "SECRET_PAYLOAD" not in captured.err
    assert parsed["timestamp"].endswith("+00:00")


def test_logging_reconfiguration_does_not_duplicate(
    capsys: CaptureFixture[str],
) -> None:
    logger = configure_logging(Settings(log_format="text"))
    assert configure_logging(Settings(log_format="text")) is logger
    assert len(logger.handlers) == 1
    logger.warning("a single record")
    captured = capsys.readouterr()
    assert captured.err.count("a single record") == 1
    assert captured.err.startswith("WARNING nohack: ")


def test_does_not_modify_root_logger() -> None:
    root = logging.getLogger()
    before = tuple(root.handlers)
    configure_logging(Settings())
    assert tuple(root.handlers) == before
