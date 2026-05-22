"""Tests for cronmap.exporter."""

import csv
import io
import json

import pytest

from cronmap.exporter import export_csv, export_json, export_schedule

SAMPLE_SCHEDULE = {
    1: [{"hour": 9, "minute": 0, "command": "backup.sh"}],
    3: [
        {"hour": 14, "minute": 30, "command": "report.py"},
        {"hour": 22, "minute": 0, "command": "cleanup.sh"},
    ],
}


def test_export_json_structure():
    result = json.loads(export_json(SAMPLE_SCHEDULE))
    assert set(result.keys()) == {
        "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
    }


def test_export_json_events_on_correct_day():
    result = json.loads(export_json(SAMPLE_SCHEDULE))
    monday = result["Monday"]
    assert len(monday) == 1
    assert monday[0]["time"] == "09:00"
    assert monday[0]["command"] == "backup.sh"


def test_export_json_empty_days_present():
    result = json.loads(export_json(SAMPLE_SCHEDULE))
    assert result["Sunday"] == []
    assert result["Saturday"] == []


def test_export_json_multiple_events():
    result = json.loads(export_json(SAMPLE_SCHEDULE))
    wednesday = result["Wednesday"]
    assert len(wednesday) == 2
    assert wednesday[0]["time"] == "14:30"
    assert wednesday[1]["time"] == "22:00"


def test_export_csv_header():
    result = export_csv(SAMPLE_SCHEDULE)
    reader = csv.reader(io.StringIO(result))
    header = next(reader)
    assert header == ["day", "time", "command"]


def test_export_csv_row_count():
    result = export_csv(SAMPLE_SCHEDULE)
    rows = [r for r in csv.reader(io.StringIO(result))]
    # 1 header + 3 events
    assert len(rows) == 4


def test_export_csv_time_formatting():
    result = export_csv(SAMPLE_SCHEDULE)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    times = {r["time"] for r in rows}
    assert "09:00" in times
    assert "14:30" in times


def test_export_schedule_dispatches_json():
    result = export_schedule(SAMPLE_SCHEDULE, "json")
    parsed = json.loads(result)
    assert "Monday" in parsed


def test_export_schedule_dispatches_csv():
    result = export_schedule(SAMPLE_SCHEDULE, "csv")
    assert "day,time,command" in result


def test_export_schedule_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_schedule(SAMPLE_SCHEDULE, "xml")
