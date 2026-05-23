"""CLI entry-point for the overlap detector."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronmap.parser import parse_crontab
from cronmap.overlap import detect_overlaps, format_overlap_report


def build_overlap_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-overlap",
        description="Detect overlapping cron entries in a crontab file.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Enable ANSI colour in output",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        dest="exit_code",
        help="Exit with code 1 when overlaps are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_overlap_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2

    text = path.read_text()
    entries = parse_crontab(text)
    overlaps = detect_overlaps(entries)
    report = format_overlap_report(overlaps, color=args.color)
    print(report)

    if args.exit_code and overlaps:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
