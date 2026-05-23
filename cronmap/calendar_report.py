"""High-level report combining calendar view with per-day entry details."""
from __future__ import annotations

import calendar
from typing import List, Optional

from cronmap.calendar_view import build_calendar_grid, render_calendar
from cronmap.parser import CronEntry


def _ansi(code: str, text: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def format_day_detail(
    year: int,
    month: int,
    day: int,
    entries: List[CronEntry],
    use_color: bool = False,
) -> str:
    """Return a formatted string listing all entries for a specific day."""
    weekday = calendar.weekday(year, month, day)
    day_name = calendar.day_name[weekday]
    title = _ansi("1", f"{day_name} {year}-{month:02d}-{day:02d}", use_color)
    if not entries:
        return f"{title}\n  (no scheduled jobs)"
    lines = [title]
    for e in entries:
        schedule = f"{e.minute} {e.hour} {e.dom} {e.month} {e.dow}"
        lines.append(
            f"  {_ansi('36', schedule, use_color)}  {e.command}"
        )
    return "\n".join(lines)


def render_calendar_report(
    year: int,
    month: int,
    entries: List[CronEntry],
    detail_day: Optional[int] = None,
    use_color: bool = False,
) -> str:
    """Render calendar overview, optionally with detail for one day."""
    parts: List[str] = [render_calendar(year, month, entries)]
    if detail_day is not None:
        grid = build_calendar_grid(year, month, entries)
        cell = grid.get(detail_day)
        if cell is None:
            parts.append(f"Day {detail_day} is not in this month.")
        else:
            day_entries = [
                e for e in entries if e.command in cell.events
            ]
            parts.append("")
            parts.append(
                format_day_detail(year, month, detail_day, day_entries, use_color)
            )
    return "\n".join(parts)
