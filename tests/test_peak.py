"""Unit tests for cronmap.peak."""
from __future__ import annotations

import pytest

from cronmap.parser import CronEntry
from cronmap.peak import (
    _expand_hours,
    build_hour_counts,
    find_peak_hours,
    format_peak_report,
    PeakResult,
)


def make_entry(minute="0", hour="0", dom="*", month="*", dow="*", command="cmd"):
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command
    )


# --- _expand_hours ---

def test_expand_hours_wildcard():
    assert _expand_hours("*") == list(range(24))


def test_expand_hours_specific():
    assert _expand_hours("9") == [9]


def test_expand_hours_range():
    assert _expand_hours("8-10") == [8, 9, 10]


def test_expand_hours_list():
    assert _expand_hours("6,12,18") == [6, 12, 18]


def test_expand_hours_step():
    assert _expand_hours("*/6") == [0, 6, 12, 18]


# --- build_hour_counts ---

def test_hour_counts_all_zeros_for_empty():
    counts = build_hour_counts([])
    assert all(v == 0 for v in counts.values())
    assert len(counts) == 24


def test_hour_counts_single_entry():
    counts = build_hour_counts([make_entry(hour="3")])
    assert counts[3] == 1
    assert counts[4] == 0


def test_hour_counts_wildcard_increments_all():
    counts = build_hour_counts([make_entry(hour="*")])
    assert all(v == 1 for v in counts.values())


def test_hour_counts_multiple_entries_same_hour():
    entries = [make_entry(hour="9"), make_entry(hour="9"), make_entry(hour="10")]
    counts = build_hour_counts(entries)
    assert counts[9] == 2
    assert counts[10] == 1


# --- PeakResult ---

def test_peak_result_identifies_busiest_hour():
    counts = {h: 0 for h in range(24)}
    counts[14] = 5
    counts[9] = 3
    result = PeakResult(hour_counts=counts)
    assert result.peak_hours == [14]
    assert result.peak_count == 5


def test_peak_result_ties_included():
    counts = {h: 1 for h in range(24)}
    counts[6] = 4
    counts[18] = 4
    result = PeakResult(hour_counts=counts)
    assert 6 in result.peak_hours
    assert 18 in result.peak_hours


# --- find_peak_hours ---

def test_find_peak_hours_returns_peak_result():
    entries = [make_entry(hour="7"), make_entry(hour="7"), make_entry(hour="8")]
    result = find_peak_hours(entries)
    assert isinstance(result, PeakResult)
    assert result.peak_hours == [7]
    assert result.peak_count == 2


# --- format_peak_report ---

def test_format_peak_report_contains_all_hours():
    result = find_peak_hours([make_entry(hour="12")])
    report = format_peak_report(result)
    for h in range(24):
        assert f"{h:02d}:00" in report


def test_format_peak_report_marks_peak():
    result = find_peak_hours([make_entry(hour="12"), make_entry(hour="12")])
    report = format_peak_report(result)
    assert "<-- peak" in report


def test_format_peak_report_no_color_has_no_ansi():
    result = find_peak_hours([make_entry(hour="6")])
    report = format_peak_report(result, color=False)
    assert "\033[" not in report


def test_format_peak_report_color_contains_ansi():
    result = find_peak_hours([make_entry(hour="6")])
    report = format_peak_report(result, color=True)
    assert "\033[" in report
