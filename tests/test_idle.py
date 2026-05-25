"""Tests for cronmap.idle — idle period detection."""
import pytest
from cronmap.parser import CronEntry
from cronmap.idle import (
    IdlePeriod,
    find_idle_periods,
    format_idle_report,
    _expand_field,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="cmd") -> CronEntry:
    return CronEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        command=command,
        raw=f"{minute} {hour} {dom} {month} {dow} {command}",
    )


# ---------------------------------------------------------------------------
# _expand_field
# ---------------------------------------------------------------------------

def test_expand_wildcard_hours():
    assert _expand_field("*", 0, 23) == list(range(24))


def test_expand_specific_value():
    assert _expand_field("5", 0, 23) == [5]


def test_expand_range():
    assert _expand_field("2-4", 0, 23) == [2, 3, 4]


def test_expand_list():
    assert _expand_field("1,3,5", 0, 23) == [1, 3, 5]


def test_expand_step():
    assert _expand_field("*/6", 0, 23) == [0, 6, 12, 18]


# ---------------------------------------------------------------------------
# find_idle_periods
# ---------------------------------------------------------------------------

def test_no_entries_all_day_idle():
    """With no entries every hour of every day is idle."""
    periods = find_idle_periods([], min_duration_hours=1)
    # 7 days × 1 period each (00–23)
    assert len(periods) == 7
    assert all(p.duration_hours == 24 for p in periods)


def test_wildcard_entry_leaves_no_idle():
    """A job running every hour every day leaves no idle periods."""
    entry = make_entry(hour="*", dow="*")
    periods = find_idle_periods([entry], min_duration_hours=1)
    assert periods == []


def test_single_hour_active_rest_idle():
    """Only hour 12 on Monday active → idle before and after on Monday."""
    entry = make_entry(hour="12", dow="1")  # Tuesday in 0-indexed? dow=1 → Tuesday
    periods = find_idle_periods([entry], min_duration_hours=1)
    day1_periods = [p for p in periods if p.day == 1]
    # Should have two idle blocks: 00–11 and 13–23
    assert len(day1_periods) == 2
    durations = sorted(p.duration_hours for p in day1_periods)
    assert durations == [11, 12]


def test_min_duration_filters_short_idle():
    """Periods shorter than min_duration_hours are excluded."""
    # Active at hours 0 and 2 on day 0 → idle at hour 1 only (1 h)
    e1 = make_entry(hour="0", dow="0")
    e2 = make_entry(hour="2", dow="0")
    periods = find_idle_periods([e1, e2], min_duration_hours=2)
    day0_periods = [p for p in periods if p.day == 0]
    # The 1-hour gap at hour 1 should be filtered out
    for p in day0_periods:
        assert p.duration_hours >= 2


def test_idle_period_duration_hours():
    p = IdlePeriod(day=0, start_hour=3, end_hour=7)
    assert p.duration_hours == 5


def test_multiple_entries_reduce_idle():
    entries = [make_entry(hour=str(h), dow="0") for h in range(0, 24, 2)]
    periods = find_idle_periods(entries, min_duration_hours=1)
    day0_periods = [p for p in periods if p.day == 0]
    # Odd hours are idle, each 1-hour block
    assert all(p.duration_hours == 1 for p in day0_periods)


# ---------------------------------------------------------------------------
# format_idle_report
# ---------------------------------------------------------------------------

def test_format_idle_report_no_periods():
    assert format_idle_report([]) == "No idle periods found."


def test_format_idle_report_contains_day_name():
    p = IdlePeriod(day=0, start_hour=2, end_hour=5)
    report = format_idle_report([p])
    assert "Monday" in report


def test_format_idle_report_contains_hours():
    p = IdlePeriod(day=3, start_hour=14, end_hour=16)
    report = format_idle_report([p])
    assert "14:00" in report
    assert "16:59" in report


def test_format_idle_report_color_contains_ansi():
    p = IdlePeriod(day=0, start_hour=0, end_hour=1)
    report = format_idle_report([p], color=True)
    assert "\033[" in report


def test_format_idle_report_no_color_no_ansi():
    p = IdlePeriod(day=0, start_hour=0, end_hour=1)
    report = format_idle_report([p], color=False)
    assert "\033[" not in report
