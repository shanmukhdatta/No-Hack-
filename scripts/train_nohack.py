"""Train No Hack hybrid stack on verified canonical Parquet splits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.training.hybrid import train_from_splits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--folds", type=int, default=4)
    parser.add_argument("--max-fpr", type=float, default=0.02)
    args = parser.parse_args()
    result = train_from_splits(
        args.data,
        args.output,
        seed=args.seed,
        folds=args.folds,
        max_false_positive_rate=args.max_fpr,
    )
    print(json.dumps(result["metrics"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
