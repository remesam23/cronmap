"""Integration tests: churn analysis pipeline."""
import textwrap

import pytest

from cronmap.parser import parse_crontab
from cronmap.churn import compute_churn, format_churn_report


CRONTAB = textwrap.dedent("""\
    * * * * * /bin/heartbeat
    */5 * * * * /bin/poll
    0 * * * * /bin/hourly
    0 6 * * * /usr/bin/backup
    0 2 * * 0 /usr/bin/weekly_report
""")


@pytest.fixture(scope="module")
def results():
    entries = parse_crontab(CRONTAB)
    return compute_churn(entries)


def test_integration_result_count(results):
    assert len(results) == 5


def test_integration_sorted_descending(results):
    fires = [r.fires_per_week for r in results]
    assert fires == sorted(fires, reverse=True)


def test_integration_heartbeat_is_first(results):
    assert results[0].entry.command == "/bin/heartbeat"


def test_integration_weekly_report_is_last(results):
    assert results[-1].entry.command == "/usr/bin/weekly_report"


def test_integration_heartbeat_fires(results):
    heartbeat = next(r for r in results if r.entry.command == "/bin/heartbeat")
    assert heartbeat.fires_per_week == 60 * 24 * 7


def test_integration_poll_fires(results):
    poll = next(r for r in results if r.entry.command == "/bin/poll")
    assert poll.fires_per_week == 12 * 24 * 7


def test_integration_labels_present(results):
    labels = {r.label for r in results}
    assert "extreme" in labels
    assert "low" in labels


def test_integration_report_contains_all_commands(results):
    report = format_churn_report(results)
    for r in results:
        assert r.entry.command in report
