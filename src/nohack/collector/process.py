"""Best-effort process context from local socket tables only."""

from __future__ import annotations

import importlib
import time
from typing import Any

from nohack.collector.flows import ProcessContext
from nohack.features import PacketMeta


class ProcessAttributor:
    """Conservative cached socket matching; ambiguous endpoints return None."""

    def __init__(self, cache_seconds: float = 2.0) -> None:
        if cache_seconds <= 0:
            raise ValueError("cache_seconds must be positive")
        self.cache_seconds = cache_seconds
        self._last = -1.0
        self._sockets: list[Any] = []

    def lookup(self, packet: PacketMeta) -> ProcessContext | None:
        try:
            psutil = importlib.import_module("psutil")
        except ImportError:
            return None
        now = time.monotonic()
        if self._last < 0 or now - self._last >= self.cache_seconds:
            try:
                self._sockets = list(psutil.net_connections(kind="inet"))
            except (OSError, RuntimeError, psutil.Error):
                self._sockets = []
            self._last = now
        candidates: set[int] = set()
        for conn in self._sockets:
            if conn.pid is None or not conn.laddr:
                continue
            if packet.protocol not in {"TCP", "UDP"}:
                continue
            if packet.protocol == "TCP" and conn.type != 1:
                continue
            if packet.protocol == "UDP" and conn.type != 2:
                continue
            local = (str(conn.laddr.ip), int(conn.laddr.port))
            src = (packet.src_ip, packet.src_port)
            dst = (packet.dst_ip, packet.dst_port)
            if local not in (src, dst):
                continue
            if conn.raddr:
                remote = (str(conn.raddr.ip), int(conn.raddr.port))
                if remote != (dst if local == src else src):
                    continue
            candidates.add(int(conn.pid))
        if len(candidates) != 1:
            return None
        try:
            pid = next(iter(candidates))
            return ProcessContext(pid=pid, name=str(psutil.Process(pid).name()))
        except (OSError, RuntimeError, ValueError, psutil.Error):
            return None
