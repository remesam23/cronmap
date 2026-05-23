"""CLI entry-point for the calendar view sub-command."""
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import List, Optional

from cronmap.calendar_report import render_calendar_report
from cronmap.parser import parse_crontab


def build_calendar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-calendar",
        description="Render a monthly calendar view of a crontab file.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year (default: current year)",
    )
    p.add_argument(
        "--month",
        type=int,
        default=None,
        help="Month 1-12 (default: current month)",
    )
    p.add_argument(
        "--day",
        type=int,
        default=None,
        help="Show detailed entry list for this day",
    )
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Enable ANSI colour output",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_calendar_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    today = datetime.date.today()
    year = args.year if args.year is not None else today.year
    month = args.month if args.month is not None else today.month

    if not (1 <= month <= 12):
        print("Error: --month must be between 1 and 12.", file=sys.stderr)
        return 1

    text = path.read_text()
    entries = parse_crontab(text)
    report = render_calendar_report(
        year, month, entries, detail_day=args.day, use_color=args.color
    )
    print(report)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
