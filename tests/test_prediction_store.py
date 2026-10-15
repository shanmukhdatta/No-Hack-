"""Privacy and read-only native companion database contract tests."""
from __future__ import annotations

import json
from pathlib import Path

from nohack.collector.flows import FlowManager
from nohack.features import PacketMeta
from nohack.native_host import handle_message
from nohack.storage.observations import ObservationStore
from nohack.storage.predictions import PredictionStore, recent_assessments


def test_local_flow_assessment_excludes_endpoints_and_payloads(tmp_path: Path) -> None:
    db = tmp_path / "observations.db"
    manager = FlowManager()
    manager.ingest(PacketMeta(
        timestamp_ns=100, src_ip="192.0.2.20", dst_ip="192.0.2.30",
        src_port=54321, dst_port=443, protocol="TCP",
        ip_length_bytes=40, tcp_flags=frozenset({"SYN"}),
    ))
    with ObservationStore(db) as store:
        store.insert(manager.flush()[0], source="replay")
    with PredictionStore(db) as store:
        pending = store.unscored()
        assert len(pending) == 1
        row_id, features = pending[0]
        assert features["total_packet_count"] == 1
        store.add(row_id, {
            "state": "UNCERTAIN", "risk_score": 27,
            "known_threat_probability": 0.27, "anomaly_percentile": 0.91,
            "model_disagreement": 0.12,
            "top_reasons": ["Synthetic fixture; not a detector"],
            "feature_schema_version": "nohackflow-v1",
        }, "sha-test-model")
        assert store.unscored() == []
    assessments = recent_assessments(db)
    assert len(assessments) == 1
    assert assessments[0]["state"] == "UNCERTAIN"
    assert "192.0.2." not in json.dumps(assessments)
    assert "54321" not in json.dumps(assessments)
    assert recent_assessments(db, limit=0) == []


def test_native_host_preserves_read_only_protocol() -> None:
    assert handle_message({"type": "start_capture"})["ok"] is False
    assert handle_message({"type": "train"})["ok"] is False
    assert handle_message({"type": "recent_assessments"})["ok"] is True
    assert handle_message({"type": "recent_assessments"})["scope"] == (
        "local_network_flows_not_browser_tabs"
    )
