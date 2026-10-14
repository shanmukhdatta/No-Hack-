"""Bounded Phase 3 observation lifecycle; no invented threat classifier."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from nohack.capture.replay import FlowProcessor
from nohack.collector.flows import CompletedFlow


@dataclass(slots=True)
class RuntimeCounters:
    emitted: int = 0
    dropped_due_to_backpressure: int = 0
    stopped: bool = False


class ObservationRuntime:
    """Own a flow processor and bounded delivery queue.

    The caller must serialize calls. No packet payload or unbounded packet
    history is kept. Overflow is explicitly counted rather than hidden.
    """

    def __init__(self, max_pending: int = 256, processor: FlowProcessor | None = None):
        if type(max_pending) is not int or max_pending <= 0:
            raise ValueError("max_pending must be a positive integer")
        self.processor = processor or FlowProcessor()
        self.max_pending = max_pending
        self._pending: deque[CompletedFlow] = deque()
        self.counters = RuntimeCounters()

    def _accept(self, records: list[CompletedFlow]) -> None:
        for record in records:
            if len(self._pending) == self.max_pending:
                self.counters.dropped_due_to_backpressure += 1
                continue
            self._pending.append(record)
            self.counters.emitted += 1

    def accept(self, packet: Any, interface_name: str | None = None) -> None:
        if self.counters.stopped:
            raise RuntimeError("Runtime is stopped")
        self._accept(self.processor.accept(packet, interface_name))

    def tick(self, timestamp_ns: int) -> None:
        if self.counters.stopped:
            raise RuntimeError("Runtime is stopped")
        self._accept(self.processor.manager.expire(timestamp_ns))

    def drain(self) -> list[CompletedFlow]:
        records = list(self._pending)
        self._pending.clear()
        return records

    def stop(self) -> list[CompletedFlow]:
        if not self.counters.stopped:
            self._accept(self.processor.finish())
            self.counters.stopped = True
        return self.drain()

    def health(self) -> dict[str, int | bool]:
        counters = self.processor.manager.counters
        return {
            "stopped": self.counters.stopped,
            "active_flows": len(self.processor.manager.active),
            "pending_flows": len(self._pending),
            "emitted": self.counters.emitted,
            "dropped_due_to_backpressure": self.counters.dropped_due_to_backpressure,
            "packet_malformed": self.processor.malformed,
            "packet_skipped": self.processor.skipped,
            "packets_out_of_order": counters.out_of_order,
            "model_loaded": False,
            "classification_active": False,
        }
