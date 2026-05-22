"""Summarizer: produce human-readable plain-text summaries for cron entries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry


@dataclass
class EntrySummary:
    entry: CronEntry
    headline: str
    detail: str

    def __str__(self) -> str:
        return f"{self.headline} — {self.entry.command}"


def _field_phrase(value: str, unit: str, zero_indexed: bool = False) -> str:
    """Return a short English phrase for a single cron field value."""
    if value == "*":
        return f"every {unit}"
    if "/" in value:
        base, step = value.split("/", 1)
        base_phrase = "every" if base == "*" else f"from {base}"
        return f"{base_phrase} {step} {unit}s"
    if "-" in value:
        lo, hi = value.split("-", 1)
        return f"from {unit} {lo} to {hi}"
    if "," in value:
        parts = value.split(",")
        joined = ", ".join(parts[:-1]) + f" and {parts[-1]}"
        return f"{unit}s {joined}"
    return f"{unit} {value}"


_DOW_NAMES = {
    "0": "Sunday", "1": "Monday", "2": "Tuesday",
    "3": "Wednesday", "4": "Thursday", "5": "Friday",
    "6": "Saturday", "7": "Sunday",
}


def _dow_phrase(value: str) -> str:
    if value == "*":
        return "every day"
    if "," in value:
        names = [_DOW_NAMES.get(v, v) for v in value.split(",")]
        return "on " + ", ".join(names[:-1]) + f" and {names[-1]}"
    if "-" in value:
        lo, hi = value.split("-", 1)
        return f"from {_DOW_NAMES.get(lo, lo)} to {_DOW_NAMES.get(hi, hi)}"
    return f"on {_DOW_NAMES.get(value, value)}s"


def summarize_entry(entry: CronEntry) -> EntrySummary:
    """Build an EntrySummary for a single CronEntry."""
    minute = _field_phrase(entry.minute, "minute")
    hour = _field_phrase(entry.hour, "hour")
    dom = _field_phrase(entry.dom, "day-of-month")
    month = _field_phrase(entry.month, "month")
    dow = _dow_phrase(entry.dow)

    if entry.minute == "0" and entry.hour != "*":
        time_phrase = f"at {entry.hour}:00"
    elif entry.minute == "0" and entry.hour == "*":
        time_phrase = "at the start of every hour"
    else:
        time_phrase = f"at {minute} past {hour}"

    parts = [time_phrase, dow]
    if dom != "every day-of-month":
        parts.append(f"on the {dom}")
    if month != "every month":
        parts.append(f"in {month}")

    headline = ", ".join(parts).capitalize()
    detail = (
        f"minute={entry.minute} hour={entry.hour} "
        f"dom={entry.dom} month={entry.month} dow={entry.dow}"
    )
    return EntrySummary(entry=entry, headline=headline, detail=detail)


def summarize_all(entries: List[CronEntry]) -> List[EntrySummary]:
    """Return a list of EntrySummary objects for each entry."""
    return [summarize_entry(e) for e in entries]


def render_summary_report(entries: List[CronEntry], color: bool = False) -> str:
    """Render a plain-text (or ANSI-colored) summary report."""
    if not entries:
        return "No cron entries found."
    summaries = summarize_all(entries)
    lines: List[str] = []
    for s in summaries:
        if color:
            lines.append(f"\033[1;36m{s.headline}\033[0m")
            lines.append(f"  \033[2m{s.detail}\033[0m")
            lines.append(f"  \033[33m$ {s.entry.command}\033[0m")
        else:
            lines.append(s.headline)
            lines.append(f"  {s.detail}")
            lines.append(f"  $ {s.entry.command}")
        lines.append("")
    return "\n".join(lines).rstrip()
