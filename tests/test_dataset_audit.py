"""No-Hack dataset audit contract tests using synthetic CSV metadata."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from nohack.datasets.csv_audit import audit_csv, sha256_file
from nohack.features import schema_fingerprint


def test_audit_reports_only_sampled_labels_without_inventing_mapping(tmp_path: Path) -> None:
    source = tmp_path / "sample.csv"
    source.write_text(
        "\ufeff Label ,Flow Duration,duration_ms,Total Fwd Packets\n"
        "BENIGN,10,20,1\nAttack,30,40,2\n", encoding="utf-8"
    )
    report = audit_csv(source, sample_rows=1)
    assert report["sampled_rows"] == 1
    assert report["sampled_labels"] == {"BENIGN": 1}
    assert report["csv_headers"] == [
        "Label", "Flow Duration", "duration_ms", "Total Fwd Packets"
    ]
    assert report["exact_header_overlap_only"] == ["duration_ms"]
    assert report["deployable_mapping_verified"] is False
    assert report["schema_sha256_target"] == schema_fingerprint()
    assert report["file_sha256"] is None
    assert report["size_bytes"] > 0


def test_duplicate_headers_bad_rows_and_absent_label(tmp_path: Path) -> None:
    source = tmp_path / "sample.csv"
    source.write_text(
        "Some, some,Label,LABEL\n1,2,x,y\nnot-enough\n", encoding="utf-8"
    )
    report = audit_csv(source)
    assert report["duplicate_normalized_headers"] == ["label", "some"]
    assert report["label_column_count"] == 2
    assert report["sampled_rows"] == 2
    assert report["sampled_malformed_width_rows"] == 1
    assert report["sampled_labels"] == {}


def test_hash_is_opt_in_and_content_based(tmp_path: Path) -> None:
    source = tmp_path / "sample.csv"
    source.write_text("Label\nBENIGN\n", encoding="utf-8")
    expect = hashlib.sha256(source.read_bytes()).hexdigest()
    assert sha256_file(source) == expect
    assert audit_csv(source, hash_file=True)["file_sha256"] == expect


@pytest.mark.parametrize("rows", [0, 100001, True, 0.5])
def test_invalid_sample_limit(tmp_path: Path, rows: object) -> None:
    source = tmp_path / "sample.csv"
    source.write_text("Label\nBENIGN\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sample_rows"):
        audit_csv(source, sample_rows=rows)  # type: ignore[arg-type]


def test_rejects_empty_and_non_csv_files(tmp_path: Path) -> None:
    source = tmp_path / "empty.csv"
    source.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="nonempty header"):
        audit_csv(source)
    with pytest.raises(ValueError, match="existing CSV"):
        audit_csv(tmp_path / "missing.csv")
    source = tmp_path / "notcsv.txt"
    source.write_text("label\nbenign", encoding="utf-8")
    with pytest.raises(ValueError, match="existing CSV"):
        audit_csv(source)


def test_rejects_malformed_utf8(tmp_path: Path) -> None:
    source = tmp_path / "invalid.csv"
    source.write_bytes(b"Label\n\xff\n")
    with pytest.raises(ValueError, match="decoding or parsing"):
        audit_csv(source)
