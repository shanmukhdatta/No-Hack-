"""Simple binary baselines for comparison with No Hack's hybrid stack."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from nohack.evaluation.report import evaluate_binary
from nohack.features import FEATURE_NAMES
from nohack.models.hybrid import encode_flow


def binary_labels(frame: pd.DataFrame) -> np.ndarray:
    if "label" not in frame:
        raise ValueError("Missing verified labels")
    return frame["label"].str.strip().str.upper().ne("BENIGN").astype(int).to_numpy()


def run_baselines(
    train: pd.DataFrame, validation: pd.DataFrame, *, seed: int = 42
) -> dict[str, dict[str, Any]]:
    """Fit on training partition; report validation only, no test selection."""
    if set(train["group_id"]) & set(validation["group_id"]):
        raise ValueError("Group leakage between train and validation")
    x_train = encode_flow(train.loc[:, list(FEATURE_NAMES)])
    x_val = encode_flow(validation.loc[:, list(FEATURE_NAMES)])
    y_train, y_val = binary_labels(train), binary_labels(validation)
    if np.unique(y_train).size != 2 or np.unique(y_val).size != 2:
        raise ValueError("Both classes required in both partitions")
    candidates = {
        "logistic_regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=1000, class_weight="balanced", random_state=seed
            ),
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=150, class_weight="balanced", random_state=seed, n_jobs=2
        ),
    }
    metrics: dict[str, dict[str, Any]] = {}
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        metrics[name] = evaluate_binary(y_val, model.predict_proba(x_val)[:, 1])
    return metrics
