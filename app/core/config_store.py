from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StoredConfig:
    payload: dict[str, Any]
    updated_at: str


class ConfigStore:
    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        try:
            return sqlite3.connect(self._path)
        except sqlite3.OperationalError as exc:
            raise sqlite3.OperationalError(
                f"unable to open database file: {self._path}. Check that the directory exists and is writable."
            ) from exc

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS router_config (
                    id INTEGER PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_config(self) -> StoredConfig | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT config_json, updated_at FROM router_config WHERE id = 1"
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row[0])
        return StoredConfig(payload=payload, updated_at=row[1])

    def set_config(self, payload: dict[str, Any]) -> None:
        serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO router_config (id, config_json, updated_at)
                VALUES (1, ?, datetime('now'))
                ON CONFLICT(id) DO UPDATE SET
                    config_json = excluded.config_json,
                    updated_at = excluded.updated_at
                """,
                (serialized,),
            )
            conn.commit()
