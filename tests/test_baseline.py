"""Tests for cronmap.baseline."""
import json
import os
import pytest

from cronmap.baseline import (
    Baseline,
    capture_baseline,
    save_baseline,
    load_baseline,
    compare_to_baseline,
)
from cronmap.parser import CronEntry


def make_entry(minute="0", hour="6", dom="*", month="*", dow="*", command="/bin/job"):
    return CronEntry(minute=minute, hour=hour, dom=dom, month=month, dow=dow, command=command)


SAMPLE_CRONTAB = "0 6 * * * /bin/backup\n30 12 * * 1 /bin/report\n"


def test_capture_baseline_entry_count():
    b = capture_baseline(SAMPLE_CRONTAB, name="test")
    assert len(b.entries) == 2


def test_capture_baseline_name_stored():
    b = capture_baseline(SAMPLE_CRONTAB, name="prod")
    assert b.name == "prod"


def test_capture_baseline_custom_timestamp():
    b = capture_baseline(SAMPLE_CRONTAB, timestamp="2024-01-01T00:00:00+00:00")
    assert b.created_at == "2024-01-01T00:00:00+00:00"


def test_baseline_to_dict_roundtrip():
    b = capture_baseline(SAMPLE_CRONTAB, name="rt", timestamp="2024-06-01T12:00:00+00:00")
    d = b.to_dict()
    b2 = Baseline.from_dict(d)
    assert b2.name == b.name
    assert b2.created_at == b.created_at
    assert len(b2.entries) == len(b.entries)


def test_save_and_load_baseline_roundtrip(tmp_path):
    path = str(tmp_path / "baseline.json")
    b = capture_baseline(SAMPLE_CRONTAB, name="save_test", timestamp="2024-01-01T00:00:00+00:00")
    save_baseline(b, path)
    assert os.path.exists(path)
    loaded = load_baseline(path)
    assert loaded.name == "save_test"
    assert len(loaded.entries) == 2


def test_saved_baseline_is_valid_json(tmp_path):
    path = str(tmp_path / "bl.json")
    b = capture_baseline(SAMPLE_CRONTAB)
    save_baseline(b, path)
    with open(path) as fh:
        data = json.load(fh)
    assert "entries" in data
    assert isinstance(data["entries"], list)


def test_compare_no_changes():
    b = capture_baseline(SAMPLE_CRONTAB)
    current = b.entries[:]
    diff = compare_to_baseline(current, b)
    assert not diff.has_changes()


def test_compare_detects_added_entry():
    b = capture_baseline(SAMPLE_CRONTAB)
    extra = make_entry(command="/bin/new")
    diff = compare_to_baseline(b.entries + [extra], b)
    assert diff.has_changes()
    assert diff.counts()["added"] == 1


def test_compare_detects_removed_entry():
    b = capture_baseline(SAMPLE_CRONTAB)
    diff = compare_to_baseline(b.entries[:1], b)
    assert diff.has_changes()
    assert diff.counts()["removed"] == 1
