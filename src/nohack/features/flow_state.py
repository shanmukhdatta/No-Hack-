"""Streaming per-flow statistics. Stores no packet payload or packet history."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from nohack.features.flow_schema import (
    FEATURE_SCHEMA_VERSION,
    FeatureValue,
    validate_features,
)
from nohack.features.packet import PacketMeta

NANOSECONDS_PER_MILLISECOND = 1_000_000
NANOSECONDS_PER_SECOND = 1_000_000_000
TRACKED_FLAGS = ("SYN", "ACK", "FIN", "RST", "PSH")


@dataclass(slots=True)
class OnlineStatistics:
    """Population statistics using Welford's stable single-pass algorithm."""

    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    minimum: float = math.inf
    maximum: float = 0.0

    def add(self, value: float) -> None:
        self.count += 1
        difference = value - self.mean
        self.mean += difference / self.count
        self.m2 += difference * (value - self.mean)
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)

    @property
    def std(self) -> float:
        return math.sqrt(max(self.m2 / self.count, 0.0)) if self.count else 0.0

    @property
    def min_or_zero(self) -> float:
        return self.minimum if self.count else 0.0


@dataclass(frozen=True, slots=True)
class FlowContext:
    """Identifiers kept separately from deployable model features."""

    flow_id: str
    src_ip: str
    dst_ip: str
    started_at_ns: int
    ended_at_ns: int


@dataclass(frozen=True, slots=True)
class NoHackFlow:
    """A validated immutable snapshot; model columns are always ordered."""

    context: FlowContext
    features: Mapping[str, FeatureValue]
    feature_schema_version: str = FEATURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        # Snapshot copies prevent mutation of a previously exported record.
        from types import MappingProxyType

        normalized = validate_features(
            self.features, version=self.feature_schema_version
        )
        object.__setattr__(self, "features", MappingProxyType(normalized))

    def to_dict(self) -> dict[str, object]:
        """Use a privacy-auditable explicit boundary for serializable records."""
        from dataclasses import asdict

        return {
            "feature_schema_version": self.feature_schema_version,
            "context": asdict(self.context),
            "features": dict(self.features),
        }


@dataclass(slots=True)
class FlowAccumulator:
    """Aggregate only one first-seen oriented, bidirectional 5-tuple."""

    first: PacketMeta
    _started_ns: int = field(init=False)
    _ended_ns: int = field(init=False)
    _forward_packets: int = field(default=0, init=False)
    _backward_packets: int = field(default=0, init=False)
    _forward_bytes: int = field(default=0, init=False)
    _backward_bytes: int = field(default=0, init=False)
    _lengths: OnlineStatistics = field(default_factory=OnlineStatistics, init=False)
    _forward_lengths: OnlineStatistics = field(
        default_factory=OnlineStatistics, init=False
    )
    _backward_lengths: OnlineStatistics = field(
        default_factory=OnlineStatistics, init=False
    )
    _iats: OnlineStatistics = field(default_factory=OnlineStatistics, init=False)
    _forward_iats: OnlineStatistics = field(
        default_factory=OnlineStatistics, init=False
    )
    _backward_iats: OnlineStatistics = field(
        default_factory=OnlineStatistics, init=False
    )
    _last_forward_ns: int | None = field(default=None, init=False)
    _last_backward_ns: int | None = field(default=None, init=False)
    _flags: dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        self._started_ns = self.first.timestamp_ns
        self._ended_ns = self.first.timestamp_ns
        self._flags = dict.fromkeys(TRACKED_FLAGS, 0)
        self.add(self.first)

    def add(self, packet: PacketMeta) -> None:
        """Ingest in timestamp order; fail rather than silently reorder."""
        forward = (
            packet.src_ip == self.first.src_ip
            and packet.src_port == self.first.src_port
            and packet.dst_ip == self.first.dst_ip
            and packet.dst_port == self.first.dst_port
            and packet.protocol == self.first.protocol
        )
        backward = (
            packet.src_ip == self.first.dst_ip
            and packet.src_port == self.first.dst_port
            and packet.dst_ip == self.first.src_ip
            and packet.dst_port == self.first.src_port
            and packet.protocol == self.first.protocol
        )
        if not (forward or backward):
            raise ValueError("Packet belongs to a different bidirectional flow")
        if packet.timestamp_ns < self._ended_ns:
            raise ValueError("Out-of-order packets require upstream normalization")

        if self._lengths.count:
            self._iats.add(
                (packet.timestamp_ns - self._ended_ns)
                / NANOSECONDS_PER_MILLISECOND
            )
        self._ended_ns = packet.timestamp_ns
        self._lengths.add(float(packet.ip_length_bytes))
        if forward:
            self._forward_packets += 1
            self._forward_bytes += packet.ip_length_bytes
            self._forward_lengths.add(float(packet.ip_length_bytes))
            if self._last_forward_ns is not None:
                self._forward_iats.add(
                    (packet.timestamp_ns - self._last_forward_ns)
                    / NANOSECONDS_PER_MILLISECOND
                )
            self._last_forward_ns = packet.timestamp_ns
        else:
            self._backward_packets += 1
            self._backward_bytes += packet.ip_length_bytes
            self._backward_lengths.add(float(packet.ip_length_bytes))
            if self._last_backward_ns is not None:
                self._backward_iats.add(
                    (packet.timestamp_ns - self._last_backward_ns)
                    / NANOSECONDS_PER_MILLISECOND
                )
            self._last_backward_ns = packet.timestamp_ns

        for flag in TRACKED_FLAGS:
            if flag in packet.tcp_flags:
                self._flags[flag] += 1

    def snapshot(self) -> NoHackFlow:
        """Produce all v1 features from a streaming state at any point."""
        duration_ns = self._ended_ns - self._started_ns
        duration_s = duration_ns / NANOSECONDS_PER_SECOND
        packets = self._forward_packets + self._backward_packets
        byte_count = self._forward_bytes + self._backward_bytes
        def per_second(count: int) -> float:
            return count / duration_s if duration_s > 0 else 0.0

        features: dict[str, object] = {
            "duration_ms": duration_ns / NANOSECONDS_PER_MILLISECOND,
            "protocol": self.first.protocol,
            "src_port": self.first.src_port,
            "dst_port": self.first.dst_port,
            "forward_packet_count": self._forward_packets,
            "backward_packet_count": self._backward_packets,
            "forward_byte_count": self._forward_bytes,
            "backward_byte_count": self._backward_bytes,
            "total_packet_count": packets,
            "total_byte_count": byte_count,
            "forward_packets_per_second": per_second(self._forward_packets),
            "backward_packets_per_second": per_second(self._backward_packets),
            "bytes_per_second": per_second(byte_count),
            "packets_per_second": per_second(packets),
            "packet_length_min": int(self._lengths.min_or_zero),
            "packet_length_max": int(self._lengths.maximum),
            "packet_length_mean": self._lengths.mean,
            "packet_length_std": self._lengths.std,
            "forward_packet_length_mean": self._forward_lengths.mean,
            "backward_packet_length_mean": self._backward_lengths.mean,
            "flow_iat_mean": self._iats.mean,
            "flow_iat_std": self._iats.std,
            "flow_iat_min": self._iats.min_or_zero,
            "flow_iat_max": self._iats.maximum,
            "forward_iat_mean": self._forward_iats.mean,
            "backward_iat_mean": self._backward_iats.mean,
            "syn_count": self._flags["SYN"],
            "ack_count": self._flags["ACK"],
            "fin_count": self._flags["FIN"],
            "rst_count": self._flags["RST"],
            "psh_count": self._flags["PSH"],
            "forward_backward_packet_ratio": (
                self._forward_packets / max(self._backward_packets, 1)
            ),
            "forward_backward_byte_ratio": (
                self._forward_bytes / max(self._backward_bytes, 1)
            ),
        }
        # A deterministic ID is for correlating synthetic/replayed flows, not
        # a secret, session token or anonymization of endpoint metadata.
        identity = (
            f"{self.first.protocol}|{self.first.src_ip}|{self.first.src_port}|"
            f"{self.first.dst_ip}|{self.first.dst_port}|{self._started_ns}"
        )
        context = FlowContext(
            flow_id=hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24],
            src_ip=self.first.src_ip,
            dst_ip=self.first.dst_ip,
            started_at_ns=self._started_ns,
            ended_at_ns=self._ended_ns,
        )
        return NoHackFlow(
            context=context,
            features=validate_features(features),
        )


def replay_packets(
    packets: Iterable[PacketMeta | Mapping[str, Any]],
) -> NoHackFlow:
    """Reference offline adapter; live sources must feed the same add() path."""
    accumulator: FlowAccumulator | None = None
    for packet in packets:
        normalized = (
            packet
            if isinstance(packet, PacketMeta)
            else PacketMeta.from_mapping(dict(packet))
        )
        if accumulator is None:
            accumulator = FlowAccumulator(normalized)
        else:
            accumulator.add(normalized)
    if accumulator is None:
        raise ValueError("At least one packet is needed to create a flow")
    return accumulator.snapshot()
