#!/usr/bin/env python3
"""hub.py — deterministic path/numbering helper for the gemini-prompt skill.

The skill owns prose (writing the DR prompt, ingesting responses) and the
personal-memory queue. This helper owns the fiddly, error-prone mechanics:
resolving which project a cwd belongs to, allocating the next NN, and
pre-creating the paired .response.md stub so Nick never has to name a file.

Stdlib only. Run via ~/venv/default/bin/python.

Two-stage layout (LAYOUT=B, canonical 2026-07-12 — the stem never changes;
staging and final share the {project}-{NN}-{slug} name):
  research/requested/                   — flat staging dir, all pending prompts
    {project}-{NN}-{slug}.prompt.md       self-describing: project visible at a glance
    {project}-{NN}-{slug}.response.md     stub until Nick pastes the Gemini output

  research/prompts/<bucket>/            — final: pair moved here on ingest, prefix kept
    {bucket}-{NN}-{slug}.prompt.md
    {bucket}-{NN}-{slug}.response.md
    <arc-dir>/                            full arcs live alongside prompt files

  research/adhoc/<topic>/               — final for ad-hoc topics, prefix kept
    {topic}-{NN}-{slug}.prompt.md         (pre-2026-07-12 pairs are bare NN-{slug};
    {topic}-{NN}-{slug}.response.md        numbering tolerates both)

  research/prompts/<parent>/<subtopic>/ — bucket with subtopic subfolders
    {subtopic}-{NN}-{slug}.prompt.md      (subtopic is the routing key; see
    {subtopic}-{NN}-{slug}.response.md     SUBTOPIC_BUCKETS, e.g. dx/code-review-bottleneck)

Commands:
  resolve [cwd]                 Print the project/bucket name implied by cwd (empty if none).
  new <project> <slug>          Allocate next NN, write stub to requested/.
                                Prints two lines: the .prompt.md path, then .response.md path.
  outstanding [project]         List pending prompts in requested/ (optional project filter).
  complete <project> <stem>     Move a filled pair from requested/ to the final bucket,
                                keeping the full stem. Prints the two final paths.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

PROJECTS_ROOT = Path("/Users/dad/Documents/sandbox")
RESEARCH_ROOT = PROJECTS_ROOT / "research"
REQUESTED = RESEARCH_ROOT / "requested"
PROMPTS_ROOT = RESEARCH_ROOT / "prompts"

# Projects with a dedicated research bucket at research/prompts/<name>/.
# Add an entry here when a project's research graduates from adhoc.
PROJECT_BUCKETS = {
    "music",
    "life-story",
    "food",
    "dahlias-laptop",
    "dx",
    "kids-skills",
    "reading",
    "health",
}

# Buckets organised into subtopic subfolders: research/prompts/<parent>/<subtopic>/.
# The subtopic slug is the routing key passed to new/complete/outstanding,
# so each subtopic gets its own NN numbering and its own synthesis.
SUBTOPIC_BUCKETS = {
    "code-review-bottleneck": "dx",
    "team-memory": "dx",
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
    if bucket in SUBTOPIC_BUCKETS:
        return PROMPTS_ROOT / SUBTOPIC_BUCKETS[bucket] / bucket
    if bucket in PROJECT_BUCKETS:
        return PROMPTS_ROOT / bucket
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
    if REQUESTED.exists():
        pattern = re.compile(rf"^{re.escape(bucket)}-(\d+)-")
        for f in REQUESTED.glob(f"{bucket}-*.prompt.md"):
            m = pattern.match(f.name)
            if m:
                nums.append(int(m.group(1)))
    final_dir = get_final_dir(project)
    if final_dir.exists():
        # Tolerate both prefixed stems and legacy bare NN- stems.
        pattern = re.compile(rf"^(?:{re.escape(bucket)}-)?(\d+)-")
        for f in final_dir.glob("*.prompt.md"):
            m = pattern.match(f.name)
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
    """Move filled pair from requested/ to the final bucket, keeping the stem."""
    final_dir = get_final_dir(project)
    final_dir.mkdir(parents=True, exist_ok=True)
    for ext in (".prompt.md", ".response.md"):
        src = REQUESTED / f"{stem}{ext}"
        dst = final_dir / f"{stem}{ext}"
        if not src.exists():
            print(f"warning: {src} not found, skipping", file=sys.stderr)
            continue
        shutil.move(str(src), dst)
        print(dst)


def _stem_project(name: str) -> str:
    known = sorted(
        PROJECT_BUCKETS | set(SUBTOPIC_BUCKETS) | set(BUCKET_ALIASES),
        key=len,
        reverse=True,
    )
    for key in known:
        if name.startswith(f"{key}-"):
            return key
    m = re.match(r"^([^-]+(?:-[^-]+)?)-(\d+)-", name)
    return m.group(1) if m else "unknown"


def outstanding(project: str | None) -> None:
    if not REQUESTED.exists():
        return
    bucket_filter = BUCKET_ALIASES.get(project, project) if project else None
    for prompt in sorted(REQUESTED.glob("*.prompt.md")):
        file_project = _stem_project(prompt.name)
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
