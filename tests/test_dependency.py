"""Tests for cronmap.dependency."""
from __future__ import annotations

import pytest

from cronmap.dependency import (
    DependencyResult,
    _earliest_minute_of_day,
    _expand_field,
    find_dependencies,
    format_dependency_report,
)
from cronmap.parser import CronEntry


def make_entry(
    minute="0", hour="2", dom="*", month="*", dow="*", command="cmd"
) -> CronEntry:
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command
    )


# --- _expand_field ---

def test_expand_wildcard():
    assert _expand_field("*", 0, 5) == [0, 1, 2, 3, 4, 5]


def test_expand_specific():
    assert _expand_field("3", 0, 59) == [3]


def test_expand_range():
    assert _expand_field("1-3", 0, 23) == [1, 2, 3]


def test_expand_list():
    assert _expand_field("0,15,30", 0, 59) == [0, 15, 30]


def test_expand_step():
    assert _expand_field("*/15", 0, 59) == [0, 15, 30, 45]


# --- _earliest_minute_of_day ---

def test_earliest_minute_specific():
    e = make_entry(minute="30", hour="3")
    assert _earliest_minute_of_day(e) == 3 * 60 + 30


def test_earliest_minute_wildcard_hour():
    e = make_entry(minute="0", hour="*")
    assert _earliest_minute_of_day(e) == 0  # hour 0, minute 0


# --- find_dependencies ---

def test_no_dependencies_large_gap():
    a = make_entry(minute="0", hour="1", command="backup")
    b = make_entry(minute="0", hour="3", command="report")
    assert find_dependencies([a, b], max_gap_minutes=10) == []


def test_finds_dependency_within_gap():
    a = make_entry(minute="0", hour="2", command="dump")
    b = make_entry(minute="5", hour="2", command="compress")
    results = find_dependencies([a, b], max_gap_minutes=10)
    assert len(results) == 1
    assert results[0].upstream.command == "dump"
    assert results[0].downstream.command == "compress"
    assert results[0].gap_minutes == 5


def test_dependency_result_bool_true():
    a = make_entry(command="a")
    b = make_entry(minute="5", command="b")
    r = DependencyResult(upstream=a, downstream=b, gap_minutes=5)
    assert bool(r) is True


def test_no_dependency_different_dow():
    a = make_entry(minute="0", hour="2", dow="1", command="weekday")
    b = make_entry(minute="5", hour="2", dow="6", command="weekend")
    assert find_dependencies([a, b], max_gap_minutes=10) == []


def test_dependency_shared_dow():
    a = make_entry(minute="0", hour="4", dow="1,2", command="job-a")
    b = make_entry(minute="3", hour="4", dow="2,3", command="job-b")
    results = find_dependencies([a, b], max_gap_minutes=10)
    assert len(results) == 1


# --- format_dependency_report ---

def test_format_no_results():
    assert format_dependency_report([]) == "No implicit dependencies detected."


def test_format_with_results():
    a = make_entry(command="alpha")
    b = make_entry(minute="5", command="beta")
    r = DependencyResult(upstream=a, downstream=b, gap_minutes=5)
    report = format_dependency_report([r])
    assert "alpha" in report
    assert "beta" in report
    assert "5m" in report


def test_format_color_contains_ansi():
    a = make_entry(command="x")
    b = make_entry(minute="2", command="y")
    r = DependencyResult(upstream=a, downstream=b, gap_minutes=2)
    report = format_dependency_report([r], color=True)
    assert "\033[" in report
