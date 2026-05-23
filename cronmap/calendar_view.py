"""Monthly calendar view renderer for cron entries."""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from cronmap.parser import CronEntry

DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass
class CalendarCell:
    day: int
    events: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        label = f"{self.day:2d}"
        if self.events:
            label += f"({len(self.events)})"
        else:
            label += "   "
        return label


def _entry_matches_dow(entry: CronEntry, weekday: int) -> bool:
    """Check if entry runs on a given ISO weekday (0=Mon … 6=Sun)."""
    dow_field = entry.dow
    if dow_field == "*":
        return True
    values: List[int] = []
    for part in dow_field.split(","):
        if "-" in part:
            lo, hi = part.split("-", 1)
            values.extend(range(int(lo), int(hi) + 1))
        elif part.isdigit():
            values.append(int(part))
    # crontab DOW: 0 or 7 = Sunday, 1=Monday … 6=Saturday
    # convert ISO weekday (0=Mon … 6=Sun) → crontab DOW
    cron_dow = (weekday + 1) % 7  # Mon→1, …, Sat→6, Sun→0
    return cron_dow in values or (cron_dow == 0 and 7 in values)


def build_calendar_grid(
    year: int, month: int, entries: List[CronEntry]
) -> Dict[int, CalendarCell]:
    """Return a mapping of day-of-month → CalendarCell for the given month."""
    _, num_days = calendar.monthrange(year, month)
    grid: Dict[int, CalendarCell] = {}
    for day in range(1, num_days + 1):
        weekday = calendar.weekday(year, month, day)  # 0=Mon
        matching = [
            e.command for e in entries if _entry_matches_dow(e, weekday)
        ]
        grid[day] = CalendarCell(day=day, events=matching)
    return grid


def render_calendar(year: int, month: int, entries: List[CronEntry]) -> str:
    """Render a simple text calendar annotated with event counts."""
    grid = build_calendar_grid(year, month, entries)
    header = calendar.month_name[month] + f" {year}"
    lines: List[str] = [header.center(7 * 7), "  ".join(DAY_ABBR)]

    first_weekday, num_days = calendar.monthrange(year, month)
    week: List[str] = ["      "] * first_weekday
    for day in range(1, num_days + 1):
        cell = grid[day]
        week.append(str(cell))
        if len(week) == 7:
            lines.append("  ".join(week))
            week = []
    if week:
        week += ["      "] * (7 - len(week))
        lines.append("  ".join(week))
    return "\n".join(lines)
