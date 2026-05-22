"""Sorting utilities for cron entries and weekly schedules."""

from typing import List, Callable, Optional
from cronmap.parser import CronEntry


def _entry_sort_key(entry: CronEntry, day: Optional[int] = None):
    """Return a sort key tuple for a CronEntry.

    Key order: (first matching day, first hour, first minute, command).
    If *day* is provided, use that day's index directly.
    """
    day_val = day if day is not None else (min(entry.days_of_week) if entry.days_of_week != list(range(7)) else 0)
    hour_val = min(entry.hours) if entry.hours else 0
    minute_val = min(entry.minutes) if entry.minutes else 0
    return (day_val, hour_val, minute_val, entry.command)


def sort_entries_by_time(entries: List[CronEntry]) -> List[CronEntry]:
    """Sort entries by (first_hour, first_minute, command) ascending."""
    return sorted(entries, key=lambda e: (min(e.hours) if e.hours else 0,
                                          min(e.minutes) if e.minutes else 0,
                                          e.command))


def sort_entries_by_day(entries: List[CronEntry]) -> List[CronEntry]:
    """Sort entries by first occurring day-of-week, then time."""
    return sorted(entries, key=lambda e: _entry_sort_key(e))


def sort_entries_by_command(entries: List[CronEntry]) -> List[CronEntry]:
    """Sort entries alphabetically by command string."""
    return sorted(entries, key=lambda e: e.command.lower())


SORT_STRATEGIES: dict[str, Callable[[List[CronEntry]], List[CronEntry]]] = {
    "time": sort_entries_by_time,
    "day": sort_entries_by_day,
    "command": sort_entries_by_command,
}


def sort_entries(entries: List[CronEntry], strategy: str = "time") -> List[CronEntry]:
    """Sort *entries* using a named strategy.

    Supported strategies: 'time' (default), 'day', 'command'.
    Raises ValueError for unknown strategy names.
    """
    if strategy not in SORT_STRATEGIES:
        raise ValueError(
            f"Unknown sort strategy '{strategy}'. "
            f"Choose from: {', '.join(SORT_STRATEGIES)}"
        )
    return SORT_STRATEGIES[strategy](entries)


def sort_schedule(
    schedule: dict[str, List[CronEntry]],
    strategy: str = "time",
) -> dict[str, List[CronEntry]]:
    """Return a new schedule dict with each day's entries sorted.

    *schedule* maps day-name strings to lists of CronEntry objects,
    as produced by ``build_weekly_schedule``.
    """
    sorter = SORT_STRATEGIES.get(strategy)
    if sorter is None:
        raise ValueError(
            f"Unknown sort strategy '{strategy}'. "
            f"Choose from: {', '.join(SORT_STRATEGIES)}"
        )
    return {day: sorter(day_entries) for day, day_entries in schedule.items()}
