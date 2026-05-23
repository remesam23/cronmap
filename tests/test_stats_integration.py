"""Integration tests combining stats + heatmap with the parser."""

import textwrap

import pytest

from cronmap.parser import parse_crontab
from cronmap.stats import compute_stats, format_stats
from cronmap.heatmap import build_heatmap_grid, render_heatmap


SAMPLE_CRONTAB = textwrap.dedent("""\
    0 9 * * 1 /usr/bin/backup
    30 17 * * 1,2,3,4,5 /usr/bin/report
    0 0 * * 0 /usr/bin/weekly_clean
    15 8 * * * /usr/bin/healthcheck
""")


@pytest.fixture
def entries():
    return parse_crontab(SAMPLE_CRONTAB)


@pytest.fixture
def stats(entries):
    """Pre-computed stats for the sample crontab entries."""
    return compute_stats(entries)


def test_integration_total_entries(stats):
    assert stats.total_entries == 4


def test_integration_unique_commands(stats):
    assert stats.unique_commands == 4


def test_integration_busiest_day_is_weekday(stats):
    """Mon-Fri entries dominate, so busiest day should be a weekday."""
    weekdays = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
    assert stats.busiest_day in weekdays


def test_integration_format_stats_is_string(stats):
    result = format_stats(stats)
    assert isinstance(result, str)
    assert len(result) > 0


def test_integration_format_stats_contains_total(stats):
    """Formatted stats output should mention the total entry count."""
    result = format_stats(stats)
    assert str(stats.total_entries) in result


def test_integration_heatmap_grid_not_empty(entries):
    grid = build_heatmap_grid(entries)
    assert len(grid) > 0


def test_integration_heatmap_render_lines(entries):
    output = render_heatmap(entries, use_color=False)
    lines = output.splitlines()
    # header + separator + 24 hour rows
    assert len(lines) >= 26


def test_integration_healthcheck_appears_every_hour_every_day(entries):
    """healthcheck runs at 08:xx every day — grid should have count >= 1 for all days at hour 8."""
    grid = build_heatmap_grid(entries)
    for day in range(7):
        assert grid.get((8, day), 0) >= 1
