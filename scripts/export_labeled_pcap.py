"""Reconstruct labeled canonical NoHackFlow CSVs from authorized PCAPs.

Each output flow requires an independently verified exact flow_id label.
This tool NEVER labels a whole PCAP malicious based on a filename.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from nohack.capture.replay import FlowProcessor, replay_pcap
from nohack.features import FEATURE_NAMES


def export_verified_flows(pcap: Path, annotations: Path, output: Path) -> int:
    if output.exists():
        raise ValueError("Output already exists (refusing to overwrite)")
    expected: dict[str, tuple[str, str]] = {}
    with annotations.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != ["flow_id", "label", "group_id"]:
            raise ValueError("Expected annotation columns: flow_id,label,group_id")
        for row in reader:
            key = row["flow_id"].strip()
            label = row["label"].strip()
            group = row["group_id"].strip()
            if not key or not label or not group or key in expected:
                raise ValueError("Annotation has duplicates, missing values or IDs")
            expected[key] = (label, group)
    if not expected:
        raise ValueError("No verified flow annotations")
    seen: set[str] = set()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".partial")
    count = 0
    try:
        with temporary.open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=[*FEATURE_NAMES, "label", "group_id"]
            )
            writer.writeheader()
            for record in replay_pcap(pcap, FlowProcessor()):
                identity = record.flow.context.flow_id
                if identity not in expected or identity in seen:
                    raise ValueError(
                        "Flow label missing or repeated; label matching failed"
                    )
                seen.add(identity)
                label, group = expected[identity]
                writer.writerow(
                    {**record.flow.features, "label": label, "group_id": group}
                )
                count += 1
        if set(expected) != seen:
            raise ValueError("Annotations contain flows not found in the PCAP")
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcap", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        f"Exported {export_verified_flows(args.pcap, args.annotations, args.output)} canonical labeled flows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
