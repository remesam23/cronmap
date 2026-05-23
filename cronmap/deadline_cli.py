"""CLI entry-point for deadline detection."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronmap.parser import parse_crontab
from cronmap.deadline import find_deadlines, format_deadline_report


def build_deadline_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-deadline",
        description="Detect cron jobs with tight scheduling deadlines.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "--threshold",
        type=int,
        default=10,
        metavar="MINUTES",
        help="Gap threshold in minutes (default: 10)",
    )
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Enable ANSI colour output",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        dest="exit_code",
        help="Exit with code 1 if tight deadlines are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_deadline_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    entries = parse_crontab(path.read_text())
    results = find_deadlines(entries, threshold_minutes=args.threshold)
    report = format_deadline_report(results, color=args.color)
    print(report)

    if args.exit_code and results:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
