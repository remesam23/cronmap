"""CLI entry-point for the peak-hour analyser."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronmap.parser import parse_crontab
from cronmap.peak import find_peak_hours, format_peak_report


def build_peak_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-peak",
        description="Show which hours of the day have the most cron activity.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Enable ANSI colour output",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Only show the top N peak hours (0 = show all)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_peak_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    entries = parse_crontab(path.read_text())
    result = find_peak_hours(entries)

    if args.top > 0:
        # Restrict peak_hours to the requested top-N by count
        sorted_hours = sorted(
            result.hour_counts, key=lambda h: result.hour_counts[h], reverse=True
        )
        result.peak_hours = sorted(sorted_hours[: args.top])

    print(format_peak_report(result, color=args.color))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
