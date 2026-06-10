#!/usr/bin/env python3
"""
scan.py — /projects-status data layer.

Emits everything the orientation report needs:
- reconciliation (hopper ↔ Things transitions this run)
- per-project health (bucket: moving | silent | needs_audit | foundational_at_risk | null_log)
- hopper grouped by project (unresolved / in_flight / terminal_recent)
- Things Today count + active project names (for the in-flight cross-reference)
- candidates_ranked (leverage-scored, for optional "push something" follow-up)
- latest weekly review's "Patterns" section (input for the HOW YOU'RE DOING synthesis)

The per-project bootstrap/develop routing helpers live below `# --- legacy ---`
and are not invoked from main(); kept for a future /project <name> skill lift.
"""

from __future__ import annotations
import argparse
import difflib
import json
import re
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECTS_ROOT = Path("/Users/dad/Documents/sandbox/projects")
THRESHOLD_DEFAULT_DAYS = 30
TERMINAL_RECENT_DAYS = 14
LIFECYCLE_OR_META = {"someday", "archive", "inbox", "claude_skills", "artifacts"}

THINGS_CLI = PROJECTS_ROOT / "claude_skills" / "things" / "things.py"
HOPPER_FILE = PROJECTS_ROOT / "next-actions.md"
RECONCILE_PY = PROJECTS_ROOT / "claude_skills" / "projects-status" / "reconcile.py"
WEEKLY_DIR = PROJECTS_ROOT / "review" / "weekly"

# Hopper section headers that aren't project sections.
META_SECTIONS = {
    "this weekend",
    "cross-cutting / infrastructure",
    "cross-cutting",
    "infrastructure",
}

DELIVERY_VERBS = (
    "write", "print", "laminate", "hang", "install", "send", "ship",
    "deliver", "record", "post", "submit", "draft", "publish",
    "photograph", "build", "make", "cook", "prep", "bake", "hand",
    "buy", "pick up", "call ", "book", "schedule", "set up", "give",
)
DESIGN_VERBS = (
    "spawn a claude", "claude convo", "claude chat", "decide", "sketch",
    "design", "audit", "evaluate", "consider", "think about", "discuss",
    "scope", "explore", "investigate",
)


# --- frontmatter / activity log helpers -------------------------------------

def parse_frontmatter(readme: Path) -> dict | None:
    if not readme.exists():
        return None
    try:
        text = readme.read_text(errors="ignore")
    except OSError:
        return None
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    out: dict[str, str] = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def parse_threshold(value: str | None) -> int:
    if not value:
        return THRESHOLD_DEFAULT_DAYS
    m = re.match(r"(\d+)\s*d", value)
    return int(m.group(1)) if m else THRESHOLD_DEFAULT_DAYS


def newest_mtime_under(path: Path) -> float | None:
    if not path.exists():
        return None
    if path.is_file():
        return path.stat().st_mtime
    newest = 0.0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                m = p.stat().st_mtime
                if m > newest:
                    newest = m
            except OSError:
                continue
    return newest or None


# --- content-aware freshness signals ---------------------------------------
#
# mtime lies. A sync, checkout, or rsync replays metadata without you having
# touched the file; six different log.md files landing on identical
# .000000000 nanosecond mtimes is the fingerprint. Content and git history
# can't be forged by a filesystem op.
#
# The ladder is: log-content date → git date → mtime. Whichever fires first
# is reported, with `freshness_signal` saying which one so the report can
# distinguish "moving — log entry" from "moving — git only, no log entry."

_DATE_HEADING_RE = re.compile(r"^##\s+(\d{4})-(\d{2})-(\d{2})\b", re.MULTILINE)
_DATE_BULLET_RE = re.compile(r"^-\s+(\d{4})-(\d{2})-(\d{2})\b", re.MULTILINE)
# Filename dates: accept YYYY-MM-DD or YYYYMMDD, anywhere in the filename
# (painting's run_logs use `chapter2_20260426_…`; review's weekly uses
# `2026-05-08-walk.md`). Year band 2000-2099 keeps false positives low.
_DATE_FILENAME_HYPHEN_RE = re.compile(r"(?<!\d)(20\d{2})-(\d{2})-(\d{2})(?!\d)")
_DATE_FILENAME_PACKED_RE = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")


def _parse_date_safe(y: str, m: str, d: str) -> date | None:
    try:
        return date(int(y), int(m), int(d))
    except ValueError:
        return None


def newest_date_from_log_content(path: Path) -> date | None:
    """Look inside files for `## YYYY-MM-DD` or `- YYYY-MM-DD` entries.
    Returns the newest date found, or None if no dated entries exist."""
    if not path.exists():
        return None
    files: list[Path] = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
    newest: date | None = None
    for f in files:
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        for rx in (_DATE_HEADING_RE, _DATE_BULLET_RE):
            for m in rx.finditer(text):
                d = _parse_date_safe(m.group(1), m.group(2), m.group(3))
                if d and (newest is None or d > newest):
                    newest = d
    return newest


def newest_date_from_log_filenames(path: Path) -> date | None:
    """For directory-style activity_logs (review/weekly, fitness/logs/{nick,farrah},
    painting/run_logs), find files whose names contain a date — either
    hyphenated YYYY-MM-DD or packed YYYYMMDD. Returns newest, or None.
    Recurses into subdirectories so health/fitness/logs/<person>/<file> works."""
    if not path.exists() or path.is_file():
        return None
    newest: date | None = None
    for f in path.rglob("*"):
        if not f.is_file():
            continue
        for rx in (_DATE_FILENAME_HYPHEN_RE, _DATE_FILENAME_PACKED_RE):
            for m in rx.finditer(f.name):
                d = _parse_date_safe(m.group(1), m.group(2), m.group(3))
                if d and (newest is None or d > newest):
                    newest = d
    return newest


def newest_date_from_git(project_dir: Path) -> date | None:
    """Last commit touching anything in the project. Each project may have
    its own .git (music/.git) — projects/ root itself isn't a repo. So we
    run `git -C <project_dir> log` only when that project owns a repo."""
    if not (project_dir / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(project_dir), "log", "-1",
             "--format=%ad", "--date=short"],
            capture_output=True, text=True, timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", out)
    return _parse_date_safe(m.group(1), m.group(2), m.group(3)) if m else None


def compute_freshness(project_dir: Path, log_full: Path | None, threshold_days: int) -> dict:
    """Returns {newest_date, days_silent, signal} using a content-first ladder.

    Nick works by *editing* log files in place — append today's entry, save.
    That's an mtime event, not a git event; git commits are rare. So mtime,
    when it's recent enough to plausibly be a real edit, is a stronger
    signal than git history. Order: log_content → log_filename → mtime
    (if within threshold) → git → mtime (stale, fallback).

    The mtime split is the key trick: a recent mtime on an undated file is
    probably a real edit; an old mtime on an undated file is probably a
    scaffold that has been sitting since creation. Same metadata, different
    meaning, distinguished by whether the time is fresh.

    signal ∈ {log_content, log_filename, mtime, git, none}.
    """
    today = date.today()

    if log_full is not None and log_full.exists():
        d = newest_date_from_log_content(log_full)
        if d:
            return {"newest_date": d.isoformat(), "days_silent": (today - d).days, "signal": "log_content"}
        d = newest_date_from_log_filenames(log_full)
        if d:
            return {"newest_date": d.isoformat(), "days_silent": (today - d).days, "signal": "log_filename"}

    # Content yielded nothing — try mtime, but only believe it if recent.
    if log_full is not None and log_full.exists():
        mtime = newest_mtime_under(log_full)
        if mtime:
            d = date.fromtimestamp(mtime)
            days = (today - d).days
            if days <= threshold_days:
                return {"newest_date": d.isoformat(), "days_silent": days, "signal": "mtime"}

    # Mtime was stale or unavailable. Try git as a final activity check —
    # for music/, which has its own .git and gets edited via commits.
    d = newest_date_from_git(project_dir)
    if d:
        return {"newest_date": d.isoformat(), "days_silent": (today - d).days, "signal": "git"}

    # Last resort: report the stale mtime so the bucket logic can see the
    # scaffold age, but the bucket will land in log_unused, not moving.
    if log_full is not None and log_full.exists():
        mtime = newest_mtime_under(log_full)
        if mtime:
            d = date.fromtimestamp(mtime)
            return {"newest_date": d.isoformat(), "days_silent": (today - d).days, "signal": "mtime"}

    return {"newest_date": None, "days_silent": None, "signal": "none"}


def newest_file_under(path: Path) -> Path | None:
    if not path.exists():
        return None
    if path.is_file():
        return path
    newest_path: Path | None = None
    newest_mtime = 0.0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                m = p.stat().st_mtime
                if m > newest_mtime:
                    newest_mtime = m
                    newest_path = p
            except OSError:
                continue
    return newest_path


def latest_log_excerpt(log_full: Path | None, max_lines: int = 60) -> dict | None:
    if log_full is None:
        return None
    target = newest_file_under(log_full)
    if target is None:
        return None
    try:
        text = target.read_text(errors="ignore")
    except OSError:
        return None
    lines = text.splitlines()
    excerpt = "\n".join(lines[-max_lines:]) if len(lines) > max_lines else text
    return {
        "file": str(target.relative_to(PROJECTS_ROOT)),
        "lines_total": len(lines),
        "excerpt": excerpt,
    }


# --- project health ---------------------------------------------------------

def project_health() -> list[dict]:
    """Per-project metadata + bucket. Used for the PROJECTS section of the report."""
    results: list[dict] = []
    for entry in sorted(PROJECTS_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if entry.name in LIFECYCLE_OR_META:
            continue
        fm = parse_frontmatter(entry / "README.md")
        if not fm:
            continue
        status = fm.get("status", "unknown").strip()
        if status not in {"active", "tool", "scaffold", "needs-audit"}:
            continue

        log_raw = fm.get("activity_log", "").strip()
        log_path = None if log_raw in {"", "null", "~"} else log_raw
        threshold_days = parse_threshold(fm.get("activity_threshold"))
        log_full = (entry / log_path) if log_path else None
        foundational = fm.get("foundational", "").strip().lower() == "true"

        fresh = compute_freshness(entry, log_full, threshold_days)
        days_silent = fresh["days_silent"]
        signal = fresh["signal"]

        if status == "needs-audit":
            bucket = "needs_audit"
        elif status == "scaffold":
            bucket = "scaffold"
        elif log_path is None:
            bucket = "null_log"
        elif log_full is not None and not log_full.exists():
            bucket = "null_log"
        elif signal == "none" or days_silent is None:
            bucket = "null_log"
        elif days_silent > threshold_days:
            # Past threshold. If the signal was content/filename, the log was
            # used at some point but went quiet — that's "silent." If the
            # signal was mtime/git (no dated entries ever), the log convention
            # itself never took — that's "log_unused."
            bucket = "silent" if signal in {"log_content", "log_filename"} else "log_unused"
        else:
            bucket = "moving"

        if foundational and bucket in {"silent", "null_log", "log_unused"}:
            bucket = "foundational_at_risk"

        results.append({
            "project": entry.name,
            "status": status,
            "priorities": fm.get("priorities", ""),
            "activity_log": log_path,
            "newest_date": fresh["newest_date"],
            "freshness_signal": signal,
            "days_silent": days_silent,
            "threshold_days": threshold_days,
            "bucket": bucket,
            "foundational": foundational,
            "log_excerpt": latest_log_excerpt(log_full),
        })
    return results


# --- hopper parsing (full — by project, by marker) --------------------------

_TERMINAL_RE = re.compile(r"^\[x\]\s*(done|killed)\s+(\d{4}-\d{2}-\d{2})\s*(?:[—-]\s*)?(.*)$")
_INFLIGHT_RE = re.compile(r"^\[([>~])\]\s*(.*)$")
_UNRESOLVED_RE = re.compile(r"^\[[ ?]\]\s+(.+)$")


def parse_hopper_full() -> tuple[dict[str, dict], dict[str, int]]:
    """Parse next-actions.md into per-project structured data.

    Returns (by_project, totals). by_project maps project name → {unresolved,
    in_flight, terminal_recent}; totals has overall counts.
    """
    if not HOPPER_FILE.exists():
        return {}, {"unresolved": 0, "in_flight": 0, "terminal_recent": 0}
    text = HOPPER_FILE.read_text(errors="ignore")
    lines = text.splitlines()
    by_project: dict[str, dict] = {}
    cutoff = (date.today() - timedelta(days=TERMINAL_RECENT_DAYS))

    current: str | None = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            current = line[3:].strip()
            continue
        if current is None:
            continue
        cur_low = current.lower()
        if any(cur_low.startswith(m) for m in META_SECTIONS):
            continue
        stripped = line.lstrip()
        if not stripped.startswith("- "):
            continue
        body_part = stripped[2:]

        slot = by_project.setdefault(current, {"unresolved": [], "in_flight": [], "terminal_recent": []})

        m_term = _TERMINAL_RE.match(body_part)
        if m_term:
            try:
                term_date = datetime.strptime(m_term.group(2), "%Y-%m-%d").date()
                if term_date >= cutoff:
                    slot["terminal_recent"].append({
                        "kind": m_term.group(1),
                        "date": m_term.group(2),
                        "body": m_term.group(3).strip(),
                    })
            except ValueError:
                pass
            continue

        m_flight = _INFLIGHT_RE.match(body_part)
        if m_flight:
            slot["in_flight"].append({
                "marker": m_flight.group(1),
                "raw": m_flight.group(2).strip(),
                "raw_line": line,
                "line_index": i,
            })
            continue

        m_unres = _UNRESOLVED_RE.match(body_part)
        if m_unres:
            slot["unresolved"].append({
                "body": m_unres.group(1).strip(),
                "raw_line": line,
                "line_index": i,
            })
            continue

        # Bare bullet (no marker) — treat as unresolved.
        if not body_part.startswith("["):
            slot["unresolved"].append({
                "body": body_part.strip(),
                "raw_line": line,
                "line_index": i,
            })

    totals = {
        "unresolved": sum(len(v["unresolved"]) for v in by_project.values()),
        "in_flight": sum(len(v["in_flight"]) for v in by_project.values()),
        "terminal_recent": sum(len(v["terminal_recent"]) for v in by_project.values()),
    }
    return by_project, totals


# --- Things integration -----------------------------------------------------

def _things_list(cmd: str) -> list[dict]:
    if not THINGS_CLI.exists():
        return []
    try:
        result = subprocess.run(
            ["python3", str(THINGS_CLI), cmd],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    if result.returncode != 0:
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return payload.get("items", [])


def things_today() -> list[dict]:
    return [
        {"title": it["title"], "tags": it.get("tags", [])}
        for it in _things_list("today")
    ]


def things_active_project_suffixes() -> set[str]:
    """Pull `— <project>` suffix from every open task in Today and Anytime.
    Lowercase, normalized."""
    titles = [it["title"] for it in _things_list("today") + _things_list("anytime")]
    out: set[str] = set()
    for t in titles:
        m = re.search(r"—\s*([A-Za-z0-9_\- ]+?)\s*$", t)
        if m:
            out.add(m.group(1).strip().lower())
    return out


# --- leverage scorer (for optional "push something" follow-up) --------------

def _normalize_project_key(name: str) -> str:
    return name.lower().replace("_", " ").replace("-", " ").strip()


def score_candidate(
    cand: dict,
    health_by_name: dict[str, dict],
    active_in_things: set[str],
    today: date,
) -> tuple[float, dict[str, float]]:
    body = cand["body"]
    body_low = body.lower()
    breakdown: dict[str, float] = {}

    proj_name = cand["project"]
    ph = (health_by_name.get(proj_name)
          or health_by_name.get(proj_name.replace("-", " "))
          or health_by_name.get(proj_name.replace(" ", "-"))
          or {})

    if ph.get("foundational"):
        breakdown["foundational"] = 3.0

    date_m = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", body)
    if date_m:
        try:
            d = date(int(date_m.group(1)), int(date_m.group(2)), int(date_m.group(3)))
            delta = (d - today).days
            if 0 <= delta <= 7:
                breakdown["hard_date_near"] = 4.0
            elif delta < 0:
                breakdown["hard_date_past"] = 1.0
        except ValueError:
            pass

    if any(re.search(rf"\b{re.escape(v)}\b", body_low) for v in DELIVERY_VERBS):
        breakdown["delivery_verb"] = 2.0
    if any(re.search(rf"\b{re.escape(v)}\b", body_low) for v in DESIGN_VERBS):
        breakdown["design_verb"] = -1.5

    proj_norm = _normalize_project_key(proj_name)
    if any(_normalize_project_key(a) == proj_norm for a in active_in_things):
        breakdown["project_in_flight"] = -2.0

    if ph.get("status") == "needs-audit":
        breakdown["needs_audit"] = -2.0

    ds = ph.get("days_silent")
    th = ph.get("threshold_days") or THRESHOLD_DEFAULT_DAYS
    if ds is not None and ds > th:
        breakdown["project_silent"] = 1.0

    log_text = ((ph.get("log_excerpt") or {}).get("excerpt") or "").lower()
    if log_text:
        body_tokens = set(re.findall(r"[a-z]{5,}", body_low))
        log_tokens = set(re.findall(r"[a-z]{5,}", log_text))
        overlap = body_tokens & log_tokens - {"claude", "convo", "chat", "project", "spawn", "going", "mojo"}
        if overlap:
            breakdown["log_overlap"] = 1.5

    return sum(breakdown.values()), breakdown


def rank_candidates(by_project: dict, health: list[dict], active: set[str]) -> list[dict]:
    health_by_name = {p["project"]: p for p in health}
    today = date.today()
    ranked: list[dict] = []
    for proj_name, slot in by_project.items():
        for item in slot["unresolved"]:
            cand = {"project": proj_name, **item}
            score, breakdown = score_candidate(cand, health_by_name, active, today)
            ranked.append({
                **cand,
                "score": round(score, 2),
                "score_breakdown": {k: round(v, 2) for k, v in breakdown.items()},
            })
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


# --- weekly review patterns (input for HOW YOU'RE DOING synthesis) ----------

def latest_weekly_review() -> dict | None:
    """Return the most recent weekly review's `## Patterns feeding the queue` section
    so the report's assessment paragraph can ground in what Nick already named.
    Returns {file, patterns} or None."""
    if not WEEKLY_DIR.exists():
        return None
    files = [p for p in WEEKLY_DIR.glob("*.md") if re.match(r"^\d{4}-\d{2}-\d{2}", p.name)]
    if not files:
        return None
    latest = max(files, key=lambda p: p.stat().st_mtime)
    try:
        text = latest.read_text(errors="ignore")
    except OSError:
        return None
    m = re.search(r"##\s+Patterns feeding the queue\s*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    return {
        "file": str(latest.relative_to(PROJECTS_ROOT)),
        "patterns": m.group(1).strip() if m else None,
    }


# --- reconcile --------------------------------------------------------------

def run_reconcile() -> dict:
    if not RECONCILE_PY.exists():
        return {"error": "reconcile.py not found", "skipped": True}
    try:
        result = subprocess.run(
            ["python3", str(RECONCILE_PY)],
            capture_output=True, text=True, timeout=20,
        )
    except (subprocess.SubprocessError, OSError) as e:
        return {"error": str(e), "skipped": True}
    if result.returncode != 0:
        return {"error": result.stderr.strip() or "non-zero exit", "skipped": True}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"reconcile output not JSON: {e}", "skipped": True}


# --- main -------------------------------------------------------------------

def main() -> int:
    argparse.ArgumentParser(description="Projects status scan.").parse_args()

    reconciliation = run_reconcile()
    health = project_health()
    hopper_by_project, hopper_totals = parse_hopper_full()
    active = things_active_project_suffixes()
    today_items = things_today()
    candidates_ranked = rank_candidates(hopper_by_project, health, active)
    weekly = latest_weekly_review()

    out = {
        "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "projects_root": str(PROJECTS_ROOT),
        "reconciliation": reconciliation,
        "things_today_count": len(today_items),
        "things_active_project_suffixes": sorted(active),
        "projects": health,
        "hopper": hopper_by_project,
        "hopper_totals": hopper_totals,
        "candidates_ranked": candidates_ranked,
        "weekly_review": weekly,
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


# --- legacy: per-project mode helpers (kept for future /project skill lift) -

def list_active_dirs() -> list[str]:
    out = []
    for d in PROJECTS_ROOT.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        if d.name in LIFECYCLE_OR_META:
            continue
        out.append(d.name)
    return sorted(out)


def resolve_target(name: str) -> dict:
    candidates = list_active_dirs()
    if name in candidates:
        return {"input": name, "resolved": name, "candidates": [name],
                "ambiguous": False, "not_found": False}
    lower_map = {c.lower(): c for c in candidates}
    if name.lower() in lower_map:
        hit = lower_map[name.lower()]
        return {"input": name, "resolved": hit, "candidates": [hit],
                "ambiguous": False, "not_found": False}
    norm = name.lower().replace("-", " ").replace("_", " ")
    norm_map = {c.lower().replace("-", " ").replace("_", " "): c for c in candidates}
    if norm in norm_map:
        hit = norm_map[norm]
        return {"input": name, "resolved": hit, "candidates": [hit],
                "ambiguous": False, "not_found": False}
    subs = [c for c in candidates if name.lower() in c.lower()]
    if len(subs) == 1:
        return {"input": name, "resolved": subs[0], "candidates": subs,
                "ambiguous": False, "not_found": False}
    if len(subs) > 1:
        return {"input": name, "resolved": None, "candidates": subs,
                "ambiguous": True, "not_found": False}
    fuzzy = difflib.get_close_matches(name.lower(), [c.lower() for c in candidates], n=3, cutoff=0.5)
    fuzzy_real = [lower_map[f] for f in fuzzy if f in lower_map]
    return {"input": name, "resolved": None, "candidates": fuzzy_real,
            "ambiguous": False, "not_found": True}


if __name__ == "__main__":
    raise SystemExit(main())
