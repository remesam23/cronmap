"""Annotate cron entries with human-readable descriptions."""

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry


@dataclass
class AnnotatedEntry:
    entry: CronEntry
    description: str
    tags: List[str]

    def __repr__(self) -> str:
        return f"AnnotatedEntry({self.entry.command!r}, {self.description!r})"


def _describe_field(value: str, unit: str, zero_label: str = "") -> str:
    if value == "*":
        return f"every {unit}"
    if "," in value:
        return f"at {unit}s {value}"
    if "-" in value and "/" not in value:
        start, end = value.split("-", 1)
        return f"from {unit} {start} to {end}"
    if value.startswith("*/"):
        step = value[2:]
        return f"every {step} {unit}s"
    if "/" in value:
        base, step = value.split("/", 1)
        return f"every {step} {unit}s starting at {base}"
    label = zero_label if value == "0" and zero_label else value
    return f"at {unit} {label}"


DAY_NAMES = {
    "0": "Sunday", "1": "Monday", "2": "Tuesday",
    "3": "Wednesday", "4": "Thursday", "5": "Friday",
    "6": "Saturday", "7": "Sunday",
}


def _describe_dow(value: str) -> str:
    if value == "*":
        return "every day"
    if "," in value:
        names = [DAY_NAMES.get(v, v) for v in value.split(",")]
        return "on " + ", ".join(names)
    if "-" in value:
        start, end = value.split("-", 1)
        return f"from {DAY_NAMES.get(start, start)} to {DAY_NAMES.get(end, end)}"
    return "on " + DAY_NAMES.get(value, value)


def _infer_tags(entry: CronEntry) -> List[str]:
    tags = []
    if entry.minute == "0" and entry.hour != "*":
        tags.append("hourly-aligned")
    if entry.minute == "0" and entry.hour == "0":
        tags.append("daily-midnight")
    if entry.dow in ("1-5",):
        tags.append("weekdays-only")
    if entry.dow in ("0", "6", "0,6", "6,0"):
        tags.append("weekends-only")
    if entry.minute.startswith("*/"):
        tags.append("frequent")
    if entry.dom != "*" and entry.dow == "*":
        tags.append("monthly")
    return tags


def annotate_entry(entry: CronEntry) -> AnnotatedEntry:
    parts = [
        _describe_field(entry.minute, "minute"),
        _describe_field(entry.hour, "hour"),
        _describe_field(entry.dom, "day-of-month"),
        _describe_field(entry.month, "month"),
        _describe_dow(entry.dow),
    ]
    description = "; ".join(parts)
    tags = _infer_tags(entry)
    return AnnotatedEntry(entry=entry, description=description, tags=tags)


def annotate_entries(entries: List[CronEntry]) -> List[AnnotatedEntry]:
    return [annotate_entry(e) for e in entries]
