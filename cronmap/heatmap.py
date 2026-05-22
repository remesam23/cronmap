"""Renders an hour-of-day × day-of-week heatmap in the terminal."""

from typing import Dict, List, Tuple

from cronmap.parser import CronEntry
from cronmap.stats import _expand_days, _expand_hours

DAY_ABBR = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# ANSI background shades (intensity 0-3)
_SHADES = [
    "",           # 0 – no events
    "\033[48;5;22m",   # dark green
    "\033[48;5;34m",   # medium green
    "\033[48;5;46m",   # bright green
]
_RESET = "\033[0m"


def build_heatmap_grid(entries: List[CronEntry]) -> Dict[Tuple[int, int], int]:
    """Return a dict mapping (hour, dow) -> event count."""
    grid: Dict[Tuple[int, int], int] = {}
    for entry in entries:
        for hour in _expand_hours(entry):
            for day in _expand_days(entry):
                key = (hour, day)
                grid[key] = grid.get(key, 0) + 1
    return grid


def _shade(count: int, max_count: int, use_color: bool) -> str:
    """Return a colored cell string for a given count."""
    if max_count == 0 or count == 0:
        cell = "  .  "
        return cell
    level = min(3, max(1, round(count / max_count * 3)))
    label = f" {count:>2}  "
    if use_color:
        return f"{_SHADES[level]}{label}{_RESET}"
    return label


def render_heatmap(entries: List[CronEntry], use_color: bool = True) -> str:
    """Render a 24-row × 7-column heatmap of cron activity."""
    grid = build_heatmap_grid(entries)
    max_count = max(grid.values(), default=0)

    header = "     " + "".join(f" {d:^4}" for d in DAY_ABBR)
    rows = [header, "     " + "+-----" * 7 + "+"]

    for hour in range(24):
        cells = "".join(
            _shade(grid.get((hour, day), 0), max_count, use_color)
            for day in range(7)
        )
        rows.append(f"{hour:02d}:xx |{cells}")

    return "\n".join(rows)
