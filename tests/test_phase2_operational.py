"""Additional Phase 2 operational, safety, and failure-boundary coverage."""

from __future__ import annotations

import json
import time
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from nohack.capture.capabilities import capture_capabilities
from nohack.capture.commands import _record_writer
from nohack.capture.replay import CaptureError, FlowProcessor, replay_pcap
from nohack.capture.session import CaptureSession, capture_for_duration
from nohack.collector.flows import FlowManager, ProcessContext
from nohack.collector.process import ProcessAttributor
from nohack.features import PacketMeta

scapy = pytest.importorskip("scapy.all")


def packet(ns: int = 1_000_000_000) -> PacketMeta:
    return PacketMeta(
        timestamp_ns=ns,
        src_ip="192.0.2.10",
        dst_ip="192.0.2.20",
        src_port=12345,
        dst_port=443,
        protocol="TCP",
        ip_length_bytes=40,
        tcp_flags=frozenset({"SYN"}),
    )


def sample_ip() -> Any:
    pkt = scapy.IP(src="192.0.2.10", dst="192.0.2.20") / scapy.TCP(
        sport=12345, dport=443, flags="S"
    )
    pkt.time = Decimal("1.000000000")
    return pkt


def test_processor_tracks_skipped_and_malformed() -> None:
    processor = FlowProcessor()
    assert processor.accept(scapy.ARP()) == []
    invalid = sample_ip()
    invalid.time = "not-a-timestamp"
    assert processor.accept(invalid) == []
    assert processor.skipped == 1
    assert processor.malformed == 1
    assert processor.accept(sample_ip()) == []
    completed = processor.finish()
    assert len(completed) == 1
    assert completed[0].flow.features["total_packet_count"] == 1


def test_cli_replay_explicit_metadata_export(tmp_path: Path, capsys: Any) -> None:
    from nohack.cli import main

    capture = tmp_path / "controlled.pcap"
    scapy.wrpcap(str(capture), [sample_ip()])
    output = tmp_path / "flows.jsonl"
    assert (
        main(
            [
                "replay-pcap",
                "--input",
                str(capture),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["flows_completed"] == 1
    assert summary["classification_active"] is False
    assert summary["capture_payloads_saved"] is False
    row = json.loads(output.read_text().strip())
    assert row["feature_schema_version"] == "nohackflow-v1"
    assert row["features"]["total_packet_count"] == 1
    assert row["process"] is None
    assert "payload" not in row
    assert main(["replay-pcap", "--input", str(capture), "--output", str(output)]) == 3
    assert "Capture error" in capsys.readouterr().err


def test_cli_replay_missing_input(capsys: Any, tmp_path: Path) -> None:
    from nohack.cli import main

    assert main(["replay-pcap", "--input", str(tmp_path / "absent")]) == 3
    assert "Capture error" in capsys.readouterr().err


def test_record_callback_explicit_file_and_context(tmp_path: Path) -> None:
    manager = FlowManager(process_resolver=lambda _: ProcessContext(7, "synthetic"))
    manager.ingest(packet())
    record = manager.flush()[0]
    assert record.to_dict()["process"] == {"pid": 7, "name": "synthetic"}
    output = tmp_path / "flow.jsonl"
    with output.open("w", encoding="utf-8") as stream:
        _record_writer(stream)(record)
    assert json.loads(output.read_text())["process"]["pid"] == 7
    _record_writer(None)(record)


def test_session_fake_npcap_start_expire_stop(monkeypatch: Any) -> None:
    import nohack.capture.session as mod

    class FakeSniffer:
        def __init__(self, **kwargs: Any) -> None:
            self.started_callback = kwargs["started_callback"]
            self.running = False
            assert kwargs["store"] is False
            assert kwargs["filter"] == "ip or ip6"
            assert kwargs["iface"] == "allowed"

        def start(self) -> None:
            self.running = True
            self.started_callback()

        def stop(self) -> None:
            self.running = False

    processor = FlowProcessor()
    processor.manager.ingest(packet())
    emitted: list[Any] = []
    session = CaptureSession("allowed", processor, emitted.append)
    with monkeypatch.context() as patch:
        patch.setattr(mod, "capture_capabilities", lambda: {"live_capture_ready": True})
        patch.setattr(mod, "list_interfaces", lambda: ["allowed"])
        patch.setattr(
            mod.importlib,
            "import_module",
            lambda _: SimpleNamespace(AsyncSniffer=FakeSniffer),
        )
        session.start()
    assert session._sniffer is not None
    session.tick(31_000_000_001)
    assert session.delivered == 1
    assert emitted[0].reason == "idle_timeout"
    session.stop()
    assert session._sniffer is None
    assert not processor.manager.active


def test_session_start_rejected_without_npcap(monkeypatch: Any) -> None:
    import nohack.capture.session as mod

    session = CaptureSession("interface", FlowProcessor(), lambda _: None)
    monkeypatch.setattr(
        mod, "capture_capabilities", lambda: {"live_capture_ready": False}
    )
    with pytest.raises(CaptureError, match="Npcap"):
        session.start()
    with pytest.raises(ValueError, match="interface"):
        CaptureSession(" ", FlowProcessor(), lambda _: None)


def test_session_rejects_unknown_interface(monkeypatch: Any) -> None:
    import nohack.capture.session as mod

    monkeypatch.setattr(
        mod, "capture_capabilities", lambda: {"live_capture_ready": True}
    )
    monkeypatch.setattr(mod, "list_interfaces", lambda: ["different"])
    with pytest.raises(CaptureError, match="unavailable"):
        CaptureSession("expected", FlowProcessor(), lambda _: None).start()


def test_session_callback_failure_is_reported(monkeypatch: Any) -> None:
    session = CaptureSession("allowed", FlowProcessor(), lambda _: None)
    monkeypatch.setattr(
        session.processor,
        "accept",
        lambda *args: (_ for _ in ()).throw(OSError("simulated output error")),
    )
    session._on_packet(object())
    with pytest.raises(CaptureError, match="processing"):
        session.tick()
    session.stop()


def test_session_tick_detects_disconnected_interface() -> None:
    session = CaptureSession("allowed", FlowProcessor(), lambda _: None)
    session._sniffer = SimpleNamespace(running=False)
    with pytest.raises(CaptureError, match="unexpectedly"):
        session.tick()
    session.stop()


def test_duration_validation_and_finally_cleanup() -> None:
    session = CaptureSession("allowed", FlowProcessor(), lambda _: None)
    with pytest.raises(ValueError, match="Duration"):
        capture_for_duration(session, 0.0)
    with pytest.raises(ValueError, match="Duration"):
        capture_for_duration(session, 301.0)


def test_process_matching_missing_ambiguous_and_denied(monkeypatch: Any) -> None:
    import nohack.collector.process as mod

    first = packet()
    access = SimpleNamespace(ip="192.0.2.10", port=12345)
    remote = SimpleNamespace(ip="192.0.2.20", port=443)

    class FakePsutil:
        Error = OSError
        sockets: list[Any] = []

        def net_connections(self, kind: str) -> list[Any]:
            return self.sockets

        def Process(self, pid: int) -> Any:
            if pid == 7:
                raise PermissionError("denied")
            return SimpleNamespace(name=lambda: "synthetic")

    fake = FakePsutil()
    with monkeypatch.context() as patch:
        patch.setattr(mod.importlib, "import_module", lambda _: fake)
        service = ProcessAttributor(cache_seconds=0.001)
        assert service.lookup(first) is None
        fake.sockets = [
            SimpleNamespace(pid=7, type=1, laddr=access, raddr=remote),
            SimpleNamespace(pid=8, type=1, laddr=access, raddr=remote),
        ]
        service._updated = -1.0
        assert service.lookup(first) is None
        fake.sockets = [fake.sockets[0]]
        service._updated = -1.0
        assert service.lookup(first) is None
        fake.sockets = [
            SimpleNamespace(pid=12, type=2, laddr=access, raddr=remote),
            SimpleNamespace(pid=None, type=1, laddr=access, raddr=remote),
            SimpleNamespace(
                pid=13,
                type=1,
                laddr=access,
                raddr=SimpleNamespace(ip="192.0.2.21", port=443),
            ),
        ]
        service._updated = -1.0
        assert service.lookup(first) is None


def test_process_table_error_gracefully_degrades(monkeypatch: Any) -> None:
    import nohack.collector.process as mod

    class Denied:
        Error = OSError

        def net_connections(self, kind: str) -> list[Any]:
            raise PermissionError("no access")

    with monkeypatch.context() as patch:
        patch.setattr(mod.importlib, "import_module", lambda _: Denied())
        assert ProcessAttributor().lookup(packet()) is None
    with pytest.raises(ValueError):
        ProcessAttributor(cache_seconds=0)
    assert time.monotonic() > 0


def test_replay_invalid_data(tmp_path: Path) -> None:
    bad = tmp_path / "bad.pcap"
    bad.write_bytes(b"not a valid pcap file")
    with pytest.raises(CaptureError):
        list(replay_pcap(bad))


def test_capabilities_with_simulated_windows(monkeypatch: Any) -> None:
    import nohack.capture.capabilities as mod

    loaded: list[str] = []
    with monkeypatch.context() as patch:
        patch.setattr(mod.sys, "platform", "win32")
        patch.setattr(mod.ctypes, "WinDLL", loaded.append, raising=False)
        report = capture_capabilities()
    assert loaded == ["wpcap.dll", "Packet.dll"]
    assert report["npcap_dlls_found"] is True
    with monkeypatch.context() as patch:
        patch.setattr(mod.sys, "platform", "win32")
        patch.setattr(
            mod.ctypes,
            "WinDLL",
            lambda _: (_ for _ in ()).throw(OSError()),
            raising=False,
        )
        assert capture_capabilities()["npcap_dlls_found"] is False


def test_cli_interruption_is_controlled(monkeypatch: Any, capsys: Any) -> None:
    import nohack.capture.commands as commands
    from nohack.cli import main

    monkeypatch.setattr(
        commands,
        "capture_for_duration",
        lambda *args: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    assert main([
        "capture-demo", "--interface", "dummy", "--authorized"
    ]) == 130
    assert "interrupted" in capsys.readouterr().err
