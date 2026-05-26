"""Unit tests for cronmap.churn."""
import pytest
from cronmap.parser import CronEntry
from cronmap.churn import (
    _count_field,
    fires_per_week,
    ChurnResult,
    compute_churn,
    format_churn_report,
)


def make_entry(minute="0", hour="0", dom="*", month="*", dow="*", command="cmd"):
    return CronEntry(minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command)


# --- _count_field ---

def test_count_field_wildcard_minutes():
    assert _count_field("*", 0, 59) == 60


def test_count_field_specific_value():
    assert _count_field("5", 0, 59) == 1


def test_count_field_range():
    assert _count_field("1-5", 0, 59) == 5


def test_count_field_list():
    assert _count_field("1,2,3", 0, 59) == 3


def test_count_field_step():
    assert _count_field("*/15", 0, 59) == 4


def test_count_field_step_with_start():
    assert _count_field("0/30", 0, 59) == 2


# --- fires_per_week ---

def test_fires_per_week_once_daily():
    e = make_entry(minute="0", hour="6", dow="*")
    assert fires_per_week(e) == 7


def test_fires_per_week_every_minute():
    e = make_entry(minute="*", hour="*", dow="*")
    assert fires_per_week(e) == 60 * 24 * 7


def test_fires_per_week_weekdays_only():
    e = make_entry(minute="0", hour="9", dow="1-5")
    assert fires_per_week(e) == 1 * 1 * 5


def test_fires_per_week_every_quarter_hour():
    e = make_entry(minute="*/15", hour="*", dow="*")
    assert fires_per_week(e) == 4 * 24 * 7


# --- ChurnResult ---

def test_churn_result_label_low():
    e = make_entry(minute="0", hour="0", dow="0")
    r = ChurnResult(e, 1)
    assert r.label == "low"


def test_churn_result_label_medium():
    r = ChurnResult(make_entry(), 500)
    assert r.label == "medium"


def test_churn_result_label_high():
    r = ChurnResult(make_entry(), 5_000)
    assert r.label == "high"


def test_churn_result_label_extreme():
    r = ChurnResult(make_entry(), 50_000)
    assert r.label == "extreme"


def test_churn_result_repr_contains_command():
    e = make_entry(command="/usr/bin/backup")
    r = ChurnResult(e, 7)
    assert "/usr/bin/backup" in repr(r)


# --- compute_churn ---

def test_compute_churn_sorted_descending():
    entries = [
        make_entry(minute="0", hour="0", dow="0", command="rare"),
        make_entry(minute="*", hour="*", dow="*", command="frequent"),
    ]
    results = compute_churn(entries)
    assert results[0].entry.command == "frequent"
    assert results[1].entry.command == "rare"


def test_compute_churn_empty():
    assert compute_churn([]) == []


# --- format_churn_report ---

def test_format_churn_report_no_entries():
    assert format_churn_report([]) == "No entries."


def test_format_churn_report_contains_command():
    e = make_entry(command="/bin/check", minute="0", hour="*", dow="*")
    results = compute_churn([e])
    report = format_churn_report(results)
    assert "/bin/check" in report


def test_format_churn_report_contains_fires_count():
    e = make_entry(minute="0", hour="0", dow="*", command="daily")
    results = compute_churn([e])
    report = format_churn_report(results)
    assert "7" in report


def test_format_churn_report_color_contains_ansi():
    e = make_entry(minute="*", hour="*", dow="*", command="noisy")
    results = compute_churn([e])
    report = format_churn_report(results, color=True)
    assert "\033[" in report
