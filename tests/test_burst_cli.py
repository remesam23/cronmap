"""Tests for cronmap.burst_cli."""
from __future__ import annotations

import os
import tempfile

import pytest

from cronmap.burst_cli import build_burst_parser, main


@pytest.fixture()
def crontab_file():
    content = "*/5 * * * * /bin/frequent\n0 2 * * * /bin/nightly\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".crontab", delete=False) as f:
        f.write(content)
        name = f.name
    yield name
    os.unlink(name)


# --- build_burst_parser ---

def test_build_burst_parser_defaults():
    p = build_burst_parser()
    args = p.parse_args(["some.crontab"])
    assert args.threshold == 10
    assert args.color is False
    assert args.exit_code is False


def test_build_burst_parser_all_flags():
    p = build_burst_parser()
    args = p.parse_args(["f", "--threshold", "5", "--color", "--exit-code"])
    assert args.threshold == 5
    assert args.color is True
    assert args.exit_code is True


# --- main ---

def test_main_missing_file_returns_error():
    rc = main(["nonexistent_file_xyz.crontab"])
    assert rc == 2


def test_main_no_bursts_returns_zero(crontab_file):
    # threshold higher than any entry fires
    rc = main([crontab_file, "--threshold", "100"])
    assert rc == 0


def test_main_bursts_found_returns_zero_without_flag(crontab_file):
    rc = main([crontab_file, "--threshold", "1"])
    assert rc == 0


def test_main_bursts_found_returns_one_with_exit_code(crontab_file):
    rc = main([crontab_file, "--threshold", "1", "--exit-code"])
    assert rc == 1


def test_main_color_flag_accepted(crontab_file):
    rc = main([crontab_file, "--color", "--threshold", "1"])
    assert rc == 0
