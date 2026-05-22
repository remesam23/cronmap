"""Terminal renderer for weekly cron schedules."""

from typing import Dict, List
from cronmap.schedule import build_weekly_schedule, schedule_summary

DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_ABBREV = {"Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed",
              "Thursday": "Thu", "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun"}

COLOR_HEADER = "\033[1;36m"
COLOR_DAY = "\033[1;33m"
COLOR_EVENT = "\033[0;32m"
COLOR_EMPTY = "\033[0;90m"
COLOR_RESET = "\033[0m"


def _format_time(hour: int, minute: int) -> str:
    """Format hour and minute as HH:MM string."""
    return f"{hour:02d}:{minute:02d}"


def render_weekly_table(entries, use_color: bool = True) -> str:
    """Render a weekly schedule table from a list of CronEntry objects."""
    schedule = build_weekly_schedule(entries)
    summary = schedule_summary(schedule)
    lines = []

    header = "=== Weekly Cron Schedule ==="
    if use_color:
        header = f"{COLOR_HEADER}{header}{COLOR_RESET}"
    lines.append(header)
    lines.append(f"Total events this week: {summary['total_events']}")
    lines.append("")

    for day in DAYS_ORDER:
        events = schedule.get(day, [])
        day_label = f"[{DAY_ABBREV[day]}] {day}"
        if use_color:
            day_label = f"{COLOR_DAY}{day_label}{COLOR_RESET}"
        lines.append(day_label)

        if not events:
            empty_msg = "  (no events)"
            if use_color:
                empty_msg = f"{COLOR_EMPTY}{empty_msg}{COLOR_RESET}"
            lines.append(empty_msg)
        else:
            for event in events:
                time_str = _format_time(event["hour"], event["minute"])
                command = event["command"]
                event_line = f"  {time_str}  {command}"
                if use_color:
                    event_line = f"{COLOR_EVENT}{event_line}{COLOR_RESET}"
                lines.append(event_line)
        lines.append("")

    return "\n".join(lines)


def render_compact(entries, use_color: bool = True) -> str:
    """Render a compact one-line-per-day summary."""
    schedule = build_weekly_schedule(entries)
    lines = []
    for day in DAYS_ORDER:
        events = schedule.get(day, [])
        abbrev = DAY_ABBREV[day]
        times = ", ".join(_format_time(e["hour"], e["minute"]) for e in events)
        count = len(events)
        line = f"{abbrev}: {count:2d} event(s)  {times}"
        if use_color:
            color = COLOR_EVENT if count > 0 else COLOR_EMPTY
            line = f"{color}{line}{COLOR_RESET}"
        lines.append(line)
    return "\n".join(lines)
