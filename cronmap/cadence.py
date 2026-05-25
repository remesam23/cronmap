"""Cadence analysis: detect the firing interval pattern of a cron entry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry


def _count_field(field: str, lo: int, hi: int) -> int:
    """Return number of distinct values a cron field resolves to."""
    if field == "*":
        return hi - lo + 1
    if field.startswith("*/"):
        step = int(field[2:])
        return len(range(lo, hi + 1, step))
    if "-" in field and "/" in field:
        range_part, step_part = field.split("/")
        a, b = range_part.split("-")
        return len(range(int(a), int(b) + 1, int(step_part)))
    if "-" in field:
        a, b = field.split("-")
        return int(b) - int(a) + 1
    if "," in field:
        return len(field.split(","))
    return 1


def fires_per_hour(entry: CronEntry) -> int:
    """Return how many times the entry fires within a single hour."""
    return _count_field(entry.minute, 0, 59)


def fires_per_day(entry: CronEntry) -> int:
    """Return how many times the entry fires within a single day."""
    minutes = _count_field(entry.minute, 0, 59)
    hours = _count_field(entry.hour, 0, 23)
    return minutes * hours


@dataclass
class CadenceResult:
    entry: CronEntry
    fires_per_hour: int
    fires_per_day: int
    fires_per_week: int
    label: str

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"CadenceResult(command={self.entry.command!r}, "
            f"label={self.label!r}, "
            f"fires_per_week={self.fires_per_week})"
        )

    def __str__(self) -> str:
        return (
            f"{self.entry.command}: {self.label} "
            f"({self.fires_per_week}x/week)"
        )


_LABELS = [
    (60 * 24 * 7, "continuous"),
    (60 * 24, "hourly or more"),
    (24, "multiple times daily"),
    (2, "daily"),
    (1, "weekly or less"),
]


def _label(fpw: int) -> str:
    for threshold, name in _LABELS:
        if fpw >= threshold:
            return name
    return "weekly or less"


def analyze_cadence(entry: CronEntry) -> CadenceResult:
    """Compute full cadence metrics for a single entry."""
    fph = fires_per_hour(entry)
    fpd = fires_per_day(entry)
    days = _count_field(entry.dow, 0, 6)
    fpw = fpd * days
    return CadenceResult(
        entry=entry,
        fires_per_hour=fph,
        fires_per_day=fpd,
        fires_per_week=fpw,
        label=_label(fpw),
    )


def analyze_all(entries: List[CronEntry]) -> List[CadenceResult]:
    """Return cadence results for every entry."""
    return [analyze_cadence(e) for e in entries]
