"""Combine only independently verified NoHackFlow datasets, preserving groups.

This tool never converts CICFlowMeter headers or invents attack labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from nohack.datasets.prepare import validate_canonical_table
from nohack.features import FEATURE_NAMES


def combine_sources(inputs: list[tuple[str, Path]], output: Path) -> dict[str, object]:
    if len(inputs) < 2:
        raise ValueError("At least two independent canonical datasets required")
    seen: set[str] = set()
    parts: list[pd.DataFrame] = []
    provenance: list[dict[str, object]] = []
    all_have_family = True
    for source_id, file in inputs:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", source_id) or source_id in seen:
            raise ValueError("Source IDs must be unique and alphanumeric")
        seen.add(source_id)
        if file.suffix.lower() == ".parquet":
            frame = pd.read_parquet(file)
        elif file.suffix.lower() == ".csv":
            frame = pd.read_csv(file)
        else:
            raise ValueError("Only canonical CSV/Parquet supported")
        columns = set(frame.columns)
        expected = set(FEATURE_NAMES) | {"label", "group_id"}
        if (
            frame.empty
            or not expected.issubset(columns)
            or columns - expected - {"attack_family"}
        ):
            raise ValueError(f"Invalid canonical columns for source {source_id}")
        all_have_family = all_have_family and "attack_family" in frame
        frame = frame.copy()
        if (
            frame.group_id.isna().any()
            or not frame.group_id.astype(str).str.strip().all()
        ):
            raise ValueError(f"Missing real group IDs for {source_id}")
        frame["group_id"] = source_id + "::" + frame["group_id"].astype(str)
        parts.append(frame)
        hasher = hashlib.sha256()
        with file.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        provenance.append(
            {
                "source_id": source_id,
                "file_sha256": hasher.hexdigest(),
                "rows": len(frame),
                "groups": int(frame.group_id.nunique()),
            }
        )
    # Never invent a family label for a source lacking verified family annotations.
    if not all_have_family:
        parts = [
            part.drop(columns=["attack_family"], errors="ignore") for part in parts
        ]
    result = validate_canonical_table(pd.concat(parts, ignore_index=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".csv":
        result.to_csv(output, index=False)
    elif output.suffix.lower() == ".parquet":
        result.to_parquet(output, index=False)
    else:
        raise ValueError("Output must be CSV/Parquet")
    report = {
        "status": "combined_schema_validated_not_semantically_certified",
        "rows": len(result),
        "groups": int(result.group_id.nunique()),
        "sources": provenance,
        "attack_family_labels_included": all_have_family,
    }
    (output.parent / (output.stem + ".provenance.json")).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--source", action="append", required=True, metavar="ID=CSV_OR_PARQUET"
    )
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    sources: list[tuple[str, Path]] = []
    for item in args.source:
        if "=" not in item:
            p.error("Expected --source ID=PATH")
        key, path = item.split("=", 1)
        sources.append((key, Path(path)))
    print(json.dumps(combine_sources(sources, args.output), indent=2))


if __name__ == "__main__":
    main()
