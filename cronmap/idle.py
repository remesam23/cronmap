"""Detect idle periods — contiguous hours in a week with no cron activity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry


def _expand_field(field: str, lo: int, hi: int) -> List[int]:
    """Return the list of integer values a cron field resolves to."""
    if field == "*":
        return list(range(lo, hi + 1))
    values: List[int] = []
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = lo if base == "*" else int(base)
            values.extend(range(start, hi + 1, int(step)))
        elif "-" in part:
            a, b = part.split("-", 1)
            values.extend(range(int(a), int(b) + 1))
        else:
            values.append(int(part))
    return sorted(set(values))


@dataclass
class IdlePeriod:
    """A contiguous block of hours (across the whole week) with no jobs."""

    day: int          # 0 = Monday … 6 = Sunday
    start_hour: int
    end_hour: int     # inclusive

    @property
    def duration_hours(self) -> int:
        return self.end_hour - self.start_hour + 1

    def __repr__(self) -> str:  # pragma: no cover
        day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][self.day]
        return (
            f"IdlePeriod({day_name} {self.start_hour:02d}:00"
            f"–{self.end_hour:02d}:59, {self.duration_hours}h)"
        )


def find_idle_periods(
    entries: List[CronEntry],
    min_duration_hours: int = 1,
) -> List[IdlePeriod]:
    """Return idle periods of at least *min_duration_hours* for each weekday."""
    # Build a set of (day, hour) pairs that are active.
    active: set = set()
    for entry in entries:
        days = _expand_field(entry.dow, 0, 6)
        hours = _expand_field(entry.hour, 0, 23)
        for d in days:
            for h in hours:
                active.add((d, h))

    idle_periods: List[IdlePeriod] = []
    for day in range(7):
        idle_start: int | None = None
        for hour in range(24):
            is_idle = (day, hour) not in active
            if is_idle and idle_start is None:
                idle_start = hour
            elif not is_idle and idle_start is not None:
                duration = hour - idle_start
                if duration >= min_duration_hours:
                    idle_periods.append(IdlePeriod(day, idle_start, hour - 1))
                idle_start = None
        # Handle idle period that runs to end of day.
        if idle_start is not None:
            duration = 24 - idle_start
            if duration >= min_duration_hours:
                idle_periods.append(IdlePeriod(day, idle_start, 23))

    return idle_periods


def format_idle_report(periods: List[IdlePeriod], *, color: bool = False) -> str:
    """Render a human-readable report of idle periods."""
    if not periods:
        return "No idle periods found."
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    lines = []
    for p in periods:
        label = f"{day_names[p.day]} {p.start_hour:02d}:00–{p.end_hour:02d}:59 ({p.duration_hours}h idle)"
        if color:
            label = f"\033[36m{label}\033[0m"
        lines.append(label)
    return "\n".join(lines)
