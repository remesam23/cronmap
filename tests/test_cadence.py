"""Tests for cronmap.cadence."""
import pytest
from cronmap.parser import CronEntry
from cronmap.cadence import (
    _count_field,
    fires_per_hour,
    fires_per_day,
    analyze_cadence,
    analyze_all,
    CadenceResult,
)


def make_entry(minute="0", hour="0", dom="*", month="*", dow="*", command="cmd"):
    return CronEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        command=command,
    )


# --- _count_field ---

def test_count_field_wildcard():
    assert _count_field("*", 0, 59) == 60


def test_count_field_specific_value():
    assert _count_field("30", 0, 59) == 1


def test_count_field_range():
    assert _count_field("0-5", 0, 59) == 6


def test_count_field_list():
    assert _count_field("0,15,30,45", 0, 59) == 4


def test_count_field_step():
    assert _count_field("*/15", 0, 59) == 4


def test_count_field_range_with_step():
    assert _count_field("0-30/10", 0, 59) == 4


# --- fires_per_hour ---

def test_fires_per_hour_wildcard_minute():
    entry = make_entry(minute="*")
    assert fires_per_hour(entry) == 60


def test_fires_per_hour_specific_minute():
    entry = make_entry(minute="0")
    assert fires_per_hour(entry) == 1


def test_fires_per_hour_step_minute():
    entry = make_entry(minute="*/10")
    assert fires_per_hour(entry) == 6


# --- fires_per_day ---

def test_fires_per_day_once_daily():
    entry = make_entry(minute="0", hour="3")
    assert fires_per_day(entry) == 1


def test_fires_per_day_every_hour():
    entry = make_entry(minute="0", hour="*")
    assert fires_per_day(entry) == 24


def test_fires_per_day_every_minute():
    entry = make_entry(minute="*", hour="*")
    assert fires_per_day(entry) == 1440


# --- analyze_cadence ---

def test_cadence_result_label_continuous():
    entry = make_entry(minute="*", hour="*", dow="*")
    result = analyze_cadence(entry)
    assert result.label == "continuous"


def test_cadence_result_label_daily():
    entry = make_entry(minute="0", hour="2", dow="*")
    result = analyze_cadence(entry)
    assert result.label == "daily"


def test_cadence_result_label_weekly():
    entry = make_entry(minute="0", hour="9", dow="1")
    result = analyze_cadence(entry)
    assert result.label == "weekly or less"
    assert result.fires_per_week == 1


def test_cadence_result_str_contains_command():
    entry = make_entry(minute="0", hour="*", dow="*", command="/usr/bin/backup")
    result = analyze_cadence(entry)
    assert "/usr/bin/backup" in str(result)


def test_cadence_fires_per_week_calculation():
    # Every 30 min, every hour, 5 days a week
    entry = make_entry(minute="0,30", hour="*", dow="1-5")
    result = analyze_cadence(entry)
    assert result.fires_per_week == 2 * 24 * 5


# --- analyze_all ---

def test_analyze_all_returns_one_per_entry():
    entries = [
        make_entry(minute="0", hour="1", command="a"),
        make_entry(minute="0", hour="2", command="b"),
        make_entry(minute="0", hour="3", command="c"),
    ]
    results = analyze_all(entries)
    assert len(results) == 3


def test_analyze_all_empty():
    assert analyze_all([]) == []


def test_analyze_all_preserves_order():
    entries = [
        make_entry(command="first"),
        make_entry(command="second"),
    ]
    results = analyze_all(entries)
    assert results[0].entry.command == "first"
    assert results[1].entry.command == "second"
