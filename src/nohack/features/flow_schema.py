"""Versioned model-input contract for metadata-only network flow features."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from typing import TypeAlias

FEATURE_SCHEMA_VERSION = "nohackflow-v1"

# Order is the model-input order; never derive it from a dataset's columns.
FEATURE_SPECS: tuple[tuple[str, str], ...] = (
    ("duration_ms", "float"),
    ("protocol", "category"),
    ("src_port", "int"),
    ("dst_port", "int"),
    ("forward_packet_count", "int"),
    ("backward_packet_count", "int"),
    ("forward_byte_count", "int"),
    ("backward_byte_count", "int"),
    ("total_packet_count", "int"),
    ("total_byte_count", "int"),
    ("forward_packets_per_second", "float"),
    ("backward_packets_per_second", "float"),
    ("bytes_per_second", "float"),
    ("packets_per_second", "float"),
    ("packet_length_min", "int"),
    ("packet_length_max", "int"),
    ("packet_length_mean", "float"),
    ("packet_length_std", "float"),
    ("forward_packet_length_mean", "float"),
    ("backward_packet_length_mean", "float"),
    ("flow_iat_mean", "float"),
    ("flow_iat_std", "float"),
    ("flow_iat_min", "float"),
    ("flow_iat_max", "float"),
    ("forward_iat_mean", "float"),
    ("backward_iat_mean", "float"),
    ("syn_count", "int"),
    ("ack_count", "int"),
    ("fin_count", "int"),
    ("rst_count", "int"),
    ("psh_count", "int"),
    ("forward_backward_packet_ratio", "float"),
    ("forward_backward_byte_ratio", "float"),
)
FEATURE_NAMES: tuple[str, ...] = tuple(name for name, _ in FEATURE_SPECS)
FEATURE_TYPES: dict[str, str] = dict(FEATURE_SPECS)
PROTOCOLS = frozenset({"TCP", "UDP", "ICMP", "ICMPV6"})
CONTEXT_NOT_MODEL_INPUTS: tuple[str, ...] = (
    "flow_id",
    "src_ip",
    "dst_ip",
    "started_at_ns",
    "ended_at_ns",
    "process_id",
    "process_name",
    "interface_name",
)
FeatureValue: TypeAlias = int | float | str


class FlowSchemaError(ValueError):
    """Flow features do not satisfy the contract required for model inputs."""


def schema_manifest() -> dict[str, object]:
    """Provide a JSON-compatible manifest without depending on ML libraries."""
    return {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "feature_types": dict(FEATURE_SPECS),
        "context_not_model_inputs": list(CONTEXT_NOT_MODEL_INPUTS),
    }


def schema_fingerprint() -> str:
    """SHA-256 of a stable representation of the feature contract."""
    encoded = json.dumps(
        schema_manifest(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_features(
    values: Mapping[str, object], *, version: str = FEATURE_SCHEMA_VERSION
) -> dict[str, FeatureValue]:
    """Reject missing, unknown or invalid columns; project into canonical order."""
    if version != FEATURE_SCHEMA_VERSION:
        raise FlowSchemaError(f"Unsupported feature schema version: {version!r}")
    if not isinstance(values, Mapping):
        raise FlowSchemaError("Feature vector must be a mapping")
    missing = set(FEATURE_NAMES) - values.keys()
    unknown = values.keys() - set(FEATURE_NAMES)
    if missing or unknown:
        raise FlowSchemaError(
            f"Feature names differ: missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )

    ordered: dict[str, FeatureValue] = {}
    for name, dtype in FEATURE_SPECS:
        value = values[name]
        if dtype == "category":
            if not isinstance(value, str) or value not in PROTOCOLS:
                raise FlowSchemaError(f"{name} must be a supported protocol")
            ordered[name] = value
        elif dtype == "int":
            if type(value) is not int or value < 0:
                raise FlowSchemaError(f"{name} must be a nonnegative integer")
            if name in {"src_port", "dst_port"} and value > 65535:
                raise FlowSchemaError(f"{name} must be <= 65535")
            ordered[name] = value
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise FlowSchemaError(f"{name} must be numeric")
            try:
                number = float(value)
            except (OverflowError, ValueError) as exc:
                raise FlowSchemaError(f"{name} must be finite") from exc
            if not math.isfinite(number) or number < 0:
                raise FlowSchemaError(f"{name} must be finite and nonnegative")
            ordered[name] = number
    return ordered


def ordered_feature_values(
    values: Mapping[str, object], *, version: str = FEATURE_SCHEMA_VERSION
) -> tuple[FeatureValue, ...]:
    """Stable ordered projection for future preprocessing and inference."""
    return tuple(validate_features(values, version=version).values())
