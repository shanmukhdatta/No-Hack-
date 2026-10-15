"""Prepare *canonical*, labeled NoHackFlow records without training-serving skew.

Do not feed CICFlowMeter CSVs directly: matching names do not prove matching semantics.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from nohack.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, schema_fingerprint

ALLOWED_LABEL_COLUMNS = ("label", "group_id", "attack_family")
NUMERIC_FIELDS = tuple(x for x in FEATURE_NAMES if x != "protocol")
PROTOCOLS = {"TCP", "UDP", "ICMP", "ICMPV6"}


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    raise ValueError("Only canonical CSV/Parquet inputs are supported")


def validate_canonical_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Require precisely NoHackFlow inputs plus provenance/labels (no IPs)."""
    required = set(FEATURE_NAMES) | {"label", "group_id"}
    unknown = set(frame.columns) - required - {"attack_family"}
    missing = required - set(frame.columns)
    if unknown or missing or frame.columns.duplicated().any():
        raise ValueError(f"Schema mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}")
    if frame.empty:
        raise ValueError("Dataset is empty")
    result = frame.copy()
    if result["protocol"].isna().any() or not result["protocol"].isin(PROTOCOLS).all():
        raise ValueError("Invalid protocol values")
    if result[["label", "group_id"]].isna().any().any():
        raise ValueError("Every observation needs a label and independent split_group")
    if not result["label"].map(lambda x: isinstance(x, str) and bool(x.strip())).all():
        raise ValueError("Labels must be nonempty strings")
    if not result["group_id"].map(lambda x: isinstance(x, str) and bool(x.strip())).all():
        raise ValueError("group_id must be a nonempty provenance string")
    if "attack_family" in result and result["attack_family"].isna().any():
        raise ValueError("attack_family cannot have null values")
    import numpy as np

    for col in NUMERIC_FIELDS:
        values = pd.to_numeric(result[col], errors="coerce")
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f"Invalid/nonfinite numeric feature: {col}")
        if col.endswith("_port") and (values > 65535).any():
            raise ValueError(f"Invalid port: {col}")
        result[col] = values
    if (result["label"].str.strip().str.upper() == "BENIGN").sum() == 0:
        raise ValueError("At least one verified BENIGN flow required")
    if (result["label"].str.strip().str.upper() != "BENIGN").sum() == 0:
        raise ValueError("At least one labeled attack class required")
    return result[[*FEATURE_NAMES, "label", "group_id", *([ "attack_family" ] if "attack_family" in result else [])]]


def prepare_dataset(
    source: Path, target: Path, *, seed: int = 42,
    test_fraction: float = 0.20, val_fraction: float = 0.20,
) -> dict[str, object]:
    """Freeze group-disjoint train/validation/test partitions and provenance."""
    if not (0 < test_fraction < 0.5 and 0 < val_fraction < 0.5):
        raise ValueError("Test and validation fractions must be between zero and 0.5")
    frame = validate_canonical_table(_read(source))
    if frame["group_id"].nunique() < 8:
        raise ValueError("Require >=8 independent scenario/host/time groups")
    group_split = GroupShuffleSplit(n_splits=1, test_size=test_fraction, random_state=seed)
    a, test_idx = next(group_split.split(frame, groups=frame["group_id"]))
    train_val = frame.iloc[a]
    remaining_val_fraction = val_fraction / (1 - test_fraction)
    sub = GroupShuffleSplit(n_splits=1, test_size=remaining_val_fraction, random_state=seed+1)
    tr, va = next(sub.split(train_val, groups=train_val["group_id"]))
    splits = {
        "train": train_val.iloc[tr].reset_index(drop=True),
        "val": train_val.iloc[va].reset_index(drop=True),
        "test": frame.iloc[test_idx].reset_index(drop=True),
    }
    for name, df in splits.items():
        labels = df["label"].str.strip().str.upper().ne("BENIGN")
        if labels.nunique() != 2:
            raise ValueError(f"{name} has only one binary class; collect more independent groups")
    for x in splits:
        for y in splits:
            if x != y and set(splits[x]["group_id"]) & set(splits[y]["group_id"]):
                raise RuntimeError("Group leakage detected")
    # Exact duplicate feature vectors can leak across provenance groups.
    feature_hashes = {
        name: set(pd.util.hash_pandas_object(df[list(FEATURE_NAMES)], index=False).tolist())
        for name, df in splits.items()
    }
    collision_counts = {
        "train_val": len(feature_hashes["train"] & feature_hashes["val"]),
        "train_test": len(feature_hashes["train"] & feature_hashes["test"]),
        "val_test": len(feature_hashes["val"] & feature_hashes["test"]),
    }
    if any(collision_counts.values()):
        raise ValueError(
            f"Exact feature-vector overlap across splits: {collision_counts}. "
            "Investigate duplicate scenarios and split provenance."
        )
    target.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "format_version": 1, "feature_schema": FEATURE_SCHEMA_VERSION,
        "feature_schema_sha256": schema_fingerprint(),
        "source_filename": source.name, "source_sha256": _digest(source),
        "seed": seed, "test_fraction": test_fraction,
        "val_fraction": val_fraction, "split_strategy": "group_shuffle_no_overlap",
        "splits": {},
    }
    for name, df in splits.items():
        file = target / f"{name}.parquet"
        df.to_parquet(file, index=False)
        manifest["splits"][name] = {
            "file": file.name, "sha256": _digest(file), "rows": len(df),
            "groups": int(df["group_id"].nunique()),
            "labels": df["label"].value_counts().to_dict(),
        }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n",encoding="utf-8")
    return manifest
