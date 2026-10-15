"""Explicitly score locally stored metadata-only flows using a trusted model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.inference.hybrid import load_bundle, predict_features
from nohack.storage.predictions import PredictionStore


def score_database(bundle: Path, database: Path, *, max_rows: int = 1000) -> dict[str, object]:
    if not 1 <= max_rows <= 1_000_000:
        raise ValueError("max_rows must be in 1..1000000")
    model = load_bundle(bundle, trust_local_artifact=True)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    total = 0
    with PredictionStore(database) as store:
        while total < max_rows:
            pending = store.unscored(limit=min(100, max_rows - total))
            if not pending:
                break
            for observation_id, features in pending:
                result = predict_features(model, features)
                store.add(observation_id, result, manifest["bundle_sha256"])
                total += 1
    return {"scored_flows": total, "database": str(database),
            "model_sha256": manifest["bundle_sha256"]}


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
