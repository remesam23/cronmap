"""Integration tests: parser -> conflict detection -> report."""
from __future__ import annotations

import textwrap

from cronmap.conflict import find_conflicts, format_conflict_report
from cronmap.parser import parse_crontab

CRONTAB = textwrap.dedent("""\
    # daily backup jobs
    0 2 * * * /usr/bin/backup_db
    0 2 * * * /usr/bin/backup_files
    # different hour — no conflict
    30 4 * * * /usr/bin/report
    # overlaps with backup via wildcard hour
    0 * * * * /usr/bin/heartbeat
""")


def test_integration_finds_backup_conflict():
    entries = parse_crontab(CRONTAB)
    conflicts = find_conflicts(entries)
    commands = {(c.entry_a.command, c.entry_b.command) for c in conflicts}
    flat = {cmd for pair in commands for cmd in pair}
    assert "/usr/bin/backup_db" in flat
    assert "/usr/bin/backup_files" in flat


def test_integration_heartbeat_conflicts_with_backup():
    entries = parse_crontab(CRONTAB)
    conflicts = find_conflicts(entries)
    heartbeat_conflicts = [
        c for c in conflicts
        if "/usr/bin/heartbeat" in (c.entry_a.command, c.entry_b.command)
    ]
    assert len(heartbeat_conflicts) >= 1


def test_integration_report_lists_all_conflicts():
    entries = parse_crontab(CRONTAB)
    conflicts = find_conflicts(entries)
    report = format_conflict_report(conflicts)
    assert str(len(conflicts)) in report


def test_integration_no_conflict_different_hours():
    text = "0 6 * * * /bin/morning\n0 18 * * * /bin/evening\n"
    entries = parse_crontab(text)
    assert find_conflicts(entries) == []


def test_integration_step_fields_overlap():
    # */2 on hours 0-23 includes hour 4; */3 includes 0,3,6... not 4 -> no overlap on hours
    text = "0 */2 * * * /bin/even_hours\n0 4 * * * /bin/at_four\n"
    entries = parse_crontab(text)
    conflicts = find_conflicts(entries)
    # hour 4 is in */2 (0,2,4,...) so they DO conflict
    assert len(conflicts) == 1
