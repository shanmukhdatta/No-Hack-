"""CLI smoke tests; no privilege or network required."""

import json

from pytest import CaptureFixture, MonkeyPatch

from nohack import __version__
from nohack.cli import main


def test_doctor_does_not_claim_a_live_detector(
    capsys: CaptureFixture[str], monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setenv("NOHACK_LOG_LEVEL", "INFO")
    monkeypatch.setenv("NOHACK_API_HOST", "127.0.0.1")
    assert main(["doctor"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["version"] == __version__
    assert output["status"] == "foundation-only"
    assert not output["capture_active"]
    assert not output["model_loaded"]


def test_invalid_configuration_exit_code(
    capsys: CaptureFixture[str], monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setenv("NOHACK_API_HOST", "0.0.0.0")
    assert main(["doctor"]) == 2
    assert "Configuration error" in capsys.readouterr().err


def test_help_when_no_command(capsys: CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "doctor" in capsys.readouterr().out
