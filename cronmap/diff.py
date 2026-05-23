"""Diff two crontab snapshots and report added/removed/changed entries."""

from dataclasses import dataclass, field
from typing import List, Tuple
from cronmap.parser import CronEntry


@dataclass
class CronDiff:
    added: List[CronEntry] = field(default_factory=list)
    removed: List[CronEntry] = field(default_factory=list)
    unchanged: List[CronEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    def summary(self) -> str:
        lines = []
        if self.added:
            lines.append(f"+{len(self.added)} added")
        if self.removed:
            lines.append(f"-{len(self.removed)} removed")
        if self.unchanged:
            lines.append(f" {len(self.unchanged)} unchanged")
        return ", ".join(lines) if lines else "no changes"

    def counts(self) -> dict:
        """Return a dictionary with counts of added, removed, and unchanged entries."""
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "unchanged": len(self.unchanged),
        }


def _entry_key(entry: CronEntry) -> Tuple[str, str]:
    """Unique key for an entry based on schedule + command."""
    schedule = f"{entry.minute} {entry.hour} {entry.dom} {entry.month} {entry.dow}"
    return (schedule.strip(), entry.command.strip())


def diff_crontabs(old: List[CronEntry], new: List[CronEntry]) -> CronDiff:
    """Compare two lists of CronEntry objects and return a CronDiff."""
    old_keys = {_entry_key(e): e for e in old}
    new_keys = {_entry_key(e): e for e in new}

    added = [new_keys[k] for k in new_keys if k not in old_keys]
    removed = [old_keys[k] for k in old_keys if k not in new_keys]
    unchanged = [old_keys[k] for k in old_keys if k in new_keys]

    return CronDiff(added=added, removed=removed, unchanged=unchanged)


def format_diff(diff: CronDiff, color: bool = False) -> str:
    """Render a human-readable diff report."""
    lines = []

    green = "\033[32m" if color else ""
    red = "\033[31m" if color else ""
    reset = "\033[0m" if color else ""

    for entry in diff.added:
        key = _entry_key(entry)
        lines.append(f"{green}+ {key[0]}  {key[1]}{reset}")

    for entry in diff.removed:
        key = _entry_key(entry)
        lines.append(f"{red}- {key[0]}  {key[1]}{reset}")

    for entry in diff.unchanged:
        key = _entry_key(entry)
        lines.append(f"  {key[0]}  {key[1]}")

    header = f"# {diff.summary()}"
    return "\n".join([header] + lines) if lines else header
