#!/usr/bin/env python3
"""
backfill_uuids.py — one-time pass to stamp Things UUIDs into legacy [>] lines
in projects/next-actions.md.

The push step before today wrote `[>] YYYY-MM-DD — <text>` with no back-reference
to the Things task it created. Reconciliation needs the UUID. This script
searches Things for a likely match per legacy line and proposes a mapping.

By default it PROPOSES (prints a JSON/markdown report, no file writes). Run with
`--apply` to write the stamps and then immediately invoke reconcile.py so the
freshly-stamped lines flip to whatever state Things actually holds (done /
rescheduled / killed / still in Today).

Usage:
  backfill_uuids.py                 # propose only, no writes
  backfill_uuids.py --apply         # stamp + reconcile
  backfill_uuids.py --apply --high-confidence-only  # skip ambiguous lines
"""
from __future__ import annotations
import argparse
import difflib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECTS_ROOT = Path("/Users/dad/Documents/sandbox/projects")
DEFAULT_HOPPER = PROJECTS_ROOT / "next-actions.md"
THINGS_DB = Path(
    "/Users/dad/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/"
    "ThingsData-OQ3NJ/Things Database.thingsdatabase/main.sqlite"
)
RECONCILE_PY = (
    PROJECTS_ROOT / "claude_skills" / "projects-status" / "reconcile.py"
)
PYTHON = Path.home() / "venv" / "default" / "bin" / "python"

# Map hopper section heading → Things title suffix after "— ".
# Default: lowercase, spaces → dashes. Override map handles the special cases.
SECTION_SUFFIX_OVERRIDES = {
    "Cross-cutting / infrastructure": "projects",
    "This weekend (Mother's Day, 2026-05-09 / 2026-05-10)": None,  # skip
}

HIGH_CONFIDENCE = 0.45
AUTO_CONFIDENCE = 0.62


def section_to_suffix(section: str) -> str | None:
    if section in SECTION_SUFFIX_OVERRIDES:
        return SECTION_SUFFIX_OVERRIDES[section]
    # Heuristic: lower + spaces→dashes. Leave underscores intact.
    return section.lower().replace(" ", "-")


def parse_hopper_for_legacy(hopper: Path):
    """Yield (line_no, section, raw, push_date, text) for [>] lines lacking UUID."""
    section: str | None = None
    section_re = re.compile(r"^##\s+(.+?)\s*$")
    pushed_re = re.compile(
        r"^(?P<lead>\s*-\s+)\[>\]\s+(?P<pd>\d{4}-\d{2}-\d{2})\s*—\s*(?P<text>.*?)"
        r"(?:\s*<!--\s*things:[A-Za-z0-9]+\s*-->)?\s*$"
    )

    for i, raw in enumerate(hopper.read_text().splitlines()):
        sm = section_re.match(raw)
        if sm:
            section = sm.group(1)
            continue
        if "<!-- things:" in raw:
            continue  # already stamped
        pm = pushed_re.match(raw)
        if not pm:
            continue
        yield {
            "line_no": i,
            "section": section,
            "raw": raw,
            "push_date": pm.group("pd"),
            "text": pm.group("text").strip(),
        }


def candidates_by_suffix(suffix: str):
    """All Things tasks (any status) whose title ends with '— <suffix>'.

    Escape `_` in LIKE — sqlite treats it as a single-char wildcard, so
    `— daily_print` would silently also match `— daily print`.
    """
    conn = sqlite3.connect(f"file:{THINGS_DB}?mode=ro&immutable=1", uri=True)
    escaped = suffix.replace("\\", "\\\\").replace("_", "\\_").replace("%", "\\%")
    pattern = f"%— {escaped}"
    rows = conn.execute(
        "SELECT uuid, title, status, trashed, start, startBucket, startDate, "
        "stopDate, creationDate FROM TMTask "
        "WHERE type=0 AND title LIKE ? ESCAPE '\\' ORDER BY creationDate",
        (pattern,),
    ).fetchall()
    return [
        {
            "uuid": r[0],
            "title": r[1],
            "status": r[2],
            "trashed": r[3],
            "start": r[4],
            "start_bucket": r[5],
            "start_date_int": r[6],
            "stop_date": r[7],
            "creation_date": r[8],
        }
        for r in rows
    ]


def temporal_score(creation_epoch: float | None, push_date: str) -> float:
    """1.0 if the task was created within ±2d of the push date; decays linearly to 0
    at ±30d, then 0 beyond."""
    if creation_epoch is None:
        return 0.0
    from datetime import datetime
    try:
        push_ts = datetime.fromisoformat(push_date).timestamp()
    except ValueError:
        return 0.0
    delta_days = abs(creation_epoch - push_ts) / 86400.0
    if delta_days <= 2:
        return 1.0
    if delta_days >= 30:
        return 0.0
    return 1.0 - (delta_days - 2) / 28.0


def strip_suffix(title: str, suffix: str) -> str:
    needle = f"— {suffix}"
    if title.endswith(needle):
        return title[: -len(needle)].strip()
    return title


def score(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def best_match(
    text: str, candidates: list[dict], suffix: str, push_date: str
) -> tuple[dict, float, list]:
    """Combined score: 0.65 fuzzy title × 0.35 temporal proximity to push date."""
    scored = []
    for c in candidates:
        fz = score(text, strip_suffix(c["title"], suffix))
        ts = temporal_score(c.get("creation_date"), push_date)
        combined = 0.65 * fz + 0.35 * ts
        scored.append((c, combined, fz, ts))
    scored.sort(key=lambda t: t[1], reverse=True)
    if not scored:
        return None, 0.0, []
    top, top_combined, _, _ = scored[0]
    top3 = [
        {"uuid": c["uuid"], "title": c["title"], "combined": round(cb, 3),
         "fuzzy": round(fz, 3), "temporal": round(ts, 3)}
        for c, cb, fz, ts in scored[:3]
    ]
    return top, top_combined, top3


def build_proposals(hopper: Path) -> list[dict]:
    proposals = []
    by_section: dict[str, list[dict]] = {}
    for item in parse_hopper_for_legacy(hopper):
        by_section.setdefault(item["section"] or "(none)", []).append(item)

    for section, items in by_section.items():
        suffix = section_to_suffix(section)
        if suffix is None:
            for item in items:
                proposals.append({**item, "suffix": None, "match": None,
                                  "score": 0.0, "verdict": "skip_section"})
            continue
        cands = candidates_by_suffix(suffix)
        for item in items:
            match, sc, top3 = best_match(item["text"], cands, suffix, item["push_date"])
            verdict = (
                "auto" if sc >= AUTO_CONFIDENCE
                else "review" if sc >= HIGH_CONFIDENCE
                else "no_match"
            )
            proposals.append(
                {
                    **item,
                    "suffix": suffix,
                    "match": match,
                    "score": round(sc, 3),
                    "verdict": verdict,
                    "top3": top3,
                }
            )
    return proposals


def apply_proposals(hopper: Path, proposals: list[dict], high_confidence_only: bool):
    raw_lines = hopper.read_text().splitlines()
    applied = 0
    skipped = 0
    for p in proposals:
        if not p["match"]:
            skipped += 1
            continue
        if p["verdict"] in ("no_match", "skip_section"):
            skipped += 1
            continue
        if high_confidence_only and p["verdict"] != "auto":
            skipped += 1
            continue
        line = raw_lines[p["line_no"]]
        if "<!-- things:" in line:
            skipped += 1
            continue
        uuid = p["match"]["uuid"]
        raw_lines[p["line_no"]] = f"{line.rstrip()} <!-- things:{uuid} -->"
        applied += 1
    hopper.write_text("\n".join(raw_lines) + "\n")
    return applied, skipped


def render_report(proposals: list[dict]) -> str:
    by_verdict = {"auto": [], "review": [], "no_match": [], "skip_section": []}
    for p in proposals:
        by_verdict.setdefault(p["verdict"], []).append(p)

    out = ["# backfill_uuids — proposed mapping", ""]
    out.append(f"Hopper lines needing UUIDs: {len(proposals)}")
    out.append(f"  auto    (≥{AUTO_CONFIDENCE}): {len(by_verdict['auto'])}")
    out.append(f"  review  (≥{HIGH_CONFIDENCE}): {len(by_verdict['review'])}")
    out.append(f"  no_match            : {len(by_verdict['no_match'])}")
    out.append(f"  skip_section        : {len(by_verdict['skip_section'])}")
    out.append("")

    def fmt(p):
        text = p["text"][:90]
        m = p["match"]
        match_str = f'{m["uuid"]}: {m["title"]}' if m else "(none)"
        return f"  L{p['line_no']+1} · {p['section']} · score={p['score']}\n      hopper:  {text}\n      things:  {match_str}"

    for label in ("auto", "review", "no_match"):
        items = by_verdict.get(label, [])
        if not items:
            continue
        out.append(f"## {label.upper()} ({len(items)})")
        for p in items:
            out.append(fmt(p))
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hopper", default=str(DEFAULT_HOPPER))
    ap.add_argument("--apply", action="store_true",
                    help="actually stamp UUIDs into the hopper and run reconcile")
    ap.add_argument("--high-confidence-only", action="store_true",
                    help="when --apply: only stamp auto-confidence matches")
    ap.add_argument("--json", action="store_true",
                    help="output the proposals as JSON instead of human report")
    args = ap.parse_args()

    hopper = Path(args.hopper)
    proposals = build_proposals(hopper)

    if args.json:
        # Strip non-serializable bits
        for p in proposals:
            if p["match"]:
                p["match"] = {k: p["match"][k] for k in ("uuid", "title", "status")}
        json.dump(proposals, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0

    if not args.apply:
        print(render_report(proposals))
        return 0

    applied, skipped = apply_proposals(hopper, proposals, args.high_confidence_only)
    print(f"backfill applied: {applied} stamped, {skipped} skipped")
    print()
    print("--- running reconcile to roll up current state ---")
    proc = subprocess.run(
        [str(PYTHON), str(RECONCILE_PY)], capture_output=False
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
