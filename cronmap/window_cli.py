"""CLI entry-point for the window sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronmap.parser import parse_crontab
from cronmap.window import entries_in_window


def build_window_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Show cron entries that fire within a time window on a given day."
    )
    if parent is not None:
        parser = parent.add_parser("window", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to crontab file")
    parser.add_argument("--dow", type=int, default=1, metavar="DOW",
                        help="Day of week (0=Sun … 6=Sat, default: 1=Mon)")
    parser.add_argument("--start", default="09:00", metavar="HH:MM",
                        help="Window start time (default: 09:00)")
    parser.add_argument("--end", default="17:00", metavar="HH:MM",
                        help="Window end time (default: 17:00)")
    parser.add_argument("--no-color", dest="color", action="store_false", default=True)
    return parser


def _parse_time(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Invalid time format: {value!r}")
    return int(parts[0]), int(parts[1])


def main(argv: list[str] | None = None) -> int:
    parser = build_window_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        sh, sm = _parse_time(args.start)
        eh, em = _parse_time(args.end)
    except (ValueError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    entries = parse_crontab(path.read_text())
    try:
        results = entries_in_window(entries, args.dow, sh, sm, eh, em)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No entries fire within the specified window.")
        return 0

    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    day_label = day_names[args.dow % 7]
    print(f"Entries firing on {day_label} between {args.start} and {args.end}:\n")
    for res in results:
        times_str = ", ".join(f"{h:02d}:{m:02d}" for h, m in res.matching_times)
        print(f"  {res.entry.command}")
        print(f"    times: {times_str}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
