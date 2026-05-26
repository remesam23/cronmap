"""Tests for cronmap.stale."""
from __future__ import annotations

import pytest

from cronmap.parser import CronEntry
from cronmap.stale import (
    StaleResult,
    _count_field,
    find_stale,
    fires_per_week,
    format_stale_report,
)


def make_entry(
    minute="0", hour="2", dom="*", month="*", dow="0", command="/bin/job"
) -> CronEntry:
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command
    )


# --- _count_field ---

def test_count_field_wildcard():
    assert _count_field("*", 0, 59) == 60


def test_count_field_specific_value():
    assert _count_field("5", 0, 59) == 1


def test_count_field_range():
    assert _count_field("1-5", 0, 59) == 5


def test_count_field_list():
    assert _count_field("1,2,3", 0, 59) == 3


def test_count_field_step():
    assert _count_field("*/15", 0, 59) == 4


# --- fires_per_week ---

def test_fires_per_week_once_weekly():
    entry = make_entry(minute="0", hour="3", dow="0")
    assert fires_per_week(entry) == 1


def test_fires_per_week_daily():
    entry = make_entry(minute="0", hour="6", dow="*")
    assert fires_per_week(entry) == 7


def test_fires_per_week_every_minute():
    entry = make_entry(minute="*", hour="*", dow="*")
    assert fires_per_week(entry) == 60 * 24 * 7


# --- StaleResult ---

def test_stale_result_is_stale_below_threshold():
    entry = make_entry(minute="0", hour="4", dow="0")
    r = StaleResult(entry=entry, fires_per_week=1, threshold=7)
    assert r.is_stale is True


def test_stale_result_not_stale_above_threshold():
    entry = make_entry(minute="0", hour="*", dow="*")
    r = StaleResult(entry=entry, fires_per_week=168, threshold=7)
    assert r.is_stale is False


def test_stale_result_label_once():
    entry = make_entry()
    r = StaleResult(entry=entry, fires_per_week=1, threshold=7)
    assert r.label == "once/week"


def test_stale_result_label_rare():
    entry = make_entry()
    r = StaleResult(entry=entry, fires_per_week=5, threshold=7)
    assert r.label == "rare"


def test_stale_result_repr_contains_command():
    entry = make_entry(command="/usr/bin/backup")
    r = StaleResult(entry=entry, fires_per_week=1, threshold=7)
    assert "/usr/bin/backup" in repr(r)


# --- find_stale ---

def test_find_stale_returns_only_stale():
    entries = [
        make_entry(minute="0", hour="2", dow="0", command="weekly"),
        make_entry(minute="*", hour="*", dow="*", command="heartbeat"),
    ]
    results = find_stale(entries, threshold=7)
    commands = [r.entry.command for r in results]
    assert "weekly" in commands
    assert "heartbeat" not in commands


def test_find_stale_sorted_ascending():
    entries = [
        make_entry(minute="0", hour="*", dow="1-5", command="workdays"),
        make_entry(minute="0", hour="3", dow="0", command="weekly"),
    ]
    results = find_stale(entries, threshold=10)
    assert results[0].fires_per_week <= results[-1].fires_per_week


def test_find_stale_empty_when_all_frequent():
    entries = [make_entry(minute="*", hour="*", dow="*", command="busy")]
    assert find_stale(entries, threshold=7) == []


# --- format_stale_report ---

def test_format_stale_report_no_results():
    assert format_stale_report([]) == "No stale entries found."


def test_format_stale_report_contains_command():
    entry = make_entry(command="/bin/weekly")
    r = StaleResult(entry=entry, fires_per_week=1, threshold=7)
    report = format_stale_report([r])
    assert "/bin/weekly" in report


def test_format_stale_report_color_contains_ansi():
    entry = make_entry(command="/bin/rare")
    r = StaleResult(entry=entry, fires_per_week=2, threshold=7)
    report = format_stale_report([r], color=True)
    assert "\033[" in report
