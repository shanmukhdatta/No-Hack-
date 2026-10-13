"""Scapy-to-PacketMeta adapter; never retains application payload bytes."""

from __future__ import annotations

import importlib
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any

from nohack.features import PacketMeta

_TCP_BITS = (
    ("FIN", 0x01),
    ("SYN", 0x02),
    ("RST", 0x04),
    ("PSH", 0x08),
    ("ACK", 0x10),
    ("URG", 0x20),
    ("ECE", 0x40),
    ("CWR", 0x80),
)


def normalize_scapy(packet: Any) -> PacketMeta | None:
    """Normalize one network-layer packet using the Phase 1 metadata contract.

    All source adapters use the same implementation. IPv4/IPv6 fragment
    packets, tunnels, non-IP and unsupported transports are intentionally
    skipped rather than incorrectly interpreted as ordinary TCP/UDP flows.
    """
    try:
        scapy = importlib.import_module("scapy.all")
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional capture extra: nohack[capture]"
        ) from exc

    network = packet
    for _ in range(16):
        if isinstance(network, (scapy.IP, scapy.IPv6)):
            break
        network = getattr(network, "payload", None)
        if network is None:
            return None
    else:
        return None
    ip4 = network if isinstance(network, scapy.IP) else None
    ip6 = network if isinstance(network, scapy.IPv6) else None
    if ip4 is not None:
        if int(ip4.frag) != 0 or int(ip4.flags) & 1:
            return None
        network = ip4
        transport = ip4.payload
        src_ip, dst_ip = str(ip4.src), str(ip4.dst)
        length = int(ip4.len) if ip4.len is not None else len(bytes(ip4))
        ipv6 = False
    elif ip6 is not None:
        if packet.haslayer(scapy.IPv6ExtHdrFragment):
            return None
        network = ip6
        transport = ip6.payload
        allowed = (
            scapy.IPv6ExtHdrHopByHop,
            scapy.IPv6ExtHdrRouting,
            scapy.IPv6ExtHdrDestOpt,
        )
        for _ in range(12):
            if not isinstance(transport, allowed):
                break
            transport = transport.payload
        if isinstance(transport, allowed):
            return None
        src_ip, dst_ip = str(ip6.src), str(ip6.dst)
        if ip6.plen is None:
            length = len(bytes(ip6))
        elif int(ip6.plen) == 0:
            return None  # IPv6 jumbograms are not supported in v1.
        else:
            length = 40 + int(ip6.plen)
        ipv6 = True
    else:
        return None

    del network
    flags: frozenset[str] = frozenset()
    if isinstance(transport, scapy.TCP):
        protocol = "TCP"
        src_port, dst_port = int(transport.sport), int(transport.dport)
        flags = frozenset(name for name, bit in _TCP_BITS if int(transport.flags) & bit)
    elif isinstance(transport, scapy.UDP):
        protocol = "UDP"
        src_port, dst_port = int(transport.sport), int(transport.dport)
    elif not ipv6 and isinstance(transport, scapy.ICMP):
        protocol = "ICMP"
        src_port, dst_port = 0, 0
    elif ipv6 and type(transport).__name__.startswith("ICMPv6"):
        protocol = "ICMPV6"
        src_port, dst_port = 0, 0
    else:
        return None

    try:
        # Decimal(str(...)) avoids binary float multiplication drift; ties-to-even.
        timestamp_ns = int(
            (Decimal(str(packet.time)) * Decimal(1_000_000_000)).to_integral_value(
                rounding=ROUND_HALF_EVEN
            )
        )
    except (InvalidOperation, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Invalid packet capture timestamp") from exc

    return PacketMeta(
        timestamp_ns=timestamp_ns,
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        ip_length_bytes=length,
        tcp_flags=flags,
    )
