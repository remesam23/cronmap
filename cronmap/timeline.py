"""Timeline builder for cronmap.

Builds a chronological list of upcoming scheduled events from parsed
cron entries, useful for showing what will run in the next N hours.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from cronmap.parser import CronEntry


@dataclass
class TimelineEvent:
    """A single scheduled event placed at a concrete datetime."""

    at: datetime
    command: str
    raw: str  # original crontab line

    def __str__(self) -> str:  # noqa: D105
        return f"{self.at.strftime('%a %Y-%m-%d %H:%M')}  {self.command}"

    def __repr__(self) -> str:  # noqa: D105
        return f"TimelineEvent(at={self.at!r}, command={self.command!r})"


def _matches_field(value: int, field_values: List[int]) -> bool:
    """Return True when *value* is contained in *field_values*."""
    return value in field_values


def build_timeline(
    entries: List[CronEntry],
    start: Optional[datetime] = None,
    hours: int = 24,
) -> List[TimelineEvent]:
    """Return upcoming :class:`TimelineEvent` objects within the next *hours*.

    The timeline is built by iterating over every minute in the window
    ``[start, start + hours)`` and checking whether each cron entry
    fires at that minute.  Duplicate (entry, minute) pairs are skipped.

    Parameters
    ----------
    entries:
        Parsed cron entries to evaluate.
    start:
        Beginning of the look-ahead window.  Defaults to *now* truncated
        to the current minute.
    hours:
        Length of the window in hours (default 24).

    Returns
    -------
    List[TimelineEvent]
        Events sorted chronologically.
    """
    if start is None:
        now = datetime.now()
        start = now.replace(second=0, microsecond=0)

    end = start + timedelta(hours=hours)
    events: List[TimelineEvent] = []

    current = start
    while current < end:
        dow = current.weekday()  # Monday=0 … Sunday=6
        # cron dow: 0=Sunday … 6=Saturday (7 also Sunday)
        cron_dow = (dow + 1) % 7

        for entry in entries:
            minute_match = _matches_field(current.minute, entry.minutes)
            hour_match = _matches_field(current.hour, entry.hours)
            dow_match = _matches_field(cron_dow, entry.days_of_week)

            if minute_match and hour_match and dow_match:
                events.append(
                    TimelineEvent(
                        at=current,
                        command=entry.command,
                        raw=entry.raw,
                    )
                )

        current += timedelta(minutes=1)

    return events


def format_timeline(events: List[TimelineEvent], color: bool = False) -> str:
    """Render *events* as a human-readable string.

    Parameters
    ----------
    events:
        Chronologically ordered timeline events.
    color:
        When *True*, ANSI colour codes are used to distinguish the
        timestamp from the command.

    Returns
    -------
    str
        Multi-line string ready for terminal output.
    """
    if not events:
        return "No events scheduled in the given window."

    lines: List[str] = []
    for ev in events:
        ts = ev.at.strftime("%a %Y-%m-%d %H:%M")
        if color:
            # dim cyan timestamp, reset before command
            line = f"\033[36m{ts}\033[0m  {ev.command}"
        else:
            line = f"{ts}  {ev.command}"
        lines.append(line)

    return "\n".join(lines)
