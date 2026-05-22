"""Tests for cronmap.cli module."""

import io
import pytest
from unittest.mock import patch, mock_open
from cronmap.cli import main, build_parser


SAMPLE_CRONTAB = "30 9 * * * backup.sh\n0 17 * * 1-5 report.py\n"


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.file is None
    assert not args.compact
    assert not args.no_color


def test_build_parser_all_flags():
    parser = build_parser()
    args = parser.parse_args(["somefile", "--compact", "--no-color"])
    assert args.file == "somefile"
    assert args.compact
    assert args.no_color


def test_main_reads_from_file(tmp_path, capsys):
    cron_file = tmp_path / "crontab.txt"
    cron_file.write_text(SAMPLE_CRONTAB)
    result = main([str(cron_file), "--no-color"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Weekly Cron Schedule" in captured.out


def test_main_compact_mode(tmp_path, capsys):
    cron_file = tmp_path / "crontab.txt"
    cron_file.write_text(SAMPLE_CRONTAB)
    result = main([str(cron_file), "--compact", "--no-color"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Mon" in captured.out


def test_main_missing_file_returns_error(capsys):
    result = main(["nonexistent_file.txt"])
    assert result == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_main_empty_crontab_returns_error(tmp_path, capsys):
    cron_file = tmp_path / "empty.txt"
    cron_file.write_text("# just a comment\n")
    result = main([str(cron_file)])
    assert result == 1
    captured = capsys.readouterr()
    assert "no valid cron entries" in captured.err


def test_main_reads_from_stdin(capsys):
    with patch("sys.stdin", io.StringIO(SAMPLE_CRONTAB)):
        result = main(["--no-color"])
    assert result == 0
    captured = capsys.readouterr()
    assert "backup.sh" in captured.out
