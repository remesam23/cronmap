"""Deadline detection: find cron entries that must finish before another starts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from cronmap.parser import CronEntry


def _expand_field(value: str, lo: int, hi: int) -> List[int]:
    """Expand a cron field string to a sorted list of integers."""
    if value == "*":
        return list(range(lo, hi + 1))
    result: List[int] = []
    for part in value.split(","):
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


def _earliest_start_minute(entry: CronEntry) -> int:
    """Return the earliest minute-of-day this entry fires."""
    hours = _expand_field(entry.hour, 0, 23)
    minutes = _expand_field(entry.minute, 0, 59)
    return hours[0] * 60 + minutes[0] if hours and minutes else 0


def _latest_start_minute(entry: CronEntry) -> int:
    """Return the latest minute-of-day this entry fires."""
    hours = _expand_field(entry.hour, 0, 23)
    minutes = _expand_field(entry.minute, 0, 59)
    return hours[-1] * 60 + minutes[-1] if hours and minutes else 1439


@dataclass
class DeadlineResult:
    predecessor: CronEntry
    successor: CronEntry
    gap_minutes: int          # minutes between latest start of pred and earliest start of succ
    tight: bool               # gap < threshold

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DeadlineResult(predecessor={self.predecessor.command!r}, "
            f"successor={self.successor.command!r}, "
            f"gap_minutes={self.gap_minutes}, tight={self.tight})"
        )

    def __bool__(self) -> bool:
        return self.tight


def find_deadlines(
    entries: List[CronEntry],
    threshold_minutes: int = 10,
) -> List[DeadlineResult]:
    """Return pairs where successor starts within *threshold_minutes* after predecessor."""
    results: List[DeadlineResult] = []
    for i, pred in enumerate(entries):
        pred_latest = _latest_start_minute(pred)
        for j, succ in enumerate(entries):
            if i == j:
                continue
            succ_earliest = _earliest_start_minute(succ)
            gap = succ_earliest - pred_latest
            if 0 < gap <= threshold_minutes:
                results.append(
                    DeadlineResult(
                        predecessor=pred,
                        successor=succ,
                        gap_minutes=gap,
                        tight=True,
                    )
                )
    return results


def format_deadline_report(
    results: List[DeadlineResult],
    color: bool = False,
) -> str:
    """Render a human-readable deadline report."""
    if not results:
        return "No tight deadlines detected."
    lines = ["Tight deadline pairs:"]
    for r in results:
        arrow = "\033[33m->\033[0m" if color else "->"
        lines.append(
            f"  [{r.gap_minutes:>3}m gap]  {r.predecessor.command}  {arrow}  {r.successor.command}"
        )
    return "\n".join(lines)
