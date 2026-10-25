"""One-command, explicitly sourced NoHackFlow experiment orchestration.

Use only externally verified canonical labels. No attack labels are invented,
and no synthetic fixture is reported as a real detector. Never overwrite a run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nohack.datasets.prepare import prepare_dataset
from nohack.models.baselines import run_baselines
from nohack.training.hybrid import train_from_splits


def run_experiment(
    source: Path, output: Path, *, seed: int = 42, folds: int = 4
) -> dict[str, object]:
    """Prepare, train baselines + hybrid and record immutable run information."""
    if output.exists() and any(output.iterdir()):
        raise ValueError("Run directory is not empty; choose a new output path")
    if not source.is_file():
        raise FileNotFoundError("Supply a verified labeled canonical CSV or Parquet")
    import pandas as pd

    splits = output / "splits"
    dataset_manifest = prepare_dataset(source, splits, seed=seed)
    train = pd.read_parquet(splits / "train.parquet")
    val = pd.read_parquet(splits / "val.parquet")
    baseline_metrics = run_baselines(train, val, seed=seed)
    model_manifest = train_from_splits(splits, output / "model", seed=seed, folds=folds)
    result: dict[str, object] = {
        "schema": "nohack-experiment-v1",
        "dataset_source_sha256": dataset_manifest["source_sha256"],
        "data_split_manifest": "splits/manifest.json",
        "trained_model_manifest": "model/manifest.json",
        "baseline_metrics_scope": "validation_only",
        "baseline_validation_metrics": baseline_metrics,
        "hybrid_heldout_metrics": model_manifest["metrics"],
        "model_validation_status": model_manifest["model_status"],
        "external_windows_validation": False,
        "synthetic_only_metric_warning": (
            "These metrics reflect only the data you supplied. "
            "Confirm source authenticity and external Windows parity."
        ),
    }
    (output / "experiment.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--folds", type=int, default=4)
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()
    report = run_experiment(a.input, a.output, folds=a.folds, seed=a.seed)
    print(
        json.dumps(
            {
                "model_validation_status": report["model_validation_status"],
                "model_manifest": str(a.output / "model" / "manifest.json"),
                "experiment_report": str(a.output / "experiment.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
