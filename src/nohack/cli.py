"""Phase 0 CLI: does not activate capture, APIs, or machine learning."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from nohack import __version__
from nohack.config.logging import configure_logging
from nohack.config.settings import load_settings
from nohack.exceptions import ConfigurationError


def main(argv: Sequence[str] | None = None) -> int:
    """Return an exit code so diagnostics can be tested without subprocesses."""

    parser = argparse.ArgumentParser(
        prog="nohack", description="No Hack local foundation diagnostics"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("doctor", help="Validate configuration and show build status")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    logger = configure_logging(settings)
    logger.info("Foundation diagnostics completed", extra={"event": "doctor"})
    report = {
        "name": "No Hack",
        "version": __version__,
        "phase": 0,
        "status": "foundation-only",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "capture_active": False,
        "model_loaded": False,
        "log_format": settings.log_format,
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "data_dir": str(settings.data_dir),
        "runtime_dir": str(settings.runtime_dir),
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
