"""Tests for cronmap.filter module."""

import pytest

from cronmap.parser import parse_cron_entry
from cronmap.filter import (
    filter_by_day,
    filter_by_hour_range,
    filter_by_command,
    filter_entries,
    deduplicate,
)


@pytest.fixture()
def sample_entries():
    return [
        parse_cron_entry("0 8 * * 1 /usr/bin/backup"),   # Monday 08:00
        parse_cron_entry("30 12 * * 3 /usr/bin/report"),  # Wednesday 12:30
        parse_cron_entry("0 22 * * 5 /usr/bin/cleanup"),  # Friday 22:00
        parse_cron_entry("0 8 * * 1 /usr/bin/sync"),      # Monday 08:00 different cmd
    ]


def test_filter_by_day_monday(sample_entries):
    result = filter_by_day(sample_entries, 1)
    assert len(result) == 2
    assert all(1 in e.days_of_week for e in result)


def test_filter_by_day_no_match(sample_entries):
    result = filter_by_day(sample_entries, 0)  # Sunday
    assert result == []


def test_filter_by_hour_range_includes_boundary(sample_entries):
    result = filter_by_hour_range(sample_entries, 8, 12)
    commands = [e.command for e in result]
    assert "/usr/bin/backup" in commands
    assert "/usr/bin/report" in commands
    assert "/usr/bin/cleanup" not in commands


def test_filter_by_hour_range_no_match(sample_entries):
    result = filter_by_hour_range(sample_entries, 0, 1)
    assert result == []


def test_filter_by_command_case_insensitive(sample_entries):
    result = filter_by_command(sample_entries, "BACKUP")
    assert len(result) == 1
    assert result[0].command == "/usr/bin/backup"


def test_filter_by_command_partial_match(sample_entries):
    result = filter_by_command(sample_entries, "/usr/bin")
    assert len(result) == 4


def test_filter_entries_combined(sample_entries):
    result = filter_entries(
        sample_entries,
        lambda e: 1 in e.days_of_week,
        lambda e: "/usr/bin/backup" in e.command,
    )
    assert len(result) == 1
    assert result[0].command == "/usr/bin/backup"


def test_filter_entries_no_predicates(sample_entries):
    result = filter_entries(sample_entries)
    assert result == sample_entries


def test_deduplicate_removes_exact_duplicates():
    entries = [
        parse_cron_entry("0 8 * * 1 /usr/bin/backup"),
        parse_cron_entry("0 8 * * 1 /usr/bin/backup"),
        parse_cron_entry("0 9 * * 1 /usr/bin/backup"),
    ]
    result = deduplicate(entries)
    assert len(result) == 2


def test_deduplicate_preserves_order(sample_entries):
    result = deduplicate(sample_entries)
    assert [e.command for e in result] == [
        "/usr/bin/backup",
        "/usr/bin/report",
        "/usr/bin/cleanup",
        "/usr/bin/sync",
    ]
