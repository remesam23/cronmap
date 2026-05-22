"""Snapshot support: save and load named crontab snapshots for diffing."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import List, Optional

from cronmap.parser import CronEntry, parse_crontab


@dataclass
class Snapshot:
    name: str
    entries: List[CronEntry]
    created_at: str  # ISO-8601 string

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "entries": [
                {
                    "minute": e.minute,
                    "hour": e.hour,
                    "day_of_month": e.day_of_month,
                    "month": e.month,
                    "day_of_week": e.day_of_week,
                    "command": e.command,
                    "raw": e.raw,
                }
                for e in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        entries = [
            CronEntry(
                minute=e["minute"],
                hour=e["hour"],
                day_of_month=e["day_of_month"],
                month=e["month"],
                day_of_week=e["day_of_week"],
                command=e["command"],
                raw=e["raw"],
            )
            for e in data["entries"]
        ]
        return cls(name=data["name"], entries=entries, created_at=data["created_at"])


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Serialise a Snapshot to *path* as JSON."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(path: str) -> Snapshot:
    """Deserialise a Snapshot from a JSON file at *path*."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot.from_dict(data)


def snapshot_from_text(name: str, text: str, created_at: Optional[str] = None) -> Snapshot:
    """Create a Snapshot from raw crontab text."""
    import datetime

    entries = parse_crontab(text)
    ts = created_at or datetime.datetime.utcnow().isoformat()
    return Snapshot(name=name, entries=entries, created_at=ts)
