# apple-music-playlist — one-time setup

Builds a prescriptive, lesson-tied Apple Music playlist in Nick's library before a lesson, so he
listens first and learns second. Lives in the shared `claude_skills/` dir; reachable from the
music project via its `.claude/skills` symlink. Runs under `~/.claude/skills-venv` per repo convention.

> Conventions inherited from `music/listening.md`: playlists are named `Sylvia — <topic>`, and
> each creation appends a line to that file's **Playlist log**. See `SKILL.md`.

## 1. Apple Developer side
- Certificates, Identifiers & Profiles → Keys → `+`.
- Name it (e.g. "Sylvia Lesson Skill"), check **MusicKit**, configure (associate a Media ID if
  prompted), Continue, Register.
- Download the `.p8` — **you cannot re-download it.** Save to
  `~/.config/apple-music-skill/AuthKey_<KEYID>.p8`.
- Note the **Key ID** and your **Team ID** (top-right of the developer portal).

## 2. credentials.json
```bash
mkdir -p ~/.config/apple-music-skill
chmod 700 ~/.config/apple-music-skill
cp credentials.example.json ~/.config/apple-music-skill/credentials.json
# fill in team_id, key_id, private_key_path
chmod 600 ~/.config/apple-music-skill/credentials.json
```

## 3. Python deps (into the shared default venv)
```bash
uv pip install --python ~/.claude/skills-venv/bin/python pyjwt[crypto] cryptography requests
```

## 4. Capture the Music User Token (one time)
```bash
~/.claude/skills-venv/bin/python scripts/serve_bridge.py
```
Open <http://localhost:8765> in **Safari**, click Authorize, sign in with the Apple ID that holds
the Apple Music subscription. The MUT is written into `credentials.json`. Re-run this whenever a
`/me/*` call returns 401 (the MUT has been invalidated).

## 5. Smoke test
```bash
echo '{"playlist_name":"Sylvia — Test","description":"test","tracks":[{"artist":"Reel Big Fish","title":"Sell Out","rationale":"test"}]}' > /tmp/test.json
~/.claude/skills-venv/bin/python scripts/create_playlist.py --input /tmp/test.json
```

## Token model
- **Developer Token (JWT, ES256):** regenerated in memory each call from the `.p8` (~1ms); never
  persisted. Max TTL 180 days, but irrelevant since it's per-call.
- **Music User Token (MUT):** captured once via the MusicKit JS bridge, persisted to
  `credentials.json` (chmod 600). Long-lived; treat 401 on `/me/*` as the re-auth signal.

## Failure modes
| Symptom | Cause | Fix |
|---|---|---|
| `auth_required` / 401 on `/me/library/playlists` | MUT expired or invalidated | Re-run `serve_bridge.py` |
| 403 right after fresh auth | MusicKit JS v3 account quirk | `music.unauthorize()` then re-auth |
| `auth_required` on catalog search | Dev token / `.p8` problem | Confirm `.p8` exists and matches Key ID |
| Track in `tracks_skipped` | Title/artist mismatch or regional gap | Add `album` to disambiguate; retry |

## Known API limitations
- **No programmatic delete.** `DELETE /v1/me/library/playlists/{id}` returns 401 — Apple doesn't
  expose library-playlist deletion to the API. A regenerated/superseded playlist must be deleted
  by hand in the Music app. (Renaming via `PATCH` is likewise unreliable; recreate instead.)
- **`globalId` lag.** Right after creation the shareable URL falls back to `…/library/playlist/p.…`,
  which resolves only in Nick's signed-in Music app. That's fine for personal use.

## Deferred (v1 scope)
Album-level expansion (whole album → tracklist), playlist folders, confirmation flow, track-miss
retry/fuzzy-match, dedup. Each lesson gets its own playlist; they accumulate in the library.
Mac only.
