"""Tests for cronmap.lint — crontab linting and issue reporting."""

import pytest
from cronmap.lint import LintIssue, lint_crontab, format_lint_report
from cronmap.parser import CronEntry


def make_entry(
    minute="0",
    hour="9",
    dom="*",
    month="*",
    dow="1",
    command="/usr/bin/backup",
    raw="0 9 * * 1 /usr/bin/backup",
    line_number=1,
):
    return CronEntry(
        minute=minute,
        hour=hour,
        dom=dom,
        month=month,
        dow=dow,
        command=command,
        raw=raw,
        line_number=line_number,
    )


# ---------------------------------------------------------------------------
# LintIssue
# ---------------------------------------------------------------------------

class TestLintIssue:
    def test_repr_contains_level_and_message(self):
        issue = LintIssue(level="warn", message="suspicious schedule", line_number=3)
        r = repr(issue)
        assert "warn" in r
        assert "suspicious schedule" in r

    def test_str_contains_line_number(self):
        issue = LintIssue(level="error", message="invalid field", line_number=7)
        assert "7" in str(issue)

    def test_level_normalised_to_lowercase(self):
        issue = LintIssue(level="WARN", message="test", line_number=1)
        assert issue.level == "warn"


# ---------------------------------------------------------------------------
# lint_crontab
# ---------------------------------------------------------------------------

class TestLintCrontab:
    def test_clean_crontab_returns_no_issues(self):
        entries = [
            make_entry(minute="0", hour="6", line_number=1),
            make_entry(minute="30", hour="12", command="/usr/bin/report", line_number=2),
        ]
        issues = lint_crontab(entries)
        assert issues == []

    def test_duplicate_entries_flagged(self):
        entry = make_entry(line_number=1)
        duplicate = make_entry(line_number=2)
        issues = lint_crontab([entry, duplicate])
        assert any("duplicate" in i.message.lower() for i in issues)

    def test_wildcard_dom_and_dow_together_flagged(self):
        # Both dom and dow set to non-wildcard is ambiguous in some cron impls
        entry = make_entry(dom="15", dow="1", line_number=5)
        issues = lint_crontab([entry])
        assert any("dom" in i.message.lower() or "dow" in i.message.lower() for i in issues)

    def test_every_minute_schedule_flagged(self):
        entry = make_entry(minute="*", hour="*", dom="*", month="*", dow="*",
                           command="/bin/ping", line_number=3)
        issues = lint_crontab([entry])
        assert any("every minute" in i.message.lower() or "frequent" in i.message.lower()
                   for i in issues)

    def test_empty_command_flagged(self):
        entry = make_entry(command="", line_number=4)
        issues = lint_crontab([entry])
        assert any("command" in i.message.lower() for i in issues)

    def test_issue_line_numbers_match_entry(self):
        entry = make_entry(command="", line_number=99)
        issues = lint_crontab([entry])
        assert all(i.line_number == 99 for i in issues)

    def test_multiple_issues_can_be_raised_for_one_entry(self):
        # every-minute AND empty command — should produce at least 2 issues
        entry = make_entry(minute="*", hour="*", dom="*", month="*", dow="*",
                           command="", line_number=1)
        issues = lint_crontab([entry])
        assert len(issues) >= 2

    def test_empty_list_returns_no_issues(self):
        assert lint_crontab([]) == []


# ---------------------------------------------------------------------------
# format_lint_report
# ---------------------------------------------------------------------------

class TestFormatLintReport:
    def test_no_issues_returns_clean_message(self):
        report = format_lint_report([])
        assert "no issues" in report.lower() or "clean" in report.lower()

    def test_report_contains_issue_messages(self):
        issues = [
            LintIssue(level="warn", message="suspicious schedule", line_number=2),
            LintIssue(level="error", message="empty command", line_number=5),
        ]
        report = format_lint_report(issues)
        assert "suspicious schedule" in report
        assert "empty command" in report

    def test_report_contains_line_numbers(self):
        issues = [LintIssue(level="warn", message="test issue", line_number=42)]
        report = format_lint_report(issues)
        assert "42" in report

    def test_report_is_string(self):
        issues = [LintIssue(level="warn", message="x", line_number=1)]
        assert isinstance(format_lint_report(issues), str)

    def test_report_separates_multiple_issues(self):
        issues = [
            LintIssue(level="warn", message="issue one", line_number=1),
            LintIssue(level="warn", message="issue two", line_number=2),
        ]
        report = format_lint_report(issues)
        assert "issue one" in report
        assert "issue two" in report
        # They should appear on separate lines
        assert report.index("issue one") != report.index("issue two")
