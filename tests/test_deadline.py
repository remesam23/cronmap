"""Tests for cronmap.deadline."""
import pytest
from cronmap.parser import CronEntry
from cronmap.deadline import (
    _expand_field,
    _earliest_start_minute,
    _latest_start_minute,
    find_deadlines,
    format_deadline_report,
    DeadlineResult,
)


def make_entry(minute="0", hour="0", dom="*", month="*", dow="*", command="cmd"):
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command
    )


# --- _expand_field ---

def test_expand_wildcard_minutes():
    assert _expand_field("*", 0, 59) == list(range(60))


def test_expand_specific_value():
    assert _expand_field("5", 0, 59) == [5]


def test_expand_range():
    assert _expand_field("2-4", 0, 59) == [2, 3, 4]


def test_expand_list():
    assert _expand_field("1,3,5", 0, 59) == [1, 3, 5]


def test_expand_step():
    assert _expand_field("*/15", 0, 59) == [0, 15, 30, 45]


# --- earliest / latest start minute ---

def test_earliest_start_minute_midnight():
    entry = make_entry(minute="0", hour="0")
    assert _earliest_start_minute(entry) == 0


def test_latest_start_minute_end_of_day():
    entry = make_entry(minute="59", hour="23")
    assert _latest_start_minute(entry) == 23 * 60 + 59


def test_earliest_start_minute_with_list_hour():
    entry = make_entry(minute="0", hour="6,12")
    assert _earliest_start_minute(entry) == 6 * 60


def test_latest_start_minute_with_list_hour():
    entry = make_entry(minute="30", hour="6,12")
    assert _latest_start_minute(entry) == 12 * 60 + 30


# --- find_deadlines ---

def test_no_deadlines_when_gap_exceeds_threshold():
    a = make_entry(minute="0", hour="1", command="job_a")
    b = make_entry(minute="30", hour="1", command="job_b")
    results = find_deadlines([a, b], threshold_minutes=10)
    assert results == []


def test_finds_tight_deadline():
    a = make_entry(minute="0", hour="2", command="backup")
    b = make_entry(minute="5", hour="2", command="verify")
    results = find_deadlines([a, b], threshold_minutes=10)
    assert len(results) == 1
    assert results[0].predecessor.command == "backup"
    assert results[0].successor.command == "verify"
    assert results[0].gap_minutes == 5
    assert results[0].tight is True


def test_gap_exactly_at_threshold_is_included():
    a = make_entry(minute="0", hour="3", command="a")
    b = make_entry(minute="10", hour="3", command="b")
    results = find_deadlines([a, b], threshold_minutes=10)
    assert len(results) == 1


def test_same_entry_not_paired_with_itself():
    a = make_entry(minute="0", hour="4", command="solo")
    results = find_deadlines([a], threshold_minutes=60)
    assert results == []


def test_bool_of_result():
    a = make_entry(minute="0", hour="5", command="a")
    b = make_entry(minute="3", hour="5", command="b")
    r = find_deadlines([a, b], threshold_minutes=10)[0]
    assert bool(r) is True


# --- format_deadline_report ---

def test_format_no_results():
    assert format_deadline_report([]) == "No tight deadlines detected."


def test_format_shows_commands():
    a = make_entry(minute="0", hour="6", command="/usr/bin/backup")
    b = make_entry(minute="8", hour="6", command="/usr/bin/verify")
    results = find_deadlines([a, b], threshold_minutes=10)
    report = format_deadline_report(results)
    assert "/usr/bin/backup" in report
    assert "/usr/bin/verify" in report


def test_format_shows_gap():
    a = make_entry(minute="0", hour="7", command="a")
    b = make_entry(minute="4", hour="7", command="b")
    results = find_deadlines([a, b], threshold_minutes=10)
    report = format_deadline_report(results)
    assert "4" in report


def test_format_color_contains_ansi():
    a = make_entry(minute="0", hour="8", command="a")
    b = make_entry(minute="2", hour="8", command="b")
    results = find_deadlines([a, b], threshold_minutes=10)
    report = format_deadline_report(results, color=True)
    assert "\033[" in report
