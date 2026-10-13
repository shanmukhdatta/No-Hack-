"""Minimal structured logging with a privacy-conscious allowlist."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from nohack.config.settings import Settings, load_settings


class JsonFormatter(logging.Formatter):
    """Only approved log attributes are serialized, not arbitrary extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, str] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("event", "component"):
            value = getattr(record, key, None)
            if isinstance(value, str):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings | None = None) -> logging.Logger:
    """Configure only the No Hack logger; never modify the root logger."""

    current = load_settings() if settings is None else settings
    logger = logging.getLogger("nohack")
    logger.setLevel(current.log_level)
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    handler = logging.StreamHandler()
    if current.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    return logger
