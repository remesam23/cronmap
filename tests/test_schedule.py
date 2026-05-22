"""Tests for the weekly schedule builder."""

import pytest
from cronmap.parser import parse_cron_entry, parse_crontab
from cronmap.schedule import build_weekly_schedule, schedule_summary, WeeklySchedule


def test_schedule_has_all_days():
    entries = parse_crontab("0 9 * * 1")
    schedule = build_weekly_schedule(entries)
    assert set(schedule.keys()) == set(range(7))


def test_event_placed_on_correct_day():
    entries = parse_crontab("0 9 * * 3 # Midweek")
    schedule = build_weekly_schedule(entries)
    assert len(schedule[3]) == 1
    assert schedule[3][0] == (9, 0, "Midweek")
    for day in [0, 1, 2, 4, 5, 6]:
        assert schedule[day] == []


def test_multiple_entries_same_day():
    text = "0 8 * * 1 # Morning\n0 17 * * 1 # Evening"
    entries = parse_crontab(text)
    schedule = build_weekly_schedule(entries)
    monday = schedule[1]
    assert len(monday) == 2
    assert monday[0][0] < monday[1][0]  # sorted by hour


def test_events_sorted_within_day():
    text = "30 10 * * 2\n0 10 * * 2\n0 8 * * 2"
    entries = parse_crontab(text)
    schedule = build_weekly_schedule(entries)
    times = [(h, m) for h, m, _ in schedule[2]]
    assert times == sorted(times)


def test_schedule_summary_counts():
    text = "0 9 * * 1 # A\n0 10 * * 1 # B\n0 9 * * 3 # C"
    entries = parse_crontab(text)
    schedule = build_weekly_schedule(entries)
    summary = schedule_summary(schedule)
    assert summary["Monday"] == 2
    assert summary["Wednesday"] == 1
    assert summary["Friday"] == 0


def test_wildcard_dow_populates_all_days():
    entries = parse_crontab("0 12 * * *")
    schedule = build_weekly_schedule(entries)
    for day in range(7):
        assert len(schedule[day]) == 1
        assert schedule[day][0][:2] == (12, 0)
