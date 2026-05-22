"""Validates crontab entries and fields for correctness."""

from typing import List, Tuple

FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "dom": (1, 31),
    "month": (1, 12),
    "dow": (0, 7),
}


class ValidationError:
    def __init__(self, field: str, value: str, message: str):
        self.field = field
        self.value = value
        self.message = message

    def __repr__(self) -> str:
        return f"ValidationError(field={self.field!r}, message={self.message!r})"

    def __str__(self) -> str:
        return f"[{self.field}] '{self.value}': {self.message}"


def _validate_single_value(value: str, low: int, high: int) -> bool:
    """Return True if value is an integer within [low, high]."""
    try:
        n = int(value)
        return low <= n <= high
    except ValueError:
        return False


def validate_field(name: str, field: str) -> List[ValidationError]:
    """Validate a single cron field string. Returns list of errors."""
    errors: List[ValidationError] = []
    low, high = FIELD_RANGES.get(name, (0, 59))

    if field == "*":
        return errors

    parts = field.split(",")
    for part in parts:
        if "/" in part:
            base, step = part.split("/", 1)
            if not step.isdigit() or int(step) < 1:
                errors.append(ValidationError(name, field, f"Invalid step value: '{step}'"))
            if base != "*" and "-" not in base:
                if not _validate_single_value(base, low, high):
                    errors.append(ValidationError(name, field, f"Value '{base}' out of range [{low}-{high}]"))
        elif "-" in part:
            bounds = part.split("-", 1)
            if len(bounds) != 2 or not bounds[0].isdigit() or not bounds[1].isdigit():
                errors.append(ValidationError(name, field, f"Invalid range: '{part}'"))
            else:
                start, end = int(bounds[0]), int(bounds[1])
                if not (low <= start <= high) or not (low <= end <= high):
                    errors.append(ValidationError(name, field, f"Range '{part}' out of bounds [{low}-{high}]"))
                if start > end:
                    errors.append(ValidationError(name, field, f"Range start > end in '{part}'"))
        else:
            if not _validate_single_value(part, low, high):
                errors.append(ValidationError(name, field, f"Value '{part}' out of range [{low}-{high}]"))

    return errors


def validate_cron_expression(expression: str) -> Tuple[bool, List[ValidationError]]:
    """Validate a full 5-field cron expression. Returns (is_valid, errors)."""
    parts = expression.strip().split()
    if len(parts) < 5:
        err = ValidationError("expression", expression, "Expected at least 5 fields")
        return False, [err]

    field_names = ["minute", "hour", "dom", "month", "dow"]
    all_errors: List[ValidationError] = []
    for name, value in zip(field_names, parts[:5]):
        all_errors.extend(validate_field(name, value))

    return len(all_errors) == 0, all_errors
