"""Tests for cronmap.baseline_cli."""
import json
import os
import pytest

from cronmap.baseline_cli import build_baseline_parser, main


SAMPLE = "0 6 * * * /bin/backup\n30 12 * * 1 /bin/report\n"


def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content)
    return str(p)


def test_build_baseline_parser_subcommands():
    parser = build_baseline_parser()
    # should not raise
    args = parser.parse_args(["capture", "somefile"])
    assert args.command == "capture"


def test_build_baseline_parser_compare_defaults():
    parser = build_baseline_parser()
    args = parser.parse_args(["compare", "somefile"])
    assert args.exit_code is False
    assert ".cronmap_baseline.json" in args.baseline


def test_main_capture_creates_file(tmp_path):
    cron = _write(tmp_path, "crontab", SAMPLE)
    out = str(tmp_path / "bl.json")
    rc = main(["capture", cron, "--output", out])
    assert rc == 0
    assert os.path.exists(out)


def test_main_capture_json_has_correct_entry_count(tmp_path):
    cron = _write(tmp_path, "crontab", SAMPLE)
    out = str(tmp_path / "bl.json")
    main(["capture", cron, "--output", out])
    with open(out) as fh:
        data = json.load(fh)
    assert len(data["entries"]) == 2


def test_main_capture_missing_file_returns_error(tmp_path):
    rc = main(["capture", str(tmp_path / "nope.txt")])
    assert rc == 1


def test_main_compare_no_changes(tmp_path):
    cron = _write(tmp_path, "crontab", SAMPLE)
    bl = str(tmp_path / "bl.json")
    main(["capture", cron, "--output", bl])
    rc = main(["compare", cron, "--baseline", bl])
    assert rc == 0


def test_main_compare_detects_changes(tmp_path):
    cron = _write(tmp_path, "crontab", SAMPLE)
    bl = str(tmp_path / "bl.json")
    main(["capture", cron, "--output", bl])
    cron2 = _write(tmp_path, "crontab2", SAMPLE + "0 3 * * * /bin/extra\n")
    rc = main(["compare", cron2, "--baseline", bl])
    assert rc == 0  # no --exit-code flag


def test_main_compare_exit_code_flag_returns_one_on_changes(tmp_path):
    cron = _write(tmp_path, "crontab", SAMPLE)
    bl = str(tmp_path / "bl.json")
    main(["capture", cron, "--output", bl])
    cron2 = _write(tmp_path, "crontab2", SAMPLE + "0 3 * * * /bin/extra\n")
    rc = main(["compare", cron2, "--baseline", bl, "--exit-code"])
    assert rc == 1


def test_main_compare_missing_baseline_returns_error(tmp_path):
    cron = _write(tmp_path, "crontab", SAMPLE)
    rc = main(["compare", cron, "--baseline", str(tmp_path / "no_baseline.json")])
    assert rc == 1
