"""Detect cron entries that fire too frequently and may throttle a system."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry

# Thresholds (fires per hour)
_WARN_THRESHOLD = 12   # more than once every 5 minutes
_CRITICAL_THRESHOLD = 30  # more than once every 2 minutes


def _count_field(field: str, lo: int, hi: int) -> int:
    """Return how many distinct values *field* expands to within [lo, hi]."""
    if field == "*":
        return hi - lo + 1
    if "/" in field:
        base, step = field.split("/", 1)
        step = int(step)
        start = lo if base == "*" else int(base.split("-")[0])
        return len(range(start, hi + 1, step))
    if "-" in field:
        a, b = field.split("-", 1)
        return int(b) - int(a) + 1
    if "," in field:
        return len(field.split(","))
    return 1


def fires_per_hour(entry: CronEntry) -> int:
    """Estimate how many times *entry* fires within a single hour."""
    return _count_field(entry.minute, 0, 59)


@dataclass
class ThrottleResult:
    entry: CronEntry
    fires_per_hour: int
    level: str          # "ok", "warn", or "critical"

    def __bool__(self) -> bool:
        return self.level != "ok"

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ThrottleResult(command={self.entry.command!r}, "
            f"fires_per_hour={self.fires_per_hour}, level={self.level!r})"
        )


def check_throttle(entry: CronEntry) -> ThrottleResult:
    """Return a :class:`ThrottleResult` for a single entry."""
    fph = fires_per_hour(entry)
    if fph >= _CRITICAL_THRESHOLD:
        level = "critical"
    elif fph >= _WARN_THRESHOLD:
        level = "warn"
    else:
        level = "ok"
    return ThrottleResult(entry=entry, fires_per_hour=fph, level=level)


def find_throttled(entries: List[CronEntry]) -> List[ThrottleResult]:
    """Return :class:`ThrottleResult` objects for entries that exceed a threshold."""
    return [r for r in (check_throttle(e) for e in entries) if r]


def format_throttle_report(results: List[ThrottleResult], *, color: bool = False) -> str:
    """Render a human-readable throttle report."""
    if not results:
        return "No throttle issues found."

    _RED = "\033[31m" if color else ""
    _YEL = "\033[33m" if color else ""
    _RST = "\033[0m" if color else ""

    lines = ["Throttle report:", ""]
    for r in results:
        colour = _RED if r.level == "critical" else _YEL
        tag = f"{colour}[{r.level.upper()}]{_RST}"
        lines.append(f"  {tag} {r.entry.command!r:40s} {r.fires_per_hour} fires/hour")
    return "\n".join(lines)
