"""Build a weekly schedule grid from parsed cron entries."""

from typing import Dict, List, Tuple
from cronmap.parser import CronEntry, DAYS_OF_WEEK

# Schedule type: day_index -> list of (hour, minute, label)
WeeklySchedule = Dict[int, List[Tuple[int, int, str]]]


def build_weekly_schedule(entries: List[CronEntry]) -> WeeklySchedule:
    """Convert a list of CronEntry objects into a day-keyed schedule."""
    schedule: WeeklySchedule = {day: [] for day in range(7)}

    for entry in entries:
        for day in sorted(entry.days_of_week):
            for hour in sorted(entry.hours):
                for minute in sorted(entry.minutes):
                    schedule[day].append((hour, minute, entry.label or entry.raw))

    for day in schedule:
        schedule[day].sort(key=lambda t: (t[0], t[1]))

    return schedule


def schedule_summary(schedule: WeeklySchedule) -> Dict[str, int]:
    """Return a summary of event counts per day name."""
    return {
        DAYS_OF_WEEK[day]: len(events)
        for day, events in schedule.items()
    }
