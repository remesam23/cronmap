"""Tests for cronmap.overlap."""
import pytest

from cronmap.parser import CronEntry
from cronmap.overlap import (
    OverlapResult,
    _expand,
    _intersect,
    find_overlap,
    detect_overlaps,
    format_overlap_report,
)


def make_entry(
    minutes=None,
    hours=None,
    days_of_week=None,
    command="cmd",
) -> CronEntry:
    return CronEntry(
        minutes=minutes or [],
        hours=hours or [],
        days_of_month=[],
        months=[],
        days_of_week=days_of_week or [],
        command=command,
        raw="* * * * * " + command,
    )


def test_expand_wildcard_minutes():
    result = _expand([], range(60))
    assert len(result) == 60
    assert result[0] == 0 and result[-1] == 59


def test_expand_specific_values():
    assert _expand([5, 10, 15], range(60)) == [5, 10, 15]


def test_intersect_common_values():
    assert _intersect([1, 2, 3], [2, 3, 4]) == [2, 3]


def test_intersect_no_common():
    assert _intersect([1, 2], [3, 4]) == []


def test_find_overlap_identical_wildcards():
    a = make_entry(command="a")
    b = make_entry(command="b")
    result = find_overlap(a, b)
    assert bool(result) is True
    assert len(result.shared_minutes) == 60
    assert len(result.shared_hours) == 24
    assert len(result.shared_days) == 7


def test_find_overlap_different_hours():
    a = make_entry(hours=[6], command="a")
    b = make_entry(hours=[12], command="b")
    result = find_overlap(a, b)
    assert bool(result) is False
    assert result.shared_hours == []


def test_find_overlap_partial_minute_overlap():
    a = make_entry(minutes=[0, 15, 30], hours=[9], command="a")
    b = make_entry(minutes=[30, 45], hours=[9], command="b")
    result = find_overlap(a, b)
    assert bool(result) is True
    assert result.shared_minutes == [30]


def test_find_overlap_different_days():
    a = make_entry(days_of_week=[1], command="a")  # Monday
    b = make_entry(days_of_week=[3], command="b")  # Wednesday
    result = find_overlap(a, b)
    assert bool(result) is False


def test_detect_overlaps_returns_conflicting_pairs():
    a = make_entry(hours=[8], command="a")
    b = make_entry(hours=[8], command="b")
    c = make_entry(hours=[10], command="c")
    results = detect_overlaps([a, b, c])
    assert len(results) == 1
    assert results[0].entry_a.command == "a"
    assert results[0].entry_b.command == "b"


def test_detect_overlaps_empty_list():
    assert detect_overlaps([]) == []


def test_detect_overlaps_single_entry():
    a = make_entry(command="only")
    assert detect_overlaps([a]) == []


def test_format_overlap_report_no_overlaps():
    assert format_overlap_report([]) == "No overlapping entries detected."


def test_format_overlap_report_contains_commands():
    a = make_entry(hours=[9], command="backup")
    b = make_entry(hours=[9], command="sync")
    overlaps = detect_overlaps([a, b])
    report = format_overlap_report(overlaps)
    assert "backup" in report
    assert "sync" in report


def test_format_overlap_report_color_flag():
    a = make_entry(command="x")
    b = make_entry(command="y")
    overlaps = detect_overlaps([a, b])
    colored = format_overlap_report(overlaps, color=True)
    assert "\033[" in colored


def test_overlap_result_repr():
    a = make_entry(hours=[6], command="foo")
    b = make_entry(hours=[6], command="bar")
    r = find_overlap(a, b)
    assert "foo" in repr(r)
    assert "bar" in repr(r)
