"""Tests for cronmap.burst."""
from __future__ import annotations

import pytest

from cronmap.burst import (
    BurstResult,
    _count_field,
    detect_bursts,
    fires_per_hour,
    format_burst_report,
)
from cronmap.parser import CronEntry


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="cmd") -> CronEntry:
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


def test_count_field_specific():
    assert _count_field("5", 0, 59) == 1


def test_count_field_range():
    assert _count_field("0-9", 0, 59) == 10


def test_count_field_list():
    assert _count_field("0,15,30,45", 0, 59) == 4


def test_count_field_step():
    assert _count_field("*/10", 0, 59) == 6


# --- fires_per_hour ---

def test_fires_per_hour_wildcard_minute():
    entry = make_entry(minute="*")
    assert fires_per_hour(entry) == 60


def test_fires_per_hour_specific_minute():
    entry = make_entry(minute="30")
    assert fires_per_hour(entry) == 1


def test_fires_per_hour_step():
    entry = make_entry(minute="*/5")
    assert fires_per_hour(entry) == 12


# --- BurstResult ---

def test_burst_result_bool_true_when_at_threshold():
    r = BurstResult(entry=make_entry(), fires_per_hour=10, threshold=10)
    assert bool(r) is True


def test_burst_result_bool_false_below_threshold():
    r = BurstResult(entry=make_entry(), fires_per_hour=9, threshold=10)
    assert bool(r) is False


def test_burst_result_label_extreme():
    r = BurstResult(entry=make_entry(), fires_per_hour=60, threshold=1)
    assert r.label == "extreme"


def test_burst_result_label_high():
    r = BurstResult(entry=make_entry(), fires_per_hour=30, threshold=1)
    assert r.label == "high"


def test_burst_result_label_moderate():
    r = BurstResult(entry=make_entry(), fires_per_hour=15, threshold=1)
    assert r.label == "moderate"


def test_burst_result_label_low():
    r = BurstResult(entry=make_entry(), fires_per_hour=5, threshold=1)
    assert r.label == "low"


# --- detect_bursts ---

def test_detect_bursts_returns_one_result_per_entry():
    entries = [make_entry(minute="*"), make_entry(minute="0")]
    results = detect_bursts(entries, threshold=10)
    assert len(results) == 2


def test_detect_bursts_flags_wildcard_minute():
    entries = [make_entry(minute="*", command="noisy")]
    results = detect_bursts(entries, threshold=10)
    assert bool(results[0]) is True


def test_detect_bursts_does_not_flag_single_fire():
    entries = [make_entry(minute="0", command="quiet")]
    results = detect_bursts(entries, threshold=10)
    assert bool(results[0]) is False


# --- format_burst_report ---

def test_format_burst_report_no_bursts():
    entries = [make_entry(minute="0")]
    results = detect_bursts(entries, threshold=10)
    report = format_burst_report(results)
    assert "No burst" in report


def test_format_burst_report_contains_command():
    entries = [make_entry(minute="*", command="/usr/bin/noisy")]
    results = detect_bursts(entries, threshold=10)
    report = format_burst_report(results)
    assert "/usr/bin/noisy" in report


def test_format_burst_report_contains_fires_per_hour():
    entries = [make_entry(minute="*/5", command="frequent")]
    results = detect_bursts(entries, threshold=10)
    report = format_burst_report(results)
    assert "12x/hr" in report


def test_format_burst_report_color_no_crash():
    entries = [make_entry(minute="*", command="loud")]
    results = detect_bursts(entries, threshold=10)
    report = format_burst_report(results, color=True)
    assert "loud" in report
