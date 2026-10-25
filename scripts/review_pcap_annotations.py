"""Two-stage, LOCAL-ONLY audit of NoHackFlow PCAP identity and flow annotations.

template: export REVIEW-ONLY endpoint/timestamp metadata from an authorized PCAP.
approve: accept only manually checked rows with explicit evidence references.
This cannot independently validate the truth of user-supplied labels.
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REVIEW_FIELDS = (
    "flow_id",
    "protocol",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "started_at_ns",
    "ended_at_ns",
    "label",
    "group_id",
    "source_evidence",
    "verification_status",
)
APPROVED_FIELDS = ("flow_id", "label", "group_id")


def write_review_template(flows: Iterable[Any], output: Path) -> int:
    """Output sensitive metadata locally and mark every label UNREVIEWED."""
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    seen: set[str] = set()
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(REVIEW_FIELDS))
        writer.writeheader()
        for record in flows:
            flow = record.flow
            context, features = flow.context, flow.features
            if context.flow_id in seen:
                raise ValueError("Duplicate flow ID in PCAP; review identity collision")
            seen.add(context.flow_id)
            writer.writerow(
                {
                    "flow_id": context.flow_id,
                    "protocol": features["protocol"],
                    "src_ip": context.src_ip,
                    "dst_ip": context.dst_ip,
                    "src_port": features["src_port"],
                    "dst_port": features["dst_port"],
                    "started_at_ns": context.started_at_ns,
                    "ended_at_ns": context.ended_at_ns,
                    "label": "",
                    "group_id": "",
                    "source_evidence": "",
                    "verification_status": "UNREVIEWED",
                }
            )
            count += 1
    return count


def approve_review(review: Path, output: Path) -> int:
    """Remove endpoint metadata after *user-attested* manual verification.

    Labels are asserted by the operator, not independently proven by code.
    ALL flow records require matching, reviewed annotation evidence.
    """
    if output.exists():
        raise ValueError("Output already exists; refusing overwrite")
    accepted: list[dict[str, str]] = []
    ids: set[str] = set()
    with review.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != list(REVIEW_FIELDS):
            raise ValueError("Review CSV header mismatch")
        for row in reader:
            flow_id = row["flow_id"].strip()
            label = row["label"].strip()
            group = row["group_id"].strip()
            evidence = row["source_evidence"].strip()
            status = row["verification_status"].strip().upper()
            if (
                not flow_id
                or flow_id in ids
                or not label
                or not group
                or not evidence
                or status != "VERIFIED"
            ):
                raise ValueError(
                    "Every flow needs a unique ID, verified label, independent "
                    "group and source evidence. Unreviewed/ambiguous flows block export."
                )
            ids.add(flow_id)
            accepted.append({"flow_id": flow_id, "label": label, "group_id": group})
    if not accepted:
        raise ValueError("Review contains no verified flows")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(APPROVED_FIELDS))
        writer.writeheader()
        writer.writerows(accepted)
    return len(accepted)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    first = sub.add_parser("template")
    first.add_argument("--pcap", required=True, type=Path)
    first.add_argument("--output", required=True, type=Path)
    second = sub.add_parser("approve")
    second.add_argument("--review", required=True, type=Path)
    second.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.mode == "template":
        from nohack.capture.replay import replay_pcap

        count = write_review_template(replay_pcap(args.pcap), args.output)
        print(f"Wrote {count} UNREVIEWED private flow records (NOT training labels)")
    else:
        count = approve_review(args.review, args.output)
        print(f"Exported {count} user-attested annotations; truth NOT proven by code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
