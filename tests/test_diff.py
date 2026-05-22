"""Tests for cronmap.diff module."""

import pytest
from cronmap.parser import CronEntry
from cronmap.diff import CronDiff, diff_crontabs, format_diff, _entry_key


def make_entry(minute="0", hour="9", dom="*", month="*", dow="*", command="/bin/task"):
    return CronEntry(
        minute=minute, hour=hour, dom=dom,
        month=month, dow=dow, command=command,
    )


# --- _entry_key ---

def test_entry_key_includes_schedule_and_command():
    e = make_entry(minute="5", hour="3", command="/usr/bin/foo")
    key = _entry_key(e)
    assert "5 3" in key[0]
    assert key[1] == "/usr/bin/foo"


def test_entry_key_same_for_identical_entries():
    e1 = make_entry()
    e2 = make_entry()
    assert _entry_key(e1) == _entry_key(e2)


# --- diff_crontabs ---

def test_diff_empty_lists():
    result = diff_crontabs([], [])
    assert result.added == []
    assert result.removed == []
    assert result.unchanged == []
    assert not result.has_changes


def test_diff_detects_added_entry():
    old = [make_entry(command="/bin/old")]
    new = [make_entry(command="/bin/old"), make_entry(command="/bin/new")]
    result = diff_crontabs(old, new)
    assert len(result.added) == 1
    assert result.added[0].command == "/bin/new"
    assert not result.removed


def test_diff_detects_removed_entry():
    old = [make_entry(command="/bin/a"), make_entry(command="/bin/b")]
    new = [make_entry(command="/bin/a")]
    result = diff_crontabs(old, new)
    assert len(result.removed) == 1
    assert result.removed[0].command == "/bin/b"


def test_diff_unchanged_entries():
    entries = [make_entry(command="/bin/same")]
    result = diff_crontabs(entries, entries)
    assert len(result.unchanged) == 1
    assert not result.has_changes


def test_diff_has_changes_when_added():
    result = diff_crontabs([], [make_entry()])
    assert result.has_changes


def test_diff_summary_all_types():
    old = [make_entry(command="/bin/gone"), make_entry(command="/bin/stay")]
    new = [make_entry(command="/bin/stay"), make_entry(command="/bin/fresh")]
    result = diff_crontabs(old, new)
    summary = result.summary()
    assert "+1 added" in summary
    assert "-1 removed" in summary
    assert "1 unchanged" in summary


def test_diff_summary_no_changes():
    result = CronDiff()
    assert result.summary() == "no changes"


# --- format_diff ---

def test_format_diff_contains_header():
    result = diff_crontabs([], [])
    output = format_diff(result)
    assert output.startswith("# ")


def test_format_diff_added_line_starts_with_plus():
    result = diff_crontabs([], [make_entry(command="/bin/new")])
    output = format_diff(result)
    assert any(line.startswith("+") for line in output.splitlines())


def test_format_diff_removed_line_starts_with_minus():
    result = diff_crontabs([make_entry(command="/bin/old")], [])
    output = format_diff(result)
    assert any(line.startswith("-") for line in output.splitlines())


def test_format_diff_color_includes_ansi():
    result = diff_crontabs([], [make_entry()])
    output = format_diff(result, color=True)
    assert "\033[" in output


def test_format_diff_no_color_no_ansi():
    result = diff_crontabs([], [make_entry()])
    output = format_diff(result, color=False)
    assert "\033[" not in output
