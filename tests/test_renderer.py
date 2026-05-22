"""Tests for cronmap.renderer module."""

import pytest
from cronmap.parser import CronEntry
from cronmap.renderer import render_weekly_table, render_compact, _format_time


SIMPLE_ENTRIES = [
    CronEntry(minutes=[30], hours=[9], days_of_week=list(range(7)), command="backup.sh"),
    CronEntry(minutes=[0], hours=[17], days_of_week=[0, 1, 2, 3, 4], command="report.py"),
]


def test_format_time_padding():
    assert _format_time(9, 5) == "09:05"
    assert _format_time(17, 30) == "17:30"
    assert _format_time(0, 0) == "00:00"


def test_render_weekly_table_contains_header():
    output = render_weekly_table(SIMPLE_ENTRIES, use_color=False)
    assert "Weekly Cron Schedule" in output


def test_render_weekly_table_contains_all_days():
    output = render_weekly_table(SIMPLE_ENTRIES, use_color=False)
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        assert day in output


def test_render_weekly_table_shows_commands():
    output = render_weekly_table(SIMPLE_ENTRIES, use_color=False)
    assert "backup.sh" in output
    assert "report.py" in output


def test_render_weekly_table_shows_times():
    output = render_weekly_table(SIMPLE_ENTRIES, use_color=False)
    assert "09:30" in output
    assert "17:00" in output


def test_render_weekly_table_no_color_no_escape():
    output = render_weekly_table(SIMPLE_ENTRIES, use_color=False)
    assert "\033[" not in output


def test_render_weekly_table_with_color_has_escape():
    output = render_weekly_table(SIMPLE_ENTRIES, use_color=True)
    assert "\033[" in output


def test_render_compact_contains_day_abbrevs():
    output = render_compact(SIMPLE_ENTRIES, use_color=False)
    for abbrev in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        assert abbrev in output


def test_render_compact_event_count():
    output = render_compact(SIMPLE_ENTRIES, use_color=False)
    # Monday should have both backup.sh (09:30) and report.py (17:00)
    monday_line = [l for l in output.splitlines() if l.startswith("Mon")][0]
    assert " 2 " in monday_line


def test_render_weekly_table_empty_day_message():
    # Only schedule on Monday (day 0)
    entries = [CronEntry(minutes=[0], hours=[8], days_of_week=[0], command="task")]
    output = render_weekly_table(entries, use_color=False)
    assert "(no events)" in output
