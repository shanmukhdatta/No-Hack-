"""End-to-end authorized local PCAP replay -> NoHackFlow -> SQLite."""

from __future__ import annotations

from pathlib import Path

from nohack.capture.replay import FlowProcessor, replay_pcap
from nohack.storage.observations import ObservationStore


def replay_to_database(pcap: Path, database: Path) -> dict[str, object]:
    """Replay flow metadata, store without endpoints, never claim ML inference."""
    count = 0
    processor = FlowProcessor()
    with ObservationStore(database) as store:
        for record in replay_pcap(pcap, processor):
            store.insert(record, source="replay")
            count += 1
    counters = processor.manager.counters
    return {
        "mode": "authorized_local_pcap_replay",
        "database": str(database),
        "flow_observations": count,
        "packets_skipped": processor.skipped,
        "packets_malformed": processor.malformed,
        "packets_out_of_order": counters.out_of_order,
        "active_flows_remaining": len(processor.manager.active),
        "assessment": "UNASSESSED",
        "model_loaded": False,
        "classification_active": False,
        "payloads_persisted": False,
        "raw_endpoint_addresses_persisted": False,
    }
