#!/usr/bin/env python3
"""Deterministic weekly scan for the rounds (Fred's pull-based synthesis).

Cowork pattern (same as music-status / music-loops): this script emits
deterministic JSON about what moved in the last window. Claude (Fred) reads the
JSON and writes the 2-pager with editorial judgment. The script makes NO
qualitative calls — it counts, dates, and extracts. Zero prose.

Sources:
  soils     -> top-level vault dirs (roster read from the filesystem), file
               mtimes in window + git activity (vault repo per-soil rollup,
               embedded repos scanned in place)
  things    -> Things 3 logbook, read-only sqlite (completed tasks in window)
  debriefs  -> debrief/retro-named .md files with recent mtimes across soils
  watchers  -> model-watcher state.json + launchd.out findings;
               recording-watcher dispatch log + pending-review backlog
  music     -> open lessons awaiting practice + debrief (delegates to the
               music-loops scan — that skill owns the how)
  prior     -> rounds/state/<date>/ history incl. last reactions.md (Nick's
               reaction to each rounds is standing input to the next)

Content rules enforced HERE (not left to judgment):
  - sensitive soils (life-story, spiritual-coupledom): counts and dates only —
    no filenames, no commit subjects, ever
  - anything minecraft-ish is invisible: filtered from every listing
  - someday/ and archive/ are not soils and are never scanned

Every section degrades gracefully: a failed source becomes {"error": ...},
never a crash.

Usage:
    ~/venv/default/bin/python scan.py            # JSON to stdout
    ~/venv/default/bin/python scan.py --out F    # also write JSON to file F
    ~/venv/default/bin/python scan.py --days 10  # widen the window
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

VAULT = Path("/Users/dad/Documents/sandbox")
HOME = Path.home()

# Not soils: lifecycle dirs, Fred's own room, Kahua's shelf, outputs, dot-dirs.
NON_SOILS = {"someday", "archive", "artifacts", "reference", "research",
             "backstairs"}
# Process-level only: counts yes, names/content never.
SENSITIVE = {"life-story", "spiritual-coupledom"}
# Invisible by law (2026-07-11): pure play, never surfaced.
INVISIBLE = re.compile(r"minecraft", re.I)

THINGS_DB = (HOME / "Library/Group Containers/"
             "JLMPQHK86H.com.culturedcode.ThingsMac/ThingsData-OQ3NJ/"
             "Things Database.thingsdatabase/main.sqlite")
MODEL_WATCHER_STATE = HOME / ".model_watcher/state.json"
MODEL_WATCHER_LOG = HOME / "Library/Logs/model-watcher/launchd.out"
RECORDING_LOG_DIR = HOME / "Library/Logs/recording-watcher"
PENDING_REVIEW_LOG = (VAULT / "backstairs/recording-watcher/captures/"
                      "pending-review.log")
MUSIC_LOOPS_SCAN = VAULT / "backstairs/music-loops/scan.py"
STATE_DIR = VAULT / "backstairs/rounds/state"

FILE_LIST_CAP = 15  # max recent files listed per soil


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def _guard(fn):
    """Run a section scanner; a failure becomes {'error': ...}, never a crash."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 — deliberate catch-all per spec
        return {"error": f"{type(e).__name__}: {e}"}


# ------------------------------------------------------------------- soils ---

def soil_roster() -> list[str]:
    return sorted(
        d.name for d in VAULT.iterdir()
        if d.is_dir() and not d.name.startswith(".")
        and d.name not in NON_SOILS
    )


def _walk_mtimes(soil: Path, cutoff: float) -> tuple[int, list[dict]]:
    """(changed_count, newest files) for regular files modified since cutoff."""
    changed: list[tuple[float, str]] = []
    stack = [soil]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except (PermissionError, FileNotFoundError):
            continue
        for p in entries:
            if p.name.startswith("."):
                continue
            if p.is_symlink():
                continue
            if p.is_dir():
                stack.append(p)
                continue
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt >= cutoff:
                rel = str(p.relative_to(soil))
                if INVISIBLE.search(rel):
                    continue
                changed.append((mt, rel))
    changed.sort(reverse=True)
    files = [{"file": rel, "modified": _iso(mt)}
             for mt, rel in changed[:FILE_LIST_CAP]]
    return len(changed), files


def _git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                       text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])}: {r.stderr.strip()[:200]}")
    return r.stdout


def _vault_git_rollup(days: int) -> dict[str, dict]:
    """Per-top-level-dir rollup of the vault repo's last-N-days commits."""
    out = _git(["log", f"--since={days}.days", "--name-only",
                "--pretty=format:%x01%ad%x02%s", "--date=short"], VAULT)
    rollup: dict[str, dict] = {}
    commit_date = ""
    for line in out.splitlines():
        if line.startswith("\x01"):
            commit_date, _, _subject = line[1:].partition("\x02")
            continue
        if not line.strip():
            continue
        top = line.split("/", 1)[0]
        if INVISIBLE.search(line):
            continue
        r = rollup.setdefault(top, {"files_touched": set(), "last_commit": ""})
        r["files_touched"].add(line)
        r["last_commit"] = max(r["last_commit"], commit_date)
    return {k: {"files_touched": len(v["files_touched"]),
                "last_commit": v["last_commit"]}
            for k, v in rollup.items()}


def _embedded_git(soil: Path, days: int, sensitive: bool) -> dict:
    out = _git(["log", f"--since={days}.days", "--pretty=format:%ad%x02%s",
                "--date=short"], soil)
    commits = []
    for line in out.splitlines():
        d, _, subject = line.partition("\x02")
        if INVISIBLE.search(subject):
            continue
        commits.append({"date": d} if sensitive
                       else {"date": d, "subject": subject[:120]})
    return {"embedded_repo": True, "commit_count": len(commits),
            "commits": commits[:10]}


def scan_soils(days: int) -> dict:
    cutoff = time.time() - days * 86400
    vault_rollup = _guard(lambda: _vault_git_rollup(days))
    soils = []
    for name in soil_roster():
        soil = VAULT / name
        sensitive = name in SENSITIVE
        count, files = _walk_mtimes(soil, cutoff)
        entry: dict = {"soil": name, "sensitive": sensitive,
                       "files_changed": count}
        if sensitive:
            # process level only: files moved yes/no — never names or content
            entry["newest_change"] = files[0]["modified"] if files else None
        else:
            entry["recent_files"] = files
        if (soil / ".git").exists():
            entry["git"] = _guard(lambda s=soil, sv=sensitive:
                                  _embedded_git(s, days, sv))
        elif isinstance(vault_rollup, dict) and "error" not in vault_rollup:
            entry["git"] = vault_rollup.get(name, {"files_touched": 0})
        else:
            entry["git"] = vault_rollup  # the rollup error, surfaced per-soil
        soils.append(entry)
    return {"roster": [s["soil"] for s in soils], "soils": soils}


# ------------------------------------------------------------------ things ---

def scan_things(days: int) -> dict:
    if not THINGS_DB.exists():
        raise FileNotFoundError(f"Things db not found: {THINGS_DB}")
    con = sqlite3.connect(f"file:{THINGS_DB}?mode=ro", uri=True, timeout=5)
    try:
        cutoff = time.time() - days * 86400
        rows = con.execute(
            "SELECT t.title, t.stopDate, p.title FROM TMTask t "
            "LEFT JOIN TMTask p ON t.project = p.uuid "
            "WHERE t.status = 3 AND t.trashed = 0 AND t.type = 0 "
            "AND t.stopDate > ? ORDER BY t.stopDate DESC", (cutoff,)
        ).fetchall()
    finally:
        con.close()
    completed = [
        {"title": title, "completed": _iso(stop), "project": project}
        for title, stop, project in rows
        if not INVISIBLE.search(title or "")
    ]
    return {"completed_count": len(completed), "completed": completed}


# ---------------------------------------------------------------- debriefs ---

DEBRIEF_NAME = re.compile(r"(debrief|retro)", re.I)


def scan_debriefs(days: int) -> dict:
    cutoff = time.time() - days * 86400
    hits, sensitive_counts = [], {}
    for name in soil_roster():
        soil = VAULT / name
        for p in soil.rglob("*.md"):
            if any(part.startswith(".") for part in p.relative_to(soil).parts):
                continue
            if not DEBRIEF_NAME.search(p.name):
                continue
            try:
                mt = p.stat().st_mtime
            except OSError:
                continue
            if mt < cutoff:
                continue
            rel = str(p.relative_to(VAULT))
            if INVISIBLE.search(rel):
                continue
            if name in SENSITIVE:
                sensitive_counts[name] = sensitive_counts.get(name, 0) + 1
            else:
                hits.append({"file": rel, "modified": _iso(mt)})
    hits.sort(key=lambda h: h["modified"], reverse=True)
    return {"recent": hits, "sensitive_soil_counts": sensitive_counts}


# ---------------------------------------------------------------- watchers ---

def _model_watcher_findings(log_text: str) -> list[dict]:
    """Extract 🚀 finding blocks: headline, body paragraph, sources."""
    findings = []
    lines = log_text.splitlines()
    i = 0
    while i < len(lines):
        if "🚀" in lines[i]:
            headline = lines[i].strip()
            body, sources = [], []
            j = i + 1
            while j < len(lines) and "🚀" not in lines[j]:
                s = lines[j].strip()
                if s.startswith("http"):
                    sources.append(s)
                elif s and s != "Sources:":
                    body.append(s)
                j += 1
            findings.append({"headline": headline,
                             "body": " ".join(body)[:1200],
                             "sources": sources})
            i = j
        else:
            i += 1
    return findings


def scan_model_watcher() -> dict:
    result: dict = {}
    if MODEL_WATCHER_STATE.exists():
        result["state"] = json.loads(MODEL_WATCHER_STATE.read_text())
    else:
        result["state"] = {"error": f"missing: {MODEL_WATCHER_STATE}"}
    if MODEL_WATCHER_LOG.exists():
        st = MODEL_WATCHER_LOG.stat()
        result["log_modified"] = _iso(st.st_mtime)
        result["findings"] = _model_watcher_findings(
            MODEL_WATCHER_LOG.read_text(errors="replace"))
    else:
        result["findings"] = []
        result["log_error"] = f"missing: {MODEL_WATCHER_LOG}"
    return result


def scan_recording_watcher(days: int) -> dict:
    cutoff = time.time() - days * 86400
    result: dict = {}
    dispatch = RECORDING_LOG_DIR / "dispatch.log"
    if dispatch.exists():
        recent = []
        for line in dispatch.read_text(errors="replace").splitlines():
            m = re.match(r"^\[?(\d{4}-\d{2}-\d{2})", line)
            if m:
                try:
                    ts = time.mktime(time.strptime(m.group(1), "%Y-%m-%d"))
                except ValueError:
                    continue
                if ts >= cutoff:
                    recent.append(line.strip()[:300])
        result["dispatches_in_window"] = recent[-20:]
        result["dispatch_log_modified"] = _iso(dispatch.stat().st_mtime)
    else:
        result["dispatch_log_error"] = f"missing: {dispatch}"
    if PENDING_REVIEW_LOG.exists():
        text = PENDING_REVIEW_LOG.read_text(errors="replace")
        result["pending_review_backlog"] = {
            "lines": len(text.splitlines()),
            "tail": text.splitlines()[-10:],
        }
    else:
        result["pending_review_backlog"] = None  # nothing queued — fine
    return result


# ------------------------------------------------------------------- music ---

def scan_music_open_lessons() -> dict:
    """Delegate to the music-loops scan — that skill owns the how."""
    r = subprocess.run([sys.executable, str(MUSIC_LOOPS_SCAN)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"music-loops scan failed: {r.stderr.strip()[:300]}")
    data = json.loads(r.stdout)
    return {"open_count": len(data.get("loops", [])),
            "loops": data.get("loops", []),
            "gates": data.get("gates", {})}


# ------------------------------------------------------------- prior rounds ---

def scan_prior_rounds() -> dict:
    if not STATE_DIR.exists():
        return {"runs": [], "last_reactions": None}
    runs = sorted(d.name for d in STATE_DIR.iterdir()
                  if d.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}", d.name))
    last_reactions = None
    for run in reversed(runs):
        rx = STATE_DIR / run / "reactions.md"
        if rx.exists():
            last_reactions = {"run": run, "text": rx.read_text()[:4000]}
            break
    return {"runs": runs, "last_reactions": last_reactions}


# -------------------------------------------------------------------- main ---

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=7, help="window in days")
    ap.add_argument("--out", help="also write JSON to this file")
    args = ap.parse_args()

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M", time.localtime()),
        "window_days": args.days,
        "window_start": _iso(time.time() - args.days * 86400),
        "soils": _guard(lambda: scan_soils(args.days)),
        "things_completed": _guard(lambda: scan_things(args.days)),
        "debriefs": _guard(lambda: scan_debriefs(args.days)),
        "watchers": {
            "model_watcher": _guard(scan_model_watcher),
            "recording_watcher": _guard(lambda: scan_recording_watcher(args.days)),
        },
        "music_open_lessons": _guard(scan_music_open_lessons),
        "prior_rounds": _guard(scan_prior_rounds),
    }

    blob = json.dumps(report, indent=2, ensure_ascii=False)
    print(blob)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(blob + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
