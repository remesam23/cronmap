"""Tests for the crontab parser module."""

import pytest
from cronmap.parser import parse_cron_entry, parse_crontab, CronEntry


def test_parse_simple_entry():
    entry = parse_cron_entry("0 9 * * 1")
    assert 0 in entry.minutes
    assert 9 in entry.hours
    assert 1 in entry.days_of_week
    assert 0 not in entry.days_of_week


def test_parse_wildcard_minutes():
    entry = parse_cron_entry("* 12 * * *")
    assert entry.minutes == set(range(0, 60))
    assert entry.days_of_week == set(range(0, 7))


def test_parse_step_field():
    entry = parse_cron_entry("*/15 * * * *")
    assert entry.minutes == {0, 15, 30, 45}


def test_parse_range_field():
    entry = parse_cron_entry("0 9-17 * * 1-5")
    assert entry.hours == set(range(9, 18))
    assert entry.days_of_week == {1, 2, 3, 4, 5}


def test_parse_list_field():
    entry = parse_cron_entry("0 8,12,18 * * *")
    assert entry.hours == {8, 12, 18}


def test_parse_label_from_comment():
    entry = parse_cron_entry("30 6 * * 1 # Morning standup")
    assert entry.label == "Morning standup"
    assert 30 in entry.minutes
    assert 6 in entry.hours


def test_parse_invalid_entry():
    with pytest.raises(ValueError):
        parse_cron_entry("0 9 * *")


def test_parse_crontab_skips_blanks_and_comments():
    text = """
# This is a comment

0 9 * * 1 # Standup
*/30 * * * * # Heartbeat
"""
    entries = parse_crontab(text)
    assert len(entries) == 2
    assert entries[0].label == "Standup"
    assert entries[1].label == "Heartbeat"


def test_parse_crontab_empty():
    assert parse_crontab("") == []
    assert parse_crontab("# only comments\n\n") == []
