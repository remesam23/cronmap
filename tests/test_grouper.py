"""Tests for cronmap.grouper."""

import pytest

from cronmap.parser import CronEntry
from cronmap.grouper import (
    DAY_NAMES,
    group_by_day,
    group_by_hour,
    group_by_command,
    group_summary,
)


def make_entry(minute="0", hour="9", dom="*", month="*", dow="*", command="/bin/task"):
    return CronEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        command=command,
    )


# --- group_by_day ---

def test_group_by_day_returns_all_seven_days():
    groups = group_by_day([])
    assert set(groups.keys()) == set(DAY_NAMES)


def test_group_by_day_wildcard_appears_in_every_day():
    entry = make_entry(dow="*")
    groups = group_by_day([entry])
    for day in DAY_NAMES:
        assert entry in groups[day]


def test_group_by_day_specific_dow():
    # dow=1 -> Monday
    entry = make_entry(dow="1")
    groups = group_by_day([entry])
    assert entry in groups["Monday"]
    assert entry not in groups["Tuesday"]


def test_group_by_day_list_dow():
    entry = make_entry(dow="1,3")  # Monday and Wednesday
    groups = group_by_day([entry])
    assert entry in groups["Monday"]
    assert entry in groups["Wednesday"]
    assert entry not in groups["Friday"]


def test_group_by_day_range_dow():
    entry = make_entry(dow="1-3")  # Mon-Wed
    groups = group_by_day([entry])
    assert entry in groups["Monday"]
    assert entry in groups["Tuesday"]
    assert entry in groups["Wednesday"]
    assert entry not in groups["Thursday"]


# --- group_by_hour ---

def test_group_by_hour_returns_24_buckets():
    groups = group_by_hour([])
    assert len(groups) == 24
    assert set(groups.keys()) == set(range(24))


def test_group_by_hour_wildcard_in_all_hours():
    entry = make_entry(hour="*")
    groups = group_by_hour([entry])
    for h in range(24):
        assert entry in groups[h]


def test_group_by_hour_specific_hour():
    entry = make_entry(hour="14")
    groups = group_by_hour([entry])
    assert entry in groups[14]
    assert entry not in groups[13]


def test_group_by_hour_step():
    entry = make_entry(hour="*/6")
    groups = group_by_hour([entry])
    for h in (0, 6, 12, 18):
        assert entry in groups[h]
    assert entry not in groups[1]


# --- group_by_command ---

def test_group_by_command_clusters_same_command():
    e1 = make_entry(hour="1", command="/bin/backup")
    e2 = make_entry(hour="2", command="/bin/backup")
    e3 = make_entry(hour="3", command="/bin/sync")
    groups = group_by_command([e1, e2, e3])
    assert len(groups["/bin/backup"]) == 2
    assert len(groups["/bin/sync"]) == 1


def test_group_by_command_empty():
    assert group_by_command([]) == {}


# --- group_summary ---

def test_group_summary_is_string():
    entries = [make_entry(hour=str(h), dow=str(h % 7)) for h in range(5)]
    result = group_summary(entries)
    assert isinstance(result, str)


def test_group_summary_contains_total():
    entries = [make_entry() for _ in range(3)]
    result = group_summary(entries)
    assert "3" in result
