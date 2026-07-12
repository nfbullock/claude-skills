#!/usr/bin/env python3
"""Traverse the similarity graph away from a seed — the non-cliché discovery engine,
with QUORUM across independent sources (Nick's 2026-07-02 ask: don't trust one source).

Two independent similarity votes:
  - ListenBrainz session-based artist similarity (keyless; from listening sessions)
  - Last.fm artist.getSimilar (API key; from scrobble co-occurrence)
They draw on different underlying data, so agreement between them is a strong,
low-bias signal. The tool merges both and ranks by:
  1. quorum  — how many sources vouch (2 > 1)
  2. consensus score — normalized similarity summed across the sources that list it

The point is NOT the famous neighbors. Fish the `deep_zone` (past the obvious head)
AND prefer `quorum == 2` — the artists both graphs independently point at — then go
into their deep catalogs. Multi-seed adds a third axis (which neighbors ≥2 seeds share).

Also the kids' "orthogonal growth" engine: walk outward from the family center,
trusting only consensus so you don't chase one source's idiosyncrasy.

Usage:
  traverse.py --seed "Phosphorescent"
  traverse.py --seed "King Tubby" --seed "Scientist" --skip-head 5
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "NickMusicResearch/0.1 (nick@bullock.im)"
MB_ARTIST = "https://musicbrainz.org/ws/2/artist/"
LB_SIMILAR = "https://labs.api.listenbrainz.org/similar-artists/json"
LB_ALGO = ("session_based_days_7500_session_300_contribution_5"
           "_threshold_10_limit_100_filter_True_skip_30")
LASTFM = "http://ws.audioscrobbler.com/2.0/"
RATE_SLEEP = 1.1


def _lastfm_key():
    p = Path(__file__).resolve().parent.parent / "credentials.json"
    try:
        return json.loads(p.read_text())["lastfm"]["api_key"] or None
    except Exception:
        return None


def _get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def resolve_mbid(name):
    url = MB_ARTIST + "?" + urllib.parse.urlencode(
        {"query": f'artist:"{name}"', "fmt": "json", "limit": 1})
    arts = _get(url).get("artists", [])
    return ({"mbid": arts[0]["id"], "name": arts[0]["name"]} if arts else None)


def lb_similar(mbid):
    url = LB_SIMILAR + "?" + urllib.parse.urlencode(
        {"artist_mbids": mbid, "algorithm": LB_ALGO})
    d = _get(url)
    items = d if isinstance(d, list) else d.get("data", [])
    return [a["name"] for a in items if a.get("name")]


def lastfm_similar(name, key):
    url = LASTFM + "?" + urllib.parse.urlencode(
        {"method": "artist.getsimilar", "artist": name, "api_key": key,
         "format": "json", "limit": 100})
    d = _get(url)
    return [a["name"] for a in d.get("similarartists", {}).get("artist", [])]


def _merge_source(merged, names, source, seed):
    """Fold one ranked list into the merged map with a normalized rank score."""
    n = len(names) or 1
    for rank, name in enumerate(names):
        k = name.lower()
        e = merged.setdefault(k, {"name": name, "sources": set(), "seeds": set(),
                                  "score": 0.0})
        e["sources"].add(source)
        e["seeds"].add(seed)
        e["score"] += 1.0 - (rank / n)   # 1.0 at top, ->0 at tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="append", required=True)
    ap.add_argument("--skip-head", type=int, default=6)
    args = ap.parse_args()

    key = _lastfm_key()
    merged, per_seed = {}, []
    seed_names = {s.lower() for s in args.seed}

    for i, name in enumerate(args.seed):
        if i:
            time.sleep(RATE_SLEEP)
        seed = resolve_mbid(name)
        entry = {"seed": name, "sources_ok": []}
        if seed:
            entry["resolved"] = seed["name"]
            time.sleep(RATE_SLEEP)
            try:
                lb = lb_similar(seed["mbid"])
                _merge_source(merged, lb, "listenbrainz", name)
                entry["sources_ok"].append(f"listenbrainz({len(lb)})")
            except Exception as e:
                entry["listenbrainz_error"] = str(e)[:120]
        else:
            entry["error"] = "not found in MusicBrainz"
        if key:
            try:
                lf = lastfm_similar(name, key)
                _merge_source(merged, lf, "lastfm", name)
                entry["sources_ok"].append(f"lastfm({len(lf)})")
            except Exception as e:
                entry["lastfm_error"] = str(e)[:120]
        else:
            entry["lastfm"] = "no api key — single-source discovery"
        per_seed.append(entry)

    # finalize: drop the seeds themselves, rank by (quorum, consensus score)
    rows = []
    for e in merged.values():
        if e["name"].lower() in seed_names:
            continue
        rows.append({
            "name": e["name"],
            "quorum": len(e["sources"]),          # how many similarity sources agree
            "sources": sorted(e["sources"]),
            "seed_overlap": len(e["seeds"]),       # how many seeds point here
            "seeds": sorted(e["seeds"]),
            "score": round(e["score"], 3),
        })
    rows.sort(key=lambda r: (r["quorum"], r["seed_overlap"], r["score"]), reverse=True)
    for rank, r in enumerate(rows):
        r["deep_zone"] = rank >= args.skip_head

    print(json.dumps({
        "seeds": args.seed,
        "quorum_available": bool(key),
        "consensus_neighbors": rows,
        "per_seed": per_seed,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
