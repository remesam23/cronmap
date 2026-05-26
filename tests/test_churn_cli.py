"""Tests for cronmap.churn_cli."""
import json
import textwrap
from pathlib import Path

import pytest

from cronmap.churn_cli import build_churn_parser, main


@pytest.fixture()
def crontab_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        * * * * * /bin/heartbeat
        0 6 * * * /usr/bin/backup
        0 * * * 1-5 /bin/workday_check
    """)
    p = tmp_path / "crontab"
    p.write_text(content)
    return p


def test_build_churn_parser_defaults():
    p = build_churn_parser()
    args = p.parse_args(["somefile"])
    assert args.top == 0
    assert args.min_fires == 0
    assert args.color is False
    assert args.exit_code is False


def test_build_churn_parser_all_flags():
    p = build_churn_parser()
    args = p.parse_args(["f", "--top", "3", "--min-fires", "100", "--color", "--exit-code"])
    assert args.top == 3
    assert args.min_fires == 100
    assert args.color is True
    assert args.exit_code is True


def test_main_missing_file_returns_error(tmp_path: Path):
    rc = main([str(tmp_path / "missing.txt")])
    assert rc == 2


def test_main_returns_zero_on_success(crontab_file: Path):
    rc = main([str(crontab_file)])
    assert rc == 0


def test_main_top_limits_output(crontab_file: Path, capsys):
    main([str(crontab_file), "--top", "1"])
    captured = capsys.readouterr().out
    # Only one command line should appear after the header
    lines = [l for l in captured.splitlines() if l.strip() and not l.startswith("Churn")]
    assert len(lines) == 1


def test_main_min_fires_filters(crontab_file: Path, capsys):
    # heartbeat fires 60*24*7 times; backup fires 7; workday_check fires 5
    main([str(crontab_file), "--min-fires", "10000"])
    out = capsys.readouterr().out
    assert "/bin/heartbeat" in out
    assert "/usr/bin/backup" not in out


def test_main_exit_code_flag_high_churn(crontab_file: Path):
    # heartbeat is extreme churn → should return 1 with --exit-code
    rc = main([str(crontab_file), "--exit-code"])
    assert rc == 1


def test_main_exit_code_flag_low_churn(tmp_path: Path):
    p = tmp_path / "quiet.txt"
    p.write_text("0 0 * * 0 /bin/weekly\n")
    rc = main([str(p), "--exit-code"])
    assert rc == 0
