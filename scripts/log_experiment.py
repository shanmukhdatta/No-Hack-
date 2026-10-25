"""Import a genuine finished training run into a local MLflow experiment.

This does not run model training and never invents evaluation metrics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--tracking-uri", default="sqlite:///mlflow.db")
    p.add_argument("--experiment", default="NoHackFlow real-data experiments")
    args = p.parse_args()
    import mlflow

    from nohack.datasets.prepare import _digest

    manifest_path = args.model_dir / "manifest.json"
    metrics_path = args.model_dir / "metrics.json"
    bundle_path = args.model_dir / "hybrid.joblib"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    metrics = json.loads(metrics_path.read_text("utf-8"))
    if manifest.get("bundle_sha256") != _digest(bundle_path):
        raise ValueError("Model bundle integrity check failed")
    if manifest.get("model_status") != "trained_not_windows_validated":
        raise ValueError("Unexpected model status; inspect provenance")
    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment)
    with mlflow.start_run() as run:
        mlflow.set_tag("data_provenance", "user_supplied_canonical_only")
        mlflow.set_tag("validation_status", "not_windows_validated")
        mlflow.set_tag("model_sha256", manifest["bundle_sha256"])
        mlflow.log_params(
            {
                "folds": manifest["n_folds"],
                "seed": manifest["seed"],
                "feature_schema": manifest["feature_schema_version"],
            }
        )
        for key in (
            "f1",
            "precision",
            "recall",
            "average_precision",
            "roc_auc",
            "brier",
            "false_positive_rate",
        ):
            if metrics.get(key) is not None:
                mlflow.log_metric("heldout_" + key, float(metrics[key]))
        mlflow.log_artifact(str(metrics_path), artifact_path="reports")
        mlflow.log_artifact(str(manifest_path), artifact_path="manifests")
        print(
            json.dumps(
                {"run_id": run.info.run_id, "model_sha256": manifest["bundle_sha256"]}
            )
        )


if __name__ == "__main__":
    main()
