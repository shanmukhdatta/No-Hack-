"""Read-only local telemetry API plus explicitly authorized offline scoring.

The Chrome MV3 extension does NOT call this API. It uses restricted Native Messaging.
Run only on loopback, and never publish this app on a public address.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from nohack.features import FEATURE_NAMES
from nohack.storage.predictions import recent_assessments


def create_app(
    database: Path | None = None,
    model_dir: Path | None = None,
    *,
    trust_local_model: bool = False,
) -> Any:
    """Build a read-only API until an explicitly trusted model is present."""
    from fastapi import FastAPI, HTTPException

    database = database or Path.home() / ".nohack" / "observations.db"
    app = FastAPI(
        title="No Hack local telemetry",
        description="Loopback-only network-flow assessments; not browser tab verdicts",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
    )
    model: dict[str, Any] | None = None
    model_sha: str | None = None
    load_error: str | None = None

    if model_dir is not None:
        if not trust_local_model:
            load_error = "A trusted locally trained model must be explicitly approved"
        else:
            try:
                from nohack.inference.hybrid import load_bundle

                model = load_bundle(model_dir, trust_local_artifact=True)
                manifest = json.loads((model_dir / "manifest.json").read_text("utf-8"))
                model_sha = str(manifest["bundle_sha256"])
            except (OSError, ValueError, KeyError, ImportError) as exc:
                load_error = type(exc).__name__

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "service": "nohack-local-api",
            "ready": True,
            "model_connected": model is not None,
        }

    @app.get("/model/status")
    def model_status() -> dict[str, object]:
        return {
            "model_connected": model is not None,
            "model_sha256": model_sha,
            "status": "ready" if model is not None else "model_not_connected",
            "reason": load_error,
            "scope": "network_flow_only",
        }

    @app.get("/assessments")
    def assessments(limit: int = 10) -> dict[str, object]:
        if not 1 <= limit <= 20:
            raise HTTPException(status_code=422, detail="limit must be 1..20")
        return {
            "scope": "network_flows_not_browser_tabs",
            "items": recent_assessments(database, limit),
        }

    @app.post("/predict")
    def predict(request: dict[str, Any]) -> dict[str, object]:
        """Optional local manual test; opt-in token is required for every request."""
        # Route-level authentication is enforced by an ASGI middleware below.
        if model is None:
            raise HTTPException(status_code=503, detail="model_not_connected")
        features = request.get("features")
        if not isinstance(features, dict) or set(features) != set(FEATURE_NAMES):
            raise HTTPException(status_code=422, detail="NoHackFlow schema mismatch")
        from nohack.inference.hybrid import predict_features

        try:
            return predict_features(model, features)
        except (ValueError, TypeError, KeyError):
            raise HTTPException(
                status_code=422, detail="Invalid NoHackFlow values"
            ) from None

    @app.middleware("http")
    async def protect_predict(request: Any, call_next: Any) -> Any:
        if request.url.path == "/predict":
            import hmac

            from fastapi.responses import JSONResponse

            secret = os.environ.get("NOHACK_API_TOKEN", "")
            received = request.headers.get("x-nohack-token", "")
            if len(secret) < 24 or not hmac.compare_digest(received, secret):
                return JSONResponse(
                    {"detail": "Local test token required"}, status_code=401
                )
        return await call_next(request)

    return app
