"""Tests for cronmap.annotator."""

import pytest
from cronmap.parser import CronEntry
from cronmap.annotator import (
    annotate_entry,
    annotate_entries,
    _describe_field,
    _describe_dow,
    _infer_tags,
)


def make_entry(minute="0", hour="*", dom="*", month="*", dow="*", cmd="/bin/task", line=1):
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=cmd, line_number=line,
    )


def test_describe_field_wildcard():
    assert _describe_field("*", "minute") == "every minute"


def test_describe_field_specific_value():
    assert _describe_field("5", "hour") == "at hour 5"


def test_describe_field_list():
    assert _describe_field("1,2,3", "minute") == "at minutes 1,2,3"


def test_describe_field_range():
    assert _describe_field("9-17", "hour") == "from hour 9 to 17"


def test_describe_field_step_wildcard():
    assert _describe_field("*/5", "minute") == "every 5 minutes"


def test_describe_field_step_with_base():
    assert _describe_field("10/15", "minute") == "every 15 minutes starting at 10"


def test_describe_dow_wildcard():
    assert _describe_dow("*") == "every day"


def test_describe_dow_single():
    assert _describe_dow("1") == "on Monday"


def test_describe_dow_range():
    assert _describe_dow("1-5") == "from Monday to Friday"


def test_describe_dow_list():
    result = _describe_dow("1,3")
    assert "Monday" in result and "Wednesday" in result


def test_infer_tags_frequent():
    entry = make_entry(minute="*/5")
    assert "frequent" in _infer_tags(entry)


def test_infer_tags_daily_midnight():
    entry = make_entry(minute="0", hour="0")
    assert "daily-midnight" in _infer_tags(entry)


def test_infer_tags_weekdays_only():
    entry = make_entry(dow="1-5")
    assert "weekdays-only" in _infer_tags(entry)


def test_infer_tags_monthly():
    entry = make_entry(dom="1", dow="*")
    assert "monthly" in _infer_tags(entry)


def test_annotate_entry_returns_annotated():
    entry = make_entry(minute="0", hour="6", cmd="/usr/bin/backup")
    ann = annotate_entry(entry)
    assert ann.entry is entry
    assert "hour 6" in ann.description
    assert isinstance(ann.tags, list)


def test_annotate_entries_length():
    entries = [make_entry(cmd=f"/bin/job{i}") for i in range(4)]
    result = annotate_entries(entries)
    assert len(result) == 4
