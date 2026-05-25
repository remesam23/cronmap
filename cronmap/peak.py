"""Peak-hour detection: find the hours of the day with the most cron activity."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from cronmap.parser import CronEntry


def _expand_hours(hour_field: str) -> List[int]:
    """Return the list of hours matched by *hour_field*."""
    if hour_field == "*":
        return list(range(24))
    hours: List[int] = []
    for part in hour_field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = 0 if base == "*" else int(base)
            hours.extend(range(start, 24, int(step)))
        elif "-" in part:
            lo, hi = part.split("-", 1)
            hours.extend(range(int(lo), int(hi) + 1))
        else:
            hours.append(int(part))
    return hours


def build_hour_counts(entries: List[CronEntry]) -> Dict[int, int]:
    """Return a mapping of hour -> number of entries that fire during that hour."""
    counts: Dict[int, int] = {h: 0 for h in range(24)}
    for entry in entries:
        for h in _expand_hours(entry.hour):
            counts[h] += 1
    return counts


@dataclass
class PeakResult:
    hour_counts: Dict[int, int]
    peak_hours: List[int] = field(default_factory=list)
    peak_count: int = 0

    def __post_init__(self) -> None:
        if self.hour_counts:
            self.peak_count = max(self.hour_counts.values())
            self.peak_hours = sorted(
                h for h, c in self.hour_counts.items() if c == self.peak_count
            )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PeakResult(peak_hours={self.peak_hours}, peak_count={self.peak_count})"
        )


def find_peak_hours(entries: List[CronEntry]) -> PeakResult:
    """Analyse *entries* and return a :class:`PeakResult`."""
    counts = build_hour_counts(entries)
    return PeakResult(hour_counts=counts)


def format_peak_report(result: PeakResult, *, color: bool = False) -> str:
    """Render a human-readable peak-hour report."""
    lines: List[str] = []
    _b = "\033[1m" if color else ""
    _r = "\033[0m" if color else ""
    _y = "\033[33m" if color else ""

    lines.append(f"{_b}Peak hours:{_r}")
    for h in range(24):
        count = result.hour_counts[h]
        bar = "#" * count
        marker = f" {_y}<-- peak{_r}" if h in result.peak_hours else ""
        lines.append(f"  {h:02d}:00  {bar:<30} ({count}){marker}")
    lines.append("")
    peak_str = ", ".join(f"{h:02d}:xx" for h in result.peak_hours)
    lines.append(f"{_b}Busiest hour(s):{_r} {peak_str} ({result.peak_count} entries)")
    return "\n".join(lines)
