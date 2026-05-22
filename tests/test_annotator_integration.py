"""Integration tests: annotator + annotation_report pipeline."""

from cronmap.parser import parse_crontab
from cronmap.annotator import annotate_entries
from cronmap.annotation_report import render_annotation_report


SAMPLE_CRONTAB = """
0 0 * * *    /usr/bin/daily-backup
*/5 * * * *  /usr/bin/health-check
0 9 * * 1-5  /usr/bin/standup-reminder
0 1 1 * *    /usr/bin/monthly-report
"""


def test_pipeline_produces_string():
    entries = parse_crontab(SAMPLE_CRONTAB)
    annotations = annotate_entries(entries)
    report = render_annotation_report(annotations, use_color=False)
    assert isinstance(report, str)
    assert len(report) > 0


def test_pipeline_all_commands_in_report():
    entries = parse_crontab(SAMPLE_CRONTAB)
    annotations = annotate_entries(entries)
    report = render_annotation_report(annotations, use_color=False)
    assert "/usr/bin/daily-backup" in report
    assert "/usr/bin/health-check" in report
    assert "/usr/bin/standup-reminder" in report
    assert "/usr/bin/monthly-report" in report


def test_pipeline_tags_for_frequent_entry():
    entries = parse_crontab(SAMPLE_CRONTAB)
    annotations = annotate_entries(entries)
    health = next(a for a in annotations if "health-check" in a.entry.command)
    assert "frequent" in health.tags


def test_pipeline_tags_for_midnight_entry():
    entries = parse_crontab(SAMPLE_CRONTAB)
    annotations = annotate_entries(entries)
    backup = next(a for a in annotations if "daily-backup" in a.entry.command)
    assert "daily-midnight" in backup.tags


def test_pipeline_weekdays_tag():
    entries = parse_crontab(SAMPLE_CRONTAB)
    annotations = annotate_entries(entries)
    standup = next(a for a in annotations if "standup" in a.entry.command)
    assert "weekdays-only" in standup.tags


def test_pipeline_monthly_tag():
    entries = parse_crontab(SAMPLE_CRONTAB)
    annotations = annotate_entries(entries)
    monthly = next(a for a in annotations if "monthly-report" in a.entry.command)
    assert "monthly" in monthly.tags


def test_pipeline_annotation_count_matches_entries():
    entries = parse_crontab(SAMPLE_CRONTAB)
    annotations = annotate_entries(entries)
    assert len(annotations) == len(entries)
