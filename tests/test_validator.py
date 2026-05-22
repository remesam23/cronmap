"""Tests for cronmap.validator module."""

import pytest
from cronmap.validator import (
    validate_field,
    validate_cron_expression,
    ValidationError,
)


# --- validate_field ---

def test_wildcard_is_always_valid():
    errors = validate_field("minute", "*")
    assert errors == []


def test_valid_single_minute():
    assert validate_field("minute", "30") == []


def test_invalid_minute_too_high():
    errors = validate_field("minute", "60")
    assert len(errors) == 1
    assert "out of range" in errors[0].message


def test_valid_hour_range():
    assert validate_field("hour", "8-17") == []


def test_invalid_hour_range_reversed():
    errors = validate_field("hour", "17-8")
    assert any("start > end" in e.message for e in errors)


def test_valid_step_expression():
    assert validate_field("minute", "*/15") == []


def test_invalid_step_zero():
    errors = validate_field("minute", "*/0")
    assert any("step" in e.message for e in errors)


def test_valid_list():
    assert validate_field("dow", "1,3,5") == []


def test_invalid_list_contains_out_of_range():
    errors = validate_field("dow", "1,3,8")
    assert len(errors) == 1


def test_valid_dom_boundary():
    assert validate_field("dom", "1") == []
    assert validate_field("dom", "31") == []


def test_invalid_dom_zero():
    errors = validate_field("dom", "0")
    assert len(errors) == 1


def test_invalid_range_non_numeric():
    errors = validate_field("hour", "a-b")
    assert len(errors) >= 1


# --- validate_cron_expression ---

def test_valid_full_expression():
    valid, errors = validate_cron_expression("0 9 * * 1-5")
    assert valid is True
    assert errors == []


def test_invalid_too_few_fields():
    valid, errors = validate_cron_expression("0 9 *")
    assert valid is False
    assert len(errors) == 1


def test_invalid_expression_bad_minute():
    valid, errors = validate_cron_expression("99 9 * * *")
    assert valid is False
    assert errors[0].field == "minute"


def test_valid_expression_with_command_ignored():
    valid, errors = validate_cron_expression("30 6 * * 0 /usr/bin/backup.sh")
    assert valid is True


def test_multiple_errors_reported():
    valid, errors = validate_cron_expression("99 25 * * *")
    assert valid is False
    assert len(errors) == 2
