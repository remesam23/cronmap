"""CLI entry-point for burst detection."""
from __future__ import annotations

import argparse
import sys

from cronmap.burst import detect_bursts, format_burst_report
from cronmap.parser import parse_crontab


def build_burst_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-burst",
        description="Detect cron entries that fire very frequently within an hour.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "--threshold",
        type=int,
        default=10,
        metavar="N",
        help="Minimum fires-per-hour to flag as a burst (default: 10)",
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
        help="Exit with code 1 when bursts are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_burst_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.file) as fh:
            text = fh.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    entries = parse_crontab(text)
    results = detect_bursts(entries, threshold=args.threshold)
    print(format_burst_report(results, color=args.color))

    if args.exit_code and any(results):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
