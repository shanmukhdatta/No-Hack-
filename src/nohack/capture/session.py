"""Explicitly authorized Windows capture session with graceful metadata flush."""

from __future__ import annotations

import importlib
import sys
import threading
import time
from collections.abc import Callable
from typing import Any

from nohack.capture.capabilities import capture_capabilities
from nohack.capture.replay import CaptureError, FlowProcessor
from nohack.collector.flows import CompletedFlow


def list_interfaces() -> list[str]:
    """List Npcap interfaces without starting capture."""
    if sys.platform != "win32":
        raise CaptureError("Live capture is supported only on Windows")
    if not capture_capabilities()["live_capture_ready"]:
        raise CaptureError("Scapy and compatible Npcap are required")
    try:
        scapy = importlib.import_module("scapy.all")
        return sorted(str(name) for name in scapy.get_if_list())
    except (OSError, RuntimeError) as exc:
        raise CaptureError("Could not enumerate Npcap interfaces") from exc


class CaptureSession:
    """No background capture starts until start() is explicitly invoked."""

    def __init__(
        self,
        interface: str,
        processor: FlowProcessor,
        on_record: Callable[[CompletedFlow], None],
    ) -> None:
        if not interface.strip():
            raise ValueError("Provide an explicit interface")
        self.interface = interface
        self.processor = processor
        self.on_record = on_record
        self.delivered = 0
        self._lock = threading.Lock()
        self._sniffer: Any = None
        self._error: str | None = None

    def _emit(self, records: list[CompletedFlow]) -> None:
        for record in records:
            self.on_record(record)
            self.delivered += 1

    def _on_packet(self, packet: Any) -> None:
        with self._lock:
            if self._error is not None:
                return
            try:
                self._emit(self.processor.accept(packet, self.interface))
            except Exception:
                # Deliberately omit packet repr and endpoint details from logs.
                self._error = "Packet processing or output failed"

    def start(self) -> None:
        if self._sniffer is not None:
            raise CaptureError("Capture was already started")
        if not capture_capabilities()["live_capture_ready"]:
            raise CaptureError("Windows capture requires Scapy and Npcap")
        if self.interface not in list_interfaces():
            raise CaptureError("Selected interface is unavailable")
        ready = threading.Event()
        try:
            scapy = importlib.import_module("scapy.all")
            self._sniffer = scapy.AsyncSniffer(
                iface=self.interface,
                filter="ip or ip6",
                prn=self._on_packet,
                store=False,
                started_callback=ready.set,
            )
            self._sniffer.start()
            if not ready.wait(timeout=3.0) or not self._sniffer.running:
                raise CaptureError("Npcap could not start; check driver and permissions")
        except (OSError, RuntimeError, PermissionError, ValueError) as exc:
            self._sniffer = None
            raise CaptureError("Failed to start authorized capture") from exc

    def tick(self, now_ns: int | None = None) -> None:
        with self._lock:
            if self._error:
                raise CaptureError(self._error)
            self._emit(
                self.processor.manager.expire(
                    time.time_ns() if now_ns is None else now_ns
                )
            )
            if self._sniffer is not None and not self._sniffer.running:
                raise CaptureError("Capture ended unexpectedly")

    def stop(self) -> None:
        try:
            if self._sniffer is not None and self._sniffer.running:
                self._sniffer.stop()
        except (OSError, RuntimeError) as exc:
            raise CaptureError("Capture shutdown failed") from exc
        finally:
            with self._lock:
                self._emit(self.processor.finish())
            self._sniffer = None


def capture_for_duration(session: CaptureSession, seconds: float) -> None:
    """Capture for a finite, explicit interval; always drain active flows."""
    if not 0 < seconds <= 300:
        raise ValueError("Duration must be greater than 0 and at most 300 seconds")
    session.start()
    try:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            time.sleep(min(0.2, max(deadline - time.monotonic(), 0.0)))
            session.tick()
    finally:
        session.stop()
