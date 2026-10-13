"""Unprivileged normalization of packet *metadata*, not payload capture."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Any

from nohack.features.flow_schema import PROTOCOLS

TCP_FLAGS = frozenset({"SYN", "ACK", "FIN", "RST", "PSH", "URG", "ECE", "CWR"})


@dataclass(frozen=True, slots=True)
class PacketMeta:
    """A single network-layer packet's metadata; timestamps use integer ns."""

    timestamp_ns: int
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str
    ip_length_bytes: int
    tcp_flags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if type(self.timestamp_ns) is not int or self.timestamp_ns < 0:
            raise ValueError("timestamp_ns must be a nonnegative integer")
        if type(self.ip_length_bytes) is not int or not (
            1 <= self.ip_length_bytes <= 2**32 - 1
        ):
            raise ValueError("ip_length_bytes must be a positive packet length")

        for field in ("src_port", "dst_port"):
            value = getattr(self, field)
            if type(value) is not int or not (0 <= value <= 65535):
                raise ValueError(f"{field} must be an integer from 0 to 65535")
        for field in ("src_ip", "dst_ip"):
            value = getattr(self, field)
            if not isinstance(value, str):
                raise ValueError(f"{field} must be an IP address string")
            try:
                normalized = str(ipaddress.ip_address(value))
            except ValueError as exc:
                raise ValueError(f"{field} is not a valid IP address") from exc
            object.__setattr__(self, field, normalized)

        if not isinstance(self.protocol, str):
            raise ValueError("protocol must be TCP, UDP, ICMP, or ICMPV6")
        protocol = self.protocol.upper()
        if protocol not in PROTOCOLS:
            raise ValueError("Unsupported IP transport protocol")
        object.__setattr__(self, "protocol", protocol)

        if protocol in {"ICMP", "ICMPV6"} and (self.src_port or self.dst_port):
            raise ValueError("ICMP packets use zero-valued transport ports")

        if isinstance(self.tcp_flags, (str, bytes)):
            raise ValueError("tcp_flags must be a collection, not a string")
        if not isinstance(self.tcp_flags, (tuple, list, set, frozenset)):
            raise ValueError("tcp_flags must be a collection")
        if any(not isinstance(flag, str) for flag in self.tcp_flags):
            raise ValueError("TCP flags must be strings")
        flags = frozenset(flag.upper() for flag in self.tcp_flags)
        if not flags.issubset(TCP_FLAGS):
            raise ValueError("Unsupported TCP flag")
        if protocol != "TCP" and flags:
            raise ValueError("TCP flags cannot occur on other protocols")
        object.__setattr__(self, "tcp_flags", flags)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> PacketMeta:
        """Strict metadata adapter shared by future offline and live sources."""
        required = {
            "timestamp_ns",
            "src_ip",
            "src_port",
            "dst_ip",
            "dst_port",
            "protocol",
            "ip_length_bytes",
        }
        unknown = raw.keys() - (required | {"tcp_flags"})
        missing = required - raw.keys()
        if missing or unknown:
            raise ValueError(
                f"Invalid packet fields: missing={sorted(missing)}, "
                f"unknown={sorted(unknown)}"
            )
        return cls(
            timestamp_ns=raw["timestamp_ns"],
            src_ip=raw["src_ip"],
            src_port=raw["src_port"],
            dst_ip=raw["dst_ip"],
            dst_port=raw["dst_port"],
            protocol=raw["protocol"],
            ip_length_bytes=raw["ip_length_bytes"],
            tcp_flags=raw.get("tcp_flags", frozenset()),
        )
