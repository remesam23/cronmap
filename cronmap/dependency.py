"""Detect cron entries that may have implicit dependencies based on timing."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from cronmap.parser import CronEntry


def _expand_field(value: str, lo: int, hi: int) -> List[int]:
    """Expand a cron field string into a sorted list of integers."""
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


@dataclass
class DependencyResult:
    upstream: CronEntry
    downstream: CronEntry
    gap_minutes: int

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DependencyResult(upstream={self.upstream.command!r}, "
            f"downstream={self.downstream.command!r}, gap={self.gap_minutes}m)"
        )

    def __bool__(self) -> bool:
        return True


def _earliest_minute_of_day(entry: CronEntry) -> int:
    """Return the earliest minute-of-day (hour*60+minute) an entry can fire."""
    hours = _expand_field(entry.hour, 0, 23)
    minutes = _expand_field(entry.minute, 0, 59)
    if not hours or not minutes:
        return 0
    return hours[0] * 60 + minutes[0]


def find_dependencies(
    entries: List[CronEntry],
    max_gap_minutes: int = 10,
) -> List[DependencyResult]:
    """Return pairs where one entry fires within *max_gap_minutes* after another.

    Only considers entries that share at least one day-of-week.
    """
    results: List[DependencyResult] = []
    timed = [(e, _earliest_minute_of_day(e)) for e in entries]
    timed.sort(key=lambda x: x[1])

    for i, (a, t_a) in enumerate(timed):
        days_a = set(_expand_field(a.dow, 0, 6))
        for j in range(i + 1, len(timed)):
            b, t_b = timed[j]
            gap = t_b - t_a
            if gap > max_gap_minutes:
                break
            if gap <= 0:
                continue
            days_b = set(_expand_field(b.dow, 0, 6))
            if days_a & days_b:
                results.append(DependencyResult(upstream=a, downstream=b, gap_minutes=gap))
    return results


def format_dependency_report(
    results: List[DependencyResult], color: bool = False
) -> str:
    """Render a human-readable dependency report."""
    if not results:
        return "No implicit dependencies detected."
    lines = [f"Implicit dependencies found: {len(results)}", ""]
    for r in results:
        arrow = "\033[33m->\033[0m" if color else "->"
        lines.append(
            f"  {r.upstream.command!r} {arrow} {r.downstream.command!r}  "
            f"(gap: {r.gap_minutes}m)"
        )
    return "\n".join(lines)
