"""Tests for cronmap.annotation_report."""

from cronmap.parser import CronEntry
from cronmap.annotator import annotate_entry, annotate_entries
from cronmap.annotation_report import (
    format_annotation,
    render_annotation_report,
    _tag_badge,
)


def make_entry(minute="0", hour="2", dom="*", month="*", dow="*", cmd="/bin/run", line=1):
    return CronEntry(
        minute=minute, hour=hour, dom=dom, month=month, dow=dow,
        command=cmd, line_number=line,
    )


def test_tag_badge_no_color():
    badge = _tag_badge("frequent", use_color=False)
    assert badge == "[frequent]"


def test_tag_badge_with_color_contains_tag():
    badge = _tag_badge("frequent", use_color=True)
    assert "frequent" in badge
    assert "\033[" in badge


def test_format_annotation_contains_command():
    ann = annotate_entry(make_entry(cmd="/usr/bin/cleanup"))
    result = format_annotation(ann, use_color=False)
    assert "/usr/bin/cleanup" in result


def test_format_annotation_contains_description_arrow():
    ann = annotate_entry(make_entry())
    result = format_annotation(ann, use_color=False)
    assert "→" in result


def test_format_annotation_contains_line_number():
    ann = annotate_entry(make_entry(line=42))
    result = format_annotation(ann, use_color=False)
    assert "42" in result


def test_format_annotation_shows_tags():
    ann = annotate_entry(make_entry(minute="*/10"))
    result = format_annotation(ann, use_color=False)
    assert "[frequent]" in result


def test_render_empty_list():
    result = render_annotation_report([], use_color=False)
    assert "No entries" in result


def test_render_report_contains_header():
    entries = [make_entry()]
    annotations = annotate_entries(entries)
    result = render_annotation_report(annotations, use_color=False)
    assert "Annotation Report" in result


def test_render_report_all_commands_present():
    entries = [make_entry(cmd=f"/bin/job{i}", line=i + 1) for i in range(3)]
    annotations = annotate_entries(entries)
    result = render_annotation_report(annotations, use_color=False)
    for i in range(3):
        assert f"/bin/job{i}" in result
