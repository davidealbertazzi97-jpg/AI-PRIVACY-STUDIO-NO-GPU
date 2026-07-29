from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from .config import PATHS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class JobStore:
    def __init__(self) -> None:
        self.path = PATHS.database
        self._lock = threading.RLock()
        self._init_schema()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._lock, self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    engine TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0,
                    stage TEXT NOT NULL DEFAULT '',
                    input_name TEXT NOT NULL,
                    input_path TEXT NOT NULL,
                    input_size INTEGER NOT NULL DEFAULT 0,
                    output_path TEXT,
                    bundle_path TEXT,
                    result_json TEXT NOT NULL DEFAULT '{}',
                    options_json TEXT NOT NULL DEFAULT '{}',
                    error TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_created
                ON jobs(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON jobs(status);
                """
            )
        self.path.chmod(0o600)

    def create(
        self,
        *,
        operation: str,
        engine: str,
        input_name: str,
        input_path: str,
        input_size: int,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        job_id = uuid.uuid4().hex
        now = utc_now()
        with self._lock, self.connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    id, created_at, updated_at, operation, engine, status,
                    progress, stage, input_name, input_path, input_size,
                    result_json, options_json
                ) VALUES (?, ?, ?, ?, ?, 'queued', 0, 'In coda', ?, ?, ?, '{}', ?)
                """,
                (
                    job_id,
                    now,
                    now,
                    operation,
                    engine,
                    input_name,
                    input_path,
                    input_size,
                    json.dumps(options or {}, ensure_ascii=False),
                ),
            )
        return self.get(job_id)

    def get(self, job_id: str) -> dict[str, Any]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._decode(row)

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
        return [self._decode(row) for row in rows]

    def queued_ids(self) -> list[str]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT id FROM jobs WHERE status = 'queued' ORDER BY created_at"
            ).fetchall()
        return [str(row["id"]) for row in rows]

    def recover_interrupted(self) -> None:
        with self._lock, self.connection() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = 'queued', stage = 'Ripresa dopo il riavvio',
                    updated_at = ?
                WHERE status = 'running'
                  AND operation NOT IN ('vault_encrypt', 'vault_decrypt')
                """,
                (utc_now(),),
            )
            conn.execute(
                """
                UPDATE jobs
                SET status = 'failed',
                    stage = 'Password non conservata: ripetere l’operazione',
                    error = ?,
                    updated_at = ?
                WHERE status IN ('running', 'queued')
                  AND operation IN ('vault_encrypt', 'vault_decrypt')
                """,
                (
                    "La cassaforte non salva mai la password. "
                    "Il lavoro interrotto deve essere reinviato.",
                    utc_now(),
                ),
            )

    def update(self, job_id: str, **changes: Any) -> dict[str, Any]:
        writable_fields = {
            "status",
            "progress",
            "stage",
            "output_path",
            "bundle_path",
            "result_json",
            "error",
        }
        unknown = set(changes) - writable_fields
        if unknown:
            raise ValueError(f"Campi non consentiti: {sorted(unknown)}")
        if "result_json" in changes and not isinstance(changes["result_json"], str):
            changes["result_json"] = json.dumps(
                changes["result_json"], ensure_ascii=False
            )
        changes["updated_at"] = utc_now()
        fields = (
            "status",
            "progress",
            "stage",
            "output_path",
            "bundle_path",
            "result_json",
            "error",
            "updated_at",
        )
        with self._lock, self.connection() as conn:
            current = conn.execute(
                """
                SELECT status, progress, stage, output_path, bundle_path,
                       result_json, error, updated_at
                FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()
            if current is None:
                raise KeyError(job_id)
            values = [changes.get(field, current[field]) for field in fields]
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, progress = ?, stage = ?, output_path = ?,
                    bundle_path = ?, result_json = ?, error = ?, updated_at = ?
                WHERE id = ?
                """,
                [*values, job_id],
            )
        return self.get(job_id)

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        for field in ("options_json", "result_json"):
            try:
                item[field.removesuffix("_json")] = json.loads(item.pop(field) or "{}")
            except json.JSONDecodeError:
                item[field.removesuffix("_json")] = {}
        item["progress"] = round(float(item["progress"]), 3)
        return item


STORE = JobStore()
