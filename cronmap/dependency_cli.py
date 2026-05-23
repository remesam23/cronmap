"""CLI entry-point for the dependency detector."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronmap.dependency import find_dependencies, format_dependency_report
from cronmap.parser import parse_crontab


def build_dependency_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-deps",
        description="Detect implicit cron job dependencies based on timing proximity.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "--gap",
        type=int,
        default=10,
        metavar="MINUTES",
        help="Maximum gap in minutes to consider a dependency (default: 10)",
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
        help="Exit with code 1 if any dependencies are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_dependency_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    entries = parse_crontab(path.read_text())
    results = find_dependencies(entries, max_gap_minutes=args.gap)
    print(format_dependency_report(results, color=args.color))

    if args.exit_code and results:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
