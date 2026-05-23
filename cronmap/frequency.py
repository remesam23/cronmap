"""Frequency analysis: classify cron entries by how often they fire."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry


# Approximate fires-per-day for each frequency bucket
_THRESHOLD_FREQUENT = 24    # >= 24 times / day  → "frequent"
_THRESHOLD_HOURLY = 1       # >= 1 time  / day   → "hourly"
_THRESHOLD_DAILY = 1 / 7    # >= 1 time  / week  → "daily"


def _field_count(field: str, lo: int, hi: int) -> int:
    """Return the number of distinct values a single cron field expands to."""
    if field == "*":
        return hi - lo + 1
    if "/" in field:
        base, step = field.split("/", 1)
        start = lo if base == "*" else int(base.split("-")[0])
        return len(range(start, hi + 1, int(step)))
    if "-" in field:
        a, b = field.split("-", 1)
        return max(0, int(b) - int(a) + 1)
    if "," in field:
        return len(field.split(","))
    return 1


def fires_per_day(entry: CronEntry) -> float:
    """Estimate how many times *entry* fires per day (averaged over the week)."""
    minutes = _field_count(entry.minute, 0, 59)
    hours = _field_count(entry.hour, 0, 23)
    days_of_week = _field_count(entry.dow, 0, 6)
    # fires per day = minutes * hours, scaled by fraction of week days active
    return minutes * hours * (days_of_week / 7)


@dataclass
class FrequencyLabel:
    entry: CronEntry
    label: str          # "frequent" | "hourly" | "daily" | "weekly" | "rare"
    rate: float         # estimated fires per day

    def __str__(self) -> str:
        return f"{self.label} (~{self.rate:.2f}/day)  {self.entry.command}"


def classify(entry: CronEntry) -> FrequencyLabel:
    """Assign a human-readable frequency label to a single entry."""
    rate = fires_per_day(entry)
    if rate >= _THRESHOLD_FREQUENT:
        label = "frequent"
    elif rate >= _THRESHOLD_HOURLY:
        label = "hourly"
    elif rate >= _THRESHOLD_DAILY:
        label = "daily"
    elif rate > 0:
        label = "weekly"
    else:
        label = "rare"
    return FrequencyLabel(entry=entry, label=label, rate=rate)


def classify_all(entries: List[CronEntry]) -> List[FrequencyLabel]:
    """Return a FrequencyLabel for every entry in *entries*."""
    return [classify(e) for e in entries]


def frequency_summary(labels: List[FrequencyLabel]) -> str:
    """Render a compact text summary of frequency distribution."""
    buckets: dict[str, int] = {}
    for fl in labels:
        buckets[fl.label] = buckets.get(fl.label, 0) + 1
    order = ["frequent", "hourly", "daily", "weekly", "rare"]
    lines = ["Frequency distribution:"]
    for bucket in order:
        count = buckets.get(bucket, 0)
        if count:
            lines.append(f"  {bucket:<10} {count}")
    return "\n".join(lines)
