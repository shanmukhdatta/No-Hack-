"""Privacy-minimized SQLite storage for ML assessments of local flows."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Any, Self

ALLOWED_STATES = {"NORMAL", "KNOWN_THREAT", "NOVEL_ANOMALY", "UNCERTAIN"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS flow_predictions (
    observation_id INTEGER PRIMARY KEY REFERENCES flow_observations(id),
    state TEXT NOT NULL CHECK (
        state IN ('NORMAL', 'KNOWN_THREAT', 'NOVEL_ANOMALY', 'UNCERTAIN')
    ),
    risk_score INTEGER NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    known_threat_probability REAL NOT NULL,
    anomaly_percentile REAL NOT NULL,
    model_disagreement REAL NOT NULL,
    top_reasons TEXT NOT NULL,
    feature_schema_version TEXT NOT NULL,
    model_sha256 TEXT NOT NULL,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


class PredictionStore:
    def __init__(self, database: Path):
        self.database = database
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> Self:
        if not self.database.exists():
            raise ValueError("Observation database does not exist")
        self.connection = sqlite3.connect(self.database, timeout=5)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute(SCHEMA)
        return self

    def __exit__(self, typ: type[BaseException] | None, exc: BaseException | None,
                 tb: TracebackType | None) -> None:
        assert self.connection is not None
        if typ is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()
        self.connection = None

    def unscored(self, limit: int = 100) -> list[tuple[int, dict[str, Any]]]:
        if not 1 <= limit <= 1000:
            raise ValueError("Invalid batch limit")
        assert self.connection is not None
        rows = self.connection.execute(
            """
            SELECT o.id, o.features_json FROM flow_observations AS o
            LEFT JOIN flow_predictions AS p ON p.observation_id = o.id
            WHERE p.observation_id IS NULL
            ORDER BY o.id ASC LIMIT ?
            """, (limit,)
        ).fetchall()
        return [(int(i), json.loads(raw)) for i, raw in rows]

    def add(self, observation_id: int, result: dict[str, Any], model_sha256: str) -> None:
        if result["state"] not in ALLOWED_STATES:
            raise ValueError("Invalid assessment state")
        if not (0 <= result["risk_score"] <= 100):
            raise ValueError("Invalid risk score")
        assert self.connection is not None
        self.connection.execute(
            """
            INSERT INTO flow_predictions (
                observation_id, state, risk_score, known_threat_probability,
                anomaly_percentile, model_disagreement, top_reasons,
                feature_schema_version, model_sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observation_id, result["state"], result["risk_score"],
                result["known_threat_probability"], result["anomaly_percentile"],
                result["model_disagreement"], json.dumps(result["top_reasons"]),
                result["feature_schema_version"], model_sha256,
            )
        )


def recent_assessments(database: Path, limit: int = 10) -> list[dict[str, Any]]:
    """Read-only, metadata-free flow assessments for Chrome Native Messaging."""
    if not 1 <= limit <= 20 or not database.is_file():
        return []
    uri = database.resolve().as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=1) as db:
            rows = db.execute(
                """
                SELECT p.state, p.risk_score, p.created_at_utc, p.top_reasons
                FROM flow_predictions p
                JOIN flow_observations o ON o.id = p.observation_id
                ORDER BY p.observation_id DESC LIMIT ?
                """, (limit,)
            ).fetchall()
    except sqlite3.Error:
        return []
    return [
        {"state": state, "risk_score": risk,
         "observed_at": timestamp, "reasons": json.loads(reasons)}
        for state, risk, timestamp, reasons in rows
    ]
