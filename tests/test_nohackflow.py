"""Canonical flow statistics and synthetic offline/streaming parity."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from nohack.features import (
    FEATURE_NAMES,
    FlowAccumulator,
    FlowSchemaError,
    PacketMeta,
    ordered_feature_values,
    replay_packets,
    schema_fingerprint,
    schema_manifest,
    validate_features,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "nohackflow_tcp_v1.json"


def packets() -> list[dict[str, object]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_manifest_matches_source_and_excludes_endpoint_identity() -> None:
    manifest = json.loads(
        (ROOT / "configs" / "nohackflow-v1.json").read_text(encoding="utf-8")
    )
    assert manifest == schema_manifest()
    assert len(FEATURE_NAMES) == 33
    assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES))
    assert set(manifest["context_not_model_inputs"]).isdisjoint(FEATURE_NAMES)
    assert len(schema_fingerprint()) == 64


def test_bidirectional_tcp_expected_statistics() -> None:
    flow = replay_packets(packets())
    f = flow.features
    expected = {
        "duration_ms": 400.0,
        "protocol": "TCP",
        "src_port": 51000,
        "dst_port": 443,
        "forward_packet_count": 2,
        "backward_packet_count": 2,
        "forward_byte_count": 140,
        "backward_byte_count": 220,
        "total_packet_count": 4,
        "total_byte_count": 360,
        "forward_packets_per_second": 5.0,
        "backward_packets_per_second": 5.0,
        "bytes_per_second": 900.0,
        "packets_per_second": 10.0,
        "packet_length_min": 60,
        "packet_length_max": 120,
        "packet_length_mean": 90.0,
        "packet_length_std": math.sqrt(500),
        "forward_packet_length_mean": 70.0,
        "backward_packet_length_mean": 110.0,
        "flow_iat_mean": 400 / 3,
        "flow_iat_std": math.sqrt(20000 / 9),
        "flow_iat_min": 100.0,
        "flow_iat_max": 200.0,
        "forward_iat_mean": 200.0,
        "backward_iat_mean": 300.0,
        "syn_count": 2,
        "ack_count": 3,
        "fin_count": 1,
        "rst_count": 0,
        "psh_count": 1,
        "forward_backward_packet_ratio": 1.0,
        "forward_backward_byte_ratio": 140 / 220,
    }
    assert tuple(f) == FEATURE_NAMES
    for name, value in expected.items():
        if isinstance(value, float):
            assert f[name] == pytest.approx(value), name
        else:
            assert f[name] == value, name
    assert flow.context.src_ip == "192.0.2.10"
    assert "src_ip" not in f
    assert json.loads(json.dumps(flow.to_dict(), allow_nan=False)) == flow.to_dict()


def test_replay_and_incremental_snapshots_are_identical() -> None:
    rows = packets()
    streaming = FlowAccumulator(PacketMeta.from_mapping(rows[0]))
    for count in range(1, len(rows) + 1):
        if count > 1:
            streaming.add(PacketMeta.from_mapping(rows[count - 1]))
        assert streaming.snapshot().to_dict() == replay_packets(rows[:count]).to_dict()
    assert replay_packets(rows).to_dict() == replay_packets(rows).to_dict()


def test_snapshot_is_immutable_and_direction_is_first_seen() -> None:
    rows = packets()
    stream = FlowAccumulator(PacketMeta.from_mapping(rows[0]))
    previous = stream.snapshot()
    stream.add(PacketMeta.from_mapping(rows[1]))
    assert previous.features["total_packet_count"] == 1
    with pytest.raises(TypeError):
        previous.features["total_packet_count"] = 9  # type: ignore[index]
    reverse_first = FlowAccumulator(PacketMeta.from_mapping(rows[1]))
    assert reverse_first.snapshot().features["src_port"] == 443


def test_zero_elapsed_time_and_zero_denominator_are_finite() -> None:
    packet = PacketMeta.from_mapping(packets()[0])
    state = FlowAccumulator(packet)
    state.add(packet)
    f = state.snapshot().features
    assert f["duration_ms"] == 0.0
    assert f["packets_per_second"] == 0.0
    assert f["bytes_per_second"] == 0.0
    assert f["flow_iat_mean"] == 0.0
    assert f["forward_backward_packet_ratio"] == 2.0
    assert f["forward_backward_byte_ratio"] == 120.0


@pytest.mark.parametrize(
    ("name", "bad"),
    [
        ("src_port", -1),
        ("src_port", 65536),
        ("src_port", True),
        ("forward_packet_count", 1.2),
        ("forward_packet_count", True),
        ("packet_length_std", float("inf")),
        ("packet_length_mean", float("nan")),
        ("bytes_per_second", -0.5),
        ("protocol", "NOT_A_PROTOCOL"),
        ("protocol", 6),
    ],
)
def test_feature_validator_rejects_bad_values(name: str, bad: object) -> None:
    features: dict[str, object] = dict(replay_packets(packets()).features)
    features[name] = bad
    with pytest.raises(FlowSchemaError):
        validate_features(features)


def test_feature_contract_rejects_missing_extra_and_wrong_version() -> None:
    values: dict[str, object] = dict(replay_packets(packets()).features)
    with pytest.raises(FlowSchemaError, match="missing"):
        validate_features({k: v for k, v in values.items() if k != "src_port"})
    with pytest.raises(FlowSchemaError, match="unknown"):
        validate_features({**values, "nsl_kdd_service": "ftp"})
    with pytest.raises(FlowSchemaError, match="version"):
        validate_features(values, version="nohackflow-v999")
    reversed_values = dict(reversed(list(values.items())))
    assert ordered_feature_values(reversed_values) == tuple(values.values())


@pytest.mark.parametrize(
    ("name", "bad"),
    [
        ("timestamp_ns", -1),
        ("timestamp_ns", 1.25),
        ("src_ip", "invalid"),
        ("dst_ip", "1.1.1.999"),
        ("src_port", -1),
        ("dst_port", 65536),
        ("src_port", True),
        ("protocol", "FTP"),
        ("ip_length_bytes", 0),
        ("tcp_flags", "SYN"),
        ("tcp_flags", ["INVALID"]),
    ],
)
def test_packet_normalizer_rejects_bad_metadata(name: str, bad: object) -> None:
    row = packets()[0]
    row[name] = bad
    with pytest.raises(ValueError):
        PacketMeta.from_mapping(row)


def test_packet_adapters_fail_on_invalid_unknown_or_mixed_data() -> None:
    rows = packets()
    with pytest.raises(ValueError, match="unknown"):
        PacketMeta.from_mapping({**rows[0], "payload": "not allowed"})
    with pytest.raises(ValueError, match="missing"):
        PacketMeta.from_mapping({k: v for k, v in rows[0].items() if k != "src_ip"})
    with pytest.raises(ValueError, match="TCP flags"):
        PacketMeta.from_mapping({**rows[0], "protocol": "UDP"})
    with pytest.raises(ValueError, match="zero-valued"):
        PacketMeta.from_mapping({**rows[0], "protocol": "ICMP", "tcp_flags": []})
    with pytest.raises(ValueError, match="Out-of-order"):
        replay_packets([rows[2], rows[0]])
    other = dict(rows[1])
    other["dst_port"] = 50000
    with pytest.raises(ValueError, match="different"):
        replay_packets([rows[0], other])
    with pytest.raises(ValueError, match="At least one"):
        replay_packets([])


def test_ipv6_udp_and_directional_empty_statistics() -> None:
    raw = {
        "timestamp_ns": 30,
        "src_ip": "2001:0DB8::0001",
        "dst_ip": "2001:db8::2",
        "src_port": 1234,
        "dst_port": 53,
        "protocol": "udp",
        "ip_length_bytes": 60,
    }
    packet = PacketMeta.from_mapping(raw)
    assert packet.src_ip == "2001:db8::1"
    assert packet.protocol == "UDP"
    flow = replay_packets([packet])
    assert flow.features["backward_packet_length_mean"] == 0.0
    assert flow.features["flow_iat_std"] == 0.0
    assert flow.features["flow_iat_min"] == 0.0
    assert flow.features["backward_iat_mean"] == 0.0
    assert flow.features["syn_count"] == 0
    assert flow.features["forward_backward_byte_ratio"] == 60.0


def test_tcp_flags_count_each_packet_once() -> None:
    row = packets()[0]
    row["tcp_flags"] = ["SYN", "ACK", "ACK"]
    flow = replay_packets([row])
    assert flow.features["syn_count"] == 1
    assert flow.features["ack_count"] == 1
