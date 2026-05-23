"""Group cron entries by various criteria for analysis and display."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from cronmap.parser import CronEntry


DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def group_by_day(entries: List[CronEntry]) -> Dict[str, List[CronEntry]]:
    """Return a mapping of day-name -> entries that run on that day.

    Wildcard dow ('*') causes the entry to appear under every day.
    Numeric values 0-6 map to Sunday-Saturday.
    """
    groups: Dict[str, List[CronEntry]] = {day: [] for day in DAY_NAMES}
    for entry in entries:
        dow = entry.dow
        if dow == "*":
            days = list(range(7))
        elif "," in dow:
            days = [int(d) % 7 for d in dow.split(",")]
        elif "-" in dow:
            parts = dow.split("-")
            start, end = int(parts[0]) % 7, int(parts[1]) % 7
            days = list(range(start, end + 1))
        else:
            days = [int(dow) % 7]
        for d in days:
            groups[DAY_NAMES[d]].append(entry)
    return groups


def group_by_hour(entries: List[CronEntry]) -> Dict[int, List[CronEntry]]:
    """Return a mapping of hour -> entries scheduled in that hour.

    Wildcard hour ('*') causes the entry to appear in every hour 0-23.
    """
    groups: Dict[int, List[CronEntry]] = {h: [] for h in range(24)}
    for entry in entries:
        hour = entry.hour
        if hour == "*":
            hours = list(range(24))
        elif "," in hour:
            hours = [int(h) for h in hour.split(",")]
        elif "-" in hour:
            parts = hour.split("-")
            hours = list(range(int(parts[0]), int(parts[1]) + 1))
        elif "/" in hour:
            step_parts = hour.split("/")
            step = int(step_parts[1])
            hours = list(range(0, 24, step))
        else:
            hours = [int(hour)]
        for h in hours:
            if 0 <= h < 24:
                groups[h].append(entry)
    return groups


def group_by_command(entries: List[CronEntry]) -> Dict[str, List[CronEntry]]:
    """Return a mapping of command string -> entries sharing that command."""
    groups: Dict[str, List[CronEntry]] = defaultdict(list)
    for entry in entries:
        groups[entry.command].append(entry)
    return dict(groups)


def group_summary(entries: List[CronEntry]) -> str:
    """Return a human-readable summary of entry counts per group type."""
    by_day = group_by_day(entries)
    by_hour = group_by_hour(entries)
    by_cmd = group_by_command(entries)

    busiest_day = max(by_day, key=lambda d: len(by_day[d]))
    busiest_hour = max(by_hour, key=lambda h: len(by_hour[h]))

    lines = [
        f"Total entries : {len(entries)}",
        f"Unique commands: {len(by_cmd)}",
        f"Busiest day   : {busiest_day} ({len(by_day[busiest_day])} entries)",
        f"Busiest hour  : {busiest_hour:02d}:00 ({len(by_hour[busiest_hour])} entries)",
    ]
    return "\n".join(lines)
