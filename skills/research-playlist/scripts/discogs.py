#!/usr/bin/env python3
"""Discogs enrichment — the second grounding vote + version/label/style depth.

Discogs indexes *releases* (not individual tracks well), so its role in the quorum
is distinct from MusicBrainz's track-level grounding:
  - STYLE/GENRE corroboration — Discogs' fine style taxonomy (Dub, Roots Reggae,
    Deep House, Acid…) is a strong genre vote, and the fuel for kids-orthogonal
    genre traversal.
  - EXISTENCE quorum at artist/release level — an artist/release Discogs *and*
    MusicBrainz both know is real (a second independent vote).
  - VERSION/PRESSING depth — how a record was pressed/versioned across labels &
    countries (the dub goldmine MusicBrainz under-covers).

Reads credentials.json (gitignored) beside the skill: {"discogs":{"consumer_key","consumer_secret"}}.

Usage:
  discogs.py --artist "Scientist"                     # aggregated genres/styles + top releases
  discogs.py --release "Scientist" "Rids the World"   # pressings/versions across labels/countries
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

UA = "NickMusicResearch/0.1 +nick@bullock.im"
API = "https://api.discogs.com/database/search"
RATE_SLEEP = 1.1  # authenticated Discogs ~60/min; stay polite


def _auth_header():
    p = Path(__file__).resolve().parent.parent / "credentials.json"
    d = json.loads(p.read_text())["discogs"]
    # personal access token is simplest; fall back to consumer key/secret
    if d.get("personal_token"):
        return f"Discogs token={d['personal_token']}"
    return f"Discogs key={d['consumer_key']}, secret={d['consumer_secret']}"


def _search(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Authorization": _auth_header(),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def artist_profile(name, pages=1):
    """Aggregate genres/styles across an artist's releases + list notable releases."""
    genres, styles = Counter(), Counter()
    releases = []
    for page in range(1, pages + 1):
        if page > 1:
            time.sleep(RATE_SLEEP)
        d = _search({"artist": name, "type": "release", "per_page": 50, "page": page})
        for r in d.get("results", []):
            genres.update(r.get("genre", []) or [])
            styles.update(r.get("style", []) or [])
            releases.append({
                "title": r.get("title"), "year": r.get("year"),
                "country": r.get("country"), "label": (r.get("label") or [None])[0],
                "style": r.get("style", []),
            })
        if not d.get("results"):
            break
    return {
        "artist": name,
        "found": bool(releases),
        "genres": [g for g, _ in genres.most_common()],
        "styles": [s for s, _ in styles.most_common(12)],
        "release_sample": releases[:12],
    }


def release_versions(artist, title):
    """List the pressings/versions of a release across labels & countries."""
    d = _search({"artist": artist, "release_title": title, "type": "release",
                 "per_page": 50})
    versions = []
    seen = set()
    for r in d.get("results", []):
        key = (r.get("year"), r.get("country"), (r.get("label") or [None])[0])
        if key in seen:
            continue
        seen.add(key)
        versions.append({
            "title": r.get("title"), "year": r.get("year"),
            "country": r.get("country"), "label": (r.get("label") or [None])[0],
            "format": r.get("format", []), "style": r.get("style", []),
        })
    return {"artist": artist, "title": title, "version_count": len(versions),
            "versions": versions}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artist")
    ap.add_argument("--release", nargs=2, metavar=("ARTIST", "TITLE"))
    args = ap.parse_args()
    if args.release:
        out = release_versions(*args.release)
    elif args.artist:
        out = artist_profile(args.artist)
    else:
        ap.error("need --artist OR --release ARTIST TITLE")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
