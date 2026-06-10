#!/usr/bin/env python3
"""
add_to_things.py — turn a transcript into a Things 3 task.

CLI:
    python handlers/add_to_things.py <transcript-file>
    python handlers/add_to_things.py <transcript-file> --audio <m4a-file>
    python handlers/add_to_things.py <transcript-file> --dry-run

Pipeline:
    1. Opus 4.7 reads the transcript and proposes:
         {best_title, clarity: clear|needs_research, description}
    2. Notes body assembled as:
         [description if any]
         ---
         transcript: <verbatim transcript>
         audio: <path to .m4a, if provided>
    3. Calls things.py add with --title and --notes. If clarity == 'needs_research',
       adds the `research` tag. Inbox by default (no --list / --when).

Auth: shells out to `claude -p` so it inherits Claude Code auth.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CLAUDE_BIN = "claude"
MODEL = "opus"
THINGS_PY = Path(__file__).resolve().parents[2] / "things" / "things.py"

PROMPT = """You are turning a voice-recorded thought into a Things 3 task. \
The transcript below is what Nick said. Produce the cleanest possible task \
title plus an optional short clarifying description.

Output format: one JSON object on stdout, nothing else, no markdown fence:

{"best_title": "<imperative-form task title, ~5-10 words>", \
"clarity": "clear" | "needs_research", \
"description": "<optional 1-2 sentence clarification, or empty string>"}

Rules:
- best_title: imperative voice ("Email Sarah about the Tahoe trip" not "I \
should email Sarah"). Drop filler ("um", "uh", "I think I want to..."). \
Preserve specifics (names, places, dates).
- clarity = "needs_research" if the task requires Nick to think more before \
he can act on it (open-ended decisions, "look into X", things he doesn't yet \
know how to start). Otherwise "clear".
- description: ONLY include if the title can't carry the necessary context. \
Don't paraphrase the whole transcript — the transcript is appended verbatim \
elsewhere.

Transcript:

<transcript>
%(transcript)s
</transcript>
"""


def _claude(prompt: str) -> str:
    proc = subprocess.run(
        [CLAUDE_BIN, "-p", "--model", MODEL, "--output-format", "json"],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def _extract_json_object(text: str) -> dict:
    try:
        envelope = json.loads(text)
        inner = envelope.get("result", text) if isinstance(envelope, dict) else text
    except json.JSONDecodeError:
        inner = text

    if isinstance(inner, dict):
        return inner

    m = re.search(r"\{.*\}", inner, re.DOTALL)
    if not m:
        sys.exit(f"add_to_things: could not find JSON object in model output:\n{inner}")
    return json.loads(m.group(0))


def synthesize(transcript: str) -> dict:
    raw = _claude(PROMPT % {"transcript": transcript})
    obj = _extract_json_object(raw)
    if not obj.get("best_title"):
        sys.exit("add_to_things: model did not return best_title")
    obj.setdefault("clarity", "clear")
    obj.setdefault("description", "")
    if obj["clarity"] not in {"clear", "needs_research"}:
        obj["clarity"] = "clear"
    return obj


def build_notes(transcript: str, description: str, audio: Path | None) -> str:
    parts: list[str] = []
    if description.strip():
        parts.append(description.strip())
        parts.append("---")
    parts.append(f"transcript: {transcript.strip()}")
    if audio is not None:
        parts.append(f"audio: {audio}")
    return "\n".join(parts)


def push_to_things(title: str, notes: str, tags: list[str], dry_run: bool) -> None:
    if not THINGS_PY.exists():
        sys.exit(f"add_to_things: things.py not found at {THINGS_PY}")
    cmd: list[str] = [sys.executable, str(THINGS_PY), "add", "--title", title, "--notes", notes]
    for t in tags:
        cmd += ["--tag", t]
    if dry_run:
        cmd.append("--dry-run")
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(prog="add_to_things")
    p.add_argument("transcript", type=Path)
    p.add_argument("--audio", type=Path, default=None,
                   help="Path to original .m4a, appended to notes for traceback")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    transcript = args.transcript.read_text().strip()
    plan = synthesize(transcript)

    tags = ["research"] if plan["clarity"] == "needs_research" else []
    notes = build_notes(transcript, plan["description"], args.audio)

    push_to_things(plan["best_title"], notes, tags, args.dry_run)
    print(json.dumps({"title": plan["best_title"], "clarity": plan["clarity"], "tags": tags}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
