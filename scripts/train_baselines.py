"""Compare simple baselines; read only frozen train+validation splits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--splits", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    import pandas as pd

    from nohack.datasets.prepare import _digest
    from nohack.models.baselines import run_baselines

    manifest = json.loads((args.splits / "manifest.json").read_text("utf-8"))
    for name in ("train", "val"):
        if (
            _digest(args.splits / f"{name}.parquet")
            != manifest["splits"][name]["sha256"]
        ):
            raise ValueError("Split checksum mismatch")
    train = pd.read_parquet(args.splits / "train.parquet")
    val = pd.read_parquet(args.splits / "val.parquet")
    result = {
        "validation_only": True,
        "heldout_test_untouched": True,
        "dataset_manifest_sha256": _digest(args.splits / "manifest.json"),
        "models": run_baselines(train, val),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", "utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
