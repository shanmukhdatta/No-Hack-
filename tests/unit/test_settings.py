"""Settings validation and absence of unintended filesystem operations."""

from pathlib import Path

import pytest

from nohack.config.settings import Settings, load_settings
from nohack.exceptions import ConfigurationError


def test_safe_defaults_are_stable() -> None:
    settings = load_settings({})
    assert settings == Settings()
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000


def test_environment_overrides(tmp_path: Path) -> None:
    storage = tmp_path / "new-data"
    settings = load_settings(
        {
            "NOHACK_LOG_LEVEL": "debug",
            "NOHACK_LOG_FORMAT": "TEXT",
            "NOHACK_API_PORT": "8123",
            "NOHACK_DATA_DIR": str(storage),
            "NOHACK_RUNTIME_DIR": str(tmp_path / "new-runtime"),
        }
    )
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "text"
    assert settings.api_port == 8123
    assert settings.data_dir == storage
    assert not storage.exists()
    assert not settings.runtime_dir.exists()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("NOHACK_LOG_LEVEL", "VERBOSE"),
        ("NOHACK_LOG_FORMAT", "xml"),
        ("NOHACK_API_HOST", "0.0.0.0"),
        ("NOHACK_API_HOST", "example.com"),
        ("NOHACK_API_PORT", "0"),
        ("NOHACK_API_PORT", "65536"),
        ("NOHACK_API_PORT", "abc"),
        ("NOHACK_DATA_DIR", " "),
        ("NOHACK_RUNTIME_DIR", ""),
    ],
)
def test_invalid_configuration_is_rejected(key: str, value: str) -> None:
    with pytest.raises(ConfigurationError):
        load_settings({key: value})


def test_loopback_ipv6_is_accepted() -> None:
    assert load_settings({"NOHACK_API_HOST": "::1"}).api_host == "::1"
