"""Synthetic end-to-end ML smoke: never represent fixture metrics as accuracy."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("sklearn")
pytest.importorskip("xgboost")
pytest.importorskip("lightgbm")
pytest.importorskip("catboost")
pytest.importorskip("pyarrow")

from nohack.datasets.prepare import prepare_dataset, validate_canonical_table
from nohack.features import FEATURE_NAMES
from nohack.features.flow_schema import FEATURE_SPECS
from nohack.inference.hybrid import load_bundle, predict_features
from nohack.training.hybrid import train_from_splits


def sample_row(group: int, index: int) -> dict[str, object]:
    sample: dict[str, object] = {
        name: (0.0 if kind == "float" else 0)
        for name, kind in FEATURE_SPECS if kind != "category"
    }
    sample.update({
        "protocol": "TCP",
        "duration_ms": float(10 + group + index / 100),
        "src_port": 2000 + group * 20 + index,
        "dst_port": 443,
        "forward_packet_count": 2 + index,
        "backward_packet_count": 1,
        "total_packet_count": 3 + index,
        "forward_byte_count": 80 + 40 * index,
        "backward_byte_count": 40,
        "total_byte_count": 120 + 40 * index,
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
        "forward_backward_packet_ratio": float(2 + index),
        "forward_backward_byte_ratio": float(2 + index),
    })
    return sample


def test_verified_schema_rejects_cicflowmeter_shortcut() -> None:
    with pytest.raises(ValueError, match="Schema mismatch"):
        validate_canonical_table(pd.DataFrame({
            "Flow Duration": [10], "Label": ["BENIGN"]
        }))


def test_end_to_end_synthetic_training_and_model_contract(tmp_path: Path) -> None:
    rows = []
    for group in range(24):
        for i in range(12):
            label = "BENIGN" if i < 6 else ("DoS" if i < 9 else "Probe")
            rows.append({
                **sample_row(group, i), "label": label,
                "group_id": f"fixture-group-{group:03}",
            })
    source = tmp_path / "synthetic-labeled.csv"
    pd.DataFrame(rows, columns=[*FEATURE_NAMES, "label", "group_id"]).to_csv(
        source, index=False
    )
    splits = tmp_path / "splits"
    prepare_dataset(source, splits)
    manifest = json.loads((splits / "manifest.json").read_text())
    assert manifest["splits"]["test"]["rows"] > 0
    model_dir = tmp_path / "model"
    report = train_from_splits(splits, model_dir, folds=3)
    assert report["metrics"]["rows"] > 0
    assert report["bundle_sha256"]
    with pytest.raises(PermissionError):
        load_bundle(model_dir)
    model = load_bundle(model_dir, trust_local_artifact=True)
    prediction = predict_features(model, sample_row(99, 1))
    assert prediction["state"] in {
        "NORMAL", "KNOWN_THREAT", "NOVEL_ANOMALY", "UNCERTAIN"
    }
    assert 0 <= prediction["risk_score"] <= 100
    assert prediction["risk_score_is_probability"] is False
    with pytest.raises(ValueError, match="missing"):
        predict_features(model, {"duration_ms": 10.0})
    # A corrupted local artifact must fail integrity checking before joblib loads.
    (model_dir / "hybrid.joblib").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="verification"):
        load_bundle(model_dir, trust_local_artifact=True)
