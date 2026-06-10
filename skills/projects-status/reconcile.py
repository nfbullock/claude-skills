#!/usr/bin/env python3
"""
reconcile.py — bring projects/next-actions.md (the hopper) into sync with Things 3.

Reads every hopper line that carries a Things UUID, bulk-queries Things,
rewrites the leading marker per this state machine:

  Marker today        Things state       Marker after reconcile
  -----------------   ---------------    -----------------------------------
  [>] PD              today/evening      [>] PD                  (no change)
  [>] PD              scheduled_future   [~] pushed PD, now ND
  [>] PD              anytime            [~] pushed PD, now anytime
  [>] PD              someday            [~] pushed PD, now someday
  [>] PD              done               [x] done SD
  [>] PD              killed             [x] killed SD-or-today
  [>] PD              not_found          [?] missing TODAY
  [~] pushed PD, *    today/evening      [>] PD
  [~] pushed PD, *    scheduled_future   [~] pushed PD, now ND   (may update ND)
  [~] pushed PD, *    anytime|someday    [~] pushed PD, now <list>
  [~] pushed PD, *    done|killed        [x] done|killed SD
  [~] pushed PD, *    not_found          [?] missing TODAY

  PD = original push date.  ND = new scheduled date.  SD = stopDate from Things.

`[x]` and `[?]` lines are terminal — read but never rewritten.
`[ ]` (or no-marker) lines have no UUID; they pass through untouched.

Usage:
  reconcile.py [--hopper PATH] [--dry-run] [--json-only]
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECTS_ROOT = Path("/Users/dad/Documents/sandbox/projects")
DEFAULT_HOPPER = PROJECTS_ROOT / "next-actions.md"
THINGS_PY = PROJECTS_ROOT / "claude_skills" / "things" / "things.py"
PYTHON = Path.home() / "venv" / "default" / "bin" / "python"

# Match a hopper line that may have a state marker and may carry a Things UUID.
#
#   - [>] 2026-05-08 — text <!-- things:ABCD... -->
#   - [~] pushed 2026-05-08, now 2026-05-14 — text <!-- things:ABCD... -->
#   - [x] done 2026-05-09 — text <!-- things:ABCD... -->
#   - [?] missing 2026-05-12 — text <!-- things:ABCD... -->
#   - [ ] text                                  (no date, no UUID)
#   - text                                      (no marker at all)
#
# We capture the marker bracket content, the body (everything after "] " up
# through the UUID comment), and the UUID. State-specific date parsing
# happens after the regex match.
LINE_RE = re.compile(
    r"^(?P<lead>\s*-\s+)"
    r"(?:\[(?P<marker>[^\]]*)\]\s+)?"
    r"(?P<body>.*?)"
    r"(?:\s*<!--\s*things:(?P<uuid>[A-Za-z0-9]+)\s*-->)?"
    r"\s*$"
)

PUSHED_DATES_RE = re.compile(
    r"^(?P<pd>\d{4}-\d{2}-\d{2})"
    r"(?:,\s*now\s+(?P<nd>\d{4}-\d{2}-\d{2}|anytime|someday|evening))?"
    r"\s*(?:—\s*)?"
)
SIMPLE_DATE_RE = re.compile(r"^(?P<d>\d{4}-\d{2}-\d{2})\s*(?:—\s*)?")
NOW_PREFIX_RE = re.compile(
    r"^pushed\s+(?P<pd>\d{4}-\d{2}-\d{2}),\s*now\s+(?P<nd>\S+)\s*(?:—\s*)?"
)


def today_iso() -> str:
    return date.today().isoformat()


# --- parse ------------------------------------------------------------------


def classify_marker(marker: str | None) -> str:
    """Return one of: candidate | pushed | rescheduled | done | killed | missing."""
    if marker is None:
        return "candidate"
    m = marker.strip()
    if m == "":
        return "candidate"
    if m == ">":
        return "pushed"
    if m == "~":
        return "rescheduled"
    if m == "?" or m.startswith("? "):
        return "missing"
    if m == "x" or m.startswith("x "):
        return "done_or_killed"
    return "candidate"


def parse_line(line: str) -> dict | None:
    """Return a dict describing a hopper line, or None if it isn't a list item."""
    m = LINE_RE.match(line)
    if not m or not line.lstrip().startswith("-"):
        return None
    marker = m.group("marker")
    body = m.group("body") or ""
    uuid = m.group("uuid")
    kind = classify_marker(marker)

    pushed_date: str | None = None
    text = body

    # Strip leading date/state prefix from the body so `text` is the human
    # description only. We re-synthesize the prefix when rewriting.
    if kind == "pushed":
        dm = SIMPLE_DATE_RE.match(body)
        if dm:
            pushed_date = dm.group("d")
            text = body[dm.end():]
    elif kind == "rescheduled":
        nm = NOW_PREFIX_RE.match(body)
        if nm:
            pushed_date = nm.group("pd")
            text = body[nm.end():]
    elif kind in ("done_or_killed", "missing"):
        # Body looks like "done 2026-05-09 — text" or "killed 2026-05-10 — text"
        # or "missing 2026-05-12 — text". The marker holds the verb when the
        # form is "[x done]" or "[x killed]" — but in our convention the verb
        # lives in the body. Strip a leading "done|killed|missing DATE" prefix.
        vm = re.match(
            r"^(?:done|killed|missing)\s+\d{4}-\d{2}-\d{2}\s*(?:—\s*)?", body
        )
        if vm:
            text = body[vm.end():]

    text = text.strip()
    return {
        "kind": kind,
        "marker": marker,
        "pushed_date": pushed_date,
        "uuid": uuid,
        "text": text,
        "lead": m.group("lead"),
        "raw": line.rstrip("\n"),
    }


# --- format -----------------------------------------------------------------


def format_line(lead: str, marker_block: str, text: str, uuid: str | None) -> str:
    """Build a hopper line. `marker_block` is everything between `- ` and ` — text`."""
    parts = [lead, marker_block, text]
    out = "".join(parts).rstrip()
    if uuid:
        out = f"{out} <!-- things:{uuid} -->"
    return out


def rewrite_line(
    parsed: dict, new_state: str, new_data: dict
) -> tuple[str | None, dict | None]:
    """Return (new_line, transition_record) — both None if state didn't change."""
    kind = parsed["kind"]
    text = parsed["text"]
    uuid = parsed["uuid"]
    pushed_date = parsed["pushed_date"] or today_iso()

    transition = None

    if new_state in ("today", "evening"):
        if kind == "pushed":
            return None, None  # no change
        marker_block = f"[>] {pushed_date} — "
        transition = "to_today"
    elif new_state == "scheduled_future":
        new_nd = new_data.get("scheduled_date")
        marker_block = f"[~] pushed {pushed_date}, now {new_nd} — "
        if kind == "rescheduled":
            # Already rescheduled — only count as transition if the date moved.
            old_now = _extract_now(parsed["raw"])
            if old_now == new_nd:
                return None, None
            transition = "rescheduled_moved"
        else:
            transition = "rescheduled_out_of_today"
    elif new_state in ("anytime", "someday"):
        marker_block = f"[~] pushed {pushed_date}, now {new_state} — "
        if kind == "rescheduled":
            old_now = _extract_now(parsed["raw"])
            if old_now == new_state:
                return None, None
            transition = "rescheduled_moved"
        else:
            transition = f"moved_to_{new_state}"
    elif new_state == "done":
        sd = new_data.get("stop_date") or today_iso()
        marker_block = f"[x] done {sd} — "
        transition = "completed"
    elif new_state == "killed":
        sd = new_data.get("stop_date") or today_iso()
        marker_block = f"[x] killed {sd} — "
        transition = "killed"
    elif new_state == "missing":
        marker_block = f"[?] missing {today_iso()} — "
        transition = "missing"
    elif new_state == "inbox":
        marker_block = f"[~] pushed {pushed_date}, now inbox — "
        transition = "moved_to_inbox"
    else:
        return None, None

    new_line = format_line(parsed["lead"], marker_block, text, uuid)
    if new_line.rstrip() == parsed["raw"].rstrip():
        return None, None
    return new_line, {
        "transition": transition,
        "uuid": uuid,
        "text": text,
        "from_kind": kind,
        "to_state": new_state,
    }


def _extract_now(raw: str) -> str | None:
    m = NOW_PREFIX_RE.match(raw.lstrip().lstrip("-").lstrip())
    # The above is fragile; fall back to a more permissive search.
    if m:
        return m.group("nd")
    m2 = re.search(r"now\s+(\S+)\s*—", raw)
    return m2.group(1) if m2 else None


# --- things integration -----------------------------------------------------


def bulk_query(uuids: list[str]) -> dict[str, dict]:
    if not uuids:
        return {}
    # Pass via --uuids-file to avoid argv length headaches on big hoppers.
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(uuids))
        path = f.name
    proc = subprocess.run(
        [str(PYTHON), str(THINGS_PY), "query", "--uuids-file", path],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"things.py query failed (rc={proc.returncode})")
    return json.loads(proc.stdout)


# --- main -------------------------------------------------------------------


def reconcile(hopper_path: Path, dry_run: bool = False) -> dict:
    raw = hopper_path.read_text().splitlines(keepends=False)
    parsed_lines: list[tuple[int, dict | None]] = []
    uuids: list[str] = []

    for i, line in enumerate(raw):
        p = parse_line(line)
        parsed_lines.append((i, p))
        if p and p["uuid"] and p["kind"] in ("pushed", "rescheduled"):
            # Only re-query transient states. [x] and [?] are terminal.
            uuids.append(p["uuid"])

    things_data = bulk_query(uuids)

    transitions: list[dict] = []
    new_raw = list(raw)

    for i, parsed in parsed_lines:
        if not parsed or not parsed["uuid"]:
            continue
        if parsed["kind"] not in ("pushed", "rescheduled"):
            continue
        td = things_data.get(parsed["uuid"], {"found": False})
        if not td.get("found"):
            new_state = "missing"
            new_data: dict = {}
        else:
            new_state = td["state"]
            new_data = td
        new_line, transition = rewrite_line(parsed, new_state, new_data)
        if new_line is not None:
            new_raw[i] = new_line
            transitions.append(
                {**transition, "line_no": i + 1, "title_in_things": td.get("title")}
            )

    if not dry_run and transitions:
        hopper_path.write_text("\n".join(new_raw) + "\n")

    # Summarize
    summary: dict[str, list] = {
        "completed": [],
        "killed": [],
        "rescheduled": [],
        "missing": [],
        "back_to_today": [],
        "other": [],
    }
    for t in transitions:
        if t["transition"] == "completed":
            summary["completed"].append(t)
        elif t["transition"] == "killed":
            summary["killed"].append(t)
        elif t["transition"] in (
            "rescheduled_out_of_today",
            "rescheduled_moved",
            "moved_to_anytime",
            "moved_to_someday",
            "moved_to_inbox",
        ):
            summary["rescheduled"].append(t)
        elif t["transition"] == "missing":
            summary["missing"].append(t)
        elif t["transition"] == "to_today":
            summary["back_to_today"].append(t)
        else:
            summary["other"].append(t)

    return {
        "as_of": today_iso(),
        "hopper": str(hopper_path),
        "dry_run": dry_run,
        "queried_uuids": len(uuids),
        "transitions_total": len(transitions),
        "summary": summary,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hopper", default=str(DEFAULT_HOPPER))
    ap.add_argument("--dry-run", action="store_true",
                    help="don't write changes, just report")
    ap.add_argument("--json-only", action="store_true",
                    help="emit only the JSON report (no human banner)")
    args = ap.parse_args()
    result = reconcile(Path(args.hopper), dry_run=args.dry_run)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
