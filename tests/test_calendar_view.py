"""Tests for cronmap.calendar_view."""
import pytest

from cronmap.calendar_view import (
    CalendarCell,
    _entry_matches_dow,
    build_calendar_grid,
    render_calendar,
)
from cronmap.parser import CronEntry


def make_entry(minute="0", hour="9", dom="*", month="*", dow="*", cmd="job"):
    return CronEntry(minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=cmd)


def test_calendar_cell_str_no_events():
    cell = CalendarCell(day=5)
    assert "5" in str(cell)
    assert "(" not in str(cell)


def test_calendar_cell_str_with_events():
    cell = CalendarCell(day=3, events=["job1", "job2"])
    assert "(2)" in str(cell)


def test_entry_matches_dow_wildcard():
    entry = make_entry(dow="*")
    for wd in range(7):
        assert _entry_matches_dow(entry, wd)


def test_entry_matches_dow_specific_monday():
    # crontab DOW 1 = Monday; ISO weekday 0 = Monday
    entry = make_entry(dow="1")
    assert _entry_matches_dow(entry, 0)   # Monday matches
    assert not _entry_matches_dow(entry, 1)  # Tuesday does not


def test_entry_matches_dow_sunday_zero():
    entry = make_entry(dow="0")
    assert _entry_matches_dow(entry, 6)  # Sunday ISO=6


def test_entry_matches_dow_sunday_seven():
    entry = make_entry(dow="7")
    assert _entry_matches_dow(entry, 6)


def test_entry_matches_dow_range():
    entry = make_entry(dow="1-5")  # Mon-Fri
    for wd in range(5):  # 0=Mon … 4=Fri
        assert _entry_matches_dow(entry, wd)
    assert not _entry_matches_dow(entry, 5)  # Saturday
    assert not _entry_matches_dow(entry, 6)  # Sunday


def test_build_calendar_grid_has_all_days():
    grid = build_calendar_grid(2024, 1, [])
    assert len(grid) == 31
    assert all(grid[d].events == [] for d in range(1, 32))


def test_build_calendar_grid_wildcard_entry_on_every_day():
    entry = make_entry(dow="*", cmd="daily")
    grid = build_calendar_grid(2024, 1, [entry])
    for cell in grid.values():
        assert "daily" in cell.events


def test_build_calendar_grid_weekday_only_entry():
    entry = make_entry(dow="1-5", cmd="weekday_job")
    grid = build_calendar_grid(2024, 1, [entry])  # Jan 2024: 1st is Monday
    # Jan 6 2024 is Saturday (weekday=5)
    assert "weekday_job" not in grid[6].events
    # Jan 5 2024 is Friday (weekday=4)
    assert "weekday_job" in grid[5].events


def test_render_calendar_contains_month_name():
    output = render_calendar(2024, 3, [])
    assert "March" in output
    assert "2024" in output


def test_render_calendar_contains_day_abbreviations():
    output = render_calendar(2024, 3, [])
    assert "Mon" in output
    assert "Sun" in output
