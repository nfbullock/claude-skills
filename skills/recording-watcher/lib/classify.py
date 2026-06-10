#!/usr/bin/env python3
"""
classify.py — Opus 4.7 reasoning over a transcript → {route, confidence, reasoning}.

CLI:
    python -m lib.classify <transcript-file>
    cat transcript.txt | python -m lib.classify -

Prints a single JSON object on stdout. Routes (v1):
    review_recording   — reflective content; downstream review factory picks cadence
    add_to_things      — "remind me to ..." / imperative capture
    unknown            — too short, ambient, off-topic

Inference posture: take all the time it needs. Pipeline is async; quality > speed.

Auth: this script shells out to `claude -p` so it inherits the same auth Claude
Code uses interactively. No ANTHROPIC_API_KEY required in env.
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

PROMPT = """You are the classifier inside Nick's recording-watcher pipeline. \
Nick records short audio thoughts on his phone via Just Press Record. The \
recording you're seeing has already been transcribed. Your job is to pick \
exactly one route for it.

Routes:

- `review_recording` — reflective content. Nick is talking *about* his life, \
work, projects, feelings, observations. Often (not always) he self-declares: \
"this is my daily review", "this is my weekly review", "monthly review", etc. \
Self-declaration is a strong signal but not required. If absent, fall back to \
content-shape: discursive, first-person, reflective, multi-topic, or has any \
"how am I doing / what did I do today" flavor → review_recording.

- `add_to_things` — task / capture / imperative. "Remind me to fix the gate", \
"I need to email so-and-so", "buy more coffee filters", "todo: ...". One \
discrete action or a short cluster of obvious next-actions. No reflection.

- `unknown` — empty, near-empty, mostly silence, ambient noise, accidental \
recording, or genuinely off-topic gibberish. When in doubt between \
review_recording and unknown, prefer review_recording. When in doubt between \
review_recording and add_to_things and there's ANY reflective content, prefer \
review_recording.

Output format: a single JSON object on stdout, nothing else, no markdown \
fence, no preamble:

{"route": "review_recording" | "add_to_things" | "unknown", \
"confidence": 0.0-1.0, \
"reasoning": "one or two sentences citing the specific cues you used"}

Transcript follows between the <transcript> tags.

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
    """The Claude CLI in --output-format json returns its own envelope with a
    `result` field that contains the model's stdout text. Pull the model's
    text out, then locate the inner JSON object."""
    try:
        envelope = json.loads(text)
        inner = envelope.get("result", text) if isinstance(envelope, dict) else text
    except json.JSONDecodeError:
        inner = text

    if isinstance(inner, dict):
        return inner

    m = re.search(r"\{.*\}", inner, re.DOTALL)
    if not m:
        sys.exit(f"classify: could not find JSON object in model output:\n{inner}")
    return json.loads(m.group(0))


def classify(transcript: str) -> dict:
    raw = _claude(PROMPT % {"transcript": transcript})
    obj = _extract_json_object(raw)

    route = obj.get("route")
    if route not in {"review_recording", "add_to_things", "unknown"}:
        sys.exit(f"classify: invalid route in model output: {route!r}")
    obj.setdefault("confidence", 0.0)
    obj.setdefault("reasoning", "")
    return obj


def main() -> int:
    p = argparse.ArgumentParser(prog="lib.classify")
    p.add_argument("transcript", help="transcript file path, or '-' for stdin")
    args = p.parse_args()

    if args.transcript == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.transcript).read_text()

    print(json.dumps(classify(text.strip())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
