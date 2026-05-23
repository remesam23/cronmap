"""Detect scheduling conflicts — entries that fire at the exact same time."""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import List, Tuple

from cronmap.parser import CronEntry


@dataclass
class ConflictResult:
    entry_a: CronEntry
    entry_b: CronEntry
    shared_minutes: List[int]
    shared_hours: List[int]
    shared_days: List[int]

    def __bool__(self) -> bool:  # noqa: D105
        return bool(self.shared_minutes and self.shared_hours and self.shared_days)

    def __repr__(self) -> str:  # noqa: D105
        return (
            f"ConflictResult(a={self.entry_a.command!r}, "
            f"b={self.entry_b.command!r}, "
            f"overlap_slots={len(self.shared_hours) * len(self.shared_minutes)})"
        )


def _expand(field_value: str, lo: int, hi: int) -> List[int]:
    """Expand a cron field string into a sorted list of integers."""
    if field_value == "*":
        return list(range(lo, hi + 1))
    result: List[int] = []
    for part in field_value.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = lo if base == "*" else int(base)
            result.extend(range(start, hi + 1, int(step)))
        elif "-" in part:
            a, b = part.split("-", 1)
            result.extend(range(int(a), int(b) + 1))
        else:
            result.append(int(part))
    return sorted(set(result))


def _intersect(a: List[int], b: List[int]) -> List[int]:
    return sorted(set(a) & set(b))


def find_conflicts(entries: List[CronEntry]) -> List[ConflictResult]:
    """Return all pairs of entries that share at least one firing slot."""
    results: List[ConflictResult] = []
    for ea, eb in combinations(entries, 2):
        mins = _intersect(
            _expand(ea.minute, 0, 59), _expand(eb.minute, 0, 59)
        )
        hours = _intersect(
            _expand(ea.hour, 0, 23), _expand(eb.hour, 0, 23)
        )
        days = _intersect(
            _expand(ea.dow, 0, 6), _expand(eb.dow, 0, 6)
        )
        cr = ConflictResult(ea, eb, mins, hours, days)
        if cr:
            results.append(cr)
    return results


def format_conflict_report(
    conflicts: List[ConflictResult], *, color: bool = False
) -> str:
    """Render a human-readable conflict report."""
    if not conflicts:
        return "No conflicts found."
    lines = [f"{len(conflicts)} conflict(s) detected:\n"]
    for i, cr in enumerate(conflicts, 1):
        lines.append(f"  [{i}] {cr.entry_a.command!r}  <>  {cr.entry_b.command!r}")
        lines.append(
            f"      hours={cr.shared_hours}  minutes={cr.shared_minutes}  dow={cr.shared_days}"
        )
    return "\n".join(lines)
