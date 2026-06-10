#!/usr/bin/env python3
"""
things.py — Things 3 read/write CLI for the /things skill.

Read: sqlite, read-only. Outputs JSON to stdout.
Write: macOS URL scheme via `open` (add-only in v1; no update/delete).

The skill (SKILL.md) is responsible for cwd-based tag inference and
synthesis. This script is a dumb data layer.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

THINGS_DB = Path(
    "/Users/dad/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/"
    "ThingsData-OQ3NJ/Things Database.thingsdatabase/main.sqlite"
)

BASE_TASK_FIELDS = """
    SELECT uuid, title, notes, start, startBucket, startDate, deadline,
           creationDate, userModificationDate, project, area
    FROM TMTask
    WHERE trashed=0 AND status=0 AND type=0
"""


def connect() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{THINGS_DB}?mode=ro&immutable=1", uri=True)


def decode_things_date(v: int | None) -> str | None:
    """Things 3 packs dates as (year<<16)|(month<<12)|(day<<7)|flags."""
    if not v:
        return None
    year = v >> 16
    month = (v >> 12) & 0xF
    day = (v >> 7) & 0x1F
    if not year or not month or not day:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def encode_today_int() -> int:
    today = date.today()
    return (today.year << 16) | (today.month << 12) | (today.day << 7)


def epoch_to_iso(v: float | None) -> str | None:
    if v is None:
        return None
    try:
        return datetime.fromtimestamp(v).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return None


def age_days(creation: float | None) -> float | None:
    if creation is None:
        return None
    return round((time.time() - creation) / 86400, 1)


def task_tags(conn: sqlite3.Connection, uuid: str) -> list[str]:
    cur = conn.execute(
        "SELECT t.title FROM TMTaskTag tt JOIN TMTag t ON tt.tags = t.uuid "
        "WHERE tt.tasks = ? ORDER BY t.title",
        (uuid,),
    )
    return [r[0] for r in cur.fetchall()]


def project_title(conn: sqlite3.Connection, uuid: str | None) -> str | None:
    """Return the project's title only if the project itself is live.
    A task can reference a trashed project — treat that as orphaned (None)."""
    if not uuid:
        return None
    cur = conn.execute(
        "SELECT title FROM TMTask WHERE uuid = ? AND type = 1 AND trashed = 0",
        (uuid,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def area_title(conn: sqlite3.Connection, uuid: str | None) -> str | None:
    if not uuid:
        return None
    cur = conn.execute("SELECT title FROM TMArea WHERE uuid = ?", (uuid,))
    row = cur.fetchone()
    return row[0] if row else None


START_LABELS = {0: "inbox", 1: "anytime", 2: "scheduled"}
BUCKET_LABELS = {0: "today", 1: "anytime", 2: "evening"}

# Status codes in TMTask.
STATUS_OPEN = 0
STATUS_CANCELLED = 2
STATUS_COMPLETED = 3


def classify_state(
    status: int,
    trashed: int,
    start: int,
    start_bucket: int,
    start_date_int: int | None,
    today_int: int,
) -> tuple[str, str | None]:
    """Return (state, scheduled_date_iso).

    state ∈ {done, killed, today, evening, anytime, someday, scheduled_future, inbox}

    scheduled_date_iso is set only for `scheduled_future`.
    """
    if trashed:
        return ("killed", None)
    if status == STATUS_COMPLETED:
        return ("done", None)
    if status == STATUS_CANCELLED:
        return ("killed", None)
    # status == open
    # Things schema: start=0 Inbox, start=1 Anytime, start=2 Scheduled (Today/Future/Someday distinguished by startDate).
    if start == 0:
        return ("inbox", None)
    if start == 1:
        if start_bucket == 2:
            return ("evening", None)
        return ("anytime", None)
    if start == 2:
        if start_date_int and start_date_int <= today_int:
            return ("evening" if start_bucket == 2 else "today", None)
        if start_date_int and start_date_int > today_int:
            return ("scheduled_future", decode_things_date(start_date_int))
        return ("someday", None)
    return ("anytime", None)


def task_row_to_dict(conn: sqlite3.Connection, row) -> dict:
    uuid, title, notes, start, bucket, sd, dl, cd, umd, proj, area = row
    return {
        "uuid": uuid,
        "title": title,
        "notes": notes if notes else None,
        "start": START_LABELS.get(start, "?"),
        "bucket": BUCKET_LABELS.get(bucket),
        "scheduledDate": decode_things_date(sd),
        "deadline": decode_things_date(dl),
        "createdDate": epoch_to_iso(cd),
        "ageDays": age_days(cd),
        "modifiedDate": epoch_to_iso(umd),
        "project": project_title(conn, proj),
        "area": area_title(conn, area),
        "tags": task_tags(conn, uuid),
    }


def emit(payload) -> None:
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def query_and_emit(query: str, params=(), label: str | None = None, **extra) -> None:
    conn = connect()
    rows = conn.execute(query, params).fetchall()
    items = [task_row_to_dict(conn, r) for r in rows]
    payload = {"count": len(items), "items": items, **extra}
    if label is not None:
        payload["label"] = label
    emit(payload)


# --- read commands ----------------------------------------------------------


def cmd_today(args) -> None:
    query_and_emit(
        BASE_TASK_FIELDS
        + " AND start = 2 AND startDate > 0 AND startDate <= ?"
        + " ORDER BY startBucket, title",
        (encode_today_int(),),
    )


def cmd_inbox(args) -> None:
    query_and_emit(
        BASE_TASK_FIELDS + " AND start = 0 ORDER BY creationDate DESC"
    )


def cmd_anytime(args) -> None:
    query_and_emit(
        BASE_TASK_FIELDS + " AND start = 1 ORDER BY userModificationDate DESC"
    )


def cmd_someday(args) -> None:
    query_and_emit(
        BASE_TASK_FIELDS
        + " AND start = 2 AND (startDate IS NULL OR startDate = 0)"
        + " ORDER BY title"
    )


def cmd_overdue(args) -> None:
    query_and_emit(
        BASE_TASK_FIELDS + " AND deadline > 0 AND deadline < ? ORDER BY deadline",
        (encode_today_int(),),
    )


def cmd_recent(args) -> None:
    cutoff = time.time() - args.days * 86400
    query_and_emit(
        BASE_TASK_FIELDS + " AND creationDate > ? ORDER BY creationDate DESC",
        (cutoff,),
        days=args.days,
    )


def cmd_tag(args) -> None:
    conn = connect()
    cur = conn.execute("SELECT uuid FROM TMTag WHERE title = ?", (args.name,))
    row = cur.fetchone()
    if not row:
        emit({"error": f"no tag named {args.name!r}", "count": 0, "items": []})
        return
    tag_uuid = row[0]
    query_and_emit(
        BASE_TASK_FIELDS
        + " AND uuid IN (SELECT tasks FROM TMTaskTag WHERE tags = ?)"
        " ORDER BY creationDate DESC",
        (tag_uuid,),
        tag=args.name,
    )


def cmd_project(args) -> None:
    conn = connect()
    cur = conn.execute(
        "SELECT uuid FROM TMTask WHERE type = 1 AND status = 0 AND trashed = 0 AND title = ?",
        (args.name,),
    )
    row = cur.fetchone()
    if not row:
        emit({"error": f"no Things project named {args.name!r}", "count": 0, "items": []})
        return
    query_and_emit(
        BASE_TASK_FIELDS + " AND project = ? ORDER BY creationDate DESC",
        (row[0],),
        project=args.name,
    )


def cmd_search(args) -> None:
    """Fuzzy match across open tasks (title + notes), all buckets."""
    pattern = f"%{args.query}%"
    query_and_emit(
        BASE_TASK_FIELDS
        + " AND (title LIKE ? OR notes LIKE ?) ORDER BY userModificationDate DESC",
        (pattern, pattern),
        searched_for=args.query,
    )


def cmd_tags(args) -> None:
    conn = connect()
    rows = conn.execute("SELECT title FROM TMTag ORDER BY title").fetchall()
    emit([r[0] for r in rows])


def cmd_projects(args) -> None:
    conn = connect()
    rows = conn.execute(
        "SELECT title FROM TMTask WHERE type = 1 AND status = 0 AND trashed = 0 ORDER BY title"
    ).fetchall()
    emit([r[0] for r in rows])


# --- reconcile-oriented read ------------------------------------------------


def cmd_query(args) -> None:
    """Look up tasks by UUID (any status). Used by reconcile.

    Output: a JSON object keyed by UUID. Missing/never-existed UUIDs map to
    {"found": false}. Found UUIDs include classified state for the reconcile
    state machine.
    """
    uuids: list[str] = list(args.uuid or [])
    if args.uuids_file:
        with open(args.uuids_file) as f:
            uuids.extend(line.strip() for line in f if line.strip())
    if not uuids:
        emit({"error": "no uuids provided (use --uuid or --uuids-file)"})
        return

    conn = connect()
    today_int = encode_today_int()
    placeholders = ",".join("?" * len(uuids))
    rows = conn.execute(
        f"SELECT uuid, title, status, trashed, start, startBucket, startDate, "
        f"stopDate FROM TMTask WHERE type=0 AND uuid IN ({placeholders})",
        uuids,
    ).fetchall()

    by_uuid: dict[str, dict] = {}
    for uuid, title, status, trashed, start, bucket, sd, stop in rows:
        state, scheduled = classify_state(status, trashed, start, bucket, sd, today_int)
        by_uuid[uuid] = {
            "found": True,
            "title": title,
            "status": {STATUS_OPEN: "open", STATUS_CANCELLED: "cancelled",
                       STATUS_COMPLETED: "completed"}.get(status, f"?({status})"),
            "trashed": bool(trashed),
            "state": state,
            "scheduled_date": scheduled,
            "stop_date": epoch_to_iso(stop),
            "tags": task_tags(conn, uuid),
        }
    for u in uuids:
        if u not in by_uuid:
            by_uuid[u] = {"found": False}

    emit(by_uuid)


# --- write commands ---------------------------------------------------------


def applescript_quote(s: str) -> str:
    """Escape a Python string for safe inline use as an AppleScript literal."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def run_osascript(script: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["osascript", "-"], input=script, capture_output=True, text=True
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def cmd_update(args) -> None:
    """Update a task in place via AppleScript. Supports title replace,
    notes append, and tag replace. UUIDs come from the read commands."""
    ops: list[str] = []
    if args.title:
        ops.append(f"set name of t to {applescript_quote(args.title)}")
    if args.add_notes:
        sep = applescript_quote("\n\n")
        ops.append(
            f"set notes of t to ((notes of t) & {sep} & {applescript_quote(args.add_notes)})"
        )
    if args.notes is not None:
        ops.append(f"set notes of t to {applescript_quote(args.notes)}")
    if args.tags is not None:
        ops.append(f"set tag names of t to {applescript_quote(', '.join(args.tags))}")

    if not ops:
        emit({"error": "no update operations specified", "id": args.id})
        return

    inner = "\n".join("  " + op for op in ops)
    script = (
        'tell application "Things3"\n'
        f"  set t to to do id {applescript_quote(args.id)}\n"
        f"{inner}\n"
        "end tell\n"
    )
    rc, _stdout, stderr = run_osascript(script)
    if rc != 0:
        emit({"error": stderr or "osascript failed", "id": args.id})
    else:
        emit(
            {
                "ok": True,
                "id": args.id,
                "title_set": args.title is not None,
                "notes_appended": args.add_notes is not None,
                "notes_replaced": args.notes is not None,
                "tags_replaced": args.tags is not None,
            }
        )


_LIST_BY_WHEN = {
    "today": "Today",
    "anytime": "Anytime",
    "someday": "Someday",
    "inbox": "Inbox",
}


def _applescript_when_clause(when: str | None) -> str:
    """Return the AppleScript fragment that places the new task `t` correctly."""
    if when is None or when == "anytime":
        return 'move t to list "Anytime"'
    if when in _LIST_BY_WHEN:
        return f'move t to list {applescript_quote(_LIST_BY_WHEN[when])}'
    if when == "tomorrow":
        return "schedule t for (current date) + (1 * days)"
    # ISO date — schedule for that calendar date
    try:
        y, m, d = (int(p) for p in when.split("-"))
    except (ValueError, AttributeError):
        raise SystemExit(f"unrecognized --when value: {when!r}")
    # Build an AppleScript date object from the ISO components.
    return (
        "set theDate to (current date)\n"
        f"  set year of theDate to {y}\n"
        f"  set month of theDate to {m}\n"
        f"  set day of theDate to {d}\n"
        "  set time of theDate to 0\n"
        "  schedule t for theDate"
    )


def cmd_add(args) -> None:
    # Build the AppleScript: create the task, set tags, place it, return UUID.
    props_parts = [f"name:{applescript_quote(args.title)}"]
    if args.notes:
        props_parts.append(f"notes:{applescript_quote(args.notes)}")
    properties = "{" + ", ".join(props_parts) + "}"

    tag_clause = ""
    if args.tags:
        tag_clause = (
            f"  set tag names of t to {applescript_quote(', '.join(args.tags))}\n"
        )

    list_clause = ""
    if args.list:
        list_clause = (
            f"  move t to project {applescript_quote(args.list)}\n"
        )

    when_clause = f"  {_applescript_when_clause(args.when)}\n"

    deadline_clause = ""
    if args.deadline:
        try:
            y, m, d = (int(p) for p in args.deadline.split("-"))
        except ValueError:
            raise SystemExit(f"unrecognized --deadline value: {args.deadline!r}")
        deadline_clause = (
            "  set dlDate to (current date)\n"
            f"  set year of dlDate to {y}\n"
            f"  set month of dlDate to {m}\n"
            f"  set day of dlDate to {d}\n"
            "  set time of dlDate to 0\n"
            "  set due date of t to dlDate\n"
        )

    script = (
        'tell application "Things3"\n'
        f"  set t to make new to do with properties {properties}\n"
        f"{tag_clause}{list_clause}{when_clause}{deadline_clause}"
        "  return id of t\n"
        "end tell\n"
    )

    if args.dry_run:
        emit({"dry_run": True, "applescript": script, "title": args.title})
        return

    rc, stdout, stderr = run_osascript(script)
    if rc != 0 or not stdout:
        emit({"error": stderr or "osascript failed", "title": args.title})
        raise SystemExit(1)

    uuid = stdout.strip()
    emit(
        {
            "ok": True,
            "uuid": uuid,
            "title": args.title,
            "tags": args.tags or [],
            "list": args.list,
            "when": args.when,
            "deadline": args.deadline,
        }
    )


# --- argparse ---------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="things.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name, fn in [
        ("today", cmd_today),
        ("inbox", cmd_inbox),
        ("anytime", cmd_anytime),
        ("someday", cmd_someday),
        ("overdue", cmd_overdue),
        ("tags", cmd_tags),
        ("projects", cmd_projects),
    ]:
        sub.add_parser(name).set_defaults(func=fn)

    sp = sub.add_parser("tag")
    sp.add_argument("name")
    sp.set_defaults(func=cmd_tag)

    sp = sub.add_parser("project")
    sp.add_argument("name")
    sp.set_defaults(func=cmd_project)

    sp = sub.add_parser("recent")
    sp.add_argument("--days", type=int, default=7)
    sp.set_defaults(func=cmd_recent)

    sp = sub.add_parser("search", help="Fuzzy match across open tasks")
    sp.add_argument("query")
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("update", help="Update a task in place via AppleScript")
    sp.add_argument("--id", required=True, help="Task UUID")
    sp.add_argument("--title", default=None, help="Replace title")
    sp.add_argument("--add-notes", dest="add_notes", default=None, help="Append to notes")
    sp.add_argument("--notes", default=None, help="Replace notes")
    sp.add_argument("--tag", action="append", dest="tags", default=None, help="Replace tag list (repeatable)")
    sp.set_defaults(func=cmd_update)

    sp = sub.add_parser("add")
    sp.add_argument("--title", required=True)
    sp.add_argument("--notes", default=None)
    sp.add_argument("--tag", action="append", dest="tags", default=None)
    sp.add_argument("--list", default=None, help="Things 3 project name")
    sp.add_argument("--when", default=None, help="today|tomorrow|anytime|someday|inbox|YYYY-MM-DD")
    sp.add_argument("--deadline", default=None, help="YYYY-MM-DD")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("query", help="Look up tasks by UUID (any status) for reconcile")
    sp.add_argument("--uuid", action="append", help="repeatable; can also use --uuids-file")
    sp.add_argument("--uuids-file", help="path to a file with one UUID per line")
    sp.set_defaults(func=cmd_query)

    return p


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
