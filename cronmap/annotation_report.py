"""Format annotated cron entries for terminal output."""

from typing import List

from cronmap.annotator import AnnotatedEntry


def _tag_badge(tag: str, use_color: bool) -> str:
    if not use_color:
        return f"[{tag}]"
    colors = {
        "frequent": "\033[91m",
        "daily-midnight": "\033[94m",
        "weekdays-only": "\033[92m",
        "weekends-only": "\033[93m",
        "monthly": "\033[95m",
        "hourly-aligned": "\033[96m",
    }
    color = colors.get(tag, "\033[90m")
    return f"{color}[{tag}]\033[0m"


def format_annotation(ann: AnnotatedEntry, use_color: bool = True) -> str:
    entry = ann.entry
    schedule = f"{entry.minute} {entry.hour} {entry.dom} {entry.month} {entry.dow}"
    badges = " ".join(_tag_badge(t, use_color) for t in ann.tags)
    line_info = f"  line {entry.line_number}" if entry.line_number else ""
    header = f"{schedule}  {entry.command}{line_info}"
    desc = f"  → {ann.description}"
    tag_line = f"  {badges}" if badges else ""
    parts = [header, desc]
    if tag_line:
        parts.append(tag_line)
    return "\n".join(parts)


def render_annotation_report(
    annotations: List[AnnotatedEntry],
    use_color: bool = True,
) -> str:
    if not annotations:
        return "No entries to annotate."
    separator = "\n" + "-" * 60 + "\n"
    blocks = [format_annotation(a, use_color) for a in annotations]
    header = "=" * 60 + "\n  Crontab Annotation Report\n" + "=" * 60
    return header + "\n" + separator.join(blocks) + "\n"
