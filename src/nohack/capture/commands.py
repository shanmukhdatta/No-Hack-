"""Safe opt-in CLI commands for Windows capture and local PCAP inspection."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from contextlib import ExitStack
from pathlib import Path
from typing import Any, TextIO

from nohack.capture.capabilities import capture_capabilities
from nohack.capture.replay import CaptureError, FlowProcessor, replay_pcap
from nohack.capture.session import (
    CaptureSession,
    capture_for_duration,
    list_interfaces,
)
from nohack.collector.flows import CompletedFlow, FlowManager
from nohack.collector.process import ProcessAttributor


def register_capture_commands(subparsers: Any) -> None:
    subparsers.add_parser("capture-check", help="Inspect Scapy/Npcap readiness")
    subparsers.add_parser("capture-interfaces", help="List Windows Npcap interfaces")
    replay = subparsers.add_parser(
        "replay-pcap", help="Summarize an authorized local PCAP"
    )
    replay.add_argument("--input", type=Path, required=True)
    replay.add_argument("--output", type=Path)
    demo = subparsers.add_parser(
        "capture-demo", help="Capture authorized local metadata for a short interval"
    )
    demo.add_argument("--interface", required=True)
    demo.add_argument("--seconds", type=float, default=10.0)
    demo.add_argument("--authorized", action="store_true", required=False)
    demo.add_argument("--output", type=Path)


def _processor(*, enrich_processes: bool = False) -> FlowProcessor:
    resolver: Callable[..., Any] | None = None
    if enrich_processes and sys.platform == "win32":
        resolver = ProcessAttributor().lookup
    return FlowProcessor(FlowManager(process_resolver=resolver))


def _summary(processor: FlowProcessor, delivered: int) -> dict[str, object]:
    counters = processor.manager.counters
    return {
        "schema": "nohackflow-v1",
        "classification_active": False,
        "capture_payloads_saved": False,
        "packets_accepted": counters.ingested - counters.out_of_order,
        "packets_skipped": processor.skipped,
        "packets_malformed": processor.malformed,
        "packets_out_of_order": counters.out_of_order,
        "flows_completed": delivered,
        "flows_evicted_for_capacity": counters.evicted,
        "active_flows_remaining": len(processor.manager.active),
    }


def _record_writer(stream: TextIO | None) -> Callable[[CompletedFlow], None]:
    def write(record: CompletedFlow) -> None:
        if stream is not None:
            # Preserve the canonical FEATURE_NAMES insertion order in JSONL.\n            stream.write(json.dumps(record.to_dict()) + "\n")

    return write


def run_capture_command(args: argparse.Namespace) -> int:
    try:
        if args.command == "capture-check":
            print(json.dumps(capture_capabilities(), sort_keys=True))
            return 0
        if args.command == "capture-interfaces":
            print(json.dumps({"interfaces": list_interfaces()}))
            return 0
        if args.command == "capture-demo" and not args.authorized:
            raise CaptureError(
                "Explicit --authorized consent is required for monitored traffic"
            )
        processor = _processor(enrich_processes=args.command == "capture-demo")
        delivered = 0
        with ExitStack() as stack:
            output = getattr(args, "output", None)
            stream = (
                stack.enter_context(output.open("x", encoding="utf-8"))
                if output is not None
                else None
            )
            writer = _record_writer(stream)
            if args.command == "replay-pcap":
                for record in replay_pcap(args.input, processor):
                    writer(record)
                    delivered += 1
            elif args.command == "capture-demo":
                session = CaptureSession(args.interface, processor, writer)
                capture_for_duration(session, args.seconds)
                delivered = session.delivered
            print(json.dumps(_summary(processor, delivered), sort_keys=True))
        return 0
    except KeyboardInterrupt:
        print("Capture interrupted; active flows flushed", file=sys.stderr)
        return 130
    except (CaptureError, OSError, ValueError) as exc:
        print(f"Capture error: {exc}", file=sys.stderr)
        return 3
