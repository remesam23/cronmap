"""Tests for cronmap.sorter."""

import pytest
from cronmap.parser import parse_cron_entry
from cronmap.sorter import (
    sort_entries_by_time,
    sort_entries_by_day,
    sort_entries_by_command,
    sort_entries,
    sort_schedule,
)


@pytest.fixture
def sample_entries():
    return [
        parse_cron_entry("45 14 * * 1 /usr/bin/backup"),
        parse_cron_entry("0 2 * * 3 /usr/bin/cleanup"),
        parse_cron_entry("30 6 * * 0 /usr/bin/report"),
        parse_cron_entry("15 2 * * 5 /usr/bin/alpha"),
    ]


def test_sort_by_time_orders_by_hour_then_minute(sample_entries):
    result = sort_entries_by_time(sample_entries)
    hours = [min(e.hours) for e in result]
    assert hours == sorted(hours)


def test_sort_by_time_same_hour_orders_by_minute():
    a = parse_cron_entry("45 2 * * 1 /cmd/a")
    b = parse_cron_entry("15 2 * * 1 /cmd/b")
    result = sort_entries_by_time([a, b])
    assert min(result[0].minutes) < min(result[1].minutes)


def test_sort_by_day_orders_by_first_dow(sample_entries):
    result = sort_entries_by_day(sample_entries)
    days = [min(e.days_of_week) for e in result]
    assert days == sorted(days)


def test_sort_by_command_is_case_insensitive():
    a = parse_cron_entry("0 1 * * 1 /z_cmd")
    b = parse_cron_entry("0 1 * * 1 /A_cmd")
    c = parse_cron_entry("0 1 * * 1 /m_cmd")
    result = sort_entries_by_command([a, b, c])
    cmds = [e.command.lower() for e in result]
    assert cmds == sorted(cmds)


def test_sort_entries_time_strategy(sample_entries):
    result = sort_entries(sample_entries, strategy="time")
    hours = [min(e.hours) for e in result]
    assert hours == sorted(hours)


def test_sort_entries_day_strategy(sample_entries):
    result = sort_entries(sample_entries, strategy="day")
    days = [min(e.days_of_week) for e in result]
    assert days == sorted(days)


def test_sort_entries_command_strategy(sample_entries):
    result = sort_entries(sample_entries, strategy="command")
    cmds = [e.command.lower() for e in result]
    assert cmds == sorted(cmds)


def test_sort_entries_unknown_strategy_raises(sample_entries):
    with pytest.raises(ValueError, match="Unknown sort strategy"):
        sort_entries(sample_entries, strategy="nonexistent")


def test_sort_schedule_returns_all_days(sample_entries):
    schedule = {
        "Monday": [sample_entries[0], sample_entries[1]],
        "Wednesday": [sample_entries[2]],
        "Friday": [],
    }
    result = sort_schedule(schedule, strategy="time")
    assert set(result.keys()) == {"Monday", "Wednesday", "Friday"}


def test_sort_schedule_sorts_each_day_independently():
    a = parse_cron_entry("45 10 * * 1 /cmd/late")
    b = parse_cron_entry("0 8 * * 1 /cmd/early")
    schedule = {"Monday": [a, b]}
    result = sort_schedule(schedule, strategy="time")
    assert result["Monday"][0].command == "/cmd/early"
    assert result["Monday"][1].command == "/cmd/late"


def test_sort_schedule_invalid_strategy_raises():
    with pytest.raises(ValueError):
        sort_schedule({"Monday": []}, strategy="bogus")
