"""Tests for cronmap.watch_cli."""

import sys
from pathlib import Path
from unittest import mock

import pytest

from cronmap.watch_cli import build_watch_parser, main


# ---------------------------------------------------------------------------
# build_watch_parser
# ---------------------------------------------------------------------------

def test_build_watch_parser_default_interval():
    parser = build_watch_parser()
    args = parser.parse_args(["mycrontab"])
    assert args.interval == 2.0


def test_build_watch_parser_custom_interval():
    parser = build_watch_parser()
    args = parser.parse_args(["mycrontab", "--interval", "5"])
    assert args.interval == 5.0


def test_build_watch_parser_no_color_flag():
    parser = build_watch_parser()
    args = parser.parse_args(["mycrontab", "--no-color"])
    assert args.no_color is True


def test_build_watch_parser_color_on_by_default():
    parser = build_watch_parser()
    args = parser.parse_args(["mycrontab"])
    assert args.no_color is False


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def test_main_missing_file_returns_error(tmp_path, capsys):
    rc = main([str(tmp_path / "nonexistent")])
    assert rc == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_main_calls_watch_with_correct_interval(tmp_path):
    f = tmp_path / "crontab"
    f.write_text("0 9 * * 1 /usr/bin/backup\n")

    with mock.patch("cronmap.watch_cli.watch") as mock_watch:
        rc = main([str(f), "--interval", "3.5"])

    assert rc == 0
    _, kwargs = mock_watch.call_args
    assert kwargs["interval"] == 3.5


def test_main_passes_no_color_to_callback(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text("0 9 * * 1 /usr/bin/backup\n")

    with mock.patch("cronmap.watch_cli.watch"):
        rc = main([str(f), "--no-color"])

    assert rc == 0


def test_main_keyboard_interrupt_returns_zero(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text("0 9 * * 1 /usr/bin/backup\n")

    with mock.patch("cronmap.watch_cli.watch", side_effect=KeyboardInterrupt):
        rc = main([str(f)])

    assert rc == 0
    assert "Stopped" in capsys.readouterr().out
