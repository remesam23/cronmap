"""Tests for cronmap.stale_cli."""
from __future__ import annotations

import json
import pathlib

import pytest

from cronmap.stale_cli import build_stale_parser, main


@pytest.fixture()
def crontab_file(tmp_path: pathlib.Path) -> pathlib.Path:
    content = "\n".join([
        "0 2 * * 0 /bin/weekly-report",
        "* * * * * /bin/heartbeat",
        "0 6 * * 1-5 /bin/workday-task",
    ])
    p = tmp_path / "crontab"
    p.write_text(content)
    return p


def test_build_stale_parser_defaults():
    p = build_stale_parser()
    args = p.parse_args(["somefile"])
    assert args.threshold == 7
    assert args.color is False
    assert args.exit_code is False


def test_build_stale_parser_all_flags():
    p = build_stale_parser()
    args = p.parse_args(["somefile", "--threshold", "3", "--color", "--exit-code"])
    assert args.threshold == 3
    assert args.color is True
    assert args.exit_code is True


def test_main_missing_file_returns_error():
    rc = main(["nonexistent_file_xyz.txt"])
    assert rc == 2


def test_main_no_stale_returns_zero(crontab_file):
    # heartbeat fires every minute — well above default threshold of 7
    # but weekly-report fires only once per week, so there WILL be stale entries
    # use a threshold of 0 so nothing qualifies
    rc = main([str(crontab_file), "--threshold", "0"])
    assert rc == 0


def test_main_stale_found_returns_zero_without_flag(crontab_file, capsys):
    rc = main([str(crontab_file), "--threshold", "7"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "weekly-report" in captured.out


def test_main_exit_code_flag_returns_one_when_stale(crontab_file):
    rc = main([str(crontab_file), "--threshold", "7", "--exit-code"])
    assert rc == 1


def test_main_color_flag_does_not_crash(crontab_file, capsys):
    rc = main([str(crontab_file), "--threshold", "7", "--color"])
    assert rc == 0
    out = capsys.readouterr().out
    assert len(out) > 0
