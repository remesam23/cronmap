"""Estimate the computational 'cost' of cron entries based on execution frequency."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronmap.parser import CronEntry

# Minutes per week
_MINUTES_PER_WEEK = 7 * 24 * 60


def _count_field(field: str, min_val: int, max_val: int) -> int:
    """Return the number of distinct values a cron field resolves to."""
    if field == "*":
        return max_val - min_val + 1
    if "/" in field:
        base, step = field.split("/", 1)
        step = int(step)
        start = min_val if base == "*" else int(base)
        return len(range(start, max_val + 1, step))
    if "-" in field:
        lo, hi = field.split("-", 1)
        return int(hi) - int(lo) + 1
    if "," in field:
        return len(field.split(","))
    return 1


def fires_per_week(entry: CronEntry) -> int:
    """Return the number of times an entry fires in a standard week."""
    minutes = _count_field(entry.minute, 0, 59)
    hours = _count_field(entry.hour, 0, 23)
    days_of_week = _count_field(entry.dow, 0, 6)
    return minutes * hours * days_of_week


@dataclass
class CostResult:
    entry: CronEntry
    fires_per_week: int
    cost_score: float  # 0.0 – 1.0 relative to maximum possible

    def __repr__(self) -> str:
        return (
            f"CostResult(command={self.entry.command!r}, "
            f"fires_per_week={self.fires_per_week}, "
            f"cost_score={self.cost_score:.4f})"
        )

    def label(self) -> str:
        if self.cost_score >= 0.5:
            return "high"
        if self.cost_score >= 0.1:
            return "medium"
        return "low"


def compute_cost(entry: CronEntry) -> CostResult:
    """Compute a normalised cost score for a single entry."""
    fpw = fires_per_week(entry)
    score = min(fpw / _MINUTES_PER_WEEK, 1.0)
    return CostResult(entry=entry, fires_per_week=fpw, cost_score=score)


def rank_by_cost(entries: List[CronEntry], descending: bool = True) -> List[CostResult]:
    """Return CostResult objects sorted by cost score."""
    results = [compute_cost(e) for e in entries]
    results.sort(key=lambda r: r.cost_score, reverse=descending)
    return results


def format_cost_report(results: List[CostResult], color: bool = False) -> str:
    """Render a simple text table of cost results."""
    _RESET = "\033[0m" if color else ""
    _BOLD = "\033[1m" if color else ""
    _RED = "\033[31m" if color else ""
    _YELLOW = "\033[33m" if color else ""
    _GREEN = "\033[32m" if color else ""

    label_color = {"high": _RED, "medium": _YELLOW, "low": _GREEN}

    header = f"{_BOLD}{'Command':<35} {'Fires/week':>12} {'Score':>8} {'Level':<8}{_RESET}"
    sep = "-" * 67
    lines = [header, sep]
    for r in results:
        lbl = r.label()
        col = label_color.get(lbl, "")
        lines.append(
            f"{r.entry.command:<35} {r.fires_per_week:>12} "
            f"{r.cost_score:>8.4f} {col}{lbl:<8}{_RESET}"
        )
    return "\n".join(lines)
