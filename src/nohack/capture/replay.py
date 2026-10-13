"""One canonical normalization pipeline for offline and live packet inputs."""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from nohack.capture.normalizer import normalize_scapy
from nohack.collector.flows import CompletedFlow, FlowManager


class CaptureError(RuntimeError):
    """Capture or replay failed safely."""


class FlowProcessor:
    """Counts rejected packets; retains only bounded metadata flow states."""

    def __init__(self, manager: FlowManager | None = None) -> None:
        self.manager = manager or FlowManager()
        self.skipped = 0
        self.malformed = 0

    def accept(
        self, packet: Any, interface_name: str | None = None
    ) -> list[CompletedFlow]:
        try:
            metadata = normalize_scapy(packet)
        except (ValueError, TypeError, AttributeError):
            self.malformed += 1
            return []
        if metadata is None:
            self.skipped += 1
            return []
        return self.manager.ingest(metadata, interface_name)

    def finish(self) -> list[CompletedFlow]:
        return self.manager.flush()


def replay_pcap(
    path: Path, processor: FlowProcessor | None = None
) -> Iterator[CompletedFlow]:
    """Feed an explicitly supplied PCAP through the shared live adapter."""
    if not path.is_file():
        raise CaptureError("PCAP input must be an existing local file")
    try:
        scapy = importlib.import_module("scapy.all")
    except ImportError as exc:
        raise CaptureError("Install nohack[capture] to enable PCAP replay") from exc
    engine = processor or FlowProcessor()
    try:
        with scapy.PcapReader(str(path)) as reader:
            for packet in reader:
                yield from engine.accept(packet)
    except (OSError, ValueError, EOFError) as exc:
        raise CaptureError("Unable to parse local PCAP") from exc
    yield from engine.finish()
