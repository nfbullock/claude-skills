#!/usr/bin/env python3
"""Scan the music project for open lesson loops.

An open loop = a generated lesson still awaiting practice + debrief/retro.
Deterministic facts only — the rendering judgment lives in SKILL.md.

Sources:
  gym    -> gym/state.md Lesson History table rows (status column)
  office -> office/lessons/*.md "### Debrief — (awaiting" marker
  field  -> field/lessons/*.md vs field/JOURNAL.md "### Song N — Lesson NN" retros
  stage  -> counted only (optional retros; never a loop)

Playlists joined from the apple-music-playlist ledger (used_tracks.jsonl),
with the listening.md log line included as listen-first material.
"""

import json
import re
import sys
from pathlib import Path

MUSIC = Path("/Users/dad/Documents/sandbox/music")
LEDGER = Path(
    "/Users/dad/Documents/sandbox/backstairs/"
    "apple-music-playlist/used_tracks.jsonl"
)
LISTENING = MUSIC / "listening.md"

PLAYLIST_URL = "https://music.apple.com/library/playlist/{}"


def load_playlists():
    """name -> {name, url, date}; later entries win (re-creates supersede)."""
    playlists = {}
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            playlists[row["playlist_name"]] = {
                "name": row["playlist_name"],
                "url": PLAYLIST_URL.format(row["playlist_id"]),
                "date": row.get("date"),
            }
    return playlists


def playlist_for(playlists, place, nn):
    """Match '🎧 {Place} {NN}: ...' tolerating zero-padding differences."""
    wanted = int(nn)
    for name, info in playlists.items():
        m = re.match(r"🎧 (\w+) (\d+):", name)
        if m and m.group(1).lower() == place.lower() and int(m.group(2)) == wanted:
            return info
    return None


def listening_log_line(playlist_name):
    """The listening.md Playlist-log line for this playlist (what-to-listen-for)."""
    if not playlist_name or not LISTENING.exists():
        return None
    for line in LISTENING.read_text().splitlines():
        if playlist_name in line and line.lstrip().startswith("-"):
            return line.strip()
    return None


def first_heading(path):
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def scan_gym(playlists):
    """Parse the Lesson History table in gym/state.md.

    state.md carries duplicated lineage blocks below the live ones —
    keep the FIRST occurrence of each lesson id (the live table).
    """
    state = MUSIC / "gym" / "state.md"
    loops, seen = [], set()
    if not state.exists():
        return loops
    for line in state.read_text().splitlines():
        if not re.match(r"^\| \d+ \|", line):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 10:
            continue
        lesson_id, instrument, lane = cells[3], cells[4], cells[5]
        title, status = cells[7], cells[8]
        if lesson_id in seen:
            continue
        seen.add(lesson_id)
        if "RELEGATED" in status or "SUPERSEDED" in status:
            continue
        low = status.lower()
        if not (low.startswith("queued") or "awaiting practice" in low):
            continue
        nn = lesson_id.split("-")[0]
        pl = playlist_for(playlists, "Gym", nn)
        if pl is None:
            # re-issued lessons carry the prior lesson's playlist — the
            # status text names it in backticks (e.g. `🎧 Gym 024: ...`)
            m = re.search(r"`(🎧 [^`]+)`", status)
            if m:
                pl = playlists.get(m.group(1))
                if pl:
                    pl = {**pl, "carried_over": True}
        loops.append({
            "track": "gym",
            "lane": lane,
            "id": lesson_id,
            "title": title,
            "instrument": instrument,
            "file": f"gym/lessons/{lesson_id}" if "-" not in lesson_id else None,
            "status_excerpt": status[:600],
            "playlist": pl,
            "listen_line": listening_log_line(pl["name"]) if pl else None,
        })
        # resolve the actual filename
        matches = list((MUSIC / "gym" / "lessons").glob(f"{lesson_id}*.md"))
        if matches:
            loops[-1]["file"] = str(matches[0].relative_to(MUSIC))
    return loops


def scan_office(playlists):
    loops = []
    for path in sorted((MUSIC / "office" / "lessons").glob("[0-9]*.md")):
        text = path.read_text()
        if "### Debrief — (awaiting" not in text:
            continue
        m = re.match(r"(\d+)-(\w+)-", path.name)
        nn = m.group(1) if m else "?"
        lane = m.group(2) if m else "?"
        pl = playlist_for(playlists, "Office", nn) if m else None
        loops.append({
            "track": "office",
            "lane": lane,
            "id": path.stem,
            "title": first_heading(path),
            "file": str(path.relative_to(MUSIC)),
            "playlist": pl,
            "listen_line": listening_log_line(pl["name"]) if pl else None,
        })
    return loops


def scan_field(playlists):
    journal = (MUSIC / "field" / "JOURNAL.md")
    jtext = journal.read_text() if journal.exists() else ""
    # retro headings are "### Song N — Lesson NN, ..." but early ones are
    # bare "### Song N" — song number tracks lesson number, so count both
    retroed = set(
        int(n) for n in re.findall(r"### Song \d+ — Lesson (\d+)", jtext)
    ) | set(int(n) for n in re.findall(r"### Song (\d+)", jtext))
    loops = []
    for path in sorted((MUSIC / "field" / "lessons").glob("[0-9]*.md")):
        m = re.match(r"(\d+)-", path.name)
        if not m:
            continue
        nn = int(m.group(1))
        if nn in retroed:
            continue
        pl = playlist_for(playlists, "Field", m.group(1))
        loops.append({
            "track": "field",
            "lane": None,
            "id": path.stem,
            "title": first_heading(path),
            "file": str(path.relative_to(MUSIC)),
            "playlist": pl,
            "listen_line": listening_log_line(pl["name"]) if pl else None,
        })
    return loops


def scan_stage():
    stage = MUSIC / "stage"
    if not stage.exists():
        return {"lessons": 0}
    lessons = [p for p in stage.rglob("*.md") if re.match(r"\d", p.name)]
    return {"lessons": len(lessons), "note": "retros optional — never a loop"}


def main():
    playlists = load_playlists()
    result = {
        "loops": scan_gym(playlists) + scan_office(playlists) + scan_field(playlists),
        "stage": scan_stage(),
        "gates": {
            "gym": "per-lane (home-lab / voice) — lanes never block each other",
            "office": "per-lane (ma / ml) — lanes never block each other",
            "field": "retro-before-next within the track; pull-based, allowed to sit quiet",
            "stage": "no gate",
        },
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()

