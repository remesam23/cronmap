"""Tests for cronmap.cli."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronmap.cli import build_parser, main


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.file is None
    assert args.compact is False
    assert args.export is None
    assert args.output is None


def test_build_parser_all_flags():
    parser = build_parser()
    args = parser.parse_args(["my.crontab", "--compact", "--export", "json", "--output", "out.json"])
    assert args.file == "my.crontab"
    assert args.compact is True
    assert args.export == "json"
    assert args.output == "out.json"


def test_main_reads_from_file(tmp_path: Path):
    crontab = tmp_path / "test.crontab"
    crontab.write_text("0 9 * * 1 /usr/bin/backup\n", encoding="utf-8")
    rc = main([str(crontab)])
    assert rc == 0


def test_main_compact_mode(tmp_path: Path, capsys):
    crontab = tmp_path / "test.crontab"
    crontab.write_text("30 14 * * 3 report.py\n", encoding="utf-8")
    rc = main([str(crontab), "--compact"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "14:30" in captured.out


def test_main_missing_file_returns_error():
    rc = main(["nonexistent_file_xyz.crontab"])
    assert rc == 1


def test_main_export_json(tmp_path: Path, capsys):
    crontab = tmp_path / "test.crontab"
    crontab.write_text("0 8 * * 2 /bin/task\n", encoding="utf-8")
    rc = main([str(crontab), "--export", "json"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "Tuesday" in data


def test_main_export_csv(tmp_path: Path, capsys):
    crontab = tmp_path / "test.crontab"
    crontab.write_text("15 6 * * 5 /bin/weekly\n", encoding="utf-8")
    rc = main([str(crontab), "--export", "csv"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "day,time,command" in captured.out


def test_main_export_to_output_file(tmp_path: Path):
    crontab = tmp_path / "test.crontab"
    crontab.write_text("0 12 * * 0 /bin/noon\n", encoding="utf-8")
    out_file = tmp_path / "schedule.json"
    rc = main([str(crontab), "--export", "json", "--output", str(out_file)])
    assert rc == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "Sunday" in data
