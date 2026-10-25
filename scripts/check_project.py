"""Offline all-component code inventory and optional self-attested acceptance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.engineering.readiness import project_inventory, self_attested_acceptance


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--evidence", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    report = project_inventory(args.root)
    if args.evidence:
        report["operator_attestation"] = self_attested_acceptance(args.evidence)
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, "utf-8")
    print(output, end="")
    return int(report["present"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
