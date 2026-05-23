"""Retry analysis: identify cron entries that likely represent retry patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from cronmap.parser import CronEntry


@dataclass
class RetryGroup:
    """A cluster of entries that appear to form a retry pattern."""

    entries: List[CronEntry] = field(default_factory=list)

    @property
    def commands(self) -> List[str]:
        return [e.command for e in self.entries]

    @property
    def intervals_minutes(self) -> List[int]:
        """Return the minute-offsets of each entry relative to the first."""
        if not self.entries:
            return []
        first = _earliest_minute(self.entries[0])
        return [_earliest_minute(e) - first for e in self.entries]

    def __repr__(self) -> str:  # pragma: no cover
        return f"RetryGroup(size={len(self.entries)}, commands={self.commands})"


def _earliest_minute(entry: CronEntry) -> int:
    """Return the smallest absolute minute-of-day for an entry."""
    hour = _first_value(entry.hour, 0, 23)
    minute = _first_value(entry.minute, 0, 59)
    return hour * 60 + minute


def _first_value(field_str: str, lo: int, hi: int) -> int:
    """Parse a cron field and return its smallest concrete value."""
    if field_str == "*":
        return lo
    if "/" in field_str:
        parts = field_str.split("/")
        start = lo if parts[0] == "*" else int(parts[0].split("-")[0])
        return start
    if "," in field_str:
        return min(int(v) for v in field_str.split(","))
    if "-" in field_str:
        return int(field_str.split("-")[0])
    return int(field_str)


def _base_command(command: str) -> str:
    """Strip common flags/arguments to find the base executable."""
    return command.strip().split()[0]


def find_retry_groups(
    entries: List[CronEntry],
    max_gap_minutes: int = 30,
) -> List[RetryGroup]:
    """Group entries that share the same base command and run within
    *max_gap_minutes* of each other on overlapping days.

    Returns a list of RetryGroup objects with two or more entries.
    """
    by_command: dict[str, List[CronEntry]] = {}
    for entry in entries:
        key = _base_command(entry.command)
        by_command.setdefault(key, []).append(entry)

    groups: List[RetryGroup] = []
    for cmd_entries in by_command.values():
        if len(cmd_entries) < 2:
            continue
        sorted_entries = sorted(cmd_entries, key=_earliest_minute)
        cluster: List[CronEntry] = [sorted_entries[0]]
        for entry in sorted_entries[1:]:
            gap = _earliest_minute(entry) - _earliest_minute(cluster[-1])
            if 0 < gap <= max_gap_minutes:
                cluster.append(entry)
            else:
                if len(cluster) >= 2:
                    groups.append(RetryGroup(entries=list(cluster)))
                cluster = [entry]
        if len(cluster) >= 2:
            groups.append(RetryGroup(entries=list(cluster)))
    return groups


def format_retry_report(groups: List[RetryGroup], color: bool = False) -> str:
    """Render a human-readable report of detected retry groups."""
    if not groups:
        return "No retry patterns detected."
    lines = []
    for i, group in enumerate(groups, 1):
        header = f"Retry group {i} — {len(group.entries)} entries"
        if color:
            header = f"\033[33m{header}\033[0m"
        lines.append(header)
        for entry in group.entries:
            lines.append(f"  {entry.minute:>5} {entry.hour:>3} {entry.dom:>3} "
                         f"{entry.month:>3} {entry.dow:>3}  {entry.command}")
    return "\n".join(lines)
