"""High-level query interface combining parsing, filtering, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from cronmap.parser import CronEntry, parse_crontab
from cronmap.filter import (
    filter_by_day,
    filter_by_hour_range,
    filter_by_command,
    filter_entries,
    deduplicate,
)
from cronmap.schedule import build_weekly_schedule, schedule_summary


@dataclass
class QueryResult:
    entries: list[CronEntry]
    schedule: dict[str, list[CronEntry]]
    summary: dict[str, int]

    @property
    def total(self) -> int:
        return len(self.entries)


@dataclass
class CronQuery:
    """Fluent builder for querying a set of cron entries."""

    _entries: list[CronEntry] = field(default_factory=list)
    _predicates: list[Callable[[CronEntry], bool]] = field(default_factory=list)
    _dedup: bool = False

    @classmethod
    def from_text(cls, text: str) -> "CronQuery":
        obj = cls()
        obj._entries = parse_crontab(text)
        return obj

    def on_day(self, day: int) -> "CronQuery":
        """Filter to entries active on *day* (0=Sunday … 6=Saturday)."""
        self._predicates.append(lambda e, d=day: d in e.days_of_week)
        return self

    def between_hours(self, start: int, end: int) -> "CronQuery":
        """Filter to entries firing within the given hour range (inclusive)."""
        self._predicates.append(
            lambda e, s=start, en=end: any(s <= h <= en for h in e.hours)
        )
        return self

    def matching_command(self, substring: str) -> "CronQuery":
        """Filter to entries whose command contains *substring*."""
        self._predicates.append(
            lambda e, sub=substring: sub.lower() in e.command.lower()
        )
        return self

    def unique(self) -> "CronQuery":
        """Remove duplicate (expression, command) pairs from results."""
        self._dedup = True
        return self

    def execute(self) -> QueryResult:
        """Apply all filters and return a QueryResult."""
        results = filter_entries(self._entries, *self._predicates)
        if self._dedup:
            results = deduplicate(results)
        schedule = build_weekly_schedule(results)
        summary = schedule_summary(schedule)
        return QueryResult(entries=results, schedule=schedule, summary=summary)
