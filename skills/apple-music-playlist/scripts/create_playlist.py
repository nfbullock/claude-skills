#!/usr/bin/env python3
"""Entry point invoked by Claude Code to create a lesson playlist.

Two modes:
  --input <json>     Create a playlist from a tracks JSON (the normal path).
  --recent <Domain>  Print the tracks used in the last N playlists for a domain
                     (Office / Gym / Field / Stage), so the curator can
                     avoid recycling them. Reads the auto-maintained ledger.

Every successful creation appends its landed tracks to `used_tracks.jsonl`
(one JSON object per playlist) next to the skill. That ledger is the machine
substrate for the "don't repeat the canon" rule — dedup no longer depends on
anyone remembering to read the prose log in listening.md.
"""
import argparse
import datetime
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # allow run from any cwd

from auth import generate_developer_token, get_music_user_token, load_credentials
from apple_music import AppleMusic, AuthRequired, AppleMusicError

LEDGER = Path(__file__).resolve().parent.parent / "used_tracks.jsonl"


def domain_of(playlist_name: str) -> str:
    """First alpha run of the name — 'Office L05: ...' -> 'Office'."""
    m = re.search(r"[A-Za-z]+", playlist_name)  # skip a leading emoji/space
    return m.group(0).lower() if m else ""


def append_ledger(domain, name, playlist_id, tracks):
    """Append one line for this playlist. Never raise into the main flow."""
    try:
        entry = {
            "domain": domain,
            "date": datetime.date.today().isoformat(),
            "playlist_id": playlist_id,
            "playlist_name": name,
            "tracks": [{"artist": t["artist"], "title": t["title"]} for t in tracks],
        }
        with open(LEDGER, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # the ledger is a convenience, not load-bearing for creation


ARTIST_WINDOW = 15      # playlists (all domains) scanned for artist over-exposure
ARTIST_SOFT_BAN = 3     # appearances in the window that flag an artist "overexposed"


def recent(domain: str, n: int):
    """Print the ban list: tracks from the last n playlists in this domain — PLUS
    artist-appearance counts over the last ARTIST_WINDOW playlists across ALL domains.
    The track ban is hard (no exact repeats); the artist view is a SOFT signal: an
    overexposed artist must earn its next slot, it is never auto-banned (the exclusion
    unit is the worn track, not the artist)."""
    domain = domain.lower()
    all_entries, entries = [], []
    if LEDGER.exists():
        with open(LEDGER) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(e, dict):
                    continue
                all_entries.append(e)
                if e.get("domain") == domain:
                    entries.append(e)
    recent_entries = entries[-n:]
    ban = []
    seen = set()
    for e in recent_entries:
        for t in (e.get("tracks") or []):
            if not isinstance(t, dict):
                continue
            key = f"{t['artist']} — {t['title']}"
            if key not in seen:
                seen.add(key)
                ban.append(key)

    # case-folded so this counter and graph.py's served_artist_counts() agree
    artist_counts = Counter()
    display = {}
    window = all_entries[-ARTIST_WINDOW:]
    for e in window:
        for t in (e.get("tracks") or []):
            if isinstance(t, dict) and t.get("artist"):
                k = t["artist"].strip().lower()
                display.setdefault(k, t["artist"].strip())
                artist_counts[k] += 1
    overexposed = [{"artist": display[a], "appearances": c}
                   for a, c in artist_counts.most_common() if c >= ARTIST_SOFT_BAN]

    print(json.dumps({
        "status": "ok",
        "domain": domain,
        "playlists_considered": len(recent_entries),
        "note": (
            "These tracks appeared in this domain's recent playlists. Do NOT reuse "
            "them — pick fresh. (At most one may return if genuinely irreplaceable.)"
        ),
        "ban_list": ban,
        "artist_frequency_window": len(window),
        "overexposed_artists": overexposed,
        "artist_note": (
            f"Artists appearing >={ARTIST_SOFT_BAN}x in the last {len(window)} playlists "
            "(all domains). SOFT signal: they must earn their next slot on concept-fit; "
            "never an artist ban."
        ),
        "recent_playlists": [
            {"name": e["playlist_name"], "date": e.get("date"),
             "tracks": [f"{t['artist']} — {t['title']}" for t in e.get("tracks", [])]}
            for e in recent_entries
        ],
    }, indent=2))


def create(input_path: str):
    with open(input_path) as f:
        payload = json.load(f)

    name = payload["playlist_name"]
    description = payload.get("description", "")
    tracks = payload["tracks"]

    try:
        creds = load_credentials()
        dev_token = generate_developer_token(creds)
        mut = get_music_user_token(creds)
    except (FileNotFoundError, ValueError) as e:
        print(json.dumps({"status": "auth_required", "reason": str(e)}))
        sys.exit(0)

    am = AppleMusic(dev_token, mut, creds.get("storefront", "us"))

    resolved_ids = []
    resolved_tracks = []
    skipped = []
    try:
        for t in tracks:
            sid = am.search_song(t["artist"], t["title"], t.get("album"))
            if sid:
                resolved_ids.append(sid)
                resolved_tracks.append(t)
            else:
                skipped.append({
                    "artist": t["artist"],
                    "title": t["title"],
                    "reason": "not found in catalog",
                })
    except AuthRequired as e:
        print(json.dumps({"status": "auth_required", "reason": str(e)}))
        sys.exit(0)

    if not resolved_ids:
        print(json.dumps({
            "status": "error",
            "reason": "no tracks could be resolved",
            "tracks_skipped": skipped,
        }))
        sys.exit(0)

    try:
        result = am.create_playlist(name, description, resolved_ids)
    except AuthRequired as e:
        print(json.dumps({"status": "auth_required", "reason": str(e)}))
        sys.exit(0)
    except AppleMusicError as e:
        print(json.dumps({"status": "error", "reason": str(e)}))
        sys.exit(1)

    append_ledger(domain_of(name), name, result["id"], resolved_tracks)

    runtime_ms = am.total_duration_ms(resolved_ids)
    runtime_min = round(runtime_ms / 60000, 1)
    print(json.dumps({
        "status": "ok",
        "playlist_url": result["url"],
        "playlist_id": result["id"],
        "tracks_added": len(resolved_ids),
        "runtime_min": runtime_min,
        "runtime_in_target": 30 <= runtime_min <= 40,  # Nick's preferred window
        "tracks_skipped": skipped,
    }))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Path to tracks JSON (create mode)")
    parser.add_argument("--recent", metavar="DOMAIN",
                        help="Print recently-used tracks for a domain "
                             "(Office/Gym/Field/Stage) and exit")
    parser.add_argument("--n", type=int, default=3,
                        help="How many recent playlists to consider (default 3)")
    args = parser.parse_args()

    if args.recent:
        recent(args.recent, args.n)
        return
    if not args.input:
        parser.error("one of --input or --recent is required")
    create(args.input)


if __name__ == "__main__":
    main()

