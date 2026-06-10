"""Per-chapter turn builder for the composition_vocabulary audiobook.

Reads NARRATOR-tagged scripts -> emits one <chapter>.turns.json per chapter.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "renderer"))

from chunker import apply_pronunciation_tweaks, compile_tweaks, parse_combined, subsplit_long  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPT_DIR = PROJECT_ROOT / "scripts"
OUT_DIR = PROJECT_ROOT / "build"

SPEAKERS = ("NARRATOR",)

# Pronunciation tweaks. Pattern is wrapped in \b...\b. Order matters for plurals/possessives.
PRONUNCIATION = [
    # Composers & theorists
    ("Schoenberg's", "Shurnberg's"),
    ("Schoenberg", "Shurnberg"),
    ("Debussy's", "Debyoosee's"),
    ("Debussy", "Debyoosee"),
    ("Mahler's", "Mahler's"),
    ("Eliade's", "Aylee-ah-day's"),
    ("Eliade", "Aylee-ah-day"),
    ("Nietzsche's", "Neechuh's"),
    ("Nietzsche", "Neechuh"),
    ("Schopenhauer", "Shopenhower"),
    ("Boulez", "boo-lezz"),
    ("Schaeffer", "Shayfer"),
    ("Mallarmé", "Mal-ar-may"),

    # Foreign musical terms
    ("attacca", "ah-tah-kah"),
    ("da capo", "dah kah-poh"),
    ("diegetic", "die-uh-jet-ick"),
    ("diegesis", "die-uh-jee-sis"),
    ("mimesis", "mim-ee-sis"),
    ("Götterdämmerung", "Gerter-demmer-oong"),
    ("Rheingold", "Rhine-gold"),
    ("qawwali", "kah-wah-lee"),
    ("kalpas", "kahl-pahs"),
    ("kalpa", "kahl-pah"),
    ("gamelan", "gam-uh-lahn"),
    ("leitmotifs", "light-moh-teefs"),
    ("leitmotif", "light-moh-teef"),
    ("motif", "moh-teef"),

    # Artists / musicians
    ("Stockhausen", "Stock-howzen"),
    ("Liebezeit", "Lee-buh-tsight"),
    ("Sigur Rós", "See-gur Rohss"),
    ("Basinski", "Buh-sinski"),
    ("Sufjan", "Soof-yahn"),
    ("Tupac", "Too-pock"),
    ("Shakur", "shah-koor"),
    ("Knxwledge", "knowledge"),

    # Album / song titles
    ("Endtroducing", "End-troh-doosing"),
    ("Hallogallo", "Hah-loh-gah-loh"),

    # Equipment / acronyms
    ("EP-133", "E P one thirty three"),
    ("EP-136", "E P one thirty six"),
    ("KO II", "K O two"),
    ("OP-1", "O P one"),
    ("OP-XY", "O P X Y"),
    ("VCS3", "V C S three"),
    ("BPM", "B P M"),
    ("MPC60", "M P C sixty"),
    ("EMT", "E M T"),
    ("DAW", "D A W"),

    # Time signatures
    ("7/4", "seven four"),
    ("4/4", "four four"),
    ("5/4", "five four"),
    ("3/4", "three four"),
    ("6/8", "six eight"),

    # Numbers in titles
    ("Andre 3000", "Andre Three Thousand"),

    # Wagner labels
    ("Tarnhelm", "Tarn-helm"),
    ("Valhalla", "Val-hahl-uh"),

    # ' that the chunker does not strip but model speaks weirdly
    ("m.A.A.d", "mad"),
]

GROUPS = {
    "chapter_00_motif": [SCRIPT_DIR / "00-motif-and-leitmotif.md"],
    "chapter_01_segue": [SCRIPT_DIR / "01-segue-crossfade-attacca.md"],
    "chapter_02_suite": [SCRIPT_DIR / "02-suite-as-form.md"],
    "chapter_03_diegetic": [SCRIPT_DIR / "03-diegetic-sound-and-voice.md"],
    "chapter_04_mix": [SCRIPT_DIR / "04-mix-and-space.md"],
    "chapter_05_voice": [SCRIPT_DIR / "05-voice-as-instrument.md"],
    "chapter_06_cyclical": [SCRIPT_DIR / "06-cyclical-structure.md"],
    "chapter_07_tonal": [SCRIPT_DIR / "07-tonal-instability.md"],
    "chapter_08_groove": [SCRIPT_DIR / "08-rhythm-and-groove.md"],
    "chapter_09_duration": [SCRIPT_DIR / "09-duration-as-element.md"],
    "chapter_10_argument": [SCRIPT_DIR / "10-album-as-argument.md"],
    "chapter_11_catalog": [SCRIPT_DIR / "11-catalog-as-composition.md"],
    "chapter_12_genre": [SCRIPT_DIR / "12-genre-as-pressure.md"],
    "chapter_13_practice": [SCRIPT_DIR / "13-vocabulary-to-practice.md"],
    "chapter_14_synthesis": [SCRIPT_DIR / "14-synthesis.md"],
}


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    tweaks = compile_tweaks(PRONUNCIATION)

    for name, paths in GROUPS.items():
        turns = parse_combined(paths, speakers=SPEAKERS)
        turns = subsplit_long(turns, max_words=200)
        turns = [(s, apply_pronunciation_tweaks(t, tweaks)) for s, t in turns]

        total_words = sum(len(t.split()) for _, t in turns)
        max_wc = max((len(t.split()) for _, t in turns), default=0)
        print(f"{name}: {len(turns)} turns, {total_words} words, longest {max_wc}")

        out_path = OUT_DIR / f"{name}.turns.json"
        out_path.write_text(json.dumps(turns, indent=2))


if __name__ == "__main__":
    main()
