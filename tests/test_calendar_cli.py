"""Tests for cronmap.calendar_cli."""
import textwrap
from pathlib import Path

import pytest

from cronmap.calendar_cli import build_calendar_parser, main


CRONTAB = textwrap.dedent("""\
    0 9 * * 1-5 /usr/bin/backup
    30 12 * * * /usr/bin/lunch
""")


def test_build_calendar_parser_defaults():
    p = build_calendar_parser()
    args = p.parse_args(["crontab"])
    assert args.year is None
    assert args.month is None
    assert args.day is None
    assert args.color is False


def test_build_calendar_parser_all_flags():
    p = build_calendar_parser()
    args = p.parse_args(["crontab", "--year", "2025", "--month", "6", "--day", "15", "--color"])
    assert args.year == 2025
    assert args.month == 6
    assert args.day == 15
    assert args.color is True


def test_main_missing_file_returns_error(tmp_path):
    rc = main([str(tmp_path / "missing.crontab")])
    assert rc == 1


def test_main_invalid_month_returns_error(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB)
    rc = main([str(f), "--month", "13"])
    assert rc == 1


def test_main_renders_calendar(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB)
    rc = main([str(f), "--year", "2024", "--month", "1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "January" in out


def test_main_with_detail_day(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB)
    rc = main([str(f), "--year", "2024", "--month", "1", "--day", "5"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "2024-01-05" in out


def test_main_color_flag_accepted(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB)
    rc = main([str(f), "--year", "2024", "--month", "3", "--color"])
    assert rc == 0
