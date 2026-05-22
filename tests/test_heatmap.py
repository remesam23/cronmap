"""Tests for cronmap.heatmap module."""

import pytest

from cronmap.parser import CronEntry
from cronmap.heatmap import build_heatmap_grid, render_heatmap
from cronmap.stats import strip_ansi  # reuse if available, else inline


def _strip(text: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", text)


def make_entry(hour="9", dow="1", command="/bin/job"):
    return CronEntry(
        minute=["0"], hour=[hour], dom=["*"], month=["*"],
        dow=[dow], command=command,
        raw=f"0 {hour} * * {dow} {command}"
    )


# --- build_heatmap_grid ---

def test_grid_single_entry():
    entry = make_entry(hour="10", dow="2")
    grid = build_heatmap_grid([entry])
    assert grid[(10, 2)] == 1


def test_grid_wildcard_hours():
    entry = CronEntry(
        minute=["0"], hour=["*"], dom=["*"], month=["*"],
        dow=["0"], command="hourly",
        raw="0 * * * 0 hourly"
    )
    grid = build_heatmap_grid([entry])
    for h in range(24):
        assert grid.get((h, 0), 0) == 1


def test_grid_wildcard_days():
    entry = CronEntry(
        minute=["0"], hour=["6"], dom=["*"], month=["*"],
        dow=["*"], command="daily",
        raw="0 6 * * * daily"
    )
    grid = build_heatmap_grid([entry])
    for d in range(7):
        assert grid.get((6, d), 0) == 1


def test_grid_accumulates_multiple_entries():
    e1 = make_entry(hour="8", dow="1")
    e2 = make_entry(hour="8", dow="1", command="/bin/other")
    grid = build_heatmap_grid([e1, e2])
    assert grid[(8, 1)] == 2


def test_grid_empty_entries():
    grid = build_heatmap_grid([])
    assert grid == {}


# --- render_heatmap ---

def test_render_heatmap_has_24_hour_rows():
    output = render_heatmap([], use_color=False)
    lines = output.splitlines()
    hour_lines = [l for l in lines if ":xx" in l]
    assert len(hour_lines) == 24


def test_render_heatmap_header_contains_days():
    output = _strip(render_heatmap([], use_color=False))
    for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
        assert day in output


def test_render_heatmap_shows_count():
    entry = make_entry(hour="12", dow="3")
    output = _strip(render_heatmap([entry], use_color=False))
    hour_lines = [l for l in output.splitlines() if l.startswith("12:xx")]
    assert len(hour_lines) == 1
    assert "1" in hour_lines[0]


def test_render_heatmap_no_color_no_ansi():
    entry = make_entry()
    output = render_heatmap([entry], use_color=False)
    assert "\033[" not in output


def test_render_heatmap_with_color_contains_ansi():
    entry = make_entry()
    output = render_heatmap([entry], use_color=True)
    assert "\033[" in output


def test_render_heatmap_empty_shows_dots():
    output = render_heatmap([], use_color=False)
    assert "." in output
