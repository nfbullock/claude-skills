#!/usr/bin/env python3
"""Deterministic status scan over Nick's music project (the four-track umbrella).

Cowork pattern (same as skills-status / projects-status): this script emits
deterministic JSON about where each track stands and the state of the source
reservoir. Claude reads the JSON and writes the report with editorial judgment.
The script makes NO qualitative calls — it counts, dates, and extracts.

Usage:
    scan.py            # human-readable summary
    scan.py --json     # raw JSON for Claude to build the report from
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

# Resolve the music project root. The skill lives at
# projects/claude_skills/music-status/; the music project is a sibling under
# projects/music/. Allow an env-independent walk.
ROOT = Path("/Users/dad/Documents/sandbox/projects/music")


def _age_days(p: Path) -> float:
    return round((time.time() - p.stat().st_mtime) / 86400, 1)


def _newest(md_files: list[Path]) -> dict | None:
    md_files = [f for f in md_files if f.name != "CLAUDE.md"]
    if not md_files:
        return None
    newest = max(md_files, key=lambda f: f.stat().st_mtime)
    return {
        "file": newest.name,
        "modified": time.strftime("%Y-%m-%d", time.localtime(newest.stat().st_mtime)),
        "age_days": _age_days(newest),
    }


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def _section(text: str, header: str) -> str:
    """Return the body of a `## header` section up to the next `## `."""
    m = re.search(rf"^##\s+{re.escape(header)}\s*$", text, re.M)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^##\s+", text[start:], re.M)
    return text[start : start + nxt.start()] if nxt else text[start:]


def scan_gym() -> dict:
    d = ROOT / "gym"
    lessons = sorted((d / "lessons").glob("*.md"))
    state = _read(d / "state.md")
    # Phase line
    phase = ""
    pm = re.search(r"^\*\*(Phase[^*]+)\*\*", _section(state, "Phase"), re.M)
    if pm:
        phase = pm.group(1).strip()
    # "Next suggested" rotation row
    nxt = ""
    nm = re.search(r"\|\s*Next suggested\s*\|(.+?)\|", state)
    if nm:
        nxt = nm.group(1).strip()
    # Count queued (printed, not practiced) lessons from the history table
    queued = len(re.findall(r"\|\s*queued", state))
    return {
        "track": "gym",
        "lesson_count": len(lessons),
        "latest": _newest(lessons),
        "phase": phase,
        "next_suggested": nxt[:300],
        "queued_lessons": queued,
        "retro_required": True,  # gym blocks next lesson on prior retro
    }


def scan_playground() -> dict:
    d = ROOT / "playground"
    lessons = sorted((d / "lessons").glob("*.md"))
    journal = _read(d / "JOURNAL.md")
    phase = ""
    pm = re.search(r"^##\s+Current phase\s*\n+(.+)$", journal, re.M)
    if pm:
        phase = pm.group(1).strip()
    cover_phase = ""
    cm = re.search(r"^##\s+Cover phase\s*\n+(.+)$", journal, re.M)
    if cm:
        cover_phase = cm.group(1).strip()[:120]
    # Active pulls: ### headers under the "Active pulls" section
    pulls_body = _section(journal, "Active pulls")
    pulls = re.findall(r"^###\s+(.+?)\s*$", pulls_body, re.M)
    # de-dup while preserving order (journal has a duplicated anchor)
    seen, uniq = set(), []
    for p in pulls:
        if p.lower().startswith("active pulls"):
            continue
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    songs = re.findall(r"^- Song \d+", _section(journal, "Songs finished"), re.M)
    return {
        "track": "playground",
        "lesson_count": len(lessons),
        "latest": _newest(lessons),
        "phase": phase,
        "cover_phase": cover_phase,
        "songs_finished": len(songs),
        "active_cover_pulls": uniq,
        "retro_required": True,  # playground blocks next lesson on prior retro
    }


def scan_stage() -> dict:
    d = ROOT / "stage"
    lessons = sorted(f for f in d.glob("*.md") if f.name != "CLAUDE.md")
    return {
        "track": "stage",
        "lesson_count": len(lessons),
        "latest": _newest(lessons),
        "retro_required": False,  # stage retros optional, never block
    }


def scan_office() -> dict:
    d = ROOT / "office"
    lessons = sorted((d / "lessons").glob("*.md"))
    return {
        "track": "office",
        "lesson_count": len(lessons),
        "latest": _newest(lessons),
        "retro_required": False,  # office retros optional, never block
    }


def scan_sources() -> dict:
    s = ROOT / "sources"
    synthesis = sorted((s / "synthesis").glob("*.md"))
    extracted = {p.name for p in (s / "extracted").iterdir() if p.is_dir()} if (s / "extracted").exists() else set()
    syn_slugs = {p.stem for p in synthesis}
    # Holes: a raw source dir with a source file but no synthesis of the same slug.
    holes = []
    raw = s / "raw"
    if raw.exists():
        for child in sorted(raw.iterdir()):
            if not child.is_dir():
                continue
            slug = child.name
            has_source = any(child.glob("source.*")) or any(child.iterdir())
            if has_source and slug not in syn_slugs:
                # classify: extracted-but-not-synthesized vs raw-only
                state = "extracted, not synthesized" if slug in extracted else "raw only"
                holes.append({"slug": slug, "state": state})
    # REQUESTED.md open Tier-1 rows (load-bearing now)
    req = _read(raw / "REQUESTED.md")
    tier1 = _section(req, "Tier 1 — Load-bearing now")
    tier1_open = len(re.findall(r"^\|\s*`", tier1, re.M))
    return {
        "synthesis_count": len(synthesis),
        "synthesis_slugs": sorted(syn_slugs),
        "holes": holes,
        "tier1_open_requests": tier1_open,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not ROOT.exists():
        print(f"music project not found: {ROOT}", file=sys.stderr)
        return 1

    report = {
        "scanned_at": time.strftime("%Y-%m-%d %H:%M", time.localtime()),
        "tracks": [scan_gym(), scan_playground(), scan_stage(), scan_office()],
        "sources": scan_sources(),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    # human-readable fallback (Claude normally reads --json)
    print(f"# music-status  ({report['scanned_at']})\n")
    for t in report["tracks"]:
        latest = t.get("latest") or {}
        line = f"## {t['track']:11} {t['lesson_count']} lessons"
        if latest:
            line += f"  | latest {latest['file']} ({latest['modified']}, {latest['age_days']}d ago)"
        print(line)
        if t.get("phase"):
            print(f"     phase: {t['phase']}")
        if t.get("cover_phase"):
            print(f"     cover phase: {t['cover_phase']}")
        if t.get("active_cover_pulls"):
            print(f"     cover pulls: {len(t['active_cover_pulls'])}")
            for p in t["active_cover_pulls"]:
                print(f"        - {p}")
        if t.get("queued_lessons"):
            print(f"     queued (printed, not practiced): {t['queued_lessons']}")
        if t.get("next_suggested"):
            print(f"     next: {t['next_suggested'][:120]}")
    src = report["sources"]
    print(f"\n## sources    {src['synthesis_count']} syntheses | "
          f"{len(src['holes'])} holes | {src['tier1_open_requests']} open Tier-1 requests")
    for h in src["holes"]:
        print(f"     hole: {h['slug']} ({h['state']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
