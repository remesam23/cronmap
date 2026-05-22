"""Command-line interface for cronmap."""

import argparse
import sys
from cronmap.parser import parse_crontab
from cronmap.renderer import render_weekly_table, render_compact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronmap",
        description="Visualize crontab entries as a weekly terminal schedule.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to a crontab file (reads from stdin if omitted).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Render a compact one-line-per-day view.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output.",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    use_color = not args.no_color

    try:
        if args.file:
            with open(args.file, "r") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
    except OSError as exc:
        print(f"cronmap: error reading input: {exc}", file=sys.stderr)
        return 1

    entries = parse_crontab(raw)
    if not entries:
        print("cronmap: no valid cron entries found.", file=sys.stderr)
        return 1

    if args.compact:
        output = render_compact(entries, use_color=use_color)
    else:
        output = render_weekly_table(entries, use_color=use_color)

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
