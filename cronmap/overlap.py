"""Detect overlapping or conflicting cron entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from cronmap.parser import CronEntry


@dataclass
class OverlapResult:
    entry_a: CronEntry
    entry_b: CronEntry
    shared_minutes: List[int] = field(default_factory=list)
    shared_hours: List[int] = field(default_factory=list)
    shared_days: List[int] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.shared_minutes and self.shared_hours and self.shared_days)

    def __repr__(self) -> str:
        return (
            f"OverlapResult(a={self.entry_a.command!r}, b={self.entry_b.command!r}, "
            f"slots={len(self.shared_hours) * len(self.shared_minutes)})"
        )


def _expand(values: List[int], wildcard_range: range) -> List[int]:
    """Return sorted unique integers; if the list is empty treat as wildcard."""
    if not values:
        return list(wildcard_range)
    return sorted(set(values))


def _intersect(a: List[int], b: List[int]) -> List[int]:
    return sorted(set(a) & set(b))


def find_overlap(a: CronEntry, b: CronEntry) -> OverlapResult:
    """Return an OverlapResult describing the time slots shared by two entries."""
    minutes_a = _expand(a.minutes, range(60))
    minutes_b = _expand(b.minutes, range(60))

    hours_a = _expand(a.hours, range(24))
    hours_b = _expand(b.hours, range(24))

    days_a = _expand(a.days_of_week, range(7))
    days_b = _expand(b.days_of_week, range(7))

    return OverlapResult(
        entry_a=a,
        entry_b=b,
        shared_minutes=_intersect(minutes_a, minutes_b),
        shared_hours=_intersect(hours_a, hours_b),
        shared_days=_intersect(days_a, days_b),
    )


def detect_overlaps(entries: List[CronEntry]) -> List[OverlapResult]:
    """Return all pairs of entries that share at least one execution slot."""
    results: List[OverlapResult] = []
    for i, a in enumerate(entries):
        for b in entries[i + 1 :]:
            result = find_overlap(a, b)
            if result:
                results.append(result)
    return results


def format_overlap_report(overlaps: List[OverlapResult], *, color: bool = False) -> str:
    """Render a human-readable overlap report."""
    if not overlaps:
        return "No overlapping entries detected."

    RED = "\033[31m" if color else ""
    RESET = "\033[0m" if color else ""
    lines = [f"{RED}Overlapping entries detected:{RESET}"]
    for ov in overlaps:
        slot_count = len(ov.shared_hours) * len(ov.shared_minutes) * len(ov.shared_days)
        lines.append(
            f"  {ov.entry_a.command!r} <-> {ov.entry_b.command!r} "
            f"({slot_count} shared slot(s) per week)"
        )
    return "\n".join(lines)
