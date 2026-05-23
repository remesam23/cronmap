"""Tests for cronmap.window_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cronmap.window_cli import build_window_parser, main


CRONTAB = textwrap.dedent("""\
    0 10 * * 1 /usr/bin/backup
    0 22 * * * /usr/bin/nightly
    */15 9-17 * * 1-5 /usr/bin/heartbeat
""")


@pytest.fixture()
def crontab_file(tmp_path: Path) -> Path:
    p = tmp_path / "crontab"
    p.write_text(CRONTAB)
    return p


# --- build_window_parser ---

def test_build_window_parser_defaults():
    parser = build_window_parser()
    args = parser.parse_args(["somefile"])
    assert args.dow == 1
    assert args.start == "09:00"
    assert args.end == "17:00"
    assert args.color is True


def test_build_window_parser_all_flags():
    parser = build_window_parser()
    args = parser.parse_args(["f", "--dow", "3", "--start", "08:00", "--end", "16:30", "--no-color"])
    assert args.dow == 3
    assert args.start == "08:00"
    assert args.end == "16:30"
    assert args.color is False


# --- main ---

def test_main_missing_file_returns_error():
    rc = main(["nonexistent_file.txt"])
    assert rc == 1


def test_main_no_matches_returns_zero(crontab_file: Path):
    rc = main([str(crontab_file), "--dow", "0", "--start", "01:00", "--end", "02:00"])
    assert rc == 0


def test_main_matches_returns_zero(crontab_file: Path):
    rc = main([str(crontab_file), "--dow", "1", "--start", "09:00", "--end", "17:00"])
    assert rc == 0


def test_main_output_contains_command(crontab_file: Path, capsys):
    main([str(crontab_file), "--dow", "1", "--start", "09:00", "--end", "11:00"])
    out = capsys.readouterr().out
    assert "/usr/bin/backup" in out or "/usr/bin/heartbeat" in out


def test_main_invalid_end_before_start_returns_error(crontab_file: Path):
    rc = main([str(crontab_file), "--start", "17:00", "--end", "09:00"])
    assert rc == 1
