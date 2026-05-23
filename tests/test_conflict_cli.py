"""Tests for cronmap.conflict_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cronmap.conflict_cli import build_conflict_parser, main


def test_build_conflict_parser_defaults():
    p = build_conflict_parser()
    args = p.parse_args(["somefile"])
    assert args.file == "somefile"
    assert args.color is False
    assert args.exit_code is False


def test_build_conflict_parser_all_flags():
    p = build_conflict_parser()
    args = p.parse_args(["f", "--color", "--exit-code"])
    assert args.color is True
    assert args.exit_code is True


def test_main_missing_file_returns_error(tmp_path):
    rc = main([str(tmp_path / "nonexistent.crontab")])
    assert rc == 2


def test_main_no_conflicts_returns_zero(tmp_path):
    crontab = tmp_path / "crontab"
    crontab.write_text("0 6 * * * /usr/bin/backup\n0 7 * * * /usr/bin/cleanup\n")
    rc = main([str(crontab)])
    assert rc == 0


def test_main_conflicts_found_returns_zero_without_flag(tmp_path):
    crontab = tmp_path / "crontab"
    crontab.write_text("0 9 * * * /bin/job_a\n0 9 * * * /bin/job_b\n")
    rc = main([str(crontab)])
    assert rc == 0


def test_main_conflicts_found_returns_one_with_flag(tmp_path):
    crontab = tmp_path / "crontab"
    crontab.write_text("0 9 * * * /bin/job_a\n0 9 * * * /bin/job_b\n")
    rc = main([str(crontab), "--exit-code"])
    assert rc == 1


def test_main_output_contains_commands(tmp_path, capsys):
    crontab = tmp_path / "crontab"
    crontab.write_text("0 9 * * * /bin/alpha\n0 9 * * * /bin/beta\n")
    main([str(crontab)])
    out = capsys.readouterr().out
    assert "/bin/alpha" in out
    assert "/bin/beta" in out
