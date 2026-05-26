"""Churn analysis: detect entries that fire most frequently across a week."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from cronmap.parser import CronEntry


def _count_field(value: str, min_val: int, max_val: int) -> int:
    """Return the number of distinct values a cron field expands to."""
    if value == "*":
        return max_val - min_val + 1
    if "/" in value:
        base, step = value.split("/", 1)
        start = min_val if base == "*" else int(base)
        return len(range(start, max_val + 1, int(step)))
    if "-" in value:
        lo, hi = value.split("-", 1)
        return int(hi) - int(lo) + 1
    if "," in value:
        return len(value.split(","))
    return 1


def fires_per_week(entry: CronEntry) -> int:
    """Estimate how many times an entry fires in a week."""
    minutes = _count_field(entry.minute, 0, 59)
    hours = _count_field(entry.hour, 0, 23)
    days = _count_field(entry.dow, 0, 6)
    return minutes * hours * days


@dataclass
class ChurnResult:
    entry: CronEntry
    fires_per_week: int

    def __repr__(self) -> str:
        return (
            f"ChurnResult(command={self.entry.command!r}, "
            f"fires_per_week={self.fires_per_week})"
        )

    @property
    def label(self) -> str:
        fpw = self.fires_per_week
        if fpw >= 10_000:
            return "extreme"
        if fpw >= 1_000:
            return "high"
        if fpw >= 100:
            return "medium"
        return "low"


def compute_churn(entries: Sequence[CronEntry]) -> List[ChurnResult]:
    """Return ChurnResult for every entry, sorted descending by fires_per_week."""
    results = [ChurnResult(e, fires_per_week(e)) for e in entries]
    results.sort(key=lambda r: r.fires_per_week, reverse=True)
    return results


def format_churn_report(results: List[ChurnResult], *, color: bool = False) -> str:
    """Render a human-readable churn report."""
    if not results:
        return "No entries."

    _COLORS = {"extreme": "\033[31m", "high": "\033[33m", "medium": "\033[36m", "low": "\033[32m"}
    _RESET = "\033[0m"

    lines = ["Churn Report (fires per week):", ""]
    for r in results:
        badge = f"[{r.label.upper()}]"
        if color:
            c = _COLORS.get(r.label, "")
            badge = f"{c}{badge}{_RESET}"
        lines.append(f"  {badge:20s}  {r.fires_per_week:>7d}  {r.entry.command}")
    return "\n".join(lines)
