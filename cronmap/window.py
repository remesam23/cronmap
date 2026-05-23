"""Detect cron entries that fire within a given time window on a given day."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronmap.parser import CronEntry


def _expand_field(value: str, lo: int, hi: int) -> List[int]:
    """Expand a cron field string to a sorted list of integers in [lo, hi]."""
    if value == "*":
        return list(range(lo, hi + 1))
    result: set[int] = set()
    for part in value.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = lo if base == "*" else int(base)
            result.update(range(start, hi + 1, int(step)))
        elif "-" in part:
            a, b = part.split("-", 1)
            result.update(range(int(a), int(b) + 1))
        else:
            result.add(int(part))
    return sorted(v for v in result if lo <= v <= hi)


@dataclass
class WindowResult:
    entry: CronEntry
    matching_times: List[tuple[int, int]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.matching_times)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"WindowResult(command={self.entry.command!r}, "
            f"matches={len(self.matching_times)})"
        )


def entries_in_window(
    entries: List[CronEntry],
    dow: int,
    start_hour: int,
    start_minute: int,
    end_hour: int,
    end_minute: int,
) -> List[WindowResult]:
    """Return WindowResult for each entry that fires within the window on *dow*.

    *dow* follows cron convention: 0 = Sunday, 6 = Saturday.
    The window is inclusive on both ends.
    """
    window_start = start_hour * 60 + start_minute
    window_end = end_hour * 60 + end_minute
    if window_end < window_start:
        raise ValueError("end time must not be before start time")

    results: List[WindowResult] = []
    for entry in entries:
        days = _expand_field(entry.dow, 0, 6)
        if dow not in days:
            continue
        hours = _expand_field(entry.hour, 0, 23)
        minutes = _expand_field(entry.minute, 0, 59)
        matching: List[tuple[int, int]] = []
        for h in hours:
            for m in minutes:
                if window_start <= h * 60 + m <= window_end:
                    matching.append((h, m))
        if matching:
            results.append(WindowResult(entry=entry, matching_times=matching))
    return results
