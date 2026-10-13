"""Side-effect-free, environment-based Phase 0 configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from nohack.exceptions import ConfigurationError

_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_LOG_FORMATS = frozenset({"json", "text"})
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated application defaults; paths are not created during loading."""

    log_level: str = "INFO"
    log_format: str = "json"
    data_dir: Path = Path("data")
    runtime_dir: Path = Path("runtime")
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    def __post_init__(self) -> None:
        if self.log_level not in _LOG_LEVELS:
            raise ConfigurationError("NOHACK_LOG_LEVEL must be a standard log level")
        if self.log_format not in _LOG_FORMATS:
            raise ConfigurationError("NOHACK_LOG_FORMAT must be json or text")
        if self.api_host not in _LOOPBACK_HOSTS:
            raise ConfigurationError("NOHACK_API_HOST must be a loopback address")
        if not 1 <= self.api_port <= 65535:
            raise ConfigurationError("NOHACK_API_PORT must be between 1 and 65535")
        if not str(self.data_dir).strip() or not str(self.runtime_dir).strip():
            raise ConfigurationError("Data and runtime paths must not be empty")


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Load NOHACK_* values without reading files or creating directories."""

    env = os.environ if environ is None else environ
    port_text = env.get("NOHACK_API_PORT", "8000")
    try:
        port = int(port_text)
    except ValueError as exc:
        raise ConfigurationError("NOHACK_API_PORT must be an integer") from exc
    for key in ("NOHACK_DATA_DIR", "NOHACK_RUNTIME_DIR"):
        if key in env and not env[key].strip():
            raise ConfigurationError(f"{key} must not be empty")
    return Settings(
        log_level=env.get("NOHACK_LOG_LEVEL", "INFO").upper(),
        log_format=env.get("NOHACK_LOG_FORMAT", "json").lower(),
        data_dir=Path(env.get("NOHACK_DATA_DIR", "data")),
        runtime_dir=Path(env.get("NOHACK_RUNTIME_DIR", "runtime")),
        api_host=env.get("NOHACK_API_HOST", "127.0.0.1"),
        api_port=port,
    )
