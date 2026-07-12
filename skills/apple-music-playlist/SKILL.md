---
name: apple-music-playlist
description: Use this skill whenever Nick requests a music lesson, theory explanation, song-structure analysis, genre study, cover deconstruction, or any teaching content where listening to reference tracks first would deepen the lesson. Triggers include "teach me", "lesson on", "give me a lesson", "explain how [artist/genre] does X", "I want to learn about [musical concept]", and lesson requests in any of the four practice tracks (gym, field, Stage, office). Before writing the lesson, this skill builds a PRESCRIPTIVE Apple Music playlist of reference tracks tied to the lesson's specific learning objectives, creates it in Nick's library, and returns the URL. Nick listens first, then reads the lesson. NOT limited to ambient/lofi — pick whatever music the lesson actually calls for.
status: active
---

# Apple Music Playlist Skill

Builds a **prescriptive, lesson-tied** Apple Music playlist before a lesson, so Nick listens
first and learns second. The playlist is curated to the lesson's specific learning objectives —
not an ambient stack. Pick whatever music the lesson calls for; Nick's taste is far wider than
lofi.

> **Context worth reading once:** `music/listening.md` is the project's listening contract. This
> skill is the programmatic fulfillment of the "made you a playlist" half of it. Two conventions:
> (1) **Name format — the STANDARD (set 2026-07-10): `{index}-{location}-{NN}-{title-slug}`.**
> All lowercase, hyphen-delimited, **NO emoji** (Apple ignores emoji when sorting — the old 🎧
> prefix scattered the playlists; retired 2026-07-10).
> - **`{index}`** — the **global running playlist integer**, zero-padded to 3 (`000`, `016`, …),
>   incrementing at the Apple-Music-library level across EVERY lesson playlist regardless of
>   track. It is the sort key and the only globally-unique field: highest = newest = listen;
>   lowest = oldest = cull. **Read it from the counter file
>   `backstairs/apple-music-playlist/next_playlist_index.txt`, use it, then increment the
>   file** (write index+1, same zero-pad). NEVER guess the next number; if the counter file is
>   missing, rebuild it as (max index in `music/listening.md`'s Playlist log) + 1.
>   **Playlist index ≠ lesson number, by decision — let them drift** (Nick: "I want an
>   apple-music-level index increment").
> - **`{location}`** — the track, lowercase: `gym` / `field` / `office` / `stage`.
> - **`{NN}`** — that location's **own lesson number as the lesson FILE writes it** (gym = its
>   3-digit global `NNN`, e.g. `025`; field/office = their per-track numbers, e.g. `10`, `02`).
>   **No instrument abbreviation** (never `vx`/`fm`/`ep`/`ma`/`ml`), no `L` prefix, never `Sylvia`.
> - **`{title-slug}`** — the lesson title, kebab-case lowercase, punctuation dropped.
>
> Examples: `000-gym-021-the-straw-the-glide-the-hills`, `015-field-10-bass-in-the-space`,
> `016-gym-027-arrange-by-subtraction`. (The old `🎧 {Place} {NN}: {Title}` standard is retired;
> the 2026-07-10 batch rename moved the whole library to this scheme — indices 000–015.)
> (2) After creation, append a line to its **Playlist log** section.

When Nick requests a lesson, follow this sequence STRICTLY.

## Step 0: Think hard — internally, not out loud
Before anything else, do a deliberate reasoning pass **in your own thinking** (not in visible
output — Nick wants the curated result, not the deliberation). Think as hard as you can about:
- the 2–4 learning objectives the lesson actually teaches;
- a generous candidate pool of tracks, each weighed against those objectives;
- which to cut, and **why this exact ordering** (the arc from accessible/canonical → contrastive/
  challenging, and how each track sets up the next).

This deliberation stays in your head. Nick sees only the playlist, a one-line note, and the
lesson. Never print the candidate list or the reasoning chain to the chat.

## Step 1: Identify learning objectives
Internally name 2–4 concrete things the lesson should teach (e.g. "how horn stabs accent the
upbeat in ska," "verse–prechorus–chorus contrast in pop-punk," "Tubby's dropout-then-throw move
on the master bus").

## Step 2: Select tracks
**The north star is that Nick LOVES every playlist.** This is an act of taste, not quota-filling.
Curate like you're making a mix for someone whose ear you respect — every track earns its place
and the sequence tells a story.

**Freshness is non-negotiable — do not recycle the canon.** Before selecting, run the ledger
check — it does the remembering for you:

```bash
~/venv/default/bin/python \
  /Users/dad/Documents/sandbox/backstairs/apple-music-playlist/scripts/create_playlist.py \
  --recent <Domain>          # Office | Gym | Field | Stage
```

It prints a `ban_list` of every track used in that domain's last 3 playlists, straight from the
auto-maintained ledger (`used_tracks.jsonl` — it updates itself on every successful create AND
on every sideload; you never maintain it), plus **`overexposed_artists`** — artists appearing ≥3×
in the last 15 playlists across ALL domains. **Treat the `ban_list` as hard-banned — do not reuse
those tracks.** Overexposed artists are a SOFT signal: they must earn their next slot on
concept-fit (never an artist ban — the exclusion unit is the worn track, not the artist). The
human-readable narrative still lives in `music/listening.md`'s Playlist log. A lesson playlist is
a growing discography of *listening-Nick* (see `music/listening.md`);
repeating the same 6–8 tracks lesson after lesson defeats its purpose and teaches nothing new.
This trap is real and it has bitten: the dub/office lessons kept collapsing onto the same canon
(Real Rock, Armagideon Time, Sleng Teng, King Tubby Meets Rockers Uptown, Super Ape, Mikey Dread) —
Nick called it out on 2026-06-08 (6 of 8 tracks identical between L04 and L05). Two causes to fight
in yourself: (a) **canon-default** — reaching for the famous handful you can recall with zero doubt
instead of mining the genre's depth (riddim families, the wider album canon, the DJ/toaster lineage,
regional scenes, later generations); (b) **availability-hedging** — picking famous tracks because
you're *sure* they won't skip. Resist both. The catalog is deep; web search can't verify Apple Music
availability anyway (the create script in Step 4 IS the catalog query), so pick fresh and **accept
some skip-risk** — the script reports skips and you patch them, rather than retreating to the canon.
If one canonical track is genuinely irreplaceable for THIS lesson's objective, you may keep ONE;
never build a list out of the previous list. See memory `feedback_playlists_push_past_canon_no_repeats`.

**Curate for a deep listener — deep by default.** Nick has a strong music background and actively
hunts new/deep music; he has *already heard* most of the canonical hits, so a playlist of obvious
picks teaches him nothing and bores him. He set the dial (2026-06-08) to **deep by default**: most
picks should be cuts he likely hasn't heard, and the famous/canonical track is the **exception that
must earn its slot** — justify it only when (a) it's the genuine irreplaceable touchstone for the
objective, or (b) the lesson explicitly anchors on it (the anchor-track rule). When a pick is the
first thing anyone would name, **deliberately go a layer deeper before committing**: the producer's
lesser-known work, the contemporaries and the scene *around* the famous name, deep album cuts and
B-sides, regional variants, the later artists carrying the torch. When the genre is one where you'd
otherwise reach for the same ten names from memory, **research it** — web-search the era / scene /
label for lesser-known names (the create script remains the availability truth, so accept skip-risk).

**Deep, not contrarian.** "Weird" is not the goal; *lovable-and-deep* is. Every pick must still
(a) teach the objective and (b) be something Nick would genuinely enjoy. A rare cut that doesn't
serve the lesson is worse than a famous one that nails it. Surprise him with something excellent he
hasn't heard — don't prove you can find the obscurest thing. *(No maintained "heard-it" exclude
list — Nick declined one 2026-06-08; the deep-default + the no-repeat ledger + his in-the-moment
flags are the whole system. If he says "heard it" about a pick, swap it and remember it for the
session.)*

### Step 2 runs ON THE ENGINE, not from memory (2026-07-03 — mandatory)

Memory-curation is the canon-gravity path; the engine is how the 2026-07-03 redo produced
playlists Nick called phenomenal. Build the pool with tools, rank it by sound, then curate the
arc from the ranking. The shared engine lives in the sibling skill —
`backstairs/research-playlist/` — and its SKILL.md carries the full precedence text; the
binding rules are inlined here because the doc in front of you is the one that wins:

1. **Decompose the concept into its AUDIBLE SIGNATURE** (not "reggae" — "the one-drop's kick+rim
   on beat 3 under floating hats"). This is your semantic job; the tools serve it.
2. **Map the neighborhood** (when the concept has a scene/lineage):
   `~/venv/default/bin/python .../research-playlist/scripts/graph.py --seed "<exemplar>" --hops 2`
   — 3-source quorum (ListenBrainz+Last.fm+Discogs), accumulating graph, `deep_zone` flags,
   served-artist demotion, `loved_artist` lift. NEVER `--novelty-filter` for a lesson pool.
3. **Build the track pool**: `track_pool.py --artist ... [--pages 2] [--mb-recordings ...]` —
   use the `all` list; head tier = familiarity COST, not a cut.
4. **Rank by concept**: `~/venv/musicdna/bin/python .../research-playlist/scripts/audio_dna.py
   --rank --weights <profile-or-custom-json> [--target "Artist :: Title"] --candidates pool.json`
   (a loved track that matches the concept is the natural `--target` — check `graph.py --taste`).
   Download-on-demand is on by default; if `ranking_valid_for_curation` is false, fix resolution
   before curating. Curate the arc FROM this ranking + the brief; check `values`/`wrong_direction`.
5. **The RHCP precedence** (settles every famous-track conflict): artist fame is NEVER a filter;
   familiarity of a specific track is a cost concept-precision can pay. Max ONE canonical track,
   only as the concept anchor, affirmed with its DNA receipt. In near-ties the less-worn track
   wins. DNA is a receipt, not the curator, on semantic-driven lessons (voice pairs, theory) —
   say which it was.
6. **Critic pass is affirm-or-swap**: for each flagged track, either name the deeper cut from the
   ranked pool that replaces it, or explicitly affirm it with evidence. Record the verdict in the
   listening.md log line.

**Default to 30–40 minutes of total runtime** (Nick's preferred sitting) — a guide, not a cage.
Go longer when the lesson carries real gravity, or when settling something hard needs the
repetition of hearing the concept several ways. Go shorter if five tracks say it perfectly.
Length serves the lesson and the love; it is never padded to hit a number. At typical song
lengths 30–40 min is ~8–11 tracks; adjust for genre. The script reports `runtime_min` and
`runtime_in_target` — use it to sanity-check, not to obey. Each track must:
- Be available on Apple Music (no obscure bootlegs; no live-only recordings unless central).
- Map clearly to at least one learning objective.
- Be ordered intentionally by the lesson's **arc**, not by fame. **Do NOT default to "famous
  first"** — Nick is a deep listener (see "Curate for a deep listener" below); lead with whatever
  best opens the objective, which is often a deep cut, not the hit.

**Anchor-track-first rule:** if the lesson explicitly names a source/anchor track ("the record:
…", "listen to X before you begin", a track to sample/cover) and it IS on Apple Music, it MUST be
track #1 — the lesson's own touchstone leads the playlist. (If it's not on Apple Music, lead with
the closest analog and Nick sources the literal one himself.)

Pick prescriptively. The right reference for a ska-horn lesson is Reel Big Fish, not Nujabes.

**The playlist is a window into what Nick is studying — NOT the lesson's literal material.**
If a lesson names a specific source to sample/loop/cover and it isn't on Apple Music, do NOT
edit the lesson and do NOT drop the idea — put a findable **analog** in the playlist (a real
Real Rock vocal version stands in for an unavailable one; a different cut by the named artist
stands in for a missing track). Nick sources the literal material himself (YouTube, vinyl).
Apple Music availability never drives a lesson edit.

## Step 3: Write the track list to JSON

> **Engine-artifact gate (2026-07-09).** Before you write this JSON, you MUST already have an
> `audio_dna.py --rank` output on disk for this lesson's pool, and the tracklist must be curated
> *from that ranking* — not from memory. No ranking file = you skipped Step 2; stop and run the
> engine (`graph.py` walk → `track_pool.py` → `audio_dna.py --rank`, targeting a loved track from
> `graph.py --taste`). Curating "deep from memory" is still the canon-gravity failure — Nick has
> flagged it twice (2026-07-03, and again 2026-07-09 when a from-memory list re-used a just-played
> anchor). The ranking file is the receipt that you didn't. The whole point of the engine is to
> offload the freshness burden off both your and Nick's cognition — skipping it defeats the tool.

Write to `/tmp/lesson_tracks.json` in this exact schema:

```json
{
  "playlist_name": "016-office-09-the-selectors-shelf",
  "description": "[1-sentence description of what Nick will hear and why]",
  "tracks": [
    {
      "artist": "Reel Big Fish",
      "title": "Sell Out",
      "album": "Turn the Radio Off",
      "rationale": "Canonical horn stabs accenting upbeats; chorus horn line in parallel thirds"
    }
  ]
}
```

`playlist_name` MUST follow the **standard `{index}-{location}-{NN}-{title-slug}`** (see the intro
convention): read `{index}` from `backstairs/apple-music-playlist/next_playlist_index.txt` and
increment the file after use; `{location}` = lowercase track (`gym`/`office`/`field`/`stage`);
`{NN}` = that location's lesson number exactly as the lesson FILE writes it (`027-lab` → `027`,
`10-…` field → `10`); `{title-slug}` = kebab-case lowercase title. **No emoji, no instrument
abbreviation, never a `Sylvia` prefix.** Examples: `000-gym-021-the-straw-the-glide-the-hills`,
`015-field-10-bass-in-the-space`. The `{location}-{NN}` pair pins which lesson the playlist belongs
to; the front integer is the global sort/cull key and may drift from the lesson number. (Older
`🎧 {Place} {NN}: {Title}` / `Office L05` forms are retired — the 2026-07-10 batch rename converted
the library.) `album` is optional but improves match precision. `rationale` is required — it
justifies the pick and doubles as Nick's reading guide.

## Delivery — the two-pass, verify-or-it-didn't-happen model (2026-07-02)

**Curation quality is decoupled from Apple's catalog. Curate the RIGHT tracks (any genre, any
depth) and let delivery worry about getting them there — never trim a tracklist to what Apple
happens to carry.** This came from a real failure: Office 06 was reported by the catalog API as
`tracks_added: 8` and actually shipped **0** — an empty playlist on Nick's phone *and* studio. The
catalog track-add is unreliable, and dub/reggae/deep cuts are often missing from the catalog
entirely. So delivery is now two passes plus a mandatory verify.

**Run delivery in a sub-agent, and WAIT for iCloud sync before finalizing (2026-07-09).** A
second real failure: `create_playlist.py` makes the playlist in the **cloud** library and adds
catalog tracks, but the local Music.app hasn't synced it down yet — so `sideload_tracks.py`'s
AppleScript add fails with `PLAYLIST_NOT_FOUND`, downloading the gap tracks but never adding them,
and the Step 6 verify then finds **no local playlist at all**. Two fixes, both baked in below:
(1) a **sync-wait gate (Step 4.5)** that polls the local Music.app until the just-created playlist
is actually visible *before* sideloading; (2) because that waiting/polling is context-heavy and
must never block curation, **hand Steps 4–6 to a sub-agent** (Agent tool, `general-purpose`) that
owns the whole `create → wait-for-sync → sideload → verify` loop and returns only once an
on-device count matches the curated track count. The main session does Steps 0–3 (curate on the
engine) and writes the lesson; the sub-agent guarantees the tracks physically landed. **Never
report a playlist as ready without the sub-agent's on-device count in hand.**

**The sub-agent owns the playlist EXCLUSIVELY while it runs (2026-07-09).** The main session must
not create/delete/edit the same playlist concurrently. If you must intervene, **`TaskStop` the
sub-agent FIRST**, then take over — a sub-agent can resume on its own (its sync-waiter fires, or it
had other children) and *race* you, deleting a list you just fixed (observed: the delivery
sub-agent deleted the populated playlist mid-repair while the main session was removing one bad
track). **And when cloud playlists never sync down within the Step 4.5 cap, don't keep waiting —
the robust path is to CREATE THE PLAYLIST LOCALLY via AppleScript and sideload every track into it**
(`make new user playlist with properties {name:…}`, then `sideload_tracks.py`; the local list +
local files sync UP to the phone when Sync Library is on, which today's other lessons confirm it
is). One more real hazard from that day: the sideloader can **mis-match an obscure title to a short
wrong clip** (a 47-second "Viens danser le smurf" stood in for Brain Damage's "Visages sur l'écran",
which has no clean full upload) — **spot-check sideloaded durations; if a track has no clean
full-length source, drop it and ship one fewer rather than a broken clip.**

### Step 4: Create the playlist + best-effort catalog pass
```bash
~/venv/default/bin/python \
  /Users/dad/Documents/sandbox/backstairs/apple-music-playlist/scripts/create_playlist.py \
  --input /tmp/lesson_tracks.json
```
This creates the named playlist, **updates the freshness ledger** (`used_tracks.jsonl` — required for
future `--recent` bans), and returns the `playlist_url`/`playlist_id`. Whatever catalog tracks it
adds are a *best-effort first pass* (catalog versions are higher quality when they land) — but
**do NOT trust `tracks_added` as proof of delivery.** It counts catalog *matches*, not tracks that
actually persisted. If `status` is `"auth_required"`, tell Nick to re-run the bridge and STOP:
```bash
~/venv/default/bin/python \
  /Users/dad/Documents/sandbox/backstairs/apple-music-playlist/scripts/serve_bridge.py
```

### Step 4.5: Wait for the playlist to sync to the local Music app (2026-07-09)
`create_playlist.py` writes to the **cloud** library; `sideload_tracks.py` adds via **local**
AppleScript. Between them, the new playlist must actually appear in the local Music.app or the
sideload silently fails (`PLAYLIST_NOT_FOUND`) — see the delivery-intro failure note. In the
sub-agent, poll until the playlist name (all-ASCII under the 2026-07-10 standard — the full
`{index}-{location}-{NN}-{title-slug}` name is the token) resolves locally, **before** sideloading.
Use an `until`-loop with a single `sleep` (run in background / with a timeout — do not chain
foreground sleeps), capped at ~10 minutes:
```bash
tok='015-field-10-bass-in-the-space'   # the playlist name (ASCII, so the whole name is the token)
until [ "$(osascript -e "tell application \"Music\" to return (count of (every user playlist whose name contains \"$tok\"))" 2>/dev/null || echo 0)" -ge 1 ] 2>/dev/null; do sleep 10; done
echo "SYNCED: $tok is visible locally"
```
If it never resolves within the cap, the cloud create didn't sync — do **not** sideload against a
phantom playlist. Nudge sync (bring Music to the foreground / toggle Sync Library off-on), or fall
back to creating the playlist **locally** via AppleScript from the same JSON, then sideload. Only
proceed once the token is visible locally.

### Step 5: Guarantee completeness by sideloading the gaps
```bash
~/venv/default/bin/python \
  /Users/dad/Documents/sandbox/backstairs/apple-music-playlist/scripts/sideload_tracks.py \
  --input /tmp/lesson_tracks.json
```
For each curated track it searches YouTube (preferring official `- Topic` audio, penalizing
live/cover/remix/long-rip results), downloads + tags an `.m4a`, and adds it to the Music library +
the named playlist. Its membership guard **skips any track already present from the catalog pass**,
so you get catalog-where-it-works + sideload-for-the-rest, no duplicates. This is what makes the
playlist catalog-independent — **the Scientist / King Tubby / deep-dub tracks Apple doesn't carry
land here.** Reads the same JSON; matches the playlist by an emoji-free token (under the
2026-07-10 naming that's the full playlist name).
**Prereqs:** `yt-dlp` + `ffmpeg` on PATH, and **Sync Library ON** in Music (or the upload never
reaches Nick's phone). Emits a per-track report (chosen video, tagged path, add status).

### Step 6: VERIFY on-device — the step whose absence shipped an empty playlist
Never report a playlist as ready without confirming the tracks are actually in it:
```bash
osascript -e 'tell application "Music"
set pl to (first user playlist whose name contains "012-office-06")
return "TOTAL:" & (count of tracks of pl)
end tell'
```
The count MUST equal the curated track count. If it's short, re-run Step 5 (or list the playlist's
track names to see which are missing) before moving on. A playlist that "resolved" is not a
playlist that delivered — Office 06 taught that the hard way.

### Step 7: Log, present, then teach
1. Append one line to the **Playlist log** in `music/listening.md`, **noting delivery** (e.g.
   "all N sideloaded" or "catalog + M sideloaded gaps", and any track absent from Apple's catalog)
   **and the critic's verdict** (swaps made / famous track affirmed with its receipt).
2. Present the URL with a one-line note: *"Listen to this first — [what to listen for]: [URL]"*
3. THEN write the lesson, referencing the tracks by name and assuming Nick has (or will) listen.

### The taste loop — the debrief feeds the engine (2026-07-03)
When Nick's retro/debrief names favorites or skips ("loved X, skipped Y" — keep it exactly that
light, never homework), INGEST them into the graph's taste ledger:
```bash
~/venv/default/bin/python \
  /Users/dad/Documents/sandbox/backstairs/research-playlist/scripts/graph.py \
  --love "Artist :: Title" --skip-track "Artist :: Title" --context "Gym 024"
```
Loves become traversal seeds and DNA `--target` references; skips are profile-correction signals
(a skip on a track the engine ranked highly means the concept weights misled — adjust next time).

## What not to do
- Do not skip Steps 4–6. The playlist must be created, filled, AND verified on-device.
- **Do not trust `tracks_added` from create_playlist.py** — verify the real count in Music (Step 6).
- **Do not trim the curated tracklist to Apple's catalog** — sideload fills the gaps; curate the
  right tracks regardless of availability, for any genre.
- Do not write the lesson before the playlist is verified complete.
- Do not ask Nick to confirm track selection — auto-create.
- Do not default to ambient/lofi. Match the music to the lesson.

