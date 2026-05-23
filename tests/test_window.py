"""Tests for cronmap.window."""
from __future__ import annotations

import pytest

from cronmap.parser import CronEntry
from cronmap.window import WindowResult, _expand_field, entries_in_window


def make_entry(minute="0", hour="9", dom="*", month="*", dow="*", command="cmd") -> CronEntry:
    return CronEntry(minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command)


# --- _expand_field ---

def test_expand_wildcard():
    assert _expand_field("*", 0, 3) == [0, 1, 2, 3]


def test_expand_specific():
    assert _expand_field("5", 0, 59) == [5]


def test_expand_range():
    assert _expand_field("2-4", 0, 6) == [2, 3, 4]


def test_expand_list():
    assert _expand_field("1,3,5", 0, 6) == [1, 3, 5]


def test_expand_step():
    assert _expand_field("*/15", 0, 59) == [0, 15, 30, 45]


# --- WindowResult ---

def test_window_result_bool_true():
    entry = make_entry()
    wr = WindowResult(entry=entry, matching_times=[(9, 0)])
    assert bool(wr) is True


def test_window_result_bool_false():
    entry = make_entry()
    wr = WindowResult(entry=entry, matching_times=[])
    assert bool(wr) is False


# --- entries_in_window ---

def test_single_entry_inside_window():
    entries = [make_entry(minute="0", hour="10", dow="1", command="backup")]
    results = entries_in_window(entries, dow=1, start_hour=9, start_minute=0, end_hour=17, end_minute=0)
    assert len(results) == 1
    assert results[0].entry.command == "backup"
    assert (10, 0) in results[0].matching_times


def test_entry_outside_window_excluded():
    entries = [make_entry(minute="0", hour="22", dow="1", command="nightly")]
    results = entries_in_window(entries, dow=1, start_hour=9, start_minute=0, end_hour=17, end_minute=0)
    assert results == []


def test_entry_wrong_dow_excluded():
    entries = [make_entry(minute="0", hour="10", dow="0", command="sunday_job")]
    results = entries_in_window(entries, dow=1, start_hour=9, start_minute=0, end_hour=17, end_minute=0)
    assert results == []


def test_wildcard_dow_matches_any_day():
    entries = [make_entry(minute="30", hour="12", dow="*", command="lunch")]
    for day in range(7):
        results = entries_in_window(entries, dow=day, start_hour=12, start_minute=0, end_hour=12, end_minute=59)
        assert len(results) == 1


def test_boundary_times_inclusive():
    entries = [make_entry(minute="0", hour="9", dow="*", command="start"),
               make_entry(minute="0", hour="17", dow="*", command="end")]
    results = entries_in_window(entries, dow=1, start_hour=9, start_minute=0, end_hour=17, end_minute=0)
    commands = [r.entry.command for r in results]
    assert "start" in commands
    assert "end" in commands


def test_multiple_firing_times_returned():
    entries = [make_entry(minute="*/30", hour="9-11", dow="*", command="freq")]
    results = entries_in_window(entries, dow=2, start_hour=9, start_minute=0, end_hour=11, end_minute=59)
    assert len(results) == 1
    # 9:00, 9:30, 10:00, 10:30, 11:00, 11:30
    assert len(results[0].matching_times) == 6


def test_invalid_window_raises():
    entries = [make_entry()]
    with pytest.raises(ValueError, match="end time"):
        entries_in_window(entries, dow=1, start_hour=17, start_minute=0, end_hour=9, end_minute=0)


def test_empty_entries_returns_empty():
    results = entries_in_window([], dow=1, start_hour=9, start_minute=0, end_hour=17, end_minute=0)
    assert results == []
