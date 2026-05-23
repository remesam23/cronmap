"""CLI entry-point for the conflict detector."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronmap.conflict import find_conflicts, format_conflict_report
from cronmap.parser import parse_crontab


def build_conflict_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-conflict",
        description="Detect cron entries that fire at the same time.",
    )
    p.add_argument("file", help="Path to crontab file")
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
        help="Exit with code 1 when conflicts are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_conflict_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    entries = parse_crontab(path.read_text())
    conflicts = find_conflicts(entries)
    report = format_conflict_report(conflicts, color=args.color)
    print(report)

    if args.exit_code and conflicts:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
