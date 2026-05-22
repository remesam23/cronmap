"""Tests for cronmap.highlighter module."""

import pytest
from cronmap.highlighter import (
    highlight_cron_expression,
    highlight_field_value,
    format_legend,
    strip_ansi,
    FIELD_NAMES,
    RESET,
)


SAMPLE_ENTRY = "30 8 * * 1 /usr/bin/backup"
SIMPLE_ENTRY = "0 12 * * * echo hello"


def test_strip_ansi_removes_codes():
    colored = "\033[32mhello\033[0m"
    assert strip_ansi(colored) == "hello"


def test_strip_ansi_no_codes():
    plain = "no color here"
    assert strip_ansi(plain) == plain


def test_highlight_cron_expression_no_color():
    result = highlight_cron_expression(SAMPLE_ENTRY, color=False)
    assert result == SAMPLE_ENTRY


def test_highlight_cron_expression_with_color_contains_fields():
    result = highlight_cron_expression(SAMPLE_ENTRY, color=True)
    plain = strip_ansi(result)
    assert "30" in plain
    assert "8" in plain
    assert "/usr/bin/backup" in plain


def test_highlight_cron_expression_contains_reset_codes():
    result = highlight_cron_expression(SAMPLE_ENTRY, color=True)
    assert RESET in result


def test_highlight_cron_expression_command_preserved():
    result = highlight_cron_expression(SIMPLE_ENTRY, color=True)
    plain = strip_ansi(result)
    assert "echo hello" in plain


def test_highlight_cron_expression_short_input_unchanged():
    short = "* * *"
    result = highlight_cron_expression(short, color=True)
    assert result == short


def test_highlight_field_value_no_color():
    result = highlight_field_value("30", field_index=0, color=False)
    assert result == "30"


def test_highlight_field_value_with_color():
    result = highlight_field_value("30", field_index=0, color=True)
    plain = strip_ansi(result)
    assert plain == "30"
    assert RESET in result


def test_highlight_field_value_out_of_range_index():
    result = highlight_field_value("*", field_index=99, color=True)
    assert result == "*"


def test_format_legend_no_color_contains_all_fields():
    legend = format_legend(color=False)
    for name in FIELD_NAMES:
        assert name in legend


def test_format_legend_with_color_plain_contains_all_fields():
    legend = format_legend(color=True)
    plain = strip_ansi(legend)
    for name in FIELD_NAMES:
        assert name in plain


def test_format_legend_with_color_has_reset():
    legend = format_legend(color=True)
    assert RESET in legend
