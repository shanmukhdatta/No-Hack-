"""Passive Windows capture dependency diagnostics; no capture at import time."""

from __future__ import annotations

import ctypes
import importlib.util
import os
import sys
from pathlib import Path


def _npcap_libraries_loadable() -> bool:
    """Probe standard Npcap and legacy compatibility DLL layouts.

    Npcap normally installs under System32/Npcap. This works without
    requiring Scapy users to enable WinPcap compatibility mode.
    """
    loader = getattr(ctypes, "WinDLL")
    root = os.environ.get("SystemRoot")
    if root:
        directory = Path(root) / "System32" / "Npcap"
        packet_dll = directory / "Packet.dll"
        pcap_dll = directory / "wpcap.dll"
        if packet_dll.is_file() and pcap_dll.is_file():
            try:
                add_dll_directory = getattr(os, "add_dll_directory")
                with add_dll_directory(str(directory)):
                    loader(str(packet_dll))
                    loader(str(pcap_dll))
                return True
            except (OSError, AttributeError):
                pass

    try:
        # For installations opting into legacy WinPcap-compatible paths.
        loader("Packet.dll")
        loader("wpcap.dll")
        return True
    except (OSError, AttributeError):
        return False


def capture_capabilities() -> dict[str, object]:
    """Inspect dependency readiness, not permissions or real capture success."""
    scapy = importlib.util.find_spec("scapy") is not None
    psutil = importlib.util.find_spec("psutil") is not None
    npcap = False
    if sys.platform == "win32":
        try:
            npcap = _npcap_libraries_loadable()
        except AttributeError:
            npcap = False
    return {
        "platform": sys.platform,
        "scapy_installed": scapy,
        "psutil_installed": psutil,
        "npcap_dlls_found": npcap,
        "live_capture_ready": sys.platform == "win32" and scapy and npcap,
        "note": "DLL loading does not prove driver health or interface permissions",
    }
