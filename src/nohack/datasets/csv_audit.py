"""Conservative metadata-only audit for public labelled flow CSV files.

Header overlap is NOT proof of equivalence to NoHackFlow model features.
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from itertools import islice
from pathlib import Path

from nohack.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, schema_fingerprint


def sha256_file(path: Path) -> str:
    """Compute an optional content fingerprint without retaining dataset rows."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_csv(
    path: Path, *, sample_rows: int = 1000, hash_file: bool = False
) -> dict[str, object]:
    """Inspect labels and headers only; never train or infer a feature mapping."""
    if type(sample_rows) is not int or not 1 <= sample_rows <= 100_000:
        raise ValueError("sample_rows must be an integer from 1 to 100000")
    if not path.is_file() or path.suffix.lower() != ".csv":
        raise ValueError("input must be an existing CSV file")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader, None)
            if not header or not any(value.strip() for value in header):
                raise ValueError("CSV must have a nonempty header")
            names = [name.strip() for name in header]
            normalized = [name.casefold() for name in names]
            duplicates = sorted(
                {name for name in normalized if normalized.count(name) > 1}
            )
            label_indices = [i for i, name in enumerate(normalized) if name == "label"]
            labels: Counter[str] = Counter()
            sampled = 0
            malformed_width = 0
            for row in islice(reader, sample_rows):
                sampled += 1
                if len(row) != len(names):
                    malformed_width += 1
                    continue
                if len(label_indices) == 1:
                    labels[row[label_indices[0]].strip()] += 1
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("CSV decoding or parsing failed") from exc

    return {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "file_sha256": sha256_file(path) if hash_file else None,
        "schema_version_target": FEATURE_SCHEMA_VERSION,
        "schema_sha256_target": schema_fingerprint(),
        "required_feature_count": len(FEATURE_NAMES),
        "csv_column_count": len(names),
        "csv_headers": names,
        "duplicate_normalized_headers": duplicates,
        "label_column_count": len(label_indices),
        "sampled_rows": sampled,
        "sampled_malformed_width_rows": malformed_width,
        "sampled_labels": dict(sorted(labels.items())),
        "exact_header_overlap_only": sorted(set(names) & set(FEATURE_NAMES)),
        "deployable_mapping_verified": False,
        "caution": (
            "Header names do not establish feature semantics, units, packet length "
            "definitions, flow lifetime or direction equivalence. NoHackFlow "
            "training requires separately reviewed, validated feature mapping."
        ),
    }
