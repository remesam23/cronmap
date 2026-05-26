"""CLI entry-point for the stale-entry detector."""
from __future__ import annotations

import argparse
import sys

from cronmap.parser import parse_crontab
from cronmap.stale import find_stale, format_stale_report


def build_stale_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-stale",
        description="Identify cron entries that fire very infrequently.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "--threshold",
        type=int,
        default=7,
        metavar="N",
        help="Max fires/week to be considered stale (default: 7)",
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
        help="Exit with code 1 when stale entries are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_stale_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.file) as fh:
            text = fh.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    entries = parse_crontab(text)
    results = find_stale(entries, threshold=args.threshold)
    print(format_stale_report(results, color=args.color))

    if args.exit_code and results:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
