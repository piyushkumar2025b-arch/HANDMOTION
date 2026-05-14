"""Storage helpers for local JSONL/CSV logs and optional Supabase access."""

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping


def _json_default(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class JsonlEventStore:
    def __init__(self, path: str | os.PathLike):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: Mapping | object) -> None:
        payload = asdict(event) if is_dataclass(event) else dict(event)
        payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=_json_default, sort_keys=True) + "\n")

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        rows = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows


def export_csv(rows: Iterable[Mapping], path: str | os.PathLike) -> Path:
    rows = [dict(row) for row in rows]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return output


def export_json(rows: Iterable[Mapping], path: str | os.PathLike) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(list(rows), handle, indent=2, default=_json_default)
    return output


class OptionalSupabaseStore:
    """Small wrapper that only imports supabase when used."""

    def __init__(self, url: str | None = None, key: str | None = None):
        self.url = url or os.getenv("SUPABASE_URL", "")
        self.key = key or os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.url or not self.key:
                raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY or SUPABASE_ANON_KEY")
            try:
                from supabase import create_client
            except ImportError as exc:
                raise RuntimeError("Install supabase with: pip install supabase") from exc
            self._client = create_client(self.url, self.key)
        return self._client

    def insert(self, table: str, rows: Iterable[Mapping] | Mapping):
        payload = dict(rows) if isinstance(rows, Mapping) else [dict(row) for row in rows]
        return self.client.table(table).insert(payload).execute()

    def recent(self, table: str, limit: int = 100):
        return self.client.table(table).select("*").order("created_at", desc=True).limit(limit).execute().data

