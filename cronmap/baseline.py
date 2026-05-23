"""Baseline: capture and compare a reference snapshot of a crontab."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from cronmap.parser import parse_crontab, CronEntry
from cronmap.diff import CronDiff


@dataclass
class Baseline:
    """A named, timestamped reference set of cron entries."""

    name: str
    created_at: str
    entries: List[CronEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "entries": [
                {
                    "minute": e.minute,
                    "hour": e.hour,
                    "dom": e.dom,
                    "month": e.month,
                    "dow": e.dow,
                    "command": e.command,
                }
                for e in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Baseline":
        entries = [
            CronEntry(
                minute=e["minute"],
                hour=e["hour"],
                dom=e["dom"],
                month=e["month"],
                dow=e["dow"],
                command=e["command"],
            )
            for e in data.get("entries", [])
        ]
        return cls(name=data["name"], created_at=data["created_at"], entries=entries)


def capture_baseline(text: str, name: str = "default", timestamp: Optional[str] = None) -> Baseline:
    """Parse *text* and return a Baseline."""
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    entries = parse_crontab(text)
    return Baseline(name=name, created_at=ts, entries=entries)


def save_baseline(baseline: Baseline, path: str) -> None:
    """Persist *baseline* to *path* as JSON."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(baseline.to_dict(), fh, indent=2)


def load_baseline(path: str) -> Baseline:
    """Load a Baseline from a JSON file at *path*."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Baseline.from_dict(data)


def compare_to_baseline(current: List[CronEntry], baseline: Baseline) -> CronDiff:
    """Return a CronDiff between *current* entries and the *baseline*."""
    return CronDiff(before=baseline.entries, after=current)
