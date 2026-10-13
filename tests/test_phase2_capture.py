"""Phase 2: controlled packet normalization, lifecycle and PCAP parity."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from nohack.capture.capabilities import capture_capabilities
from nohack.capture.normalizer import normalize_scapy
from nohack.capture.replay import CaptureError, FlowProcessor, replay_pcap
from nohack.capture.session import CaptureSession
from nohack.collector.flows import FlowLimits, FlowManager
from nohack.collector.process import ProcessAttributor
from nohack.features import FEATURE_NAMES, PacketMeta

scapy = pytest.importorskip("scapy.all")


def tcp(
    time_ns: int,
    *,
    reverse: bool = False,
    flags: str = "A",
    sport: int = 50000,
) -> Any:
    src, dst = ("192.0.2.2", "192.0.2.1") if reverse else (
        "192.0.2.1", "192.0.2.2"
    )
    packet = scapy.IP(src=src, dst=dst) / scapy.TCP(
        sport=443 if reverse else sport,
        dport=sport if reverse else 443,
        flags=flags,
    )
    packet.time = Decimal(time_ns) / Decimal(1_000_000_000)
    return packet


def metadata(time_ns: int, *, reverse: bool = False, flags: str = "A") -> PacketMeta:
    normalized = normalize_scapy(tcp(time_ns, reverse=reverse, flags=flags))
    assert normalized is not None
    return normalized


def test_normalization_exact_ipv4_tcp_length_flags_and_timestamp() -> None:
    packet = tcp(1_500_000_001, flags="SA")
    meta = normalize_scapy(packet)
    assert meta is not None
    assert meta.timestamp_ns == 1_500_000_001
    assert meta.ip_length_bytes == 40
    assert meta.tcp_flags == frozenset({"SYN", "ACK"})
    assert meta.src_port == 50000


def test_ipv6_udp_and_ipv4_icmp_and_fragments() -> None:
    ipv6 = scapy.IPv6(src="2001:db8::1", dst="2001:db8::2") / scapy.UDP(
        sport=20, dport=30
    )
    ipv6.time = 2
    meta = normalize_scapy(ipv6)
    assert meta is not None
    assert meta.protocol == "UDP"
    assert meta.ip_length_bytes == 48

    icmp = scapy.IP(src="192.0.2.1", dst="192.0.2.2") / scapy.ICMP()
    icmp.time = 2
    im = normalize_scapy(icmp)
    assert im is not None
    assert im.protocol == "ICMP"
    assert (im.src_port, im.dst_port) == (0, 0)

    fragment = scapy.IP(
        src="192.0.2.1", dst="192.0.2.2", flags="MF"
    ) / scapy.UDP(sport=1, dport=2)
    fragment.time = 2
    assert normalize_scapy(fragment) is None
    assert normalize_scapy(scapy.ARP()) is None


def test_bidirectional_lifecycle_fin_and_ack() -> None:
    manager = FlowManager(FlowLimits(close_grace_ns=10))
    assert manager.ingest(metadata(100, flags="S")) == []
    assert manager.ingest(metadata(110, reverse=True, flags="SA")) == []
    assert manager.ingest(metadata(120, flags="FA")) == []
    assert manager.ingest(metadata(130, reverse=True, flags="A")) == []
    assert len(manager.active) == 1  # one FIN does not close it.
    assert manager.ingest(metadata(140, reverse=True, flags="FA")) == []
    assert manager.ingest(metadata(145, flags="A")) == []
    completed = manager.expire(150)
    assert len(completed) == 1
    f = completed[0].flow.features
    assert completed[0].reason == "tcp_closed"
    assert f["total_packet_count"] == 6
    assert f["forward_packet_count"] == 3
    assert f["backward_packet_count"] == 3
    assert f["fin_count"] == 2
    assert f["syn_count"] == 2
    assert list(f) == list(FEATURE_NAMES)


def test_tcp_rst_and_shutdown_preserve_records() -> None:
    manager = FlowManager()
    assert manager.ingest(metadata(1_000, flags="S")) == []
    completed = manager.ingest(metadata(2_000, reverse=True, flags="R"))
    assert len(completed) == 1
    assert completed[0].reason == "tcp_rst"
    assert completed[0].flow.features["rst_count"] == 1
    manager.ingest(metadata(3_000, flags="S"))
    drained = manager.flush()
    assert len(drained) == 1
    assert drained[0].flow.features["total_packet_count"] == 1
    assert not manager.active


def test_reuse_syn_and_retransmitted_syn() -> None:
    manager = FlowManager()
    manager.ingest(metadata(1, flags="S"))
    manager.ingest(metadata(2, flags="S"))
    assert len(manager.active) == 1
    manager.ingest(metadata(3, reverse=True, flags="SA"))
    completed = manager.ingest(metadata(4, flags="S"))
    assert len(completed) == 1
    assert completed[0].reason == "tcp_reuse"
    assert completed[0].flow.features["total_packet_count"] == 3
    assert len(manager.active) == 1
    assert manager.flush()[0].flow.features["total_packet_count"] == 1


def test_idle_max_duration_capacity_and_ordering() -> None:
    limits = FlowLimits(
        idle_timeout_ns=10, max_lifetime_ns=20, max_active=1, close_grace_ns=2
    )
    manager = FlowManager(limits)
    assert manager.ingest(metadata(100)) == []
    assert manager.ingest(metadata(99)) == []
    assert manager.counters.out_of_order == 1
    assert manager.expire(110)[0].reason == "idle_timeout"
    manager.ingest(metadata(120))
    different = tcp(121, sport=50001)
    other = normalize_scapy(different)
    assert other is not None
    completed = manager.ingest(other)
    assert completed[0].reason == "capacity"
    assert manager.counters.evicted == 1
    assert manager.expire(141)[0].reason == "max_lifetime"
    assert not manager.active


def test_offline_live_pipeline_parity(tmp_path: Path) -> None:
    packets = [
        tcp(1_000_000_000, flags="S"),
        tcp(1_100_000_000, reverse=True, flags="SA"),
        tcp(1_150_000_000, flags="PA"),
    ]
    path = tmp_path / "synthetic.pcap"
    scapy.wrpcap(str(path), packets)
    streaming = FlowProcessor()
    for packet in packets:
        assert streaming.accept(packet) == []
    expected = [r.to_dict() for r in streaming.finish()]
    replayed = FlowProcessor()
    actual = [r.to_dict() for r in replay_pcap(path, replayed)]
    assert actual == expected
    assert expected[0]["features"]["total_packet_count"] == 3
    assert expected[0]["features"]["duration_ms"] == pytest.approx(150)
    assert replayed.manager.counters.ingested == 3


def test_invalid_pcap_path_and_no_implicit_capture(tmp_path: Path) -> None:
    with pytest.raises(CaptureError):
        list(replay_pcap(tmp_path / "missing.pcap"))
    session = CaptureSession("not-a-real-interface", FlowProcessor(), lambda _: None)
    assert session.delivered == 0
    assert session.processor.manager.counters.ingested == 0
    caps = capture_capabilities()
    assert isinstance(caps["scapy_installed"], bool)


def test_conservative_process_attribution(monkeypatch: pytest.MonkeyPatch) -> None:
    import nohack.collector.process as process_module

    class FakePsutil:
        Error = OSError

        def net_connections(self, kind: str) -> list[Any]:
            assert kind == "inet"
            return [SimpleNamespace(
                pid=12,
                type=1,
                laddr=SimpleNamespace(ip="192.0.2.1", port=50000),
                raddr=SimpleNamespace(ip="192.0.2.2", port=443),
            )]

        def Process(self, pid: int) -> Any:
            return SimpleNamespace(name=lambda: "synthetic-process", pid=pid)

    fake = FakePsutil()
    monkeypatch.setattr(process_module.importlib, "import_module", lambda _: fake)
    attribution = ProcessAttributor().lookup(metadata(1))
    assert attribution is not None
    assert attribution.pid == 12
    assert attribution.name == "synthetic-process"
    assert ProcessAttributor().lookup(metadata(1, reverse=True)) is not None


def test_flow_config_rejects_invalid_settings() -> None:
    with pytest.raises(ValueError):
        FlowLimits(max_active=0)
    with pytest.raises(ValueError):
        FlowLimits(close_grace_ns=-1)
    with pytest.raises(ValueError):
        FlowLimits(idle_timeout_ns=True)


def test_cli_requires_opt_in(capsys: pytest.CaptureFixture[str]) -> None:
    from nohack.cli import main

    assert main(["capture-demo", "--interface", "something"]) == 3
    assert "--authorized" in capsys.readouterr().err
    assert main(["capture-check"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["live_capture_ready"] in {True, False}
    assert main(["doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["model_loaded"] is False
