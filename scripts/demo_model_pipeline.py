"""Local end-to-end synthetic smoke, never a real intrusion-detection benchmark.

Generates artificial NoHackFlow records, freezes group-disjoint splits,
fits the existing hybrid stack, and checks a trusted local model load.
Never ship the demo bundle as a real cybersecurity detector.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from nohack.datasets.prepare import prepare_dataset
from nohack.features import FEATURE_NAMES
from nohack.features.flow_schema import FEATURE_SPECS
from nohack.inference.hybrid import load_bundle, predict_features
from nohack.training.hybrid import train_from_splits

DEMO_WARNING = "SYNTHETIC DEMO ONLY — labels and scores are artificial; NOT validated security detection"


def make_demo_flow(group: int, row_id: int) -> dict[str, object]:
    if not (0 <= group < 1000 and 0 <= row_id < 12):
        raise ValueError("Demo group or row out of bounds")
    row: dict[str, object] = {
        name: (0 if kind == "int" else 0.0)
        for name, kind in FEATURE_SPECS
        if kind != "category"
    }
    forward_count = 2 + row_id
    backward_count = 1
    forward_bytes = 80 + 40 * row_id
    backward_bytes = 40
    row.update(
        {
            "protocol": "TCP",
            "duration_ms": float(100 + group * 3 + row_id / 100),
            "src_port": 2000 + group * 20 + row_id,
            "dst_port": 443,
            "forward_packet_count": forward_count,
            "backward_packet_count": backward_count,
            "total_packet_count": forward_count + backward_count,
            "forward_byte_count": forward_bytes,
            "backward_byte_count": backward_bytes,
            "total_byte_count": forward_bytes + backward_bytes,
            "forward_packets_per_second": 30.0,
            "backward_packets_per_second": 15.0,
            "packets_per_second": 45.0,
            "bytes_per_second": 100.0,
            "packet_length_min": 40,
            "packet_length_max": 80,
            "packet_length_mean": 50.0,
            "packet_length_std": 10.0,
            "forward_packet_length_mean": 60.0,
            "backward_packet_length_mean": 40.0,
            "flow_iat_mean": 2.0,
            "flow_iat_std": 0.2,
            "flow_iat_min": 1.0,
            "flow_iat_max": 3.0,
            "forward_iat_mean": 2.0,
            "backward_iat_mean": 2.0,
            "syn_count": 1,
            "ack_count": 1,
            "forward_backward_packet_ratio": float(forward_count),
            "forward_backward_byte_ratio": float(forward_bytes / backward_bytes),
        }
    )
    return row


def make_fixture(groups: int = 24) -> pd.DataFrame:
    """All groups contain both binary classes; feature vectors are unique."""
    if not 16 <= groups <= 100:
        raise ValueError("Use between 16 and 100 independent fixture groups")
    records = []
    for group in range(groups):
        for i in range(12):
            family = "BENIGN" if i < 6 else ("Probe" if i < 9 else "DoS")
            records.append(
                {
                    **make_demo_flow(group, i),
                    "label": family,
                    "group_id": f"synthetic-demo-group-{group:03d}",
                }
            )
    return pd.DataFrame(records, columns=[*FEATURE_NAMES, "label", "group_id"])


def run_demo(directory: Path, *, groups: int = 24, folds: int = 3) -> dict[str, object]:
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / "synthetic-demo-only.csv"
    make_fixture(groups).to_csv(source, index=False)
    splits = directory / "splits"
    prepare_dataset(source, splits)
    model_dir = directory / "model"
    trained = train_from_splits(splits, model_dir, folds=folds)
    manifest_path = model_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["synthetic_demo_only"] = True
    manifest["training_data_kind"] = "synthetic_demo"
    manifest["model_status"] = "synthetic_demo_not_security_validated"
    manifest["demo_warning"] = DEMO_WARNING
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    bundle = load_bundle(model_dir, trust_local_artifact=True)
    assessment = predict_features(bundle, make_demo_flow(50, 5))
    assert assessment["state"] in {
        "NORMAL",
        "KNOWN_THREAT",
        "NOVEL_ANOMALY",
        "UNCERTAIN",
    }
    report = {
        "status": "software_smoke_passed_not_detection_accuracy",
        "warning": DEMO_WARNING,
        "synthetic_rows": groups * 12,
        "model_dir": str(model_dir),
        "model_bundle_sha256": trained["bundle_sha256"],
        "example_flow_state": assessment["state"],
        "metrics_not_reported_as_real": True,
    }
    (directory / "demo_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("artifacts/demo/nohack-smoke")
    )
    parser.add_argument("--groups", type=int, default=24)
    parser.add_argument("--folds", type=int, default=3)
    args = parser.parse_args()
    print(
        json.dumps(
            run_demo(args.output_dir, groups=args.groups, folds=args.folds), indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
