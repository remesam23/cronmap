"""CLI for baseline capture and comparison."""
from __future__ import annotations

import argparse
import sys

from cronmap.baseline import capture_baseline, load_baseline, save_baseline, compare_to_baseline
from cronmap.parser import parse_crontab


DEFAULT_BASELINE_PATH = ".cronmap_baseline.json"


def build_baseline_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronmap-baseline",
        description="Capture or compare a crontab baseline.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="Save current crontab as baseline.")
    cap.add_argument("file", help="Path to crontab file.")
    cap.add_argument("--output", default=DEFAULT_BASELINE_PATH, help="Where to write the baseline JSON.")
    cap.add_argument("--name", default="default", help="Label for this baseline.")

    cmp = sub.add_parser("compare", help="Compare a crontab file against a saved baseline.")
    cmp.add_argument("file", help="Path to current crontab file.")
    cmp.add_argument("--baseline", default=DEFAULT_BASELINE_PATH, help="Path to baseline JSON.")
    cmp.add_argument("--exit-code", action="store_true", help="Exit 1 if changes detected.")

    return parser


def main(argv=None) -> int:
    parser = build_baseline_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1

    if args.command == "capture":
        baseline = capture_baseline(text, name=args.name)
        save_baseline(baseline, args.output)
        print(f"Baseline '{baseline.name}' saved to {args.output} ({len(baseline.entries)} entries).")
        return 0

    # compare
    try:
        baseline = load_baseline(args.baseline)
    except FileNotFoundError:
        print(f"error: baseline not found: {args.baseline}", file=sys.stderr)
        return 1

    current = parse_crontab(text)
    diff = compare_to_baseline(current, baseline)

    if not diff.has_changes():
        print("No changes detected.")
        return 0

    counts = diff.counts()
    print(diff.summary())
    print(f"  Added:   {counts['added']}")
    print(f"  Removed: {counts['removed']}")

    if args.exit_code:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
