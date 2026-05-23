"""Tests for cronmap.retry — retry-pattern detection."""
import pytest

from cronmap.parser import CronEntry
from cronmap.retry import (
    RetryGroup,
    _base_command,
    _earliest_minute,
    _first_value,
    find_retry_groups,
    format_retry_report,
)


def make_entry(minute="0", hour="2", dom="*", month="*", dow="*", command="/usr/bin/job") -> CronEntry:
    return CronEntry(minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command)


# --- _first_value ---

def test_first_value_wildcard():
    assert _first_value("*", 0, 59) == 0


def test_first_value_specific():
    assert _first_value("15", 0, 59) == 15


def test_first_value_range():
    assert _first_value("10-20", 0, 59) == 10


def test_first_value_list():
    assert _first_value("5,10,15", 0, 59) == 5


def test_first_value_step():
    assert _first_value("*/5", 0, 59) == 0


def test_first_value_step_with_start():
    assert _first_value("10/5", 0, 59) == 10


# --- _earliest_minute ---

def test_earliest_minute_simple():
    entry = make_entry(minute="30", hour="3")
    assert _earliest_minute(entry) == 3 * 60 + 30


def test_earliest_minute_wildcard_hour():
    entry = make_entry(minute="0", hour="*")
    assert _earliest_minute(entry) == 0


# --- _base_command ---

def test_base_command_strips_args():
    assert _base_command("/usr/bin/backup --full") == "/usr/bin/backup"


def test_base_command_no_args():
    assert _base_command("/usr/bin/job") == "/usr/bin/job"


# --- find_retry_groups ---

def test_find_retry_groups_detects_pair():
    entries = [
        make_entry(minute="0", hour="6", command="/usr/bin/sync"),
        make_entry(minute="15", hour="6", command="/usr/bin/sync"),
    ]
    groups = find_retry_groups(entries)
    assert len(groups) == 1
    assert len(groups[0].entries) == 2


def test_find_retry_groups_respects_max_gap():
    entries = [
        make_entry(minute="0", hour="6", command="/usr/bin/sync"),
        make_entry(minute="45", hour="6", command="/usr/bin/sync"),
    ]
    groups = find_retry_groups(entries, max_gap_minutes=30)
    assert groups == []


def test_find_retry_groups_ignores_single_entry():
    entries = [make_entry(minute="0", hour="6", command="/usr/bin/solo")]
    assert find_retry_groups(entries) == []


def test_find_retry_groups_different_commands_not_grouped():
    entries = [
        make_entry(minute="0", hour="6", command="/usr/bin/alpha"),
        make_entry(minute="10", hour="6", command="/usr/bin/beta"),
    ]
    assert find_retry_groups(entries) == []


def test_find_retry_groups_three_entries():
    entries = [
        make_entry(minute="0", hour="8", command="/usr/bin/job"),
        make_entry(minute="10", hour="8", command="/usr/bin/job"),
        make_entry(minute="20", hour="8", command="/usr/bin/job"),
    ]
    groups = find_retry_groups(entries)
    assert len(groups) == 1
    assert len(groups[0].entries) == 3


def test_retry_group_intervals():
    entries = [
        make_entry(minute="0", hour="9", command="/usr/bin/task"),
        make_entry(minute="15", hour="9", command="/usr/bin/task"),
    ]
    group = find_retry_groups(entries)[0]
    assert group.intervals_minutes == [0, 15]


# --- format_retry_report ---

def test_format_retry_report_no_groups():
    assert format_retry_report([]) == "No retry patterns detected."


def test_format_retry_report_contains_command():
    entries = [
        make_entry(minute="0", hour="6", command="/usr/bin/sync"),
        make_entry(minute="10", hour="6", command="/usr/bin/sync"),
    ]
    groups = find_retry_groups(entries)
    report = format_retry_report(groups)
    assert "/usr/bin/sync" in report


def test_format_retry_report_color_contains_ansi():
    entries = [
        make_entry(minute="0", hour="6", command="/usr/bin/sync"),
        make_entry(minute="5", hour="6", command="/usr/bin/sync"),
    ]
    groups = find_retry_groups(entries)
    report = format_retry_report(groups, color=True)
    assert "\033[" in report
