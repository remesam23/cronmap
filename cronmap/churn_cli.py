"""CLI entry-point for the churn analyser."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronmap.parser import parse_crontab
from cronmap.churn import compute_churn, format_churn_report


def build_churn_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronmap-churn",
        description="Report how frequently each crontab entry fires per week.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Show only the top N entries (0 = all)",
    )
    p.add_argument(
        "--min-fires",
        type=int,
        default=0,
        metavar="N",
        help="Only show entries that fire at least N times per week",
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
        help="Exit with code 1 when any high/extreme churn entries are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_churn_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    entries = parse_crontab(path.read_text())
    results = compute_churn(entries)

    if args.min_fires > 0:
        results = [r for r in results if r.fires_per_week >= args.min_fires]

    if args.top > 0:
        results = results[: args.top]

    print(format_churn_report(results, color=args.color))

    if args.exit_code and any(r.label in ("high", "extreme") for r in results):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
