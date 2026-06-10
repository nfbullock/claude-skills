"""Preprocess source markdown into [NARRATOR]-tagged scripts the chunker can parse.

Reads files from sources/research/composition_vocabulary/, strips headers, prepends
[NARRATOR] to each paragraph, writes tagged versions into scripts/.
"""
from __future__ import annotations
from pathlib import Path

SRC = Path("/Users/dad/Documents/sandbox/projects/research/composition_vocabulary")
DST = Path(__file__).resolve().parent / "scripts"
DST.mkdir(exist_ok=True)

CHAPTERS = [
    "00-motif-and-leitmotif",
    "01-segue-crossfade-attacca",
    "02-suite-as-form",
    "03-diegetic-sound-and-voice",
    "04-mix-and-space",
    "05-voice-as-instrument",
    "06-cyclical-structure",
    "07-tonal-instability",
    "08-rhythm-and-groove",
    "09-duration-as-element",
    "10-album-as-argument",
    "11-catalog-as-composition",
    "12-genre-as-pressure",
    "13-vocabulary-to-practice",
    "14-synthesis",
]


def tag_paragraphs(text: str) -> str:
    out: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            body = " ".join(paragraph).strip()
            if body:
                out.append(f"[NARRATOR] {body}")
            paragraph.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            flush()
            continue
        if stripped.startswith("---") and not paragraph:
            # Skip frontmatter delimiters
            continue
        if not stripped:
            flush()
        else:
            paragraph.append(stripped)
    flush()
    return "\n\n".join(out) + "\n"


def main() -> None:
    for ch in CHAPTERS:
        src_path = SRC / f"{ch}.md"
        if not src_path.exists():
            print(f"  MISSING: {src_path}")
            continue
        text = src_path.read_text()
        tagged = tag_paragraphs(text)
        dst_path = DST / f"{ch}.md"
        dst_path.write_text(tagged)
        wc = sum(len(p.split()) - 1 for p in tagged.split("\n\n") if p.startswith("[NARRATOR]"))
        print(f"  {ch}: {wc} words")


if __name__ == "__main__":
    main()
