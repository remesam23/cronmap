"""Export weekly schedule to various formats (JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from typing import Dict, List

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

SUPPORTED_FORMATS = {"json", "csv"}


def export_json(schedule: Dict[int, List[dict]]) -> str:
    """Serialize the weekly schedule to a JSON string."""
    output: Dict[str, List[dict]] = {}
    for day_index in range(7):
        day_name = DAYS[day_index]
        events = schedule.get(day_index, [])
        output[day_name] = [
            {
                "time": f"{e['hour']:02d}:{e['minute']:02d}",
                "command": e["command"],
            }
            for e in events
        ]
    return json.dumps(output, indent=2)


def export_csv(schedule: Dict[int, List[dict]]) -> str:
    """Serialize the weekly schedule to a CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["day", "time", "command"])
    for day_index in range(7):
        day_name = DAYS[day_index]
        for event in schedule.get(day_index, []):
            time_str = f"{event['hour']:02d}:{event['minute']:02d}"
            writer.writerow([day_name, time_str, event["command"]])
    return buf.getvalue()


def export_schedule(schedule: Dict[int, List[dict]], fmt: str) -> str:
    """Dispatch to the appropriate exporter based on *fmt* ('json' or 'csv').

    Args:
        schedule: Mapping of day index (0=Sunday … 6=Saturday) to a list of
            event dicts, each containing 'hour', 'minute', and 'command' keys.
        fmt: Output format; must be one of 'json' or 'csv' (case-insensitive).

    Returns:
        The serialized schedule as a string in the requested format.

    Raises:
        ValueError: If *fmt* is not a supported format.
    """
    fmt = fmt.lower().strip()
    if fmt == "json":
        return export_json(schedule)
    if fmt == "csv":
        return export_csv(schedule)
    raise ValueError(
        f"Unsupported export format: {fmt!r}. "
        f"Choose one of: {', '.join(sorted(SUPPORTED_FORMATS))}."
    )
