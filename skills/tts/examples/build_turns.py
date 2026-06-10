"""Per-project turn builder. Copy this into a new podcast project, edit, run.

Reads markdown scripts -> emits <name>.turns.json that the renderer consumes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the renderer/ dir importable regardless of where we're run from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "renderer"))

from chunker import apply_pronunciation_tweaks, compile_tweaks, parse_combined, subsplit_long  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPT_DIR = PROJECT_ROOT / "scripts"
OUT_DIR = PROJECT_ROOT / "build"

# Edit per project --------------------------------------------------------

SPEAKERS = ("HOST", "GUEST")

# (pattern, replacement) — pattern is wrapped in \b...\b by default.
PRONUNCIATION = [
    ("API", "A P I"),
    ("APIs", "A P Is"),
    ("URL", "U R L"),
]

GROUPS = {
    "episode": [SCRIPT_DIR / "episode.md"],
    # "act1": [SCRIPT_DIR / "act1.md"],
    # "act2": [SCRIPT_DIR / "act2.md"],
}

# -------------------------------------------------------------------------


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    tweaks = compile_tweaks(PRONUNCIATION)

    for name, paths in GROUPS.items():
        turns = parse_combined(paths, speakers=SPEAKERS)
        turns = subsplit_long(turns, max_words=200)
        turns = [(s, apply_pronunciation_tweaks(t, tweaks)) for s, t in turns]

        total_words = sum(len(t.split()) for _, t in turns)
        per_speaker = {sp: sum(1 for s, _ in turns if s == sp) for sp in SPEAKERS}
        max_wc = max((len(t.split()) for _, t in turns), default=0)
        print(
            f"{name}: {len(turns)} turns ({per_speaker}), "
            f"{total_words} words, longest turn {max_wc} words"
        )

        out_path = OUT_DIR / f"{name}.turns.json"
        out_path.write_text(json.dumps(turns, indent=2))
        print(f"  -> {out_path}")


if __name__ == "__main__":
    main()
