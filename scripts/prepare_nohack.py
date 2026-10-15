"""CLI to freeze group-safe canonical NoHackFlow partitions."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from nohack.datasets.prepare import prepare_dataset


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True,help="VERIFIED canonical labeled flow CSV or Parquet")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=42)
    args=p.parse_args()
    result=prepare_dataset(args.input,args.output,seed=args.seed)
    print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
