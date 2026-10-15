"""Opt-in finite Windows capture -> SQLite -> local ML scoring.

Capture only interfaces/traffic the operator is authorized to monitor. No
payloads are persisted, and this never auto-starts from a Chrome extension.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.capture.replay import FlowProcessor
from nohack.capture.session import CaptureSession, capture_for_duration
from nohack.collector.flows import CompletedFlow
from nohack.storage.observations import ObservationStore

from scripts.score_observations import score_database


def run_authorized_capture(
    interface: str, seconds: float, database: Path, bundle: Path
) -> dict[str, object]:
    if not 1 <= seconds <= 120:
        raise ValueError("seconds must be between 1 and 120")
    written = 0
    with ObservationStore(database) as store:
        def persist(record: CompletedFlow) -> None:
            nonlocal written
            store.insert(record, source="live")
            written += 1
        session = CaptureSession(interface, FlowProcessor(), persist)
        capture_for_duration(session, seconds)
    result = score_database(bundle, database, max_rows=10000)
    return {"flow_observations": written, "scoring": result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--database", type=Path,
                        default=Path.home() / ".nohack" / "observations.db")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--trust-local-bundle", action="store_true")
    args = parser.parse_args()
    if not args.authorized or not args.trust_local_bundle:
        parser.error("Both --authorized and --trust-local-bundle are required")
    print(json.dumps(run_authorized_capture(
        args.interface, args.seconds, args.database, args.bundle
    )))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
