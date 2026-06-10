"""Build turns for pull-learning chapter renders.

Spoken-word format: single NARRATOR voice. Source chapters live in the research arc
directory; this script preprocesses them with [NARRATOR] paragraph tags and emits
the turns.json for the per-turn renderer.

Add chapters to CHAPTERS as they're ready to render.
"""

from __future__ import annotations

import json
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
ARC_DIR = Path("/Users/dad/Documents/sandbox/projects/research/pull-learning")

SPEAKERS = ("NARRATOR",)

# Pronunciation regex pairs. Patterns get \b...\b wrapping by compile_tweaks.
# Conservative initial set; expand each time the model mangles a term.
PRONUNCIATION = [
    ("Illich", "Ill itch"),
    ("Papert", "Pay pert"),
    ("Knowles", "Noles"),
    ("andragogy", "an druh GOH jee"),
    ("Mindstorms", "Mind storms"),
    ("Csikszentmihalyi", "chick sent me HIGH ee"),
    ("McGilchrist", "muh GILL krist"),
    ("Hillman", "Hill man"),
    ("Polanyi", "po LAHN yee"),
    ("Montessori", "MON tess OR ee"),
    ("Hirsch", "Hersh"),
    ("Sweller", "SWELL er"),
    ("Bjork", "be ORK"),
    ("Ericsson", "ERR ick son"),
    ("Kierkegaard", "KEER kuh gard"),
    ("Welwood", "WELL wood"),
    ("Hollis", "HOLL iss"),
    ("daimon", "DYE mon"),
    ("metaxu", "meh TAX oo"),
    ("Reggio", "REJ ee oh"),
    ("Malaguzzi", "mal uh GOOT see"),
    ("Paley", "PAY lee"),
    ("Zettelkasten", "ZET ul kass ten"),
    ("Ahrens", "AR ens"),
    ("Matuschak", "muh TOO shack"),
    ("Luhmann", "LOO mun"),
    ("Roediger", "RED uh ger"),
    ("Kornell", "kor NELL"),
    ("Nückles", "NUCK less"),
    ("Macnamara", "mack nuh MAR uh"),
    ("Hambrick", "HAM brick"),
    ("Kalyuga", "kuh LYOO guh"),
    ("Stanovich", "stan OH vitch"),
    ("Hirsch", "Hersh"),
    ("Holt", "Holt"),
    ("Gopnik", "GOP nick"),
    # acronyms / tech terms
    ("REPL", "REP ul"),
    ("MOOC", "mook"),
    ("MOOCs", "mooks"),
    ("ARPANET", "ARPA net"),
    ("pytest", "pie test"),
    ("Duolingo", "doo oh LING go"),
    ("LOGO", "LOH go"),
    ("IFS", "I F S"),
    ("GTD", "G T D"),
    ("PKM", "P K M"),
    ("TTS", "T T S"),
    ("SRS", "S R S"),
    ("PDF", "P D F"),
    ("PDFs", "P D Fs"),
    ("ToM", "T o M"),
    ("OP-1", "O P one"),
    ("KSC", "K S C"),
    ("MicroWorlds", "micro worlds"),
    ("Folgezettel", "FOLE guh ZET ul"),
    ("Hmelo-Silver", "muh LOH sil ver"),
]

# Chapters to build. Add as they get rendered.
CHAPTERS = {
    "00-topology": ARC_DIR / "00-topology.md",
}


def tag_for_narration(text: str) -> str:
    """Prefix [NARRATOR] to each paragraph. Headers are passed through; the
    chunker strips them downstream."""
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

    for name, source_path in CHAPTERS.items():
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
