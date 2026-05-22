"""Suggest fixes or improvements for crontab entries.

Provides heuristic-based suggestions such as spreading out wildcard
schedules, flagging overly frequent jobs, and recommending named
special strings (@daily, @hourly, etc.) where applicable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronmap.parser import CronEntry


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Suggestion:
    """A single improvement suggestion for a cron entry."""

    line: int
    command: str
    message: str
    level: str = "info"  # 'info' | 'warning' | 'tip'

    def __post_init__(self) -> None:
        self.level = self.level.lower()

    def __repr__(self) -> str:  # pragma: no cover
        return f"Suggestion(line={self.line}, level={self.level!r}, message={self.message!r})"

    def __str__(self) -> str:
        return f"[line {self.line}] {self.level.upper()}: {self.message}  →  {self.command}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SPECIAL_MAP = {
    # (minute, hour, dom, month, dow) -> special string
    ("0", "0", "*", "*", "*"): "@daily",
    ("0", "0", "*", "*", "0"): "@weekly",
    ("0", "0", "1", "*", "*"): "@monthly",
    ("0", "0", "1", "1", "*"): "@yearly",
    ("0", "*", "*", "*", "*"): "@hourly",
}


def _is_every_minute(entry: CronEntry) -> bool:
    """Return True when the job runs every single minute."""
    return (
        entry.minute == ["*"]
        and entry.hour == ["*"]
        and entry.day_of_week == ["*"]
    )


def _is_every_hour(entry: CronEntry) -> bool:
    """Return True when the job runs at minute 0 of every hour."""
    return (
        entry.minute == ["0"]
        and entry.hour == ["*"]
        and entry.day_of_week == ["*"]
    )


def _raw_fields(entry: CronEntry) -> tuple:
    """Return the five raw schedule fields as a tuple of strings."""
    return (
        " ".join(entry.minute),
        " ".join(entry.hour),
        " ".join(entry.dom),
        " ".join(entry.month),
        " ".join(entry.dow),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def suggest_entry(entry: CronEntry, line: int = 0) -> List[Suggestion]:
    """Return a list of :class:`Suggestion` objects for a single entry.

    Parameters
    ----------
    entry:
        A parsed :class:`~cronmap.parser.CronEntry`.
    line:
        The 1-based line number in the original crontab (used for reporting).
    """
    suggestions: List[Suggestion] = []

    # --- overly frequent: every minute ---
    if _is_every_minute(entry):
        suggestions.append(
            Suggestion(
                line=line,
                command=entry.command,
                message="Job runs every minute — consider whether this frequency is necessary.",
                level="warning",
            )
        )

    # --- suggest @special strings ---
    key = _raw_fields(entry)
    special = _SPECIAL_MAP.get(key)
    if special:
        suggestions.append(
            Suggestion(
                line=line,
                command=entry.command,
                message=f"Schedule can be simplified to '{special}'.",
                level="tip",
            )
        )

    # --- midnight-only job: suggest @daily if not already caught above ---
    if (
        special is None
        and entry.minute == ["0"]
        and entry.hour == ["0"]
        and entry.day_of_week != ["*"]
    ):
        suggestions.append(
            Suggestion(
                line=line,
                command=entry.command,
                message="Runs at midnight on specific days — verify day-of-week restriction is intentional.",
                level="info",
            )
        )

    return suggestions


def suggest_crontab(entries: List[CronEntry]) -> List[Suggestion]:
    """Return aggregated suggestions for a list of parsed entries.

    Parameters
    ----------
    entries:
        Parsed cron entries, typically from :func:`~cronmap.parser.parse_crontab`.
    """
    all_suggestions: List[Suggestion] = []
    for idx, entry in enumerate(entries, start=1):
        all_suggestions.extend(suggest_entry(entry, line=idx))
    return all_suggestions


def format_suggestions(suggestions: List[Suggestion]) -> str:
    """Format a list of suggestions as a human-readable string."""
    if not suggestions:
        return "No suggestions — crontab looks good!"
    lines = [f"  {s}" for s in suggestions]
    header = f"{len(suggestions)} suggestion(s) found:"
    return "\n".join([header] + lines)
