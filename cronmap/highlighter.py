"""Syntax highlighter for cron expressions in terminal output."""

from typing import Optional

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
DIM = "\033[2m"

# Field labels in order
FIELD_NAMES = ["minute", "hour", "day-of-month", "month", "day-of-week"]

FIELD_COLORS = [
    CYAN,     # minute
    YELLOW,   # hour
    GREEN,    # day-of-month
    MAGENTA,  # month
    BLUE,     # day-of-week
]


def highlight_cron_expression(expression: str, color: bool = True) -> str:
    """Colorize each field of a cron expression with a distinct color."""
    if not color:
        return expression

    parts = expression.split()
    if len(parts) < 5:
        return expression

    fields = parts[:5]
    command_parts = parts[5:]

    colored_fields = [
        f"{FIELD_COLORS[i]}{field}{RESET}"
        for i, field in enumerate(fields)
    ]

    command_str = " ".join(command_parts)
    colored_command = f"{BOLD}{WHITE}{command_str}{RESET}" if command_str else ""

    result = " ".join(colored_fields)
    if colored_command:
        result += f"  {colored_command}"
    return result


def highlight_field_value(value: str, field_index: int, color: bool = True) -> str:
    """Colorize a single field value based on its position."""
    if not color or field_index >= len(FIELD_COLORS):
        return value
    return f"{FIELD_COLORS[field_index]}{value}{RESET}"


def format_legend(color: bool = True) -> str:
    """Return a legend string explaining the color coding."""
    entries = []
    for i, name in enumerate(FIELD_NAMES):
        if color:
            entries.append(f"{FIELD_COLORS[i]}{name}{RESET}")
        else:
            entries.append(name)
    return "  ".join(entries)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from a string."""
    import re
    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    return ansi_escape.sub("", text)
