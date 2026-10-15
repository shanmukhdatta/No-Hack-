"""Score stored authorized NoHackFlow observations without changing raw records."""
from __future__ import annotations

import json
from pathlib import Path

from nohack.inference.hybrid import load_bundle, predict_features
from nohack.storage.predictions import PredictionStore


def score_database(bundle: Path, database: Path, *, max_rows: int = 1000) -> dict[str, object]:
    if not 1 <= max_rows <= 1_000_000:
        raise ValueError("max_rows must be in 1..1000000")
    model = load_bundle(bundle, trust_local_artifact=True)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    total = 0
    with PredictionStore(database) as store:
        while total < max_rows:
            pending = store.unscored(limit=min(100, max_rows - total))
            if not pending:
                break
            for observation_id, features in pending:
                result = predict_features(model, features)
                store.add(observation_id, result, manifest["bundle_sha256"])
                total += 1
    return {"scored_flows": total, "database": str(database),
            "model_sha256": manifest["bundle_sha256"]}
