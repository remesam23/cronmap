"""Format watcher diffs into human-readable reports."""

from cronmap.diff import CronDiff

_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def _entry_line(entry) -> str:
    """Return a short one-line representation of a CronEntry."""
    schedule = f"{entry.minute} {entry.hour} {entry.dom} {entry.month} {entry.dow}"
    return f"{schedule}  {entry.command}"


def format_watch_diff(diff: CronDiff, *, color: bool = True) -> str:
    """Return a formatted string describing what changed between two crontab
    snapshots as detected by the watcher.

    Parameters
    ----------
    diff:
        A :class:`~cronmap.diff.CronDiff` produced by :func:`~cronmap.diff.diff_crontabs`.
    color:
        When *True* (default) ANSI colour codes are included.
    """
    lines: list[str] = []

    def _c(code: str, text: str) -> str:
        return f"{code}{text}{_RESET}" if color else text

    lines.append(_c(_YELLOW, "=== crontab changed ==="))

    for entry in diff.added:
        lines.append(_c(_GREEN, f"  + {_entry_line(entry)}"))

    for entry in diff.removed:
        lines.append(_c(_RED, f"  - {_entry_line(entry)}"))

    summary = diff.summary()
    lines.append(_c(_YELLOW, f"--- {summary} ---"))
    return "\n".join(lines)


def print_watch_diff(diff: CronDiff, *, color: bool = True) -> None:
    """Print a formatted diff to stdout."""
    print(format_watch_diff(diff, color=color))
