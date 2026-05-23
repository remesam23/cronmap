"""Tests for cronmap.cost."""

import pytest

from cronmap.parser import CronEntry
from cronmap.cost import (
    _count_field,
    fires_per_week,
    compute_cost,
    rank_by_cost,
    format_cost_report,
    CostResult,
)


def make_entry(minute="0", hour="0", dom="*", month="*", dow="*", command="cmd"):
    return CronEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        command=command,
        raw=f"{minute} {hour} {dom} {month} {dow} {command}",
        line_number=1,
    )


# --- _count_field ---

def test_count_field_wildcard_minutes():
    assert _count_field("*", 0, 59) == 60


def test_count_field_specific_value():
    assert _count_field("5", 0, 59) == 1


def test_count_field_range():
    assert _count_field("1-5", 0, 59) == 5


def test_count_field_list():
    assert _count_field("0,15,30,45", 0, 59) == 4


def test_count_field_step():
    assert _count_field("*/15", 0, 59) == 4


def test_count_field_step_from_base():
    assert _count_field("0/30", 0, 59) == 2


# --- fires_per_week ---

def test_fires_per_week_once_daily():
    entry = make_entry(minute="0", hour="3", dow="*")
    assert fires_per_week(entry) == 7


def test_fires_per_week_every_minute():
    entry = make_entry(minute="*", hour="*", dow="*")
    assert fires_per_week(entry) == 7 * 24 * 60


def test_fires_per_week_weekdays_only():
    entry = make_entry(minute="0", hour="9", dow="1-5")
    assert fires_per_week(entry) == 5


def test_fires_per_week_hourly_on_mondays():
    entry = make_entry(minute="0", hour="*", dow="1")
    assert fires_per_week(entry) == 24


# --- compute_cost ---

def test_compute_cost_returns_cost_result():
    entry = make_entry(minute="0", hour="0", dow="*")
    result = compute_cost(entry)
    assert isinstance(result, CostResult)


def test_compute_cost_score_bounded():
    entry = make_entry(minute="*", hour="*", dow="*")
    result = compute_cost(entry)
    assert result.cost_score == pytest.approx(1.0)


def test_compute_cost_low_frequency_low_score():
    entry = make_entry(minute="0", hour="2", dow="0")
    result = compute_cost(entry)
    assert result.cost_score < 0.01


def test_cost_result_label_high():
    entry = make_entry(minute="*", hour="*", dow="*")
    result = compute_cost(entry)
    assert result.label() == "high"


def test_cost_result_label_low():
    entry = make_entry(minute="0", hour="0", dow="0")
    result = compute_cost(entry)
    assert result.label() == "low"


# --- rank_by_cost ---

def test_rank_by_cost_descending_order():
    entries = [
        make_entry(minute="0", hour="0", dow="*", command="daily"),
        make_entry(minute="*", hour="*", dow="*", command="every_minute"),
        make_entry(minute="0", hour="0", dow="0", command="weekly"),
    ]
    ranked = rank_by_cost(entries)
    scores = [r.cost_score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_by_cost_ascending():
    entries = [
        make_entry(minute="*", hour="*", dow="*", command="every_minute"),
        make_entry(minute="0", hour="0", dow="0", command="weekly"),
    ]
    ranked = rank_by_cost(entries, descending=False)
    assert ranked[0].entry.command == "weekly"


# --- format_cost_report ---

def test_format_cost_report_contains_header():
    entries = [make_entry(command="backup.sh")]
    ranked = rank_by_cost(entries)
    report = format_cost_report(ranked)
    assert "Command" in report
    assert "Fires/week" in report


def test_format_cost_report_contains_command():
    entries = [make_entry(command="/usr/bin/backup")]
    ranked = rank_by_cost(entries)
    report = format_cost_report(ranked)
    assert "/usr/bin/backup" in report


def test_format_cost_report_no_ansi_without_color():
    entries = [make_entry(command="task")]
    ranked = rank_by_cost(entries)
    report = format_cost_report(ranked, color=False)
    assert "\033[" not in report
