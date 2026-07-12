---
name: research-playlist
description: On-demand, standalone deep-playlist research for Nick (and his kids' orthogonal music education) — NOT tied to a lesson. Use when Nick asks to "make a playlist about X", "research a playlist", "deep cuts of / around Y", "build the kids a playlist that grows their taste", or wants a non-cliché, non-obvious playlist on any theme/artist/scene/mood/era. Curates deep-by-default, GROUNDS every track against the MusicBrainz graph so nothing is hallucinated, discovers alternate versions (live/acoustic/session), and delivers via sideload (catalog-independent). Sibling to apple-music-playlist (that one is lesson-tied; this one is free-standing and research-driven). STATUS: v0 — iterate early.
status: active
---

# research-playlist — on-demand, graph-grounded, non-hallucinating

The standalone cousin of `apple-music-playlist`. That skill builds a playlist to serve a *lesson*;
**this one answers a free-standing request** — "make me a deep playlist about the Bristol sound,"
"deep cuts *around* Alice Coltrane, not the famous ones," "build the kids something that grows their
ear orthogonally to mine." No lesson, no debrief gate. Just: a top-quality, non-cliché playlist,
on demand, that **contains only real tracks** and **actually lands on the device.**

## The two non-negotiables (why this exists)

1. **No hallucinated tracks.** Nick has a large lexicon and cannot abide invented "deep cuts." Every
   proposed track is **grounded against MusicBrainz** (`ground_tracks.py`) before it ships — a real
   recording by that artist, or it's cut. The sideload download is a *second* truth-check: a track
   that can't be found to download doesn't make it either. The model proposes; the graph and the
   download dispose.
2. **No cliché.** Deep-by-default, hard. The obvious hit is the exception that must earn its slot
   (same discipline as `apple-music-playlist` — see memories `feedback_playlists_push_past_canon_no_repeats`,
   `feedback_playlist_taste_no_chiptune_synth_affinity`). Curate like a record-store lifer making a
   mix for someone whose ear you respect.
3. **Quorum, not single-source (Nick's ask, 2026-07-02).** Never land on the first solution or trust
   one source. Cross-reference **multiple independent signals** and prefer what *more than one*
   vouches for. "Which version is the good one" and "is this a genuine deep cut" are decided by
   **agreement across independent crowd-signals** (YouTube reception + RateYourMusic + Last.fm
   playcounts + critical writing), not one. Curation doesn't one-shot: generate more than one
   candidate direction and let the critic pass pick/merge (a judge-panel, not a first draft).
4. **Curate TRACKS around a felt quality — NOT artists (Nick's correction, 2026-07-02).** The failure
   mode to refuse: *artist-recommendation → grab their tracks → "band hits."* That algorithm sucks
   and it's exactly the mundane Nick escapes. **The unit of curation is the track (and its specific
   version); the through-line is a *feeling*, and the artist is incidental.** A seed is a **track (+
   version) or a felt/semantic brief**, not an artist. `traverse.py` (artist similarity) is a
   **net-widener only** — never the engine. The engine is track-level: `track.getSimilar`
   (co-listening, but popularity-biased) + **audio-DNA** (the popularity-INDEPENDENT, version-specific
   sonic match — the piece that kills the hits-bias; treat as CENTRAL, not optional) + Sylvia's
   aesthetic judgment of the brief. Popularity-biased signals (top-tracks, co-listen, tags) always
   drift to hits — audio-DNA + the brief are the counterweights.
5. **PULL is the metric; his idols are the compass, mainstream pop is the floor (Nick, 2026-07-02).**
   The test of a playlist is not "is it a correct exemplar" — it's **"does it PULL Nick to hit play,
   and to come back for the next one."** A playlist that doesn't pull is why he stopped listening.
   Three rules fall out:
   - **Hard reject — mainstream pop cliché** (Katy Perry / Taylor Swift / the Top-40 lane): NEVER
     serve it unless it is the *only* way to teach a specific, important point. Same category of
     aesthetic reject as chiptune.
   - **His idols are the COMPASS, not a stale-list to subtract.** His Apple Music library
     (~2958 tracks; read via `osascript` — top play counts = Shakey Graves, Mac Miller, Sublime, NOFX,
     Ben Harper, Groundation, Bob Marley, Rancid, Nine Inch Nails — a reggae/punk/folk/hip-hop core)
     is the *taste center of gravity to curate toward*. Do NOT avoid what he loves; curate **new
     music in its spirit.** (The library is a map, not the territory — a strong proxy, not gospel.)
   - **Pull = fresh discovery, even for basic concepts.** Concepts (triads, major progressions) are
     *abundant* — every song has them — so never spend a slot on the tired canonical exemplar
     ("Let It Be" — which he *loves* but which doesn't pull him into a *new* playlist). Pick something
     awesome he hasn't heard that teaches it just as well. New-to-him in his idols' spirit = the pull.

## Why the graph, not the model's memory (the architecture)

Music metadata is **low-volatility and open** — you mirror it once, it's good for years, and the
*value is the network* (artists ↔ works ↔ recordings ↔ versions ↔ covers ↔ labels). Three layers:

- **The graph — MusicBrainz (spine, live now) + Discogs (release/version/label depth, esp. dub — Phase 2) + Last.fm/ListenBrainz (the "listeners also loved" similarity graph — Phase 2).** Free, keyless-or-cheap, mirror-able. This is the anti-hallucination spine and the "traverse *away* from the cliché" engine. MusicBrainz's *work↔recording* relationships explicitly model **live / acoustic / session / cover / instrumental** versions — so "does the stripped Spotify-session version exist" is a query, not a guess.
- **Audio-DNA (BPM/key/energy/acousticness).** Spotify's audio-features/analysis API was **deprecated Nov 2024 and has no replacement (still 403 for new apps in 2026)** — don't depend on it. Apple deliberately never exposed one. **Plan: compute features locally with essentia/librosa on the `.m4a` we already download when we sideload** (Phase 2). We generate the DNA ourselves; we don't rent it.
- **Taste / "which version is the *good* one."** The one genuine research problem (the Song-for-Zula case: MusicBrainz shows the acoustic *exists*; it can't say it's *better*). That verdict lives in crowd signal — YouTube views/comments, RateYourMusic, Last.fm playcounts, Reddit, critical writing — and is synthesized by **grounded LLM research, always cross-checked against the graph** so it can't invent a track. Phase 2.

**Apple's role:** a delivery endpoint + an editorial voice — *not* the knowledge graph. Don't look to Apple for the network.

## The quality rubric (aim, then critique against it)

Every research playlist is scored — by a critic pass (below) — on six dimensions:
1. **Theme-fit** — each track demonstrably serves the request.
2. **Depth / anti-cliché** — deep cuts and the scene *around* the obvious name dominate; a famous
   track is the exception that must earn its slot.
3. **Arc** — intentional ordering (energy/mood/complexity curve), not shuffle.
4. **Taste-fit** — inside Nick's loves, clear of his no-gos (chiptune); for kids, age-open + orthogonal.
5. **Freshness** — no recycling of recent same-context playlists (the `--recent` ledger still applies).
6. **Coherence** — plays like a mix a person who loves music made, not a query result.

## Precedence — settles every famous-track conflict (the RHCP rule, 2026-07-03)

Nick's test case: he grew up loving Red Hot Chili Peppers — not all their stuff. Does the engine
say no to RHCP because they're massively successful? **No. Fame of the artist is NEVER a filter;
familiarity of the specific track is a COST that concept-precision can pay.** Written precedence:

1. **Concept-precision outranks freshness.** A familiar track that *uniquely* nails the concept
   ships — affirmed, not swapped.
2. **At most ONE canonical/hit track per playlist**, and only as the *concept anchor*, affirmed
   with its DNA receipt (its `audio_dna.py` score under the lesson's weight profile). That is the
   "earn its slot" test — audible signature, not vibes.
3. **The exclusion unit is the WORN TRACK, never the artist.** Worn = in the `--recent` ban-list,
   or head-tier over-familiar without a DNA case. No artist-level bans exist anywhere in this
   pipeline: `--novelty-filter` *demotes* (discovery runs only), `--exclude-library` is reserved
   for explicit "only new artists" requests, and compass artists' catalogs compete on DNA like
   everyone else's.
4. **Popularity arbitrates only near-ties** in DNA score. It never pre-cuts the pool. And the
   tiebreak direction is: **in a near-tie the less-worn track wins** (deep-by-default); the familiar
   track only takes a near-tie when it's claiming the single rule-2 anchor slot.

## The workflow (v1 — tool-chained; the tools are mandatory, not decorative)

Interpreters: `audio_dna.py` MUST run under `~/venv/musicdna/bin/python` (numpy/librosa; 3.12 for
numba). Everything else is stdlib — `~/venv/default/bin/python` or any python works.

1. **Read the request + taste context.** Absorb `music/listening.md` (what Nick studies), his loves
   (dark/cinematic synth, acid, dub, reggae) and no-gos (chiptune/8-bit). For a kids' request, read
   `project_playlists_kid_exposure_and_listen_discipline` and aim for *orthogonal growth* (Kids' mode below).
2. **Pull the ban-lists BEFORE curating:**
   ```bash
   ~/venv/default/bin/python .../apple-music-playlist/scripts/create_playlist.py --recent <Domain>
   ```
   `ban_list` = hard no-repeat (exact tracks). `overexposed_artists` = soft signal: those artists
   must earn their next slot on concept-fit.
3. **Traverse — map the neighborhood (multi-hop, persistent, 3-source quorum):**
   ```bash
   ~/venv/default/bin/python .../research-playlist/scripts/graph.py \
     --seed "<artist>" [--seed "<artist2>"] --hops 2 [--novelty-filter]
   ```
   ListenBrainz + Last.fm + Discogs label-adjacency vote; quorum-3 is the strongest signal. The
   graph accumulates in `musicgraph.db` (expansions refresh after 120 days — `--max-age-days` to
   force sooner). Fish `deep_zone: true` candidates; `--novelty-filter` only for taste-discovery
   runs, NEVER for lesson/concept pools (precedence rule 3). Served artists auto-demote via the
   ledger. (`traverse.py` is the superseded one-hop tool; use `graph.py`.)
4. **Build the track pool — all tiers, plus the popularity-blind feeder:**
   ```bash
   ~/venv/default/bin/python .../research-playlist/scripts/track_pool.py \
     --artist "<a1>" --artist "<a2>" [--pages 2] [--mb-recordings "<a1>" --persist]
   ```
   Use the `all` list (head/body/deep/obscure tagged) as the DNA candidate pool — head is a
   familiarity cost, not a cut. `--mb-recordings` enumerates the artist's full MusicBrainz catalog
   so zero-scrobble B-sides can enter the pool at all.
5. **Rank by concept — audio-DNA is the selector, not a decoration:**
   ```bash
   ~/venv/musicdna/bin/python .../research-playlist/scripts/audio_dna.py \
     --rank --weights <profile> [--target "Artist :: Title"] --candidates /tmp/pool.json
   ```
   Download-on-demand fills unscored candidates by default (`.dna-cache/`). If
   `ranking_valid_for_curation` is false (>20% unresolved), the ranking is NOT a curation verdict —
   fix resolution first. Curate the arc FROM this ranking + the brief; check each pick's `values` /
   `wrong_direction` against the concept's audible signature.
6. **Ground every candidate** (kills hallucinations, discovers versions):
   ```bash
   ~/venv/default/bin/python \
     .../apple-music-playlist/scripts/ground_tracks.py --input /tmp/lesson_tracks.json
   ```
   Cut anything `exists: false` — but a cut track that came from the MB-recordings feeder or has a
   Discogs release is real; existence-cut only on NO source vouching. Where `has_alt_versions` is
   true and a version serves the intent better (a stripped session, a dub, a live take — the
   Song-for-Zula move), **choose it deliberately** and carry its exact version title forward.
7. **Critic pass — affirm-or-swap, with receipts (do NOT skip).** The critic scores against the six
   rubric dimensions and for each flagged track must either (a) name the deeper cut from the ranked
   pool that replaces it, or (b) **explicitly affirm it** — a famous track affirmed as the concept
   anchor cites its DNA score (precedence rule 2). Apply the *accepted* swaps. Record the critic's
   verdict (swaps + affirmations) in the listening.md log line — an unlogged critic pass didn't happen.
8. **Deliver via sideload + verify** (identical to `apple-music-playlist` Steps 4–6): create the
   playlist / update the ledger (`create_playlist.py`), fill gaps + alt-versions from YouTube
   (`sideload_tracks.py`), then **verify on-device count == curated count** via `osascript`.
   ⚠️ **Playlist-surgery hazard (2026-07-02 incident):** AppleScript-deleting SUBSCRIPTION tracks
   from a user playlist can remove them from the LIBRARY (play history lost), and concurrent
   mutations can drop untouched kept tracks via cloud-sync races. Local-file (sideloaded) tracks
   are safe to remove surgically. For a redo: check `cloud status` before deleting, disclose
   library-destructive removals, and after the batch re-verify BOTH the playlist contents AND that
   every kept track still exists in the library. See memory
   `reference_music_app_playlist_surgery_hazard`.
9. **Post-delivery concept check.** Run `audio_dna.py --rank` over the DELIVERED files (they're on
   disk from the sideload) against the same profile; eyeball each track's `values` beside the
   concept's signature. This closes the loop SPEC §7 asks for — count-verify proves delivery,
   this proves the playlist nails the concept.
10. **Log + present.** Append a line to `music/listening.md`'s Playlist log (research-playlist,
   alt-versions chosen, critic verdict). Present the URL with a one-line "listen for…".

Track JSON schema and playlist-name rules are shared with `apple-music-playlist` (`🎧 {Place} {NN}:
{Title}` is for *lesson* playlists; a free-standing research playlist can use a plain descriptive
title with the 🎧 prefix, e.g. `🎧 Deep: The Bristol Sound` or `🎧 Kids: Rhythms of the World`).

## The taste loop — debrief favorites are engine input (2026-07-03)

Nick's retro/debrief on any lesson may include a plain **"I listened — loved these, skipped
these."** That's the whole protocol (his idea; keep it exactly this light — never homework, never
ratings). Whenever he names favorites or skips, INGEST THEM:

```bash
~/venv/default/bin/python .../research-playlist/scripts/graph.py \
  --love "Scientist :: Your Teeth in My Neck" --skip-track "Artist :: Title" \
  --context "Office 06"
```

What the ledger does downstream (all automatic or one flag away):
- **Loves become traversal seeds.** Seed the next discovery run from recent loves, not only the
  historical idols — the frontier moves with his taste (the deepest anti-stagnation force).
  Loved artists also get a modest transparent lift (×1.25, `loved_artist: true`) in ranking.
- **Loves become DNA reference targets.** A loved track that matches a future concept is the
  `--target` ("find more that FEELS like this") — the Song-for-Zula move, grounded in his ear.
- **Skips correct the profiles.** A skip on a track the engine ranked highly is a profile error
  signal — check which features misled and adjust the concept weights next time.
- `graph.py --taste` prints the ledger (loves show how many DNA versions are cached).

## Kids' mode — orthogonal growth as graph traversal

"Grow the kids' taste *orthogonally* to mine" is a **graph-traversal problem**, which is exactly why
the network matters: walk the similarity graph *away* from the family's listening center into
adjacent-but-new territory, or build **developmental arcs** for a young ear (rhythm → melody →
texture → arrangement; or one instrument / one region / one decade at a time). Not "dad's records
at them" — deliberately new, age-open, and *earned* from the graph, not from cliché. A kids'
playlist still grounds + sideloads + verifies like any other; only the curation lens changes.

## Named-listener briefs — playlists for anyone (2026-07-03)

Kids' mode generalizes: Nick can hand a **rich taste brief for any named listener** — "my wife
likes …, make her a playlist called 'wife happy'" — and the engine runs the same pipeline with
three substitutions:
- **The brief replaces Nick's compass.** The listener's described taste is the center of gravity;
  Nick's idols/library/taste-ledger inform nothing unless the brief says "stuff we both love."
  Seed traversal from the brief's exemplars; the anti-cliché dial stays on unless the brief asks
  for comfort food (a gift playlist may WANT some warm familiarity — read the brief's intent).
- **Novelty filtering is against the LISTENER, not Nick's library** — usually just off, since we
  can't read her library; the brief's "she already loves X" lines are the manual stale-list.
- **Feedback is context-tagged so it never blurs Nick's taste model:** log her verdicts with
  `graph.py --love "…" --context "wife"` — the taste ledger keys on context, so wife-loves can
  seed HER next playlist without tilting his.
Naming: freestanding form — `🎧 Wife Happy` (🎧 prefix, no Place/NN — that's for lesson playlists).
Ground + sideload + verify exactly as always; log to listening.md noting the listener.

## Roadmap (v1 as of 2026-07-03)

- **Built:** MusicBrainz grounding + version discovery (`ground_tracks.py`); **the accumulating
  SQLite music-graph + multi-hop traversal (`graph.py`, `musicgraph.db`)** — write-through,
  read-first with 120-day expansion refresh, walk-scoped ranking, served-artist demotion,
  novelty-DEMOTE (never artist bans); **playcount-tiered track pools with artist-relative floor +
  the popularity-blind MusicBrainz recordings feeder (`track_pool.py`)**; **audio-DNA
  (`audio_dna.py`, `~/venv/musicdna`)** — AcousticBrainz fast-path + librosa workhorse,
  version-keyed cache, download-on-demand, per-method normalization, concept weight-profiles
  (brightness-fm, groove-16th, sparse-intimate, open-harmony, one-drop, dub-riddim); Discogs
  styles/versions (`discogs.py`); sideload delivery + on-device verify (`sideload_tracks.py`);
  two-pass delivery; rubric + affirm-or-swap critic; artist-frequency soft-ban
  (`create_playlist.py --recent`).
- **Quorum status:** existence + version-depth + style: **two sources** (MusicBrainz + Discogs).
  Discovery similarity: **three sources** (ListenBrainz + Last.fm + Discogs label-adjacency in
  `graph.py`; quorum-3 queryable via `stats.edges_quorum3`). **Discogs caveat:** plain artist-name
  search conflates same-named artists (dub Scientist vs a metal Scientist) — the quorum requirement
  filters most of it; disambiguate via MB artist id when it bites. **Version-quality quorum** (which
  cut is beloved): grounded research across YouTube + RYM + Last.fm playcounts + critical writing —
  no key, do it in the research pass.
- **Next:** register `/research-playlist` as an invocable slash command via `sync-skills` ·
  Discogs release-tracklist fetch (per-release track enumeration — deepens the popularity-blind
  feeder) · track-level novelty (is this *track* in his library, vs artist-level) · new-release
  awareness (MB release feed for followed artists).
- **Keys:** Discogs personal token — DONE. Last.fm API key — DONE (both in gitignored
  `credentials.json`).
