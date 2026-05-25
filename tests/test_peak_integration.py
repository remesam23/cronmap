"""Integration tests: peak detection wired through parser → peak → report."""
from __future__ import annotations

import pytest

from cronmap.parser import parse_crontab
from cronmap.peak import find_peak_hours, format_peak_report

CRONTAB = """\
0 6 * * * /usr/bin/morning-sync
30 6 * * * /usr/bin/morning-report
0 6 * * * /usr/bin/morning-backup
0 12 * * * /usr/bin/noon-job
*/5 * * * * /usr/bin/heartbeat
"""


@pytest.fixture(scope="module")
def result():
    entries = parse_crontab(CRONTAB)
    return find_peak_hours(entries)


def test_integration_hour_counts_length(result):
    assert len(result.hour_counts) == 24


def test_integration_heartbeat_increments_all_hours(result):
    # */5 fires every hour, so every hour should have at least 1
    assert all(v >= 1 for v in result.hour_counts.values())


def test_integration_hour_6_has_most_entries(result):
    # 3 explicit entries at hour 6 + heartbeat → hour 6 count > hour 12 count
    assert result.hour_counts[6] > result.hour_counts[12]


def test_integration_peak_hours_includes_6(result):
    assert 6 in result.peak_hours


def test_integration_report_is_string(result):
    report = format_peak_report(result)
    assert isinstance(report, str)
    assert len(report) > 0


def test_integration_report_mentions_busiest_hour(result):
    report = format_peak_report(result)
    assert "06:xx" in report


def test_integration_report_contains_bar_characters(result):
    report = format_peak_report(result)
    assert "#" in report
