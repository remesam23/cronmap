"""Tests for cronmap.overlap_cli."""
import textwrap
from pathlib import Path

import pytest

from cronmap.overlap_cli import build_overlap_parser, main


SAMPLE_OVERLAP = textwrap.dedent("""\
    0 9 * * * /usr/bin/backup
    0 9 * * * /usr/bin/sync
""")

SAMPLE_NO_OVERLAP = textwrap.dedent("""\
    0 8 * * * /usr/bin/backup
    0 10 * * * /usr/bin/sync
""")


def test_build_overlap_parser_defaults():
    p = build_overlap_parser()
    args = p.parse_args(["some_file"])
    assert args.file == "some_file"
    assert args.color is False
    assert args.exit_code is False


def test_build_overlap_parser_color_flag():
    p = build_overlap_parser()
    args = p.parse_args(["f", "--color"])
    assert args.color is True


def test_build_overlap_parser_exit_code_flag():
    p = build_overlap_parser()
    args = p.parse_args(["f", "--exit-code"])
    assert args.exit_code is True


def test_main_missing_file_returns_error(tmp_path):
    rc = main([str(tmp_path / "nonexistent.crontab")])
    assert rc == 2


def test_main_no_overlaps_returns_zero(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(SAMPLE_NO_OVERLAP)
    rc = main([str(f)])
    assert rc == 0


def test_main_overlaps_returns_zero_without_exit_code_flag(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(SAMPLE_OVERLAP)
    rc = main([str(f)])
    assert rc == 0


def test_main_overlaps_returns_one_with_exit_code_flag(tmp_path):
    f = tmp_path / "crontab"
    f.write_text(SAMPLE_OVERLAP)
    rc = main([str(f), "--exit-code"])
    assert rc == 1


def test_main_output_contains_commands(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text(SAMPLE_OVERLAP)
    main([str(f)])
    captured = capsys.readouterr()
    assert "backup" in captured.out
    assert "sync" in captured.out


def test_main_no_overlap_output_message(tmp_path, capsys):
    f = tmp_path / "crontab"
    f.write_text(SAMPLE_NO_OVERLAP)
    main([str(f)])
    captured = capsys.readouterr()
    assert "No overlapping" in captured.out
