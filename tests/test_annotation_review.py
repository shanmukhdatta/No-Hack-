"""Manual label evidence is required; generated templates start unreviewed."""
from __future__ import annotations

import csv
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.review_pcap_annotations import (
    APPROVED_FIELDS,
    REVIEW_FIELDS,
    approve_review,
    write_review_template,
)


def test_annotation_gates_private_metadata(tmp_path: Path) -> None:
    flow = SimpleNamespace(
        context=SimpleNamespace(
            flow_id="abc123", src_ip="192.0.2.1", dst_ip="192.0.2.2",
            started_at_ns=10, ended_at_ns=20,
        ),
        features={"protocol": "TCP", "src_port": 1234, "dst_port": 443},
    )
    template, approved = tmp_path / "private.csv", tmp_path / "labels.csv"
    assert write_review_template([SimpleNamespace(flow=flow)], template) == 1
    with pytest.raises(ValueError, match="Every flow"):
        approve_review(template, approved)
    with template.open(newline="", encoding="utf-8") as fh:
        records = list(csv.DictReader(fh))
    records[0].update(
        label="BENIGN", group_id="independently-checked-session-1",
        source_evidence="review-log-line-123", verification_status="VERIFIED"
    )
    with template.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(REVIEW_FIELDS))
        writer.writeheader()
        writer.writerows(records)
    assert approve_review(template, approved) == 1
    with approved.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == list(APPROVED_FIELDS)
        assert list(reader)[0]["label"] == "BENIGN"
    assert "192.0.2.1" not in approved.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="exists"):
        approve_review(template, approved)
