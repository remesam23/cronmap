"""Tests for cronmap.gap — gap detection in weekly schedules."""
import pytest

from cronmap.parser import CronEntry
from cronmap.gap import GapResult, find_gaps, _expand_dow, _expand_hours


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", cmd="job") -> CronEntry:
    return CronEntry(
        minute=minute, hour=hour, dom=dom,
        month=month, dow=dow, command=cmd,
    )


# --- _expand_dow ---

def test_expand_dow_wildcard():
    assert _expand_dow("*") == list(range(7))


def test_expand_dow_specific():
    assert _expand_dow("1") == [1]


def test_expand_dow_range():
    assert _expand_dow("1-5") == [1, 2, 3, 4, 5]


def test_expand_dow_list():
    assert _expand_dow("0,6") == [0, 6]


# --- _expand_hours ---

def test_expand_hours_wildcard():
    assert _expand_hours("*") == list(range(24))


def test_expand_hours_specific():
    assert _expand_hours("9") == [9]


def test_expand_hours_range():
    assert _expand_hours("8-10") == [8, 9, 10]


def test_expand_hours_step():
    assert _expand_hours("*/6") == [0, 6, 12, 18]


# --- find_gaps ---

def test_no_entries_yields_full_day_gaps():
    gaps = find_gaps([], min_duration=1)
    # Every hour of every day is free → one big gap per day
    assert len(gaps) == 7
    for g in gaps:
        assert g.start_hour == 0
        assert g.end_hour == 24
        assert g.duration_hours == 24


def test_wildcard_hour_entry_leaves_no_gaps():
    entry = make_entry(hour="*", dow="*")
    gaps = find_gaps([entry], min_duration=1)
    assert gaps == []


def test_gap_detected_between_jobs():
    # Jobs only at hour 8 and 17 on Monday (dow=0)
    entries = [
        make_entry(hour="8", dow="0"),
        make_entry(hour="17", dow="0"),
    ]
    gaps = find_gaps(entries, min_duration=1)
    monday_gaps = [g for g in gaps if g.day == 0]
    # Gap from 0-8 and 9-17 and 18-24 should all appear
    gap_starts = {g.start_hour for g in monday_gaps}
    assert 0 in gap_starts
    assert 9 in gap_starts
    assert 18 in gap_starts


def test_min_duration_filters_short_gaps():
    # Only hour 5 is busy on day 0; gap 0-5 (5h) and 6-24 (18h)
    entries = [make_entry(hour="5", dow="0")]
    long_gaps = find_gaps(entries, min_duration=10)
    monday_gaps = [g for g in long_gaps if g.day == 0]
    durations = {g.duration_hours for g in monday_gaps}
    assert 5 not in durations          # 5-hour gap filtered out
    assert any(d >= 10 for d in durations)


def test_gap_result_duration_property():
    g = GapResult(day=0, start_hour=2, end_hour=8)
    assert g.duration_hours == 6


def test_specific_dow_does_not_affect_other_days():
    # Entry only on Wednesday (dow=3)
    entries = [make_entry(hour="*", dow="3")]
    gaps = find_gaps(entries, min_duration=1)
    wednesday_gaps = [g for g in gaps if g.day == 3]
    other_gaps = [g for g in gaps if g.day != 3]
    assert wednesday_gaps == []          # fully covered
    assert len(other_gaps) == 6         # other days fully free
