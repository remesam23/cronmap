"""Crontab entry parser module."""

from dataclasses import dataclass, field
from typing import List, Set


DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


@dataclass
class CronEntry:
    raw: str
    minutes: Set[int] = field(default_factory=set)
    hours: Set[int] = field(default_factory=set)
    days_of_week: Set[int] = field(default_factory=set)
    label: str = ""


def _parse_field(field_str: str, min_val: int, max_val: int) -> Set[int]:
    """Parse a single cron field into a set of integers."""
    values: Set[int] = set()

    if field_str == "*":
        return set(range(min_val, max_val + 1))

    for part in field_str.split(","):
        if "/" in part:
            range_part, step = part.split("/", 1)
            step = int(step)
            if range_part == "*":
                start, end = min_val, max_val
            elif "-" in range_part:
                start, end = map(int, range_part.split("-", 1))
            else:
                start = int(range_part)
                end = max_val
            values.update(range(start, end + 1, step))
        elif "-" in part:
            start, end = map(int, part.split("-", 1))
            values.update(range(start, end + 1))
        else:
            values.add(int(part))

    return values


def parse_cron_entry(line: str) -> CronEntry:
    """Parse a crontab line into a CronEntry object."""
    line = line.strip()
    label = ""

    if "#" in line:
        parts = line.split("#", 1)
        line = parts[0].strip()
        label = parts[1].strip()

    tokens = line.split()
    if len(tokens) < 5:
        raise ValueError(f"Invalid cron entry (expected 5 fields): '{line}'")

    minute_field, hour_field, _, _, dow_field = tokens[:5]

    entry = CronEntry(raw=line, label=label)
    entry.minutes = _parse_field(minute_field, 0, 59)
    entry.hours = _parse_field(hour_field, 0, 23)
    entry.days_of_week = _parse_field(dow_field, 0, 6)

    return entry


def parse_crontab(text: str) -> List[CronEntry]:
    """Parse multiple crontab lines, skipping blanks and comment-only lines."""
    entries = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(parse_cron_entry(stripped))
    return entries
