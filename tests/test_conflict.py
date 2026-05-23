"""Unit tests for cronmap.conflict."""
from __future__ import annotations

import pytest

from cronmap.conflict import (
    ConflictResult,
    _expand,
    _intersect,
    find_conflicts,
    format_conflict_report,
)
from cronmap.parser import CronEntry


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="cmd"):
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command
    )


# --- _expand -----------------------------------------------------------------

def test_expand_wildcard_minutes():
    assert _expand("*", 0, 59) == list(range(60))


def test_expand_specific_value():
    assert _expand("5", 0, 59) == [5]


def test_expand_range():
    assert _expand("1-3", 0, 59) == [1, 2, 3]


def test_expand_list():
    assert _expand("0,15,30", 0, 59) == [0, 15, 30]


def test_expand_step():
    assert _expand("*/15", 0, 59) == [0, 15, 30, 45]


# --- _intersect --------------------------------------------------------------

def test_intersect_common_values():
    assert _intersect([1, 2, 3], [2, 3, 4]) == [2, 3]


def test_intersect_no_common():
    assert _intersect([1, 2], [3, 4]) == []


# --- find_conflicts ----------------------------------------------------------

def test_no_conflicts_different_hours():
    entries = [
        make_entry(minute="0", hour="6", command="job_a"),
        make_entry(minute="0", hour="7", command="job_b"),
    ]
    assert find_conflicts(entries) == []


def test_conflict_same_minute_and_hour():
    entries = [
        make_entry(minute="30", hour="9", command="job_a"),
        make_entry(minute="30", hour="9", command="job_b"),
    ]
    result = find_conflicts(entries)
    assert len(result) == 1
    assert bool(result[0]) is True


def test_conflict_wildcard_overlaps():
    entries = [
        make_entry(minute="*", hour="*", command="every_minute"),
        make_entry(minute="0", hour="12", command="noon"),
    ]
    result = find_conflicts(entries)
    assert len(result) == 1


def test_no_conflicts_different_dow():
    entries = [
        make_entry(minute="0", hour="8", dow="1", command="mon_job"),
        make_entry(minute="0", hour="8", dow="2", command="tue_job"),
    ]
    assert find_conflicts(entries) == []


def test_conflict_result_bool_false_when_no_shared_slots():
    ea = make_entry(minute="0", hour="6", command="a")
    eb = make_entry(minute="30", hour="7", command="b")
    cr = ConflictResult(ea, eb, [], [], list(range(7)))
    assert bool(cr) is False


def test_repr_contains_commands():
    ea = make_entry(command="alpha")
    eb = make_entry(command="beta")
    cr = ConflictResult(ea, eb, [0], [0], [0])
    assert "alpha" in repr(cr)
    assert "beta" in repr(cr)


# --- format_conflict_report --------------------------------------------------

def test_format_no_conflicts():
    assert format_conflict_report([]) == "No conflicts found."


def test_format_lists_commands():
    ea = make_entry(minute="0", hour="9", command="job_a")
    eb = make_entry(minute="0", hour="9", command="job_b")
    conflicts = find_conflicts([ea, eb])
    report = format_conflict_report(conflicts)
    assert "job_a" in report
    assert "job_b" in report


def test_format_shows_conflict_count():
    entries = [
        make_entry(minute="0", hour="9", command="x"),
        make_entry(minute="0", hour="9", command="y"),
        make_entry(minute="0", hour="9", command="z"),
    ]
    report = format_conflict_report(find_conflicts(entries))
    assert "3 conflict" in report
