"""CLI entry-point for the crontab file watcher."""

import argparse
import sys
from pathlib import Path

from cronmap.watcher import watch
from cronmap.watch_report import print_watch_diff


def build_watch_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronmap-watch",
        description="Watch a crontab file and print diffs as it changes.",
    )
    parser.add_argument("file", help="Path to the crontab file to watch.")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_watch_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    color = not args.no_color
    print(f"Watching {path} (interval={args.interval}s) — press Ctrl-C to stop.")

    try:
        watch(
            path,
            callback=lambda diff: print_watch_diff(diff, color=color),
            interval=args.interval,
        )
    except KeyboardInterrupt:
        print("\nStopped.")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
