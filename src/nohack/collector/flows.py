"""Bounded, metadata-only bidirectional flow lifecycle on top of Phase 1."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeAlias

from nohack.features import FlowAccumulator, NoHackFlow, PacketMeta

Endpoint: TypeAlias = tuple[str, int]
FlowKey: TypeAlias = tuple[str, Endpoint, Endpoint]


@dataclass(frozen=True, slots=True)
class FlowLimits:
    idle_timeout_ns: int = 30_000_000_000
    max_lifetime_ns: int = 120_000_000_000
    close_grace_ns: int = 1_000_000_000
    max_active: int = 4096

    def __post_init__(self) -> None:
        for name in ("idle_timeout_ns", "max_lifetime_ns", "max_active"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.close_grace_ns) is not int or self.close_grace_ns < 0:
            raise ValueError("close_grace_ns must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class ProcessContext:
    pid: int
    name: str


@dataclass(frozen=True, slots=True)
class CompletedFlow:
    flow: NoHackFlow
    reason: str
    interface_name: str | None = None
    process: ProcessContext | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            **self.flow.to_dict(),
            "completion_reason": self.reason,
            "interface_name": self.interface_name,
            "process": (
                {"pid": self.process.pid, "name": self.process.name}
                if self.process is not None
                else None
            ),
        }


@dataclass(slots=True)
class FlowCounters:
    ingested: int = 0
    out_of_order: int = 0
    completed: int = 0
    expired: int = 0
    evicted: int = 0


@dataclass(slots=True)
class _Active:
    accumulator: FlowAccumulator
    last_ns: int
    interface_name: str | None
    process: ProcessContext | None
    fin_sides: set[int] = field(default_factory=set)
    close_start_ns: int | None = None
    established: bool = False


def _key(packet: PacketMeta) -> FlowKey:
    src = (packet.src_ip, packet.src_port)
    dst = (packet.dst_ip, packet.dst_port)
    return packet.protocol, min(src, dst), max(src, dst)


def _side(packet: PacketMeta, state: _Active) -> int:
    first = state.accumulator.first
    return int((packet.src_ip, packet.src_port) != (first.src_ip, first.src_port))


class FlowManager:
    """Streaming manager; completed records are returned, never accumulated.

    The caller serializes callbacks, or protects calls with a lock. One accepted
    packet is added exactly once. TCP retransmissions are genuine observations
    and are not deduplicated using unreliable timestamp/length heuristics.
    """

    def __init__(
        self,
        limits: FlowLimits | None = None,
        process_resolver: Callable[[PacketMeta], ProcessContext | None] | None = None,
    ) -> None:
        self.limits = limits or FlowLimits()
        self.process_resolver = process_resolver
        self.active: dict[FlowKey, _Active] = {}
        self.counters = FlowCounters()
        self.watermark_ns = 0

    def _finish(self, key: FlowKey, reason: str) -> CompletedFlow:
        state = self.active.pop(key)
        self.counters.completed += 1
        if reason in {"idle_timeout", "max_lifetime", "tcp_closed"}:
            self.counters.expired += 1
        if reason == "capacity":
            self.counters.evicted += 1
        return CompletedFlow(
            state.accumulator.snapshot(),
            reason,
            state.interface_name,
            state.process,
        )

    def expire(self, now_ns: int) -> list[CompletedFlow]:
        if type(now_ns) is not int or now_ns < 0:
            raise ValueError("now_ns must be a nonnegative integer")
        self.watermark_ns = max(self.watermark_ns, now_ns)
        completed: list[CompletedFlow] = []
        for key, state in list(self.active.items()):
            first = state.accumulator.first.timestamp_ns
            if now_ns - first >= self.limits.max_lifetime_ns:
                completed.append(self._finish(key, "max_lifetime"))
            elif (
                state.close_start_ns is not None
                and now_ns - state.close_start_ns >= self.limits.close_grace_ns
            ):
                completed.append(self._finish(key, "tcp_closed"))
            elif now_ns - state.last_ns >= self.limits.idle_timeout_ns:
                completed.append(self._finish(key, "idle_timeout"))
        return completed

    def ingest(
        self, packet: PacketMeta, interface_name: str | None = None
    ) -> list[CompletedFlow]:
        if not isinstance(packet, PacketMeta):
            raise TypeError("FlowManager accepts only validated PacketMeta")
        self.counters.ingested += 1
        key = _key(packet)
        state = self.active.get(key)
        # Reject packets earlier than the per-flow watermark, not merely
        # earlier than the most recent global event (interleaving is normal).
        if state is not None and packet.timestamp_ns < state.last_ns:
            self.counters.out_of_order += 1
            return []
        if packet.timestamp_ns < self.watermark_ns:
            # Prevent already-expired tuples from reopening as stale sessions.
            self.counters.out_of_order += 1
            return []
        completed = self.expire(packet.timestamp_ns)
        state = self.active.get(key)
        if (
            state is not None
            and packet.protocol == "TCP"
            and "SYN" in packet.tcp_flags
            and "ACK" not in packet.tcp_flags
            and state.established
            and _side(packet, state) == 0
        ):
            completed.append(self._finish(key, "tcp_reuse"))
            state = None
        if state is None:
            if len(self.active) >= self.limits.max_active:
                oldest = min(
                    self.active,
                    key=lambda k: self.active[k].last_ns,
                )
                completed.append(self._finish(oldest, "capacity"))
            process = (
                self.process_resolver(packet)
                if self.process_resolver is not None
                else None
            )
            state = _Active(
                accumulator=FlowAccumulator(packet),
                last_ns=packet.timestamp_ns,
                interface_name=interface_name,
                process=process,
            )
            self.active[key] = state
        else:
            state.accumulator.add(packet)
            state.last_ns = packet.timestamp_ns
            # A SYN retransmission alone does not indicate an established flow.
            if _side(packet, state) == 1 or packet.tcp_flags != frozenset({"SYN"}):
                state.established = True
        if packet.protocol == "TCP":
            if "FIN" in packet.tcp_flags:
                state.fin_sides.add(_side(packet, state))
                if len(state.fin_sides) == 2:
                    state.close_start_ns = packet.timestamp_ns
            if "RST" in packet.tcp_flags:
                completed.append(self._finish(key, "tcp_rst"))
        return completed

    def flush(self) -> list[CompletedFlow]:
        """Drain all active records on shutdown, including half-closed TCP."""
        return [self._finish(key, "shutdown") for key in list(self.active)]
