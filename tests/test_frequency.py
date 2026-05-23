"""Tests for cronmap.frequency."""
import pytest
from cronmap.parser import CronEntry
from cronmap.frequency import (
    fires_per_day,
    classify,
    classify_all,
    frequency_summary,
    _field_count,
)


def make_entry(minute="0", hour="0", dom="*", month="*", dow="*", command="cmd"):
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command
    )


# --- _field_count ---

def test_field_count_wildcard_minutes():
    assert _field_count("*", 0, 59) == 60


def test_field_count_specific_value():
    assert _field_count("5", 0, 59) == 1


def test_field_count_range():
    assert _field_count("9-11", 0, 23) == 3


def test_field_count_list():
    assert _field_count("1,2,3", 0, 59) == 3


def test_field_count_step():
    # */15 → 0,15,30,45 → 4 values
    assert _field_count("*/15", 0, 59) == 4


# --- fires_per_day ---

def test_fires_per_day_once_daily():
    entry = make_entry(minute="0", hour="6", dow="*")
    assert fires_per_day(entry) == pytest.approx(1.0)


def test_fires_per_day_every_minute():
    entry = make_entry(minute="*", hour="*", dow="*")
    assert fires_per_day(entry) == pytest.approx(60 * 24)


def test_fires_per_day_weekly_job():
    # Runs once, on Monday only
    entry = make_entry(minute="0", hour="9", dow="1")
    rate = fires_per_day(entry)
    assert 0 < rate < 1


# --- classify ---

def test_classify_frequent():
    entry = make_entry(minute="*", hour="*", dow="*")
    result = classify(entry)
    assert result.label == "frequent"


def test_classify_hourly():
    # Fires once per hour, every day
    entry = make_entry(minute="0", hour="*", dow="*")
    result = classify(entry)
    assert result.label == "hourly"


def test_classify_daily():
    entry = make_entry(minute="0", hour="3", dow="*")
    result = classify(entry)
    assert result.label == "daily"


def test_classify_weekly():
    entry = make_entry(minute="0", hour="9", dow="1")
    result = classify(entry)
    assert result.label == "weekly"


def test_classify_str_contains_label_and_command():
    entry = make_entry(minute="0", hour="3", dow="*", command="/usr/bin/backup")
    result = classify(entry)
    text = str(result)
    assert result.label in text
    assert "/usr/bin/backup" in text


# --- classify_all ---

def test_classify_all_returns_same_length():
    entries = [make_entry(), make_entry(minute="*", hour="*")]
    labels = classify_all(entries)
    assert len(labels) == 2


# --- frequency_summary ---

def test_frequency_summary_contains_buckets():
    entries = [
        make_entry(minute="0", hour="3", dow="*"),   # daily
        make_entry(minute="*", hour="*", dow="*"),   # frequent
        make_entry(minute="0", hour="9", dow="1"),   # weekly
    ]
    labels = classify_all(entries)
    summary = frequency_summary(labels)
    assert "daily" in summary
    assert "frequent" in summary
    assert "weekly" in summary


def test_frequency_summary_omits_empty_buckets():
    entries = [make_entry(minute="0", hour="3", dow="*")]  # daily only
    labels = classify_all(entries)
    summary = frequency_summary(labels)
    assert "frequent" not in summary
    assert "daily" in summary
