"""Phase 3 bounded lifecycle and SQLite pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nohack.collector.flows import FlowManager
from nohack.features import PacketMeta
from nohack.runtime.pipeline import replay_to_database
from nohack.runtime.service import ObservationRuntime
from nohack.storage.observations import ObservationStore


def packet(n: int, port: int = 60000) -> PacketMeta:
    return PacketMeta(
        timestamp_ns=n,
        src_ip="192.0.2.1",
        src_port=port,
        dst_ip="192.0.2.2",
        dst_port=443,
        protocol="TCP",
        ip_length_bytes=40,
        tcp_flags=frozenset({"SYN"}),
    )


def test_flow_store_omits_raw_addresses(tmp_path: Path) -> None:
    manager = FlowManager()
    manager.ingest(packet(1))
    result = manager.flush()
    assert len(result) == 1
    with ObservationStore(tmp_path / "nested" / "flows.db") as store:
        store.insert(result[0], source="replay")
        rows = store.recent()
        assert len(rows) == 1
        assert rows[0]["assessment"] == "UNASSESSED"
        assert rows[0]["features"]["total_packet_count"] == 1
        assert "192.0.2." not in json.dumps(rows)
        assert store.delete_ended_before(2) == 1
        assert store.recent() == []


def test_store_transaction_rollback(tmp_path: Path) -> None:
    db = tmp_path / "events.db"
    manager = FlowManager()
    manager.ingest(packet(1))
    record = manager.flush()[0]
    with pytest.raises(RuntimeError, match="fail"):
        with ObservationStore(db) as store:
            store.insert(record, source="live")
            raise RuntimeError("fail")
    with ObservationStore(db) as store:
        assert store.recent() == []


def test_storage_rejects_invalid_source_and_limit(tmp_path: Path) -> None:
    manager = FlowManager()
    manager.ingest(packet(1))
    record = manager.flush()[0]
    with ObservationStore(tmp_path / "events.db") as store:
        with pytest.raises(ValueError, match="source"):
            store.insert(record, source="untrusted")
        with pytest.raises(ValueError, match="limit"):
            store.recent(limit=1001)
        with pytest.raises(ValueError, match="cutoff"):
            store.delete_ended_before(-1)


def test_runtime_is_bounded_and_flushes_on_stop() -> None:
    runtime = ObservationRuntime(max_pending=1)
    runtime.processor.manager.ingest(packet(1, 60000))
    runtime.processor.manager.ingest(packet(2, 60001))
    state = runtime.health()
    assert state["active_flows"] == 2
    runtime.tick(300_000_000_000)
    assert runtime.health()["dropped_due_to_backpressure"] >= 1
    pending = runtime.stop()
    assert len(pending) == 1
    assert runtime.stop() == []
    assert runtime.health()["stopped"] is True
    with pytest.raises(RuntimeError, match="stopped"):
        runtime.tick(400_000_000_000)


def test_runtime_invalid_capacity() -> None:
    with pytest.raises(ValueError, match="max_pending"):
        ObservationRuntime(max_pending=0)


def test_pcap_end_to_end(tmp_path: Path) -> None:
    scapy = pytest.importorskip("scapy.all")
    pcap = tmp_path / "authorized-fixture.pcap"
    db = tmp_path / "history.db"
    packets: list[Any] = [
        scapy.IP(src="192.0.2.1", dst="192.0.2.2")
        / scapy.TCP(sport=54321, dport=443, flags="S"),
        scapy.IP(src="192.0.2.2", dst="192.0.2.1")
        / scapy.TCP(sport=443, dport=54321, flags="R"),
    ]
    packets[0].time = 1
    packets[1].time = 2
    scapy.wrpcap(str(pcap), packets)
    report = replay_to_database(pcap, db)
    assert report["flow_observations"] == 1
    assert report["classification_active"] is False
    with ObservationStore(db) as store:
        rows = store.recent()
        assert rows[0]["assessment"] == "UNASSESSED"
        assert rows[0]["features"]["total_packet_count"] == 2
        assert "192.0.2." not in json.dumps(rows)
