"""Explicitly score locally stored metadata-only flows using a trusted model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.inference.scoring import score_database



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=Path.home() / ".nohack" / "observations.db")
    parser.add_argument("--max-rows", type=int, default=1000)
    parser.add_argument(
        "--trust-local-bundle", action="store_true",
        help="I generated/verified these joblib files from trusted training code",
    )
    args = parser.parse_args()
    if not args.trust_local_bundle:
        parser.error("Required: --trust-local-bundle (joblib can execute code)")
    print(json.dumps(score_database(args.bundle, args.database, max_rows=args.max_rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
