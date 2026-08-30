"""Immediate, resumable SQLite cache for model coalition evaluations."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class CacheKey:
    model_id: str
    model_revision: str
    prompt_template_hash: str
    memory_bank_id: str
    query_id: str
    coalition_mask: str
    generation_config: Mapping[str, object]
    seed: int
    code_commit: str | None
    request_sha256: str = "legacy-unspecified"
    runtime_sha256: str = "legacy-unspecified"
    scoring_sha256: str = "legacy-unspecified"
    schema_version: int = 2

    def canonical_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CachedEvaluation:
    raw_output: str
    parsed_action: str | None
    reward: float
    latency_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    timestamp_utc: str


class EvaluationCache:
    """SQLite cache that commits every new model result before returning."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                cache_key TEXT PRIMARY KEY,
                key_json TEXT NOT NULL,
                raw_output TEXT NOT NULL,
                parsed_action TEXT,
                reward REAL NOT NULL,
                latency_seconds REAL NOT NULL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                timestamp_utc TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def get(self, key: CacheKey) -> CachedEvaluation | None:
        row = self._connection.execute(
            """
            SELECT raw_output, parsed_action, reward, latency_seconds,
                   input_tokens, output_tokens, timestamp_utc
            FROM evaluations WHERE cache_key = ?
            """,
            (key.digest(),),
        ).fetchone()
        if row is None:
            return None
        return CachedEvaluation(
            raw_output=str(row[0]),
            parsed_action=row[1],
            reward=float(row[2]),
            latency_seconds=float(row[3]),
            input_tokens=row[4],
            output_tokens=row[5],
            timestamp_utc=str(row[6]),
        )

    def put(
        self,
        key: CacheKey,
        *,
        raw_output: str,
        parsed_action: str | None,
        reward: float,
        latency_seconds: float,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> CachedEvaluation:
        timestamp = datetime.now(timezone.utc).isoformat()
        self._connection.execute(
            """
            INSERT OR IGNORE INTO evaluations (
                cache_key, key_json, raw_output, parsed_action, reward,
                latency_seconds, input_tokens, output_tokens, timestamp_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key.digest(),
                key.canonical_json(),
                raw_output,
                parsed_action,
                float(reward),
                float(latency_seconds),
                input_tokens,
                output_tokens,
                timestamp,
            ),
        )
        self._connection.commit()
        stored = self.get(key)
        if stored is None:
            raise RuntimeError("cache write did not persist")
        return stored

    def count(self) -> int:
        return int(self._connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0])

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "EvaluationCache":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
