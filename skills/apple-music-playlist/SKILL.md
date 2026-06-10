---
name: apple-music-playlist
description: Use this skill whenever Nick requests a music lesson, theory explanation, song-structure analysis, genre study, cover deconstruction, or any teaching content where listening to reference tracks first would deepen the lesson. Triggers include "teach me", "lesson on", "give me a lesson", "explain how [artist/genre] does X", "I want to learn about [musical concept]", and lesson requests in any of the four practice tracks (gym, playground, Stage, office). Before writing the lesson, this skill builds a PRESCRIPTIVE Apple Music playlist of reference tracks tied to the lesson's specific learning objectives, creates it in Nick's library, and returns the URL. Nick listens first, then reads the lesson. NOT limited to ambient/lofi — pick whatever music the lesson actually calls for.
status: active
---

# Apple Music Playlist Skill

Builds a **prescriptive, lesson-tied** Apple Music playlist before a lesson, so Nick listens
first and learns second. The playlist is curated to the lesson's specific learning objectives —
not an ambient stack. Pick whatever music the lesson calls for; Nick's taste is far wider than
lofi.

> **Context worth reading once:** `music/listening.md` is the project's listening contract. This
> skill is the programmatic fulfillment of the "made you a playlist" half of it. Two conventions:
> (1) name playlists by **domain**, never with a "Sylvia" prefix — `Office L03: The Second Voice`,
> `Gym — Filter Envelopes`, `Playground — Pocket & Swing`; the track the lesson belongs to leads
> the name. (2) After creation, append a line to its **Playlist log** section.

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
~/.claude/skills-venv/bin/python \
  /Users/dad/Documents/sandbox/projects/claude_skills/apple-music-playlist/scripts/create_playlist.py \
  --recent <Domain>          # Office | Gym | Playground | Stage
```

It prints a `ban_list` of every track used in that domain's last 3 playlists, straight from the
auto-maintained ledger (`used_tracks.jsonl` — it updates itself on every successful create; you
never maintain it). **Treat the `ban_list` as hard-banned — do not reuse those tracks.** The
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
Write to `/tmp/lesson_tracks.json` in this exact schema:

```json
{
  "playlist_name": "Office L05: The Selector's Shelf",
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

`playlist_name` is **domain-named** — `Office L05: The Selector's Shelf`, `Gym — Filter Envelopes`,
`Playground — Pocket & Swing` (the track the lesson belongs to leads the name). It must **never**
start with a `Sylvia — ` prefix — that was an early convention, since retired; the `listening.md`
log confirms the domain-named form. `album` is optional but improves match precision. `rationale`
is required — it justifies the pick and doubles as Nick's reading guide.

## Step 4: Invoke the skill script
```bash
~/.claude/skills-venv/bin/python \
  /Users/dad/Documents/sandbox/projects/claude_skills/apple-music-playlist/scripts/create_playlist.py \
  --input /tmp/lesson_tracks.json
```

The script prints JSON to stdout:
```json
{
  "status": "ok",
  "playlist_url": "https://music.apple.com/us/playlist/…/pl.u-…",
  "playlist_id": "pl.u-…",
  "tracks_added": 8,
  "tracks_skipped": [{"artist": "…", "title": "…", "reason": "not found in catalog"}]
}
```

If `status` is `"auth_required"`, tell Nick to re-run the bridge and STOP — do not write the lesson:
```bash
~/.claude/skills-venv/bin/python \
  /Users/dad/Documents/sandbox/projects/claude_skills/apple-music-playlist/scripts/serve_bridge.py
```

## Step 5: Log, present, then teach
1. Append one line to the **Playlist log** in `music/listening.md`:
   `- **YYYY-MM-DD** — *<topic>* (<n> tracks) — <playlist_url>`
2. Present the URL with a one-line note: *"Listen to this first — [what to listen for]: [URL]"*
3. If tracks were skipped, mention them in one line.
4. THEN write the lesson, referencing the playlist tracks by name and assuming Nick has (or will)
   listen to them.

## What not to do
- Do not skip Step 4. The playlist must actually be created.
- Do not write the lesson before the playlist URL is returned.
- Do not ask Nick to confirm track selection — auto-create.
- Do not invent tracks. If unsure a track exists, exclude it.
- Do not default to ambient/lofi. Match the music to the lesson.
