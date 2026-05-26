"""Detect cron entries that haven't fired recently or fire very infrequently."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry


def _count_field(field: str, min_val: int, max_val: int) -> int:
    """Return the number of distinct values a field resolves to."""
    if field == "*":
        return max_val - min_val + 1
    if "/" in field:
        base, step = field.split("/", 1)
        start = min_val if base == "*" else int(base)
        return len(range(start, max_val + 1, int(step)))
    if "-" in field:
        lo, hi = field.split("-", 1)
        return max(0, int(hi) - int(lo) + 1)
    if "," in field:
        return len(field.split(","))
    return 1


def fires_per_week(entry: CronEntry) -> int:
    """Estimate how many times an entry fires per week."""
    minutes = _count_field(entry.minute, 0, 59)
    hours = _count_field(entry.hour, 0, 23)
    days = _count_field(entry.dow, 0, 6)
    return minutes * hours * days


@dataclass
class StaleResult:
    entry: CronEntry
    fires_per_week: int
    threshold: int

    @property
    def is_stale(self) -> bool:
        return self.fires_per_week <= self.threshold

    @property
    def label(self) -> str:
        if self.fires_per_week == 0:
            return "never"
        if self.fires_per_week == 1:
            return "once/week"
        if self.fires_per_week <= 7:
            return "rare"
        return "infrequent"

    def __repr__(self) -> str:
        return (
            f"StaleResult(command={self.entry.command!r}, "
            f"fires_per_week={self.fires_per_week}, "
            f"stale={self.is_stale})"
        )


def find_stale(
    entries: List[CronEntry], threshold: int = 7
) -> List[StaleResult]:
    """Return StaleResult for every entry at or below *threshold* fires/week."""
    results = []
    for entry in entries:
        fpw = fires_per_week(entry)
        result = StaleResult(entry=entry, fires_per_week=fpw, threshold=threshold)
        if result.is_stale:
            results.append(result)
    results.sort(key=lambda r: r.fires_per_week)
    return results


def format_stale_report(results: List[StaleResult], color: bool = False) -> str:
    """Render a human-readable stale report."""
    if not results:
        return "No stale entries found."
    lines = ["Stale cron entries (low firing frequency):", ""]
    for r in results:
        badge = f"[{r.label}]"
        if color:
            badge = f"\033[33m{badge}\033[0m"
        lines.append(f"  {badge} {r.entry.command}  ({r.fires_per_week}x/week)")
        lines.append(f"       schedule: {r.entry.minute} {r.entry.hour} "
                     f"{r.entry.dom} {r.entry.month} {r.entry.dow}")
    return "\n".join(lines)
