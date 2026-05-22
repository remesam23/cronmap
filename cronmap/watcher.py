"""Watch a crontab file for changes and emit diffs."""

import time
import hashlib
from pathlib import Path
from typing import Callable, Optional

from cronmap.parser import parse_crontab
from cronmap.diff import diff_crontabs, CronDiff


def _file_hash(path: Path) -> str:
    """Return MD5 hex digest of file contents."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def _read_entries(path: Path):
    """Parse cron entries from *path*, returning an empty list on error."""
    try:
        return parse_crontab(path.read_text())
    except Exception:
        return []


def watch(
    path: str | Path,
    callback: Callable[[CronDiff], None],
    interval: float = 2.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *path* every *interval* seconds and call *callback* with a
    :class:`~cronmap.diff.CronDiff` whenever the file changes.

    Parameters
    ----------
    path:
        Path to the crontab file to watch.
    callback:
        Callable invoked with the diff when a change is detected.
    interval:
        Polling interval in seconds.
    max_iterations:
        Stop after this many poll cycles (``None`` means run forever).
        Useful for testing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Crontab file not found: {path}")

    previous_hash = _file_hash(path)
    previous_entries = _read_entries(path)
    iterations = 0

    while True:
        if max_iterations is not None and iterations >= max_iterations:
            break
        time.sleep(interval)
        iterations += 1

        if not path.exists():
            continue

        current_hash = _file_hash(path)
        if current_hash == previous_hash:
            continue

        current_entries = _read_entries(path)
        diff = diff_crontabs(previous_entries, current_entries)
        if diff.has_changes:
            callback(diff)

        previous_hash = current_hash
        previous_entries = current_entries
