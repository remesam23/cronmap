"""Detect burst patterns: entries that fire many times within a short window."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry


def _count_field(field: str, lo: int, hi: int) -> int:
    """Count how many values a field expands to within [lo, hi]."""
    if field == "*":
        return hi - lo + 1
    if "/" in field:
        base, step = field.split("/", 1)
        step = int(step)
        start = lo if base == "*" else int(base)
        return len(range(start, hi + 1, step))
    if "-" in field:
        a, b = field.split("-", 1)
        return max(0, int(b) - int(a) + 1)
    if "," in field:
        return len(field.split(","))
    return 1


def fires_per_hour(entry: CronEntry) -> int:
    """Return how many times the entry fires within a single hour."""
    return _count_field(entry.minute, 0, 59)


@dataclass
class BurstResult:
    entry: CronEntry
    fires_per_hour: int
    threshold: int

    def __bool__(self) -> bool:
        return self.fires_per_hour >= self.threshold

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"BurstResult(command={self.entry.command!r}, "
            f"fires_per_hour={self.fires_per_hour}, "
            f"threshold={self.threshold}, burst={bool(self)})"
        )

    @property
    def label(self) -> str:
        if self.fires_per_hour >= 60:
            return "extreme"
        if self.fires_per_hour >= 30:
            return "high"
        if self.fires_per_hour >= 10:
            return "moderate"
        return "low"


def detect_bursts(
    entries: List[CronEntry], threshold: int = 10
) -> List[BurstResult]:
    """Return BurstResult for every entry; only those where bool() is True are bursting."""
    results = []
    for entry in entries:
        fph = fires_per_hour(entry)
        results.append(BurstResult(entry=entry, fires_per_hour=fph, threshold=threshold))
    return results


def format_burst_report(
    results: List[BurstResult], color: bool = False
) -> str:
    """Render a human-readable burst report."""
    bursting = [r for r in results if r]
    if not bursting:
        return "No burst patterns detected."
    lines = ["Burst patterns detected:", ""]
    for r in bursting:
        badge = f"[{r.label.upper()}]"
        if color:
            _colors = {"extreme": "\033[31m", "high": "\033[33m", "moderate": "\033[36m"}
            c = _colors.get(r.label, "")
            badge = f"{c}{badge}\033[0m"
        lines.append(f"  {badge} {r.entry.command}  ({r.fires_per_hour}x/hr)")
    return "\n".join(lines)
