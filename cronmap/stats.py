"""Statistics and analytics for crontab entries."""

from collections import Counter, defaultdict
from typing import Dict, List, NamedTuple

from cronmap.parser import CronEntry


class CronStats(NamedTuple):
    total_entries: int
    busiest_day: str
    busiest_hour: int
    events_per_day: Dict[str, int]
    events_per_hour: Dict[int, int]
    most_frequent_command: str
    unique_commands: int


DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _expand_days(entry: CronEntry) -> List[int]:
    """Return list of weekday integers (0=Sun..6=Sat) for a given entry."""
    if entry.dow == ["*"]:
        return list(range(7))
    days = []
    for d in entry.dow:
        try:
            days.append(int(d))
        except ValueError:
            pass
    return days


def _expand_hours(entry: CronEntry) -> List[int]:
    """Return list of hour integers for a given entry."""
    if entry.hour == ["*"]:
        return list(range(24))
    hours = []
    for h in entry.hour:
        try:
            hours.append(int(h))
        except ValueError:
            pass
    return hours


def compute_stats(entries: List[CronEntry]) -> CronStats:
    """Compute aggregate statistics from a list of CronEntry objects."""
    if not entries:
        return CronStats(
            total_entries=0,
            busiest_day="N/A",
            busiest_hour=0,
            events_per_day={d: 0 for d in DAY_NAMES},
            events_per_hour={h: 0 for h in range(24)},
            most_frequent_command="N/A",
            unique_commands=0,
        )

    day_counter: Counter = Counter()
    hour_counter: Counter = Counter()
    command_counter: Counter = Counter()

    for entry in entries:
        for day in _expand_days(entry):
            day_counter[day] += 1
        for hour in _expand_hours(entry):
            hour_counter[hour] += 1
        command_counter[entry.command.strip()] += 1

    busiest_day_idx = day_counter.most_common(1)[0][0] if day_counter else 0
    busiest_hour = hour_counter.most_common(1)[0][0] if hour_counter else 0

    events_per_day = {DAY_NAMES[i]: day_counter.get(i, 0) for i in range(7)}
    events_per_hour = {h: hour_counter.get(h, 0) for h in range(24)}

    return CronStats(
        total_entries=len(entries),
        busiest_day=DAY_NAMES[busiest_day_idx],
        busiest_hour=busiest_hour,
        events_per_day=events_per_day,
        events_per_hour=events_per_hour,
        most_frequent_command=command_counter.most_common(1)[0][0],
        unique_commands=len(command_counter),
    )


def format_stats(stats: CronStats) -> str:
    """Render stats as a human-readable string."""
    lines = [
        f"Total entries     : {stats.total_entries}",
        f"Unique commands   : {stats.unique_commands}",
        f"Most frequent cmd : {stats.most_frequent_command}",
        f"Busiest day       : {stats.busiest_day}",
        f"Busiest hour      : {stats.busiest_hour:02d}:00",
    ]
    return "\n".join(lines)
