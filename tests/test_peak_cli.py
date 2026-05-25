"""Unit tests for cronmap.peak_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronmap.peak_cli import build_peak_parser, main


@pytest.fixture()
def crontab_file(tmp_path: Path) -> Path:
    p = tmp_path / "crontab"
    p.write_text(
        "0 9 * * * /bin/backup\n"
        "30 9 * * * /bin/report\n"
        "0 14 * * * /bin/cleanup\n"
        "0 14 * * * /bin/sync\n"
    )
    return p


# --- build_peak_parser ---

def test_build_peak_parser_defaults():
    p = build_peak_parser()
    args = p.parse_args(["somefile"])
    assert args.file == "somefile"
    assert args.color is False
    assert args.top == 0


def test_build_peak_parser_all_flags():
    p = build_peak_parser()
    args = p.parse_args(["somefile", "--color", "--top", "3"])
    assert args.color is True
    assert args.top == 3


# --- main ---

def test_main_missing_file_returns_error(tmp_path: Path):
    rc = main([str(tmp_path / "no_such_file")])
    assert rc == 1


def test_main_returns_zero_on_success(crontab_file: Path):
    rc = main([str(crontab_file)])
    assert rc == 0


def test_main_output_contains_hours(crontab_file: Path, capsys):
    main([str(crontab_file)])
    out = capsys.readouterr().out
    assert "09:00" in out
    assert "14:00" in out


def test_main_output_marks_peak_hour(crontab_file: Path, capsys):
    main([str(crontab_file)])
    out = capsys.readouterr().out
    # 14:xx has 2 entries — should be marked as peak
    assert "<-- peak" in out


def test_main_top_flag_restricts_peaks(crontab_file: Path, capsys):
    main([str(crontab_file), "--top", "1"])
    out = capsys.readouterr().out
    # Only one hour should be marked as peak
    assert out.count("<-- peak") == 1


def test_main_color_flag_adds_ansi(crontab_file: Path, capsys):
    main([str(crontab_file), "--color"])
    out = capsys.readouterr().out
    assert "\033[" in out
