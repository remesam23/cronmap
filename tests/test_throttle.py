"""Tests for cronmap.throttle."""
import pytest
from cronmap.parser import CronEntry
from cronmap.throttle import (
    ThrottleResult,
    check_throttle,
    find_throttled,
    fires_per_hour,
    format_throttle_report,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", command="cmd"):
    return CronEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        command=command,
    )


# ---------------------------------------------------------------------------
# fires_per_hour
# ---------------------------------------------------------------------------

def test_fires_per_hour_wildcard_minute():
    assert fires_per_hour(make_entry(minute="*")) == 60


def test_fires_per_hour_specific_minute():
    assert fires_per_hour(make_entry(minute="30")) == 1


def test_fires_per_hour_step_minute():
    # */5 → 0,5,10,...,55 → 12 values
    assert fires_per_hour(make_entry(minute="*/5")) == 12


def test_fires_per_hour_range_minute():
    # 0-9 → 10 values
    assert fires_per_hour(make_entry(minute="0-9")) == 10


def test_fires_per_hour_list_minute():
    assert fires_per_hour(make_entry(minute="0,15,30,45")) == 4


# ---------------------------------------------------------------------------
# check_throttle levels
# ---------------------------------------------------------------------------

def test_check_throttle_ok():
    r = check_throttle(make_entry(minute="0"))
    assert r.level == "ok"
    assert not r


def test_check_throttle_warn():
    # */4 → 15 fires/hour — above warn (12), below critical (30)
    r = check_throttle(make_entry(minute="*/4"))
    assert r.level == "warn"
    assert bool(r)


def test_check_throttle_critical():
    r = check_throttle(make_entry(minute="*"))
    assert r.level == "critical"
    assert bool(r)


def test_check_throttle_stores_entry_and_fph():
    entry = make_entry(minute="*/2", command="/usr/bin/poll")
    r = check_throttle(entry)
    assert r.entry is entry
    assert r.fires_per_hour == 30


# ---------------------------------------------------------------------------
# find_throttled
# ---------------------------------------------------------------------------

def test_find_throttled_empty_list():
    assert find_throttled([]) == []


def test_find_throttled_excludes_ok_entries():
    entries = [make_entry(minute="0"), make_entry(minute="30")]
    assert find_throttled(entries) == []


def test_find_throttled_includes_warn_and_critical():
    entries = [
        make_entry(minute="0", command="hourly"),
        make_entry(minute="*/5", command="every5"),
        make_entry(minute="*", command="every_minute"),
    ]
    results = find_throttled(entries)
    commands = {r.entry.command for r in results}
    assert "every5" in commands
    assert "every_minute" in commands
    assert "hourly" not in commands


# ---------------------------------------------------------------------------
# format_throttle_report
# ---------------------------------------------------------------------------

def test_format_throttle_report_no_issues():
    assert format_throttle_report([]) == "No throttle issues found."


def test_format_throttle_report_contains_level():
    r = ThrottleResult(entry=make_entry(command="/bin/poll"), fires_per_hour=60, level="critical")
    report = format_throttle_report([r])
    assert "CRITICAL" in report
    assert "/bin/poll" in report


def test_format_throttle_report_no_color_has_no_ansi():
    r = ThrottleResult(entry=make_entry(command="x"), fires_per_hour=15, level="warn")
    report = format_throttle_report([r], color=False)
    assert "\033[" not in report


def test_format_throttle_report_color_contains_ansi():
    r = ThrottleResult(entry=make_entry(command="x"), fires_per_hour=60, level="critical")
    report = format_throttle_report([r], color=True)
    assert "\033[" in report
