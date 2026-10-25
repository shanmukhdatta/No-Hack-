"""Launch the optional No Hack API strictly on loopback."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database", type=Path, default=Path.home() / ".nohack" / "observations.db"
    )
    parser.add_argument("--model", type=Path)
    parser.add_argument("--trust-local-model", action="store_true")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be an unprivileged TCP port")
    import uvicorn

    from nohack.api.app import create_app

    app = create_app(
        args.database, args.model, trust_local_model=args.trust_local_model
    )
    uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
