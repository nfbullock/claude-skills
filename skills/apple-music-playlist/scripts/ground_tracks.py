#!/usr/bin/env python3
"""Ground a proposed tracklist against MusicBrainz — the anti-hallucination gate.

The model proposes tracks (deep, non-cliché); this tool checks each against the
open MusicBrainz recording graph and reports:
  - exists: is this a real recording by this artist? (kills hallucinated tracks)
  - canonical artist/title (fixes spelling/credit drift)
  - versions: the studio/live/acoustic/session variants MusicBrainz knows about,
    each classified + with length — so a curator can deliberately choose the
    "live From Spotify London" cut over the studio one (the Song-for-Zula move).

MusicBrainz is free, needs no key, but requires a descriptive User-Agent and
rate-limits anonymous callers to ~1 req/sec (we sleep 1.1s between queries).

Usage:
  ground_tracks.py --input tracks.json          # same schema as create_playlist
  ground_tracks.py --artist "Phosphorescent" --title "Song for Zula"

Emits a JSON report to stdout. Does NOT touch Music.app — grounding only; feed the
chosen (artist, title[, exact version title]) onward to sideload_tracks.py.
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

MB_ROOT = "https://musicbrainz.org/ws/2/recording/"
UA = "NickMusicResearch/0.1 (nick@bullock.im)"
RATE_SLEEP = 1.1  # anonymous MusicBrainz limit is ~1 req/sec

# version classification from a recording's title + disambiguation
_VERSION_RULES = [
    ("session", ("spotify", "session", "bbc", "kexp", "daytrotter", "peel",
                 "radio", "npr", "tiny desk", "live from spotify")),
    ("acoustic", ("acoustic", "unplugged", "stripped")),
    ("live", ("live", "concert", "at st", "solo at")),
    ("demo", ("demo",)),
    ("instrumental", ("instrumental",)),
    ("remix", ("remix", "rmx", "dub mix", "edit", "mix)")),
]


def classify_version(title, disambiguation):
    blob = f"{title} {disambiguation}".lower()
    for label, needles in _VERSION_RULES:
        if any(n in blob for n in needles):
            return label
    return "studio"


def _fmt_len(ms):
    if not ms:
        return None
    return f"{ms // 60000}:{(ms // 1000) % 60:02d}"


def query_mb(artist, title, limit=25):
    q = f'artist:"{artist}" AND recording:"{title}"'
    url = MB_ROOT + "?" + urllib.parse.urlencode({"query": q, "fmt": "json", "limit": limit})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def ground_one(artist, title):
    try:
        data = query_mb(artist, title)
    except Exception as e:  # network / rate / parse
        return {"artist": artist, "title": title, "exists": None, "error": str(e)[:200]}

    recs = data.get("recordings", [])
    # existence: a high-score recording whose credited artist matches closely
    top = recs[0] if recs else None
    exists = bool(top and top.get("score", 0) >= 90)
    canonical = None
    if top:
        canonical = {
            "artist": (top.get("artist-credit", [{}])[0].get("name", artist)),
            "title": top.get("title", title),
        }

    # collect distinct versions (dedup by title+disambiguation)
    versions, seen = [], set()
    for r in recs:
        if r.get("score", 0) < 70:
            continue
        t, dis = r.get("title", ""), r.get("disambiguation", "")
        key = (t.lower(), dis.lower())
        if key in seen:
            continue
        seen.add(key)
        versions.append({
            "title": t,
            "disambiguation": dis,
            "length": _fmt_len(r.get("length")),
            "kind": classify_version(t, dis),
        })

    kinds = sorted({v["kind"] for v in versions})
    return {
        "artist": artist, "title": title,
        "exists": exists, "canonical": canonical,
        "version_kinds_found": kinds,
        "has_alt_versions": any(k != "studio" for k in kinds),
        "versions": versions,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="tracks JSON (create_playlist schema)")
    ap.add_argument("--artist")
    ap.add_argument("--title")
    args = ap.parse_args()

    if args.artist and args.title:
        pairs = [(args.artist, args.title)]
    elif args.input:
        data = json.loads(open(args.input).read())
        pairs = [(t["artist"], t["title"]) for t in data["tracks"]]
    else:
        ap.error("need --input OR --artist/--title")

    results = []
    for i, (a, t) in enumerate(pairs):
        if i:
            time.sleep(RATE_SLEEP)
        results.append(ground_one(a, t))

    real = sum(1 for r in results if r.get("exists"))
    print(json.dumps({
        "grounded": len(results), "verified_real": real,
        "flagged": [f"{r['artist']} — {r['title']}"
                    for r in results if r.get("exists") is False],
        "results": results,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

