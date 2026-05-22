"""Command-line interface for cronmap."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronmap.exporter import export_schedule
from cronmap.parser import parse_crontab
from cronmap.renderer import render_compact, render_weekly_table
from cronmap.schedule import build_weekly_schedule


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronmap",
        description="Visualize crontab entries as a weekly schedule.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to a crontab file (defaults to stdin).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        default=False,
        help="Render a compact one-line-per-event view.",
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv"],
        metavar="FORMAT",
        help="Export schedule to FORMAT (json or csv) instead of rendering.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # --- read input ---
    try:
        if args.file:
            text = Path(args.file).read_text(encoding="utf-8")
        else:
            text = sys.stdin.read()
    except FileNotFoundError:
        print(f"cronmap: error: file not found: {args.file}", file=sys.stderr)
        return 1

    entries = parse_crontab(text)
    schedule = build_weekly_schedule(entries)

    # --- produce output ---
    if args.export:
        content = export_schedule(schedule, args.export)
    elif args.compact:
        content = render_compact(schedule)
    else:
        content = render_weekly_table(schedule)

    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
