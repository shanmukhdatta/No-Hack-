"""Check code presence and external acceptance without inventing tests."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Component:
    name: str
    paths: tuple[str, ...]
    requires_external_acceptance: bool = False


COMPONENTS = (
    Component("Canonical flow features", ("src/nohack/features/flow_schema.py",)),
    Component("Authorized capture", ("src/nohack/capture/session.py",), True),
    Component("PCAP replay", ("src/nohack/capture/replay.py",), True),
    Component("Private annotation workflow", ("scripts/review_pcap_annotations.py",), True),
    Component("Dataset audit/splitting", ("src/nohack/datasets/prepare.py",), True),
    Component("Beginner-to-advanced notebooks", ("notebooks/01_dataset_audit.ipynb", "notebooks/05_hybrid_stack_export.ipynb")),
    Component("Baseline experiments", ("src/nohack/models/baselines.py",)),
    Component("Stacked hybrid training", ("src/nohack/training/hybrid.py",), True),
    Component("Trusted model inference", ("src/nohack/inference/hybrid.py",), True),
    Component("Measured latency", ("src/nohack/evaluation/latency.py",), True),
    Component("Heldout evaluation", ("src/nohack/evaluation/report.py",), True),
    Component("XGB explanation", ("src/nohack/explainability/shap_report.py",), True),
    Component("Local SQLite assessment", ("src/nohack/storage/predictions.py",)),
    Component("Local API", ("src/nohack/api/app.py",), True),
    Component("Native Messaging", ("src/nohack/native_host.py",), True),
    Component("Chrome extension", ("extension/manifest.json", "extension/ui.js"), True),
    Component("UI alert gate", ("src/nohack/monitoring/alerts.py",)),
    Component("Data drift", ("src/nohack/monitoring/drift.py",), True),
    Component("MLflow logging", ("scripts/log_experiment.py",), True),
    Component("Desktop preview (optional)", ("src/nohack/ui/desktop.py",), True),
    Component("Chrome ZIP", ("scripts/package_extension.py",), True),
    Component("Native host build", (".github/workflows/package-preview.yml",), True),
    Component("GitHub Pages", ("site/index.html", ".github/workflows/pages.yml"), True),
    Component("Security review", ("docs/SECURITY_REVIEW.md",), True),
)


def project_inventory(root: Path) -> dict[str, Any]:
    """Check source existence only. No compilation/testing/deployment is implied."""
    records = []
    for component in COMPONENTS:
        missing = [name for name in component.paths if not (root / name).is_file()]
        records.append(
            {
                "name": component.name,
                "source_present": not missing,
                "missing_files": missing,
                "external_acceptance_required": component.requires_external_acceptance,
                "acceptance_verified_by_inventory": False,
            }
        )
    return {
        "report_kind": "source_inventory_not_test_or_release_evidence",
        "components": records,
        "present": sum(int(item["source_present"]) for item in records),
        "total": len(records),
        "production_ready": False,
        "external_validation_pending": True,
    }


def artifact_digest(path: Path) -> str:
    """Streaming SHA256 for a chosen local release artifact."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def self_attested_acceptance(evidence_file: Path) -> dict[str, Any]:
    """Record user attestations, explicitly not independent verification."""
    data = json.loads(evidence_file.read_text(encoding="utf-8"))
    gates = (
        "real_label_provenance",
        "independent_heldout_evaluation",
        "false_positive_review",
        "local_capture_parity",
        "windows_chrome_integration",
        "package_security_review",
        "published_site_checked",
    )
    if not isinstance(data, dict) or set(data) != set(gates):
        raise ValueError("Require each external acceptance gate explicitly")
    for key in gates:
        record = data[key]
        if not isinstance(record, dict) or set(record) != {"accepted", "evidence"}:
            raise ValueError(f"Invalid external acceptance record: {key}")
        if type(record["accepted"]) is not bool or not isinstance(record["evidence"], str):
            raise ValueError(f"Invalid external acceptance value: {key}")
        if record["accepted"] and not record["evidence"].strip():
            raise ValueError(f"Accepted gate lacks evidence reference: {key}")
    return {
        "report_kind": "operator_self_attestation_not_independent_certification",
        "claimed_accepted_gates": sum(int(data[key]["accepted"]) for key in gates),
        "total_gates": len(gates),
        "all_self_attested": all(data[key]["accepted"] for key in gates),
        "independently_verified": False,
    }
