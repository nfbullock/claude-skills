"""Build turns for formative-identity chapter renders.

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
ARC_DIR = Path("/Users/dad/Documents/sandbox/research/formative-identity")

SPEAKERS = ("NARRATOR",)

# Pronunciation regex pairs. Patterns get \b...\b wrapping by compile_tweaks.
# Conservative initial set; expand each time the model mangles a term.
PRONUNCIATION = [
    # Attachment / developmental theorists
    ("Bowlby", "BOLE bee"),
    ("Bartholomew", "bar THOL uh myoo"),
    ("Ainsworth", "AINZ worth"),
    ("Falbo", "FAL boh"),
    ("Polit", "POH lit"),
    ("Jurkovic", "yur KOH vich"),
    ("Kohut", "KOH hoot"),
    ("Heinz", "Hines"),
    ("Fonagy", "FON uh gee"),
    ("Gergely", "GAIR guh lee"),
    ("Bateman", "BATE man"),
    ("Schore", "SHORE"),
    ("Siegel", "SEE gul"),
    ("Tulving", "TUL ving"),
    ("Endel", "EN dell"),
    ("Roisman", "ROYZ man"),
    ("Sroufe", "SROW fuh"),
    ("Egeland", "EG uh land"),
    ("Padrón", "pa DROHN"),
    ("Padron", "pa DROHN"),
    ("Klimecki", "klee MET ski"),
    ("Tania", "TAN ya"),
    ("Hodgdon", "HODGE don"),
    ("Brophy", "BROH fee"),
    ("Planck", "PLONK"),
    ("Cassidy", "KASS uh dee"),
    ("Benoit", "ben WAH"),
    ("Goldwyn", "GOLD win"),
    ("Tikotzky", "tih KOTS kee"),
    ("Sharabany", "shar uh BAH nee"),
    ("Dozier", "DOH zher"),
    ("Bernard", "ber NARD"),
    ("Lewis-Morrarty", "Lewis mor RAR tee"),
    ("Lindhiem", "LIND heim"),
    ("Bakermans-Kranenburg", "BAH ker mans KRAH nen burg"),
    ("IJzendoorn", "EYE zen dorn"),
    ("Schechter", "SHEK ter"),
    ("Wiebe", "WEE bee"),
    ("Johnson", "JOHN son"),
    ("Greenman", "GREEN man"),
    ("Tronick", "TRAH nick"),
    ("Mesman", "MES man"),
    ("Beattie", "BEE tee"),
    ("Mellody", "MEL uh dee"),
    ("Peele", "Peel"),
    # Depth psychology / persona / midlife
    ("Winnicott", "WIN ih cott"),
    ("Jung", "Yoong"),
    ("Jungian", "YOONG ee un"),
    ("Hollis", "HOLL iss"),
    ("Hillman", "HILL man"),
    ("Bly", "Bly"),
    ("Woodman", "WOOD man"),
    ("Hyde", "Hyde"),
    ("Bollas", "BOLL us"),
    ("Bromberg", "BROM berg"),
    ("Fosha", "FOH shuh"),
    ("Schwartz", "SHWORTS"),
    # Father absence / masculine
    ("Lamb", "Lamb"),
    ("McLanahan", "muh LAN uh han"),
    ("Sandefur", "SAN duh fur"),
    ("Blankenhorn", "BLANK en horn"),
    ("Popenoe", "POP eh no"),
    ("Niobe", "nye OH bee"),
    ("Reichert", "RYE kert"),
    ("Kimmel", "KIM ul"),
    ("Forward", "FOR werd"),
    # Recovery / values / philosophy
    ("Maté", "mah TAY"),
    ("Gabor", "gah BOR"),
    ("Bukowski", "buh KOW ski"),
    ("Csikszentmihalyi", "chick sent me HIGH ee"),
    ("Bogenschutz", "BOH gen shoots"),
    ("Carhart-Harris", "CAR hart Harris"),
    ("Lembke", "LEM kee"),
    ("Volkow", "VOLE koh"),
    ("Berridge", "BAIR ij"),
    ("Koob", "Koob"),
    ("Pickkers", "PIK ers"),
    ("Buijze", "BOYT zuh"),
    ("Šrámek", "SHRAH mek"),
    ("Sramek", "SHRAH mek"),
    ("Janský", "YAHN skee"),
    ("Porges", "POR jess"),
    ("Levine", "luh VEEN"),
    ("Sadeh", "SAH day"),
    ("Sagi", "SAH ghee"),
    ("Mitchell", "MIT chull"),
    ("Pieper", "PEE per"),
    ("Hadot", "ah DOH"),
    ("MacIntyre", "MAK in tyre"),
    ("Kegan", "KEY gun"),
    ("Marcia", "MAR see uh"),
    ("Turner", "TURN er"),
    ("Bridges", "BRIJ iz"),
    ("Brené", "bren AY"),
    ("Brown", "Brown"),
    ("Tharp", "Tharp"),
    ("Pressfield", "PRESS feeld"),
    ("Herrigel", "HAIR ih gul"),
    ("Suzuki", "soo ZOO key"),
    ("Yamada", "yah MAH duh"),
    ("Shōji", "SHOH jee"),
    ("Shoji", "SHOH jee"),
    ("Zatorre", "zah TOR ay"),
    ("Salimpoor", "sah lim POOR"),
    ("Juslin", "YOOSE lin"),
    ("Sloboda", "sloh BOH duh"),
    ("DeNora", "duh NOR uh"),
    ("Hesmondhalgh", "HES mond hah"),
    ("Pareto", "pa REH toh"),
    # Acronyms (initialisms)
    ("AAI", "A A I"),
    ("IFS", "I F S"),
    ("EFT", "E F T"),
    ("EMDR", "E M D R"),
    ("MBT", "M B T"),
    ("AEDP", "A E D P"),
    ("ABC", "A B C"),
    ("CBT", "C B T"),
    ("CBT-I", "C B T I"),
    ("BPD", "B P D"),
    ("PTSD", "P T S D"),
    ("DSM", "D S M"),
    ("DSM-5", "D S M five"),
    ("PNAS", "P N A S"),
    ("ENTP", "E N T P"),
    ("ICER", "EYE sir"),
    ("FDA", "F D A"),
    ("MDMA", "M D M A"),
    ("MAPS", "maps"),
    ("MAPP1", "MAP one"),
    ("MAPP2", "MAP two"),
    ("MKP", "M K P"),
    ("MDD", "M D D"),
    ("BRECVEMA", "B R E C V E M A"),
    ("SSRI", "S S R I"),
    ("SSRIs", "S S R Is"),
    ("RCT", "R C T"),
    ("RCTs", "R C T s"),
    ("PAWS", "paws"),
    ("PET", "pet"),
    ("F3", "F three"),
    ("OP-1", "O P one"),
    ("SAMHSA", "SAM suh"),
    ("NWTA", "N W T A"),
    ("TTS", "T T S"),
    # Other compound names
    ("Self-Authoring", "Self Authoring"),
    ("Memento", "muh MEN toh"),
]

# Chapters to build. The render.sh script takes the slug as its argument.
CHAPTERS = {
    "01-configuration-attachment": ARC_DIR / "01-configuration-attachment.md",
    "02-false-self-fool": ARC_DIR / "02-false-self-fool.md",
    "03-masculine-identity-father": ARC_DIR / "03-masculine-identity-father.md",
    "04-marriage-codependence-fatherhood": ARC_DIR / "04-marriage-codependence-fatherhood.md",
    "05-work-anhedonia-sleep": ARC_DIR / "05-work-anhedonia-sleep.md",
    "06-music-bukowski": ARC_DIR / "06-music-bukowski.md",
    "07-values-recovery-modalities": ARC_DIR / "07-values-recovery-modalities.md",
    "08-synthesis": ARC_DIR / "08-synthesis.md",
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
