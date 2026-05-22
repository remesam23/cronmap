"""Filter and search utilities for cron schedule entries."""

from __future__ import annotations

from typing import Callable

from cronmap.parser import CronEntry


def filter_by_day(entries: list[CronEntry], day: int) -> list[CronEntry]:
    """Return entries that fire on the given weekday (0=Sunday, 6=Saturday)."""
    return [e for e in entries if day in e.days_of_week]


def filter_by_hour_range(
    entries: list[CronEntry], start_hour: int, end_hour: int
) -> list[CronEntry]:
    """Return entries that have at least one minute firing within [start_hour, end_hour]."""
    result = []
    for entry in entries:
        if any(start_hour <= h <= end_hour for h in entry.hours):
            result.append(entry)
    return result


def filter_by_command(entries: list[CronEntry], substring: str) -> list[CronEntry]:
    """Return entries whose command contains *substring* (case-insensitive)."""
    lower = substring.lower()
    return [e for e in entries if lower in e.command.lower()]


def filter_entries(
    entries: list[CronEntry],
    *predicates: Callable[[CronEntry], bool],
) -> list[CronEntry]:
    """Apply all predicate functions and return entries that satisfy every one."""
    result = entries
    for predicate in predicates:
        result = [e for e in result if predicate(e)]
    return result


def deduplicate(entries: list[CronEntry]) -> list[CronEntry]:
    """Remove duplicate entries based on (raw_expression, command) pairs."""
    seen: set[tuple[str, str]] = set()
    unique: list[CronEntry] = []
    for entry in entries:
        key = (entry.raw, entry.command)
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique
