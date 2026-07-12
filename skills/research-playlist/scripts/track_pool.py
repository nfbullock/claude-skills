#!/usr/bin/env python3
"""Track-level candidate pool — closes the bottleneck where track *selection* was
still the LLM guessing (Nick, 2026-07-02: "quorum on related artists ≠ quorum on
non-standard tracks — are we burying a bottleneck?").

Artist-similarity quorum (graph.py) decides WHICH artists. This decides WHICH TRACKS,
from data instead of memory. Two feeders:

1. Last.fm playcount tiers (popularity-SHAPED — useful, but only half the truth):
     - head   : ranks 1-3   -> the over-familiar; a FAMILIARITY COST, not a cut —
                               head tracks stay in the pool, tagged, and compete on
                               audio-DNA like everything else (the RHCP rule: a hit
                               that uniquely nails the concept ships as the anchor)
     - body   : ranks 4-7
     - deep   : rank >=8 above a live-floor -> non-standard but genuinely listened to
     - obscure: below the floor -> kept in the pool too; audio-DNA decides if the
                               sound matters, not the scrobble count
   The live-floor is ARTIST-RELATIVE by default (1% of the artist's top track,
   min 200) — an absolute floor made 'deep' collapse to hits-or-nothing exactly for
   the obscure artists the traversal works hardest to reach (2026-07 review finding).

2. MusicBrainz full-recording enumeration (--mb-recordings; popularity-BLIND):
   every recording MB credits to the artist, scrobbles or not. This is how a dub
   B-side that exists only on a tracklist enters the pool at all — audio-DNA can
   then judge it by its sound. Optionally --persist track nodes into musicgraph.db.

A second track-level vote (Last.fm `track.getSimilar`) is available via --similar-to.
Reads credentials.json (lastfm.api_key) beside the skill.

Usage:
  track_pool.py --artist "Prince Far I" --artist "Keith Hudson"
  track_pool.py --artist "Scientist" --pages 2 --limit 50       # reach past rank 50
  track_pool.py --artist "Scientist" --live-floor 4000          # absolute override
  track_pool.py --mb-recordings "Scientist" --mb-pages 3 --persist
  track_pool.py --similar-to "Augustus Pablo" "King Tubby Meets Rockers Uptown"
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

LASTFM = "http://ws.audioscrobbler.com/2.0/"
MB_ARTIST = "https://musicbrainz.org/ws/2/artist/"
MB_RECORDING = "https://musicbrainz.org/ws/2/recording"
UA = "NickMusicResearch/0.1 (nick@bullock.im)"
RATE_SLEEP = 0.3
MB_SLEEP = 1.1   # anonymous MusicBrainz ~1 req/sec


def _key():
    p = Path(__file__).resolve().parent.parent / "credentials.json"
    return json.loads(p.read_text())["lastfm"]["api_key"]


def _get(params):
    params = {**params, "api_key": _key(), "format": "json"}
    url = LASTFM + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _mb_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _aslist(v):
    """Last.fm's XML->JSON layer collapses single-item lists to a bare object."""
    if isinstance(v, dict):
        return [v]
    return v or []


def top_tracks(artist, limit=50, pages=1):
    """Last.fm top tracks, paginated — page 2+ reaches past the all-time top 50
    (the static-shelf fix: the same ~30 'deep' tracks were the pool forever)."""
    out = []
    for page in range(1, max(1, pages) + 1):
        if page > 1:
            time.sleep(RATE_SLEEP)
        d = _get({"method": "artist.gettoptracks", "artist": artist,
                  "limit": limit, "page": page})
        rows = _aslist(d.get("toptracks", {}).get("track", []))
        for t in rows:
            out.append({"title": t["name"],
                        "playcount": int(t.get("playcount", 0)),
                        "listeners": int(t.get("listeners", 0))})
        if len(rows) < limit:
            break
    return out


def tier_pool(artist, limit=50, live_floor=None, pages=1):
    """Tier an artist's tracks relative to that artist. NOTHING is cut: every track
    lands in `all` with its tier tag; head = familiarity cost, obscure = unproven,
    and audio-DNA arbitrates on sound. The floor is artist-relative unless overridden."""
    tracks = top_tracks(artist, limit, pages)
    head_pc = tracks[0]["playcount"] if tracks else 0
    floor = live_floor if live_floor is not None else max(200, int(head_pc * 0.01))
    pool = {"artist": artist, "found": bool(tracks),
            "artist_scale": {"head_playcount": head_pc, "live_floor_used": floor,
                             "floor_mode": "absolute" if live_floor is not None
                                           else "relative(1% of head, min 200)"},
            "head": [], "body": [], "deep": [], "obscure": [], "all": []}
    for rank, t in enumerate(tracks):
        row = {**t, "rank": rank + 1, "artist": artist}
        if rank < 3:
            tier = "head"       # over-familiar risk — competes, tagged, never pre-cut
        elif rank < 7:
            tier = "body"
        elif t["playcount"] >= floor:
            tier = "deep"       # non-standard but alive: the default curation shelf
        else:
            tier = "obscure"    # below the floor — DNA decides, not the scrobbles
        row["tier"] = tier
        pool[tier].append(row)
        pool["all"].append(row)
    pool["deep_count"] = len(pool["deep"])
    return pool


def mb_recordings(artist, pages=3):
    """Popularity-blind feeder: enumerate the artist's recordings from MusicBrainz
    (browse API, keyless). Returns unique titles with a recording MBID each — the
    path by which a zero-scrobble B-side can enter the candidate pool at all."""
    url = MB_ARTIST + "?" + urllib.parse.urlencode(
        {"query": f'artist:"{artist}"', "fmt": "json", "limit": 1})
    arts = _mb_get(url).get("artists", [])
    if not arts:
        return {"artist": artist, "found": False}
    mbid, canonical = arts[0]["id"], arts[0]["name"]

    seen = {}
    total = 0
    page = 0
    for page in range(max(1, pages)):
        time.sleep(MB_SLEEP)
        d = _mb_get(MB_RECORDING + "?" + urllib.parse.urlencode(
            {"artist": mbid, "limit": 100, "offset": page * 100, "fmt": "json"}))
        recs = d.get("recordings", [])
        total = d.get("recording-count", total)
        for r in recs:
            title = (r.get("title") or "").strip()
            key = title.lower()
            if title and key not in seen:
                seen[key] = {"title": title, "artist": canonical,
                             "mbid": r["id"], "length_ms": r.get("length")}
        if (page + 1) * 100 >= total or not recs:
            break
    return {"artist": canonical, "found": True, "artist_mbid": mbid,
            "recordings_in_mb": total, "pages_fetched": page + 1,
            "unique_titles": len(seen), "recordings": list(seen.values())}


def persist_recordings(result):
    """Write MB recordings through to musicgraph.db as track nodes (SPEC §5 write-through)."""
    from graph import Graph
    g = Graph()
    n = 0
    for rec in result.get("recordings", []):
        g.upsert_node("track", rec["title"], artist=result["artist"], mbid=rec["mbid"])
        n += 1
    g.close()
    return n


def similar_tracks(artist, title, limit=30):
    d = _get({"method": "track.getsimilar", "artist": artist, "track": title,
              "limit": limit})
    out = []
    for t in _aslist(d.get("similartracks", {}).get("track", [])):
        out.append({"title": t["name"],
                    "artist": t.get("artist", {}).get("name"),
                    "match": round(float(t.get("match", 0)), 3)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artist", action="append", default=[])
    ap.add_argument("--similar-to", nargs=2, metavar=("ARTIST", "TITLE"))
    ap.add_argument("--mb-recordings", metavar="ARTIST",
                    help="enumerate ALL the artist's recordings from MusicBrainz "
                         "(popularity-blind feeder)")
    ap.add_argument("--mb-pages", type=int, default=3,
                    help="MusicBrainz pages (100 recordings each) to fetch")
    ap.add_argument("--persist", action="store_true",
                    help="write --mb-recordings results into musicgraph.db as track nodes")
    ap.add_argument("--limit", type=int, default=50, help="Last.fm tracks per page")
    ap.add_argument("--pages", type=int, default=1,
                    help="Last.fm pages per artist (page 2+ reaches past the top 50)")
    ap.add_argument("--live-floor", type=int, default=None,
                    help="ABSOLUTE playcount floor for the deep tier "
                         "(default: artist-relative — 1%% of head track, min 200)")
    args = ap.parse_args()

    out = {}
    if args.similar_to:
        out["similar_tracks"] = {
            "seed": args.similar_to,
            "tracks": similar_tracks(*args.similar_to, limit=args.limit),
        }
    if args.mb_recordings:
        res = mb_recordings(args.mb_recordings, pages=args.mb_pages)
        if args.persist and res.get("found"):
            res["persisted_track_nodes"] = persist_recordings(res)
        out["mb_recordings"] = res
    if args.artist:
        pools = []
        for i, a in enumerate(args.artist):
            if i:
                time.sleep(RATE_SLEEP)
            pools.append(tier_pool(a, args.limit, args.live_floor, args.pages))
        out["pools"] = pools
    if not out:
        ap.error("need --artist, --similar-to, and/or --mb-recordings")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
