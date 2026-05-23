"""Detect gaps (quiet periods) in a weekly cron schedule."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry


@dataclass
class GapResult:
    """A contiguous block of hours with no scheduled events."""

    day: int          # 0 = Monday … 6 = Sunday
    start_hour: int
    end_hour: int     # exclusive – first hour that has activity again

    @property
    def duration_hours(self) -> int:
        return self.end_hour - self.start_hour

    def __repr__(self) -> str:  # pragma: no cover
        day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][self.day]
        return (
            f"GapResult(day={day_name}, "
            f"start={self.start_hour:02d}:00, "
            f"end={self.end_hour:02d}:00, "
            f"duration={self.duration_hours}h)"
        )


def _expand_dow(field: str) -> List[int]:
    """Return list of weekday ints (0-6) covered by a DOW field."""
    if field == "*":
        return list(range(7))
    days: List[int] = []
    for part in field.split(","):
        if "-" in part:
            lo, hi = part.split("-", 1)
            days.extend(range(int(lo), int(hi) + 1))
        else:
            days.append(int(part))
    return days


def _expand_hours(field: str) -> List[int]:
    """Return list of hours (0-23) covered by an hour field."""
    if field == "*":
        return list(range(24))
    hours: List[int] = []
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = 0 if base == "*" else int(base)
            hours.extend(range(start, 24, int(step)))
        elif "-" in part:
            lo, hi = part.split("-", 1)
            hours.extend(range(int(lo), int(hi) + 1))
        else:
            hours.append(int(part))
    return hours


def find_gaps(entries: List[CronEntry], min_duration: int = 1) -> List[GapResult]:
    """Return gaps of at least *min_duration* hours for each day of the week."""
    # Build a set of (day, hour) pairs that have at least one event.
    busy: set = set()
    for entry in entries:
        for day in _expand_dow(entry.dow):
            for hour in _expand_hours(entry.hour):
                busy.add((day, hour))

    gaps: List[GapResult] = []
    for day in range(7):
        start: int | None = None
        for hour in range(25):  # sentinel at 24
            active = (day, hour) in busy
            if not active and start is None:
                start = hour
            elif active and start is not None:
                duration = hour - start
                if duration >= min_duration:
                    gaps.append(GapResult(day=day, start_hour=start, end_hour=hour))
                start = None
    return gaps
