"""Compare two Snapshots and report added / removed / unchanged entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from cronmap.diff import _entry_key
from cronmap.parser import CronEntry
from cronmap.snapshot import Snapshot


@dataclass
class SnapshotDiff:
    old_name: str
    new_name: str
    added: List[CronEntry] = field(default_factory=list)
    removed: List[CronEntry] = field(default_factory=list)
    unchanged: List[CronEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    def summary(self) -> str:
        lines = [
            f"Snapshot diff: '{self.old_name}' -> '{self.new_name}'",
            f"  Added:     {len(self.added)}",
            f"  Removed:   {len(self.removed)}",
            f"  Unchanged: {len(self.unchanged)}",
        ]
        if self.added:
            lines.append("  + " + "\n  + ".join(e.raw for e in self.added))
        if self.removed:
            lines.append("  - " + "\n  - ".join(e.raw for e in self.removed))
        return "\n".join(lines)


def diff_snapshots(old: Snapshot, new: Snapshot) -> SnapshotDiff:
    """Return a SnapshotDiff describing changes between *old* and *new*."""
    old_keys = {_entry_key(e): e for e in old.entries}
    new_keys = {_entry_key(e): e for e in new.entries}

    added = [new_keys[k] for k in new_keys if k not in old_keys]
    removed = [old_keys[k] for k in old_keys if k not in new_keys]
    unchanged = [old_keys[k] for k in old_keys if k in new_keys]

    return SnapshotDiff(
        old_name=old.name,
        new_name=new.name,
        added=added,
        removed=removed,
        unchanged=unchanged,
    )
