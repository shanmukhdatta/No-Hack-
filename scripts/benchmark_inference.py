"""Benchmark a trusted locally trained model on provided canonical feature rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.evaluation.latency import benchmark
from nohack.features import FEATURE_NAMES
from nohack.inference.hybrid import load_bundle, predict_features


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--input", type=Path, required=True, help="Canonical CSV/Parquet")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--trust-local-bundle", action="store_true")
    p.add_argument("--max-rows", type=int, default=100)
    args = p.parse_args()
    if not args.trust_local_bundle:
        p.error("Explicit --trust-local-bundle required: joblib may execute code")
    if not 1 <= args.max_rows <= 10000:
        p.error("--max-rows must be 1..10000")
    import pandas as pd

    data = (
        pd.read_parquet(args.input)
        if args.input.suffix.lower() == ".parquet"
        else pd.read_csv(args.input)
        if args.input.suffix.lower() == ".csv"
        else None
    )
    if data is None or not set(FEATURE_NAMES).issubset(data.columns):
        raise ValueError("Input must contain all canonical NoHackFlow features")
    rows = data.loc[:, list(FEATURE_NAMES)].head(args.max_rows).to_dict("records")
    bundle = load_bundle(args.bundle, trust_local_artifact=True)
    result = benchmark(lambda row: predict_features(bundle, row), rows)
    manifest = json.loads((args.bundle / "manifest.json").read_text("utf-8"))
    result.update(
        {
            "model_sha256": manifest["bundle_sha256"],
            "synthetic_demo_only": manifest.get("synthetic_demo_only") is True,
            "label_accuracy_not_measured": True,
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
