"""Tests for cronmap.watcher and cronmap.watch_report."""

import time
from pathlib import Path

import pytest

from cronmap.watcher import watch, _file_hash
from cronmap.watch_report import format_watch_diff, print_watch_diff
from cronmap.diff import diff_crontabs
from cronmap.parser import parse_crontab


CRONTAB_A = "0 9 * * 1 /usr/bin/backup\n"
CRONTAB_B = "0 9 * * 1 /usr/bin/backup\n0 12 * * * /usr/bin/report\n"


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------

def test_file_hash_changes_when_content_changes(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_A)
    h1 = _file_hash(f)
    f.write_text(CRONTAB_B)
    h2 = _file_hash(f)
    assert h1 != h2


def test_file_hash_stable_for_same_content(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_A)
    assert _file_hash(f) == _file_hash(f)


# ---------------------------------------------------------------------------
# watch()
# ---------------------------------------------------------------------------

def test_watch_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        watch(tmp_path / "missing", callback=lambda d: None, max_iterations=0)


def test_watch_calls_callback_on_change(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_A)

    received = []

    def _write_then_stop(iteration_counter):
        """Mutate file on first poll tick."""
        if iteration_counter[0] == 0:
            f.write_text(CRONTAB_B)
        iteration_counter[0] += 1

    counter = [0]
    original_sleep = time.sleep

    import unittest.mock as mock

    def fake_sleep(_):
        _write_then_stop(counter)

    with mock.patch("cronmap.watcher.time.sleep", side_effect=fake_sleep):
        watch(f, callback=received.append, interval=0.0, max_iterations=2)

    assert len(received) == 1
    assert received[0].has_changes


def test_watch_no_callback_when_unchanged(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_A)
    received = []

    import unittest.mock as mock

    with mock.patch("cronmap.watcher.time.sleep"):
        watch(f, callback=received.append, interval=0.0, max_iterations=3)

    assert received == []


# ---------------------------------------------------------------------------
# format_watch_diff
# ---------------------------------------------------------------------------

def test_format_watch_diff_contains_added_command():
    entries_a = parse_crontab(CRONTAB_A)
    entries_b = parse_crontab(CRONTAB_B)
    diff = diff_crontabs(entries_a, entries_b)
    report = format_watch_diff(diff, color=False)
    assert "/usr/bin/report" in report


def test_format_watch_diff_marks_added_with_plus():
    entries_a = parse_crontab(CRONTAB_A)
    entries_b = parse_crontab(CRONTAB_B)
    diff = diff_crontabs(entries_a, entries_b)
    report = format_watch_diff(diff, color=False)
    assert "+" in report


def test_format_watch_diff_marks_removed_with_minus():
    entries_a = parse_crontab(CRONTAB_B)
    entries_b = parse_crontab(CRONTAB_A)
    diff = diff_crontabs(entries_a, entries_b)
    report = format_watch_diff(diff, color=False)
    assert "-" in report


def test_format_watch_diff_with_color_contains_ansi():
    entries_a = parse_crontab(CRONTAB_A)
    entries_b = parse_crontab(CRONTAB_B)
    diff = diff_crontabs(entries_a, entries_b)
    report = format_watch_diff(diff, color=True)
    assert "\033[" in report


def test_format_watch_diff_no_color_no_ansi():
    entries_a = parse_crontab(CRONTAB_A)
    entries_b = parse_crontab(CRONTAB_B)
    diff = diff_crontabs(entries_a, entries_b)
    report = format_watch_diff(diff, color=False)
    assert "\033[" not in report
