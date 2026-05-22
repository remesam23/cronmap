"""Tests for cronmap.snapshot and cronmap.snapshot_diff."""

import json
import os
import tempfile

import pytest

from cronmap.parser import CronEntry
from cronmap.snapshot import (
    Snapshot,
    load_snapshot,
    save_snapshot,
    snapshot_from_text,
)
from cronmap.snapshot_diff import SnapshotDiff, diff_snapshots


RAW_CRONTAB = "0 9 * * 1 /usr/bin/backup\n30 18 * * 5 /usr/bin/report\n"


def make_entry(minute="0", hour="9", dow="1", command="/cmd") -> CronEntry:
    raw = f"{minute} {hour} * * {dow} {command}"
    return CronEntry(
        minute=minute,
        hour=hour,
        day_of_month="*",
        month="*",
        day_of_week=dow,
        command=command,
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Snapshot round-trip
# ---------------------------------------------------------------------------

def test_snapshot_from_text_creates_entries():
    snap = snapshot_from_text("test", RAW_CRONTAB)
    assert snap.name == "test"
    assert len(snap.entries) == 2


def test_snapshot_from_text_sets_created_at():
    snap = snapshot_from_text("test", RAW_CRONTAB)
    assert snap.created_at  # non-empty


def test_snapshot_from_text_accepts_custom_timestamp():
    snap = snapshot_from_text("test", RAW_CRONTAB, created_at="2024-01-01T00:00:00")
    assert snap.created_at == "2024-01-01T00:00:00"


def test_save_and_load_snapshot_roundtrip():
    snap = snapshot_from_text("roundtrip", RAW_CRONTAB, created_at="2024-06-01T12:00:00")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_snapshot(snap, path)
        loaded = load_snapshot(path)
        assert loaded.name == snap.name
        assert loaded.created_at == snap.created_at
        assert len(loaded.entries) == len(snap.entries)
        assert loaded.entries[0].command == snap.entries[0].command
    finally:
        os.unlink(path)


def test_save_snapshot_writes_valid_json():
    snap = snapshot_from_text("json-check", RAW_CRONTAB)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
    try:
        save_snapshot(snap, path)
        with open(path) as fh:
            data = json.load(fh)
        assert data["name"] == "json-check"
        assert isinstance(data["entries"], list)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# SnapshotDiff
# ---------------------------------------------------------------------------

def test_diff_no_changes():
    snap = snapshot_from_text("a", RAW_CRONTAB, created_at="t1")
    snap2 = snapshot_from_text("b", RAW_CRONTAB, created_at="t2")
    result = diff_snapshots(snap, snap2)
    assert not result.has_changes
    assert len(result.unchanged) == 2


def test_diff_detects_added_entry():
    old = snapshot_from_text("old", RAW_CRONTAB)
    new_text = RAW_CRONTAB + "0 0 * * 0 /usr/bin/weekly\n"
    new = snapshot_from_text("new", new_text)
    result = diff_snapshots(old, new)
    assert len(result.added) == 1
    assert "/usr/bin/weekly" in result.added[0].command


def test_diff_detects_removed_entry():
    old_text = RAW_CRONTAB + "0 0 * * 0 /usr/bin/weekly\n"
    old = snapshot_from_text("old", old_text)
    new = snapshot_from_text("new", RAW_CRONTAB)
    result = diff_snapshots(old, new)
    assert len(result.removed) == 1


def test_diff_summary_contains_names():
    old = snapshot_from_text("snap-v1", RAW_CRONTAB)
    new = snapshot_from_text("snap-v2", RAW_CRONTAB + "0 3 * * 2 /bin/nightly\n")
    result = diff_snapshots(old, new)
    summary = result.summary()
    assert "snap-v1" in summary
    assert "snap-v2" in summary
    assert "Added:" in summary
