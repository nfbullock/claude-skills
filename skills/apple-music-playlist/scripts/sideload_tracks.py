#!/usr/bin/env python3
"""Sideload lesson tracks from YouTube into Apple Music (library + a named playlist).

The delivery-robust alternative to the catalog-API path in create_playlist.py.
create_playlist.py depends on Apple Music's catalog: tracks missing from it get
dropped (silent gaps), and the library-playlist track-add is itself unreliable —
it can report success while nothing lands (this is what shipped an empty Office 06).

This script decouples curation from Apple's catalog entirely: for each curated track
it searches YouTube (preferring official "- Topic" audio), downloads + tags an .m4a,
then drives Music.app via AppleScript to add it to the library AND to the target
playlist. With Sync Library on, the upload propagates to the phone. What you curate
is what ships — any genre, no catalog gaps.

Input JSON is the SAME schema create_playlist.py consumes:
  {"playlist_name": "🎧 Office 06: The 16th-Note Roll",
   "tracks": [{"artist": "...", "title": "...", "album": "...", "rationale": "..."}]}

Usage:
  sideload_tracks.py --input tracks.json
  sideload_tracks.py --input tracks.json --skip "Scientist - Your Teeth in My Neck"
  sideload_tracks.py --input tracks.json --download-only   # stage files, no Music.app
  sideload_tracks.py --input tracks.json --playlist "🎧 Office 06: The 16th-Note Roll"

Prereqs: yt-dlp + ffmpeg on PATH; Music.app with Sync Library ON (for phone sync).
Emits a JSON report to stdout (per-track: chosen video, tagged path, add status).
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent / "used_tracks.jsonl"

# --- YouTube candidate selection -------------------------------------------------

# Keywords that usually mean the WRONG version for a study playlist, unless the
# curated title itself asks for them.
_BAD_KEYWORDS = [
    "live", "cover", "reaction", "remix", "instrumental", "karaoke",
    "sped up", "slowed", "reverb", "8d", "loop", "1 hour", "hour version",
    "lyrics", "tutorial", "how to", "bass boosted", "nightcore",
]


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def search_candidates(query, n=6):
    """Return list of dicts {id,duration,uploader,title} for a YouTube search."""
    fmt = "%(id)s\t%(duration)s\t%(uploader)s\t%(title)s"
    r = _run([
        "yt-dlp", "--no-warnings", "--skip-download", "--flat-playlist",
        "--print", fmt, f"ytsearch{n}:{query}",
    ])
    out = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        vid, dur, uploader, title = parts[0], parts[1], parts[2], "\t".join(parts[3:])
        try:
            dur = int(float(dur))
        except (ValueError, TypeError):
            dur = 0
        out.append({"id": vid, "duration": dur, "uploader": uploader, "title": title})
    return out


def score_candidate(cand, artist, title):
    """Higher is better. Prefers official Topic audio, penalizes wrong-version noise."""
    score = 0.0
    up = (cand["uploader"] or "").lower()
    t = (cand["title"] or "").lower()
    a = artist.lower()
    ti = title.lower()

    # Official auto-generated audio channel — the cleanest source.
    if up.endswith("- topic"):
        score += 100
    # Artist name present in uploader or title is a good sign.
    if a in up or a in t:
        score += 20
    # Title of the track present.
    if ti in t:
        score += 25
    # Penalize wrong-version keywords UNLESS the curated title asked for them.
    for kw in _BAD_KEYWORDS:
        if kw in t and kw not in ti:
            score -= 40
    # Plausible song duration (2–9 min); hard-penalize very long (full-album rips).
    d = cand["duration"]
    if 90 <= d <= 560:
        score += 15
    elif d > 900:
        score -= 30
    return score


def pick_best(candidates, artist, title):
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda c: score_candidate(c, artist, title), reverse=True)
    return ranked[0]


# --- Download + tag --------------------------------------------------------------

def _slug(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")


def _fname(s):
    """Filename-safe component — '/' in an artist/title must not become a directory."""
    return re.sub(r"[/\\:]+", "-", s or "").strip()


def download_and_tag(track, video_id, staging: Path):
    """Download bestaudio -> m4a, then rewrite clean metadata. Returns final path."""
    base = _slug(f"{track['artist']} - {track['title']}")
    raw = staging / f"{base}.raw.m4a"
    final = staging / f"{_fname(track['artist'])} - {_fname(track['title'])}.m4a"

    dl = _run([
        "yt-dlp", "--no-warnings", "-x", "--audio-format", "m4a",
        "--audio-quality", "0", "-o", str(raw),
        f"https://youtu.be/{video_id}",
    ])
    if not raw.exists():
        return None, dl.stderr.strip()[-400:]

    meta = [
        "-metadata", f"title={track['title']}",
        "-metadata", f"artist={track['artist']}",
        "-metadata", f"album_artist={track['artist']}",
    ]
    if track.get("album"):
        meta += ["-metadata", f"album={track['album']}"]
    ff = _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-c", "copy",
        *meta, str(final),
    ])
    raw.unlink(missing_ok=True)
    if not final.exists():
        return None, ff.stderr.strip()[-400:]
    return final, None


# --- Music.app sideload (AppleScript) --------------------------------------------

_APPLESCRIPT = r'''
on run argv
	set plToken to item 1 of argv
	set filePaths to rest of argv
	set report to ""
	tell application "Music"
		if it is not running then launch
		set foundPl to missing value
		repeat with p in user playlists
			if name of p contains plToken then
				set foundPl to p
				exit repeat
			end if
		end repeat
		if foundPl is missing value then
			return "PLAYLIST_NOT_FOUND:" & plToken
		end if
		repeat with fp in filePaths
			with timeout of 300 seconds
				try
					set newTrack to add (POSIX file (fp as text))
					set tn to name of newTrack
					set ta to artist of newTrack
					-- avoid re-adding if already present. Name AND artist: two artists
					-- covering one title are different tracks (the name-only guard
					-- silently dropped Iron & Wine's cover behind Postal Service's).
					if (count of (tracks of foundPl whose name is tn and artist is ta)) is 0 then
						duplicate newTrack to foundPl
					end if
					set report to report & "OK\t" & tn & linefeed
				on error errm
					set report to report & "ERR\t" & (fp as text) & "\t" & errm & linefeed
				end try
			end timeout
		end repeat
	end tell
	return report
end run
'''


def playlist_token(name):
    """A distinctive, emoji-free substring for AppleScript `contains` matching."""
    # e.g. "🎧 Office 06: The 16th-Note Roll" -> "Office 06"
    m = re.search(r"([A-Za-z]+\s+\d+)", name)
    if m:
        return m.group(1)
    # fallback: strip leading non-alphanumerics, take text before a colon
    stripped = re.sub(r"^[^A-Za-z0-9]+", "", name)
    return stripped.split(":")[0].strip() or stripped


def sideload_into_music(files, token, staging: Path):
    script_path = staging / "_sideload.applescript"
    script_path.write_text(_APPLESCRIPT, encoding="utf-8")
    args = ["osascript", str(script_path), token] + [str(f) for f in files]
    r = _run(args)
    return r.stdout.strip(), r.stderr.strip()


# --- main ------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="tracks JSON (create_playlist schema)")
    ap.add_argument("--playlist", help="override playlist_name from the JSON")
    ap.add_argument("--skip", action="append", default=[],
                    help='"Artist - Title" to skip (already in the playlist). Repeatable.')
    ap.add_argument("--staging", help="dir for downloaded m4a (default: temp)")
    ap.add_argument("--download-only", action="store_true",
                    help="download + tag only; do not touch Music.app")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text())
    playlist_name = args.playlist or data["playlist_name"]
    token = playlist_token(playlist_name)
    skip = {s.strip().lower() for s in args.skip}

    staging = Path(args.staging) if args.staging else Path(tempfile.mkdtemp(prefix="sideload_"))
    staging.mkdir(parents=True, exist_ok=True)

    results = []
    ready_files = []
    for tr in data["tracks"]:
        key = f"{tr['artist']} - {tr['title']}".lower()
        if key in skip:
            results.append({"track": key, "status": "skipped"})
            continue
        query = f"{tr['artist']} {tr['title']}"
        cands = search_candidates(query)
        best = pick_best(cands, tr["artist"], tr["title"])
        if not best:
            results.append({"track": key, "status": "no_candidate"})
            continue
        path, err = download_and_tag(tr, best["id"], staging)
        if not path:
            results.append({"track": key, "status": "download_failed", "error": err})
            continue
        ready_files.append(path)
        results.append({
            "track": key, "status": "staged",
            "video": f"https://youtu.be/{best['id']}",
            "uploader": best["uploader"], "duration_s": best["duration"],
            "official_topic": best["uploader"].lower().endswith("- topic"),
            "path": str(path),
        })

    report = {"playlist": playlist_name, "token": token, "staging": str(staging),
              "results": results}

    if not args.download_only and ready_files:
        out, errout = sideload_into_music(ready_files, token, staging)
        report["sideload_stdout"] = out
        report["sideload_stderr"] = errout
        for line in out.splitlines():
            if line.startswith("OK\t"):
                name = line.split("\t", 1)[1]
                for r in results:
                    if r.get("status") == "staged" and name.lower() in r["track"]:
                        r["status"] = "added"
        _append_ledger(playlist_name, data["tracks"], results)

    print(json.dumps(report, indent=2, ensure_ascii=False))


def _append_ledger(playlist_name, tracks, results):
    """Record sideloaded tracks in the freshness ledger. Without this, off-catalog
    deep cuts — the tracks this tool exists for — are invisible to the no-repeat ban
    and the served-artist demotion, and get re-served as 'fresh'. Never raises."""
    try:
        added = {r["track"] for r in results if r.get("status") == "added"}
        if not added:
            return
        landed = [{"artist": t["artist"], "title": t["title"]} for t in tracks
                  if f"{t['artist']} - {t['title']}".lower() in added]
        if not landed:
            return
        m = re.search(r"[A-Za-z]+", playlist_name)          # same rule as create_playlist
        entry = {
            "domain": m.group(0).lower() if m else "",
            "date": datetime.date.today().isoformat(),
            "playlist_id": None,
            "playlist_name": playlist_name,
            "via": "sideload",
            "tracks": landed,
        }
        with open(LEDGER, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # the ledger is a convenience, not load-bearing for delivery


if __name__ == "__main__":
    main()

