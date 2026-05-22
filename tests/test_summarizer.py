"""Tests for cronmap.summarizer."""

import pytest

from cronmap.parser import CronEntry
from cronmap.summarizer import (
    EntrySummary,
    _dow_phrase,
    _field_phrase,
    render_summary_report,
    summarize_all,
    summarize_entry,
)


def make_entry(
    minute="0", hour="9", dom="*", month="*", dow="*", command="/usr/bin/job"
) -> CronEntry:
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command
    )


# --- _field_phrase ---

def test_field_phrase_wildcard():
    assert _field_phrase("*", "hour") == "every hour"


def test_field_phrase_specific_value():
    assert _field_phrase("5", "minute") == "minute 5"


def test_field_phrase_step():
    result = _field_phrase("*/15", "minute")
    assert "15" in result and "minute" in result


def test_field_phrase_range():
    result = _field_phrase("9-17", "hour")
    assert "9" in result and "17" in result


def test_field_phrase_list():
    result = _field_phrase("1,3,5", "day")
    assert "1" in result and "3" in result and "5" in result


# --- _dow_phrase ---

def test_dow_phrase_wildcard():
    assert _dow_phrase("*") == "every day"


def test_dow_phrase_single():
    assert "Monday" in _dow_phrase("1")


def test_dow_phrase_list():
    result = _dow_phrase("1,3,5")
    assert "Monday" in result and "Wednesday" in result and "Friday" in result


def test_dow_phrase_range():
    result = _dow_phrase("1-5")
    assert "Monday" in result and "Friday" in result


# --- summarize_entry ---

def test_summarize_entry_returns_entry_summary():
    entry = make_entry()
    result = summarize_entry(entry)
    assert isinstance(result, EntrySummary)
    assert result.entry is entry


def test_summarize_entry_headline_is_string():
    result = summarize_entry(make_entry())
    assert isinstance(result.headline, str) and len(result.headline) > 0


def test_summarize_entry_detail_contains_fields():
    entry = make_entry(minute="30", hour="6")
    result = summarize_entry(entry)
    assert "minute=30" in result.detail
    assert "hour=6" in result.detail


def test_summarize_entry_str_contains_command():
    entry = make_entry(command="/bin/backup")
    result = summarize_entry(entry)
    assert "/bin/backup" in str(result)


def test_summarize_entry_top_of_hour_phrase():
    entry = make_entry(minute="0", hour="14")
    result = summarize_entry(entry)
    assert "14:00" in result.headline


# --- summarize_all ---

def test_summarize_all_returns_one_per_entry():
    entries = [make_entry(), make_entry(command="/bin/other")]
    results = summarize_all(entries)
    assert len(results) == 2


# --- render_summary_report ---

def test_render_summary_report_empty():
    assert render_summary_report([]) == "No cron entries found."


def test_render_summary_report_contains_command():
    entries = [make_entry(command="/usr/bin/mytask")]
    report = render_summary_report(entries)
    assert "/usr/bin/mytask" in report


def test_render_summary_report_no_color_no_ansi():
    entries = [make_entry()]
    report = render_summary_report(entries, color=False)
    assert "\033[" not in report


def test_render_summary_report_color_contains_ansi():
    entries = [make_entry()]
    report = render_summary_report(entries, color=True)
    assert "\033[" in report


def test_render_summary_report_multiple_entries():
    entries = [make_entry(command="/bin/a"), make_entry(command="/bin/b")]
    report = render_summary_report(entries)
    assert "/bin/a" in report and "/bin/b" in report
