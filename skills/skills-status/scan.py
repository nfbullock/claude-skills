#!/usr/bin/env python3
"""
scan.py — Claude skills status scan.

Walks projects/claude_skills/*/SKILL.md, reads frontmatter, buckets each skill
by status. Stubs always show; stubs past the staleness threshold yell louder.
SKILL.md files without a status field are surfaced as needing retrofit.

Output: JSON to stdout. The /skills-status skill formats it for Nick.
"""

from __future__ import annotations
import argparse
import difflib
import json
import re
import sys
import time
from pathlib import Path

SKILLS_ROOT = Path("/Users/dad/Documents/sandbox/projects/claude_skills")
STALE_STUB_DAYS = 30


def parse_frontmatter(skill_md: Path) -> dict | None:
    if not skill_md.exists():
        return None
    try:
        text = skill_md.read_text(errors="ignore")
    except OSError:
        return None
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def newest_mtime(path: Path) -> float:
    """Newest mtime in the directory tree, or the dir's own mtime if empty."""
    newest = path.stat().st_mtime
    for p in path.rglob("*"):
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if m > newest:
            newest = m
    return newest


def scan() -> dict:
    now = time.time()
    skills = []

    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith("."):
            continue

        skill_md = skill_dir / "SKILL.md"
        entry: dict = {
            "skill": skill_dir.name,
            "status": None,
            "bucket": None,
            "days_since_touched": None,
        }

        if not skill_md.exists():
            entry["bucket"] = "no_skill_md"
            skills.append(entry)
            continue

        fm = parse_frontmatter(skill_md)
        days = round((now - newest_mtime(skill_dir)) / 86400, 1)
        entry["days_since_touched"] = days

        if fm is None:
            entry["bucket"] = "no_frontmatter"
            skills.append(entry)
            continue

        status = fm.get("status")
        entry["status"] = status

        if status is None:
            entry["bucket"] = "no_status"
        elif status == "active":
            entry["bucket"] = "active"
        elif status == "stub":
            entry["bucket"] = "stale_stub" if days > STALE_STUB_DAYS else "stub"
        elif status == "deprecated":
            entry["bucket"] = "deprecated"
        else:
            entry["bucket"] = f"unknown_status:{status}"

        skills.append(entry)

    return {
        "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "skills_root": str(SKILLS_ROOT),
        "stale_stub_threshold_days": STALE_STUB_DAYS,
        "skills": skills,
    }


def list_skill_dirs() -> list[str]:
    return sorted(d.name for d in SKILLS_ROOT.iterdir()
                  if d.is_dir() and not d.name.startswith("."))


def resolve_target(name: str) -> dict:
    candidates = list_skill_dirs()
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


def classify_skill(skill_dir: Path) -> dict:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"route": "bootstrap", "confidence": "confident",
                "reasons": ["SKILL.md missing"]}
    fm = parse_frontmatter(skill_md)
    if not fm:
        return {"route": "bootstrap", "confidence": "confident",
                "reasons": ["SKILL.md has no frontmatter"]}
    status = fm.get("status", "").strip()
    if not status:
        return {"route": "bootstrap", "confidence": "borderline",
                "reasons": ["status field missing — frontmatter retrofit"]}
    if status == "stub":
        return {"route": "develop", "confidence": "confident",
                "reasons": ["status: stub"]}
    if status == "active":
        return {"route": "refine", "confidence": "confident",
                "reasons": ["status: active — open-ended refine conversation"]}
    if status == "deprecated":
        return {"route": "cleanup", "confidence": "confident",
                "reasons": ["status: deprecated"]}
    return {"route": "unknown", "confidence": "borderline",
            "reasons": [f"unrecognized status: {status}"]}


def file_text(path: Path, max_chars: int = 8000) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return None
    return text if len(text) <= max_chars else text[:max_chars] + "\n...[truncated]"


def file_listing(skill_dir: Path) -> list[dict]:
    out = []
    now = time.time()
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file():
            continue
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        out.append({
            "file": str(p.relative_to(skill_dir)),
            "mtime_days_ago": round((now - m) / 86400, 1),
        })
    return out


def scan_single_skill(name: str) -> dict:
    resolution = resolve_target(name)
    payload: dict = {"name_resolution": resolution}
    if resolution["not_found"] or resolution["ambiguous"] or resolution["resolved"] is None:
        if resolution["not_found"]:
            payload["route"] = "bootstrap_greenfield"
            payload["confidence"] = "confident"
            payload["reasons"] = [f"no skill directory matched '{name}'"]
        return payload

    resolved = resolution["resolved"]
    skill_dir = SKILLS_ROOT / resolved
    skill_md = skill_dir / "SKILL.md"
    fm = parse_frontmatter(skill_md) or {}
    classification = classify_skill(skill_dir)
    days = round((time.time() - newest_mtime(skill_dir)) / 86400, 1)
    payload.update({
        "skill": resolved,
        "route": classification["route"],
        "confidence": classification["confidence"],
        "reasons": classification["reasons"],
        "days_since_touched": days,
        "frontmatter": fm,
        "skill_md_text": file_text(skill_md),
        "file_listing": file_listing(skill_dir),
    })
    scan_py = skill_dir / "scan.py"
    if scan_py.exists():
        payload["scan_py_preview"] = file_text(scan_py, max_chars=4000)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Skills status scan.")
    parser.add_argument("target", nargs="?", default=None,
                        help="Optional skill name. If supplied, scope to that skill.")
    args = parser.parse_args()

    if args.target:
        out = {
            "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "skills_root": str(SKILLS_ROOT),
            "mode": "single_target",
            "target": scan_single_skill(args.target),
        }
    else:
        out = scan()
        out["mode"] = "sweep"
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
