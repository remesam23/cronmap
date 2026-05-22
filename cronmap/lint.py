"""Lint a crontab text block and report all validation issues."""

from typing import List, NamedTuple
from cronmap.validator import validate_cron_expression, ValidationError


class LintIssue(NamedTuple):
    line_number: int
    raw_line: str
    errors: List[ValidationError]


def lint_crontab(text: str) -> List[LintIssue]:
    """Parse and validate each non-comment, non-empty line of a crontab.

    Returns a list of LintIssue for every line that has validation errors.
    """
    issues: List[LintIssue] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Extract the cron expression (first 5 tokens) ignoring command tail
        tokens = line.split()
        if len(tokens) < 5:
            issues.append(
                LintIssue(
                    line_number=lineno,
                    raw_line=raw,
                    errors=[
                        type(
                            "ValidationError",
                            (),
                            {
                                "field": "expression",
                                "value": line,
                                "message": "Too few fields (need at least 5)",
                                "__str__": lambda self: f"[expression] '{self.value}': {self.message}",
                            },
                        )()
                    ],
                )
            )
            continue
        expression = " ".join(tokens[:5])
        valid, errors = validate_cron_expression(expression)
        if not valid:
            issues.append(LintIssue(line_number=lineno, raw_line=raw, errors=errors))
    return issues


def format_lint_report(issues: List[LintIssue]) -> str:
    """Render lint issues as a human-readable string."""
    if not issues:
        return "No issues found."
    lines = []
    for issue in issues:
        lines.append(f"Line {issue.line_number}: {issue.raw_line.strip()}")
        for err in issue.errors:
            lines.append(f"  - {err}")
    return "\n".join(lines)
