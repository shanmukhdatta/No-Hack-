"""Local SQLite observations; no threat predictions or raw endpoints stored."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Self

from nohack.collector.flows import CompletedFlow


class ObservationStore:
    """Transactional local store for completed metadata-derived flows.

    The model state is explicitly UNASSESSED until a validated inference
    release exists. Raw source/destination IPs and process names are omitted.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> Self:
        if self.path.exists() and not self.path.is_file():
            raise ValueError("SQLite path must reference a file")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path), timeout=5.0)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS flow_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flow_id TEXT NOT NULL,
                started_at_ns INTEGER NOT NULL,
                ended_at_ns INTEGER NOT NULL,
                feature_schema_version TEXT NOT NULL,
                features_json TEXT NOT NULL,
                completion_reason TEXT NOT NULL,
                assessment TEXT NOT NULL CHECK (assessment = 'UNASSESSED'),
                source TEXT NOT NULL CHECK (source IN ('replay', 'live'))
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_flow_observed_time "
            "ON flow_observations(ended_at_ns)"
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.connection is None:
            return
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()
        self.connection = None

    def _connection(self) -> sqlite3.Connection:
        if self.connection is None:
            raise RuntimeError("ObservationStore must be opened with 'with'")
        return self.connection

    def insert(self, record: CompletedFlow, *, source: str) -> int:
        if source not in {"replay", "live"}:
            raise ValueError("Invalid observation source")
        snapshot = record.flow
        ctx = snapshot.context
        cursor = self._connection().execute(
            """
            INSERT INTO flow_observations
                (flow_id, started_at_ns, ended_at_ns, feature_schema_version,
                 features_json, completion_reason, assessment, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ctx.flow_id,
                ctx.started_at_ns,
                ctx.ended_at_ns,
                snapshot.feature_schema_version,
                json.dumps(dict(snapshot.features), allow_nan=False),
                record.reason,
                "UNASSESSED",
                source,
            ),
        )
        assert cursor.lastrowid is not None
        return cursor.lastrowid

    def recent(self, *, limit: int = 100) -> list[dict[str, object]]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        rows = self._connection().execute(
            """
            SELECT id, flow_id, started_at_ns, ended_at_ns,
                   feature_schema_version, features_json,
                   completion_reason, assessment, source
            FROM flow_observations ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        )
        return [
            {
                "id": row[0],
                "flow_id": row[1],
                "started_at_ns": row[2],
                "ended_at_ns": row[3],
                "feature_schema_version": row[4],
                "features": json.loads(row[5]),
                "completion_reason": row[6],
                "assessment": row[7],
                "source": row[8],
            }
            for row in rows
        ]

    def delete_ended_before(self, cutoff_ns: int) -> int:
        if type(cutoff_ns) is not int or cutoff_ns < 0:
            raise ValueError("cutoff_ns must be a nonnegative integer")
        cursor = self._connection().execute(
            "DELETE FROM flow_observations WHERE ended_at_ns < ?", (cutoff_ns,)
        )
        return cursor.rowcount
