"""Report unlabeled numeric drift for *canonical* NoHackFlow CSV/Parquet tables."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.features import FEATURE_NAMES
from nohack.monitoring.drift import numeric_drift_report


def read_frame(path: Path):
    import pandas as pd

    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError("Input must be CSV or Parquet")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", required=True, type=Path)
    p.add_argument("--current", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    ref, cur = read_frame(args.reference), read_frame(args.current)
    numeric = [x for x in FEATURE_NAMES if x != "protocol"]
    for df in (ref, cur):
        if not set(FEATURE_NAMES).issubset(df.columns):
            raise ValueError("Only canonical NoHackFlow features are allowed")
    report = numeric_drift_report(
        {k: ref[k].to_numpy() for k in numeric},
        {k: cur[k].to_numpy() for k in numeric},
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"warning_count": report["warning_count"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
