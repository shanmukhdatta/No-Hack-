"""Audit local public flow CSVs without uploading records or training models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.datasets.csv_audit import audit_csv


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV or CSV folder")
    parser.add_argument("--sample-rows", type=int, default=1000)
    parser.add_argument("--hash-files", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional local report path")
    args = parser.parse_args()

    files = sorted(args.input.rglob("*.csv")) if args.input.is_dir() else [args.input]
    if not files or len(files) > 50:
        parser.error("Expected 1 to 50 CSV files")
    try:
        reports = [
            audit_csv(path, sample_rows=args.sample_rows, hash_file=args.hash_files)
            for path in files
        ]
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    text = json.dumps({"audit_version": 1, "files": reports}, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote metadata-only audit to {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
