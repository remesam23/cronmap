"""Tests for cronmap.dependency_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cronmap.dependency_cli import build_dependency_parser, main


CRONTAB_CLOSE = textwrap.dedent("""\
    0 2 * * * /usr/bin/dump
    5 2 * * * /usr/bin/compress
""")

CRONTAB_FAR = textwrap.dedent("""\
    0 1 * * * /usr/bin/morning
    0 6 * * * /usr/bin/evening
""")


def test_build_dependency_parser_defaults():
    p = build_dependency_parser()
    args = p.parse_args(["crontab"])
    assert args.gap == 10
    assert args.color is False
    assert args.exit_code is False


def test_build_dependency_parser_all_flags():
    p = build_dependency_parser()
    args = p.parse_args(["crontab", "--gap", "5", "--color", "--exit-code"])
    assert args.gap == 5
    assert args.color is True
    assert args.exit_code is True


def test_main_missing_file_returns_error(tmp_path):
    rc = main([str(tmp_path / "missing.crontab")])
    assert rc == 2


def test_main_no_dependencies_returns_zero(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_FAR)
    rc = main([str(f)])
    assert rc == 0


def test_main_dependencies_found_returns_zero_without_flag(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_CLOSE)
    rc = main([str(f)])
    assert rc == 0


def test_main_dependencies_found_returns_one_with_flag(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_CLOSE)
    rc = main([str(f), "--exit-code"])
    assert rc == 1


def test_main_custom_gap_suppresses_dependency(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_CLOSE)  # gap is 5 minutes
    rc = main([str(f), "--gap", "4", "--exit-code"])
    assert rc == 0  # gap too small, no dependency detected


def test_main_output_contains_commands(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text(CRONTAB_CLOSE)
    main([str(f)])
    captured = capsys.readouterr()
    assert "dump" in captured.out or "compress" in captured.out
