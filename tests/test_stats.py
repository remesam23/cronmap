"""Tests for cronmap.stats module."""

import pytest

from cronmap.parser import CronEntry
from cronmap.stats import (
    CronStats,
    DAY_NAMES,
    _expand_days,
    _expand_hours,
    compute_stats,
    format_stats,
)


def make_entry(minute="0", hour="9", dom="*", month="*", dow="1", command="/bin/task"):
    return CronEntry(
        minute=[minute],
        hour=[hour],
        dom=[dom],
        month=[month],
        dow=[dow],
        command=command,
        raw=f"{minute} {hour} {dom} {month} {dow} {command}",
    )


# --- _expand_days ---

def test_expand_days_wildcard():
    entry = make_entry(dow="*")
    assert _expand_days(entry) == list(range(7))


def test_expand_days_specific():
    entry = make_entry(dow="3")
    assert _expand_days(entry) == [3]


def test_expand_days_multiple():
    entry = CronEntry(
        minute=["0"], hour=["8"], dom=["*"], month=["*"],
        dow=["1", "3", "5"], command="backup",
        raw="0 8 * * 1,3,5 backup"
    )
    assert _expand_days(entry) == [1, 3, 5]


# --- _expand_hours ---

def test_expand_hours_wildcard():
    entry = make_entry(hour="*")
    assert _expand_hours(entry) == list(range(24))


def test_expand_hours_specific():
    entry = make_entry(hour="14")
    assert _expand_hours(entry) == [14]


# --- compute_stats ---

def test_compute_stats_empty():
    stats = compute_stats([])
    assert stats.total_entries == 0
    assert stats.busiest_day == "N/A"
    assert stats.most_frequent_command == "N/A"


def test_compute_stats_total_entries():
    entries = [make_entry(command="/bin/a"), make_entry(command="/bin/b")]
    stats = compute_stats(entries)
    assert stats.total_entries == 2


def test_compute_stats_unique_commands():
    entries = [
        make_entry(command="/bin/a"),
        make_entry(command="/bin/a"),
        make_entry(command="/bin/b"),
    ]
    stats = compute_stats(entries)
    assert stats.unique_commands == 2


def test_compute_stats_most_frequent_command():
    entries = [
        make_entry(command="/bin/a"),
        make_entry(command="/bin/a"),
        make_entry(command="/bin/b"),
    ]
    stats = compute_stats(entries)
    assert stats.most_frequent_command == "/bin/a"


def test_compute_stats_busiest_day():
    # dow=1 is Monday (index 1)
    entries = [
        make_entry(dow="1"),
        make_entry(dow="1"),
        make_entry(dow="2"),
    ]
    stats = compute_stats(entries)
    assert stats.busiest_day == "Monday"


def test_compute_stats_busiest_hour():
    entries = [
        make_entry(hour="9"),
        make_entry(hour="9"),
        make_entry(hour="14"),
    ]
    stats = compute_stats(entries)
    assert stats.busiest_hour == 9


def test_compute_stats_events_per_day_keys():
    stats = compute_stats([make_entry()])
    assert set(stats.events_per_day.keys()) == set(DAY_NAMES)


def test_compute_stats_events_per_hour_keys():
    stats = compute_stats([make_entry()])
    assert set(stats.events_per_hour.keys()) == set(range(24))


# --- format_stats ---

def test_format_stats_contains_total():
    stats = compute_stats([make_entry()])
    output = format_stats(stats)
    assert "Total entries" in output
    assert "1" in output


def test_format_stats_contains_busiest_day():
    stats = compute_stats([make_entry(dow="1")])
    output = format_stats(stats)
    assert "Monday" in output


def test_format_stats_contains_busiest_hour():
    stats = compute_stats([make_entry(hour="7")])
    output = format_stats(stats)
    assert "07:00" in output
