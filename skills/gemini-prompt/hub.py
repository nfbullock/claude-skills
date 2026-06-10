#!/usr/bin/env python3
"""hub.py — deterministic path/numbering helper for the gemini-prompt skill.

The skill owns prose (writing the DR prompt, ingesting responses) and the
personal-memory queue. This helper owns the fiddly, error-prone mechanics:
resolving which project a cwd belongs to, allocating the next NN, and
pre-creating the paired .response.md stub so Nick never has to name a file.

Stdlib only. Run via ~/venv/default/bin/python.

Two-stage layout:
  research/requested/                   — flat staging dir, all pending prompts
    {project}-{NN}-{slug}.prompt.md       self-describing: project visible at a glance
    {project}-{NN}-{slug}.response.md     stub until Nick pastes the Gemini output

  research/<bucket>/                    — final: project prefix stripped on ingest
    {NN}-{slug}.prompt.md
    {NN}-{slug}.response.md
    <arc-dir>/                            full arcs live alongside prompt files

  research/adhoc/<topic>/               — final for ad-hoc topics
    {NN}-{slug}.prompt.md
    {NN}-{slug}.response.md

Commands:
  resolve [cwd]                 Print the project/bucket name implied by cwd (empty if none).
  new <project> <slug>          Allocate next NN, write stub to requested/.
                                Prints two lines: the .prompt.md path, then .response.md path.
  outstanding [project]         List pending prompts in requested/ (optional project filter).
  complete <project> <stem>     Move a filled pair from requested/ to the final bucket,
                                stripping the project prefix. Prints the two final paths.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

PROJECTS_ROOT = Path("/Users/dad/Documents/sandbox/projects")
RESEARCH_ROOT = PROJECTS_ROOT / "research"
REQUESTED = RESEARCH_ROOT / "requested"

# Projects with a dedicated research bucket at research/<name>/.
# Add an entry here when a project's research graduates from adhoc.
PROJECT_BUCKETS = {
    "music",
    "life-story",
    "food",
}

# Normalise cwd-resolved project names to their bucket slug.
BUCKET_ALIASES = {}

STUB_MARKER = "<!-- Paste the full Gemini Deep Research output below."


def stub_text(project: str, stem: str) -> str:
    return (
        f"# Response — {project}/{stem}\n\n"
        f"{STUB_MARKER} Prompt: {stem}.prompt.md -->\n"
    )


def get_final_dir(project: str) -> Path:
    bucket = BUCKET_ALIASES.get(project, project)
    if bucket in PROJECT_BUCKETS:
        return RESEARCH_ROOT / bucket
    return RESEARCH_ROOT / "adhoc" / bucket


def resolve(cwd: str | None) -> str:
    base = Path(cwd) if cwd else Path.cwd()
    try:
        rel = base.resolve().relative_to(PROJECTS_ROOT)
    except ValueError:
        return ""
    parts = rel.parts
    if not parts:
        return ""
    project = parts[0]
    if project == "research":
        return ""
    return BUCKET_ALIASES.get(project, project)


def _next_nn(project: str) -> str:
    """Allocate next NN across requested/ and the final bucket for this project."""
    bucket = BUCKET_ALIASES.get(project, project)
    nums = []
    # Scan requested/ for {project}-NN- prefixed files
    if REQUESTED.exists():
        pattern = re.compile(rf"^{re.escape(bucket)}-(\d+)-")
        for f in REQUESTED.glob(f"{bucket}-*.prompt.md"):
            m = pattern.match(f.name)
            if m:
                nums.append(int(m.group(1)))
    # Scan final bucket for NN- prefixed files
    final_dir = get_final_dir(project)
    if final_dir.exists():
        for f in final_dir.glob("*.prompt.md"):
            m = re.match(r"^(\d+)-", f.name)
            if m:
                nums.append(int(m.group(1)))
    nxt = (max(nums) + 1) if nums else 1
    return f"{nxt:02d}"


def new(project: str, slug: str) -> None:
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    bucket = BUCKET_ALIASES.get(project, project)
    REQUESTED.mkdir(parents=True, exist_ok=True)
    nn = _next_nn(project)
    stem = f"{bucket}-{nn}-{slug}"
    prompt_path = REQUESTED / f"{stem}.prompt.md"
    response_path = REQUESTED / f"{stem}.response.md"
    if not response_path.exists():
        response_path.write_text(stub_text(bucket, stem))
    print(prompt_path)
    print(response_path)


def complete(project: str, stem: str) -> None:
    """Move filled pair from requested/ to final bucket, stripping project prefix."""
    bucket = BUCKET_ALIASES.get(project, project)
    # Strip "{bucket}-" prefix to get the bare stem for the final bucket
    prefix = f"{bucket}-"
    bare_stem = stem[len(prefix):] if stem.startswith(prefix) else stem
    final_dir = get_final_dir(project)
    final_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".prompt.md", ".response.md"):
        src = REQUESTED / f"{stem}{ext}"
        dst = final_dir / f"{bare_stem}{ext}"
        if not src.exists():
            print(f"warning: {src} not found, skipping", file=sys.stderr)
            continue
        shutil.move(str(src), dst)
        print(dst)


def outstanding(project: str | None) -> None:
    if not REQUESTED.exists():
        return
    bucket_filter = BUCKET_ALIASES.get(project, project) if project else None
    for prompt in sorted(REQUESTED.glob("*.prompt.md")):
        # Extract project from filename: {project}-{NN}-{slug}.prompt.md
        m = re.match(r"^([^-]+(?:-[^-]+)?)-(\d+)-", prompt.name)
        file_project = m.group(1) if m else "unknown"
        if bucket_filter and file_project != bucket_filter:
            continue
        response = prompt.with_suffix("").with_suffix(".response.md")
        unfilled = (not response.exists()) or (
            STUB_MARKER in response.read_text()
            and len(response.read_text().strip().splitlines()) <= 3
        )
        if unfilled:
            print(f"{file_project}\t{prompt.name}")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "resolve":
        print(resolve(rest[0] if rest else None))
    elif cmd == "new":
        if len(rest) < 2:
            print("usage: hub.py new <project> <slug>", file=sys.stderr)
            return 2
        new(rest[0], rest[1])
    elif cmd == "complete":
        if len(rest) < 2:
            print("usage: hub.py complete <project> <stem>", file=sys.stderr)
            return 2
        complete(rest[0], rest[1])
    elif cmd == "outstanding":
        outstanding(rest[0] if rest else None)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
