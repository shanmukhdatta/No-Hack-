"""Optional capture dependency diagnostics; importing this never starts capture."""

from __future__ import annotations

import ctypes
import importlib.util
import sys


def capture_capabilities() -> dict[str, object]:
    """Check availability, not permission or real capture success."""
    scapy = importlib.util.find_spec("scapy") is not None
    psutil = importlib.util.find_spec("psutil") is not None
    npcap = False
    if sys.platform == "win32":
        try:
            ctypes.WinDLL("wpcap.dll")  # type: ignore[attr-defined]
            ctypes.WinDLL("Packet.dll")  # type: ignore[attr-defined]
            npcap = True
        except (OSError, AttributeError):
            pass
    return {
        "platform": sys.platform,
        "scapy_installed": scapy,
        "psutil_installed": psutil,
        "npcap_dlls_found": npcap,
        "live_capture_ready": sys.platform == "win32" and scapy and npcap,
        "note": "DLL presence cannot guarantee authorization or interface access",
    }
