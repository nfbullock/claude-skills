"""Build turns for weekly-review touchstone renders.

Spoken-word format: single NARRATOR voice (Fred). Source script lives at
review/weekly/<date>-walk.md; this script strips frontmatter, prefixes each
paragraph with [NARRATOR], and emits the turns.json for the per-turn renderer.

Add new weekly entries to ENTRIES as Fridays roll over.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "renderer"))

from chunker import (  # noqa: E402
    apply_pronunciation_tweaks,
    compile_tweaks,
    parse_combined,
    subsplit_long,
)

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPT_DIR = PROJECT_ROOT / "scripts"
OUT_DIR = PROJECT_ROOT / "build"
WEEKLY_DIR = Path("/Users/dad/Documents/sandbox/review/weekly")

SPEAKERS = ("NARRATOR",)

# Pronunciation regex pairs. Patterns get \b...\b wrapping by compile_tweaks.
# Project names, acronyms, terms Fred uses by name in the touchstone.
PRONUNCIATION = [
    # Project names that might mangle
    ("OP-1", "O P one"),
    ("KO II", "K O two"),
    ("KO2", "K O two"),
    ("TRX", "T R X"),
    ("TTS", "T T S"),
    ("RP", "R P"),
    ("API", "A P I"),
    ("shim_api", "shim A P I"),
    ("token_economics", "token economics"),
    ("daily_print", "daily print"),
    # People
    ("Farrah", "FAIR uh"),
    ("Plaud", "Plawd"),
    # Numbers / dates the model sometimes flubs
    ("5am", "five A M"),
    ("4PM", "four P M"),
    ("6x", "six times"),
    ("90", "ninety"),
    ("43K", "forty three thousand"),
    ("2028", "twenty twenty eight"),
    ("2026", "twenty twenty six"),
]

FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

ENTRIES = {
    "2026-05-15": WEEKLY_DIR / "2026-05-15-walk.md",
    "2026-05-17": WEEKLY_DIR / "2026-05-17-walk.md",
}


def tag_for_narration(text: str) -> str:
    """Strip frontmatter, then prefix [NARRATOR] to each paragraph.
    Headers are passed through; the chunker strips them downstream.
    Bracketed stage directions like [pause] are stripped by the chunker too.
    Horizontal rules (---) are dropped as they're not narration."""
    text = FRONTMATTER_RE.sub("", text)
    out_lines: list[str] = []
    in_paragraph = False
    for raw_line in text.split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            out_lines.append("")
            in_paragraph = False
        elif stripped.startswith("#"):
            out_lines.append(line)
            in_paragraph = False
        elif stripped == "---":
            # horizontal rule, drop
            out_lines.append("")
            in_paragraph = False
        else:
            if not in_paragraph:
                out_lines.append(f"[NARRATOR] {line}")
                in_paragraph = True
            else:
                out_lines.append(line)
    return "\n".join(out_lines)


def main() -> None:
    SCRIPT_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)
    tweaks = compile_tweaks(PRONUNCIATION)

    for name, source_path in ENTRIES.items():
        if not source_path.exists():
            print(f"{name}: source not found at {source_path}, skipping")
            continue
        tagged_path = SCRIPT_DIR / f"{name}.md"
        tagged_path.write_text(tag_for_narration(source_path.read_text()))

        turns = parse_combined([tagged_path], speakers=SPEAKERS)
        turns = subsplit_long(turns, max_words=200)
        turns = [(s, apply_pronunciation_tweaks(t, tweaks)) for s, t in turns]

        total_words = sum(len(t.split()) for _, t in turns)
        max_wc = max((len(t.split()) for _, t in turns), default=0)
        print(
            f"{name}: {len(turns)} turns, {total_words} words, longest turn {max_wc} words"
        )

        out_path = OUT_DIR / f"{name}.turns.json"
        out_path.write_text(json.dumps(turns, indent=2))
        print(f"  -> {out_path}")


if __name__ == "__main__":
    main()
