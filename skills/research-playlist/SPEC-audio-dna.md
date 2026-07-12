# SPEC — Audio-DNA + the accumulating music-graph (build spec for a fresh session)

> **STATUS: BUILT — 2026-07-03.** §5 (`graph.py` + `musicgraph.db`) and §6 (`audio_dna.py` +
> `~/venv/musicdna`) are live, plus a hardening round from the same-day adversarial review
> (expansion TTL, walk-scoped ranking, novelty-DEMOTE not artist-ban, artist-relative track-pool
> floor, MusicBrainz popularity-blind feeder, version-keyed DNA cache, per-method normalization,
> tempo octave-folding, download-on-demand, Discogs as 3rd similarity vote, artist-frequency
> ledger). §7's done-test ran on the dub/riddim concept: "Your Teeth in My Neck" scored 0.25 on
> the dub-riddim profile — best in pool, matching Nick's ear. The executed workflow lives in
> SKILL.md (v1, tool-chained, with the RHCP precedence rule). This file is now lineage.

> **Purpose of this file.** A self-contained work order. It was written 2026-07-02 at the end of a
> long design session so the *next* session can build without re-deriving anything. Read §0 to
> orient, then build §5 (SQLite graph) and §6 (audio-DNA) — in that order. This is high priority to
> Nick ("REALLY important to me").

---

## 0. Orientation — what already exists (don't rebuild it)

**Project:** `~/Documents/sandbox/music/` — Nick's DAWless music-practice umbrella (gym /
field / Stage / office tracks). Playlists are the **listen-first half of every lesson**; when they're
bad, he stops listening and the whole pedagogy leaks. That's what we're fixing.

**Two playlist skills** (both in `~/Documents/sandbox/backstairs/`):
- `apple-music-playlist/` — **lesson-tied**. Builds the playlist for a specific lesson. Also owns the
  shared delivery scripts: `create_playlist.py` (makes the playlist + updates the freshness ledger
  `used_tracks.jsonl` + returns URL), `sideload_tracks.py` (YouTube → tagged `.m4a` → Music.app
  library + playlist; catalog-independent), `ground_tracks.py` (MusicBrainz existence + version
  discovery).
- `research-playlist/` — **standalone, on-demand** (this skill). `scripts/`: `traverse.py` (quorum
  artist-similarity: ListenBrainz + Last.fm), `track_pool.py` (Last.fm playcount-tiered
  "non-standard-but-alive" track pools + `track.getSimilar`), `discogs.py` (styles + version/pressing
  depth + 2nd existence vote). Credentials in **gitignored** `research-playlist/credentials.json`
  (Discogs token + Last.fm api_key present; Nick's Last.fm user `nfbullock` is empty).

**Delivery model (already built + proven):** two-pass — catalog best-effort (`create_playlist.py`)
→ sideload the gaps (`sideload_tracks.py`) → **verify on-device** (`osascript` track count ==
curated count). Never trust `tracks_added`. This exists because the catalog API silently shipped an
empty playlist once.

**Read these memories first** (they encode hard constraints):
`feedback_lesson_playlist_nail_the_concept` (THE north star), `feedback_playlist_pull_idols_compass_no_pop`,
`feedback_playlist_sideload_delivery_catalog_secondary`, `project_research_playlist_skill_graph_grounded`.

**The north star (why this spec exists):** a lesson teaches a *specific* concept/spirit; the playlist
must be **as close as possible to NAILING it** — precise, not vaguely on-genre — *and* pull (fresh,
in his idols' spirit, no cliché/pop). Objective = **concept-precision × pull × freshness**.

**The gaps this spec closes:**
1. Discovery is one hop and re-queries APIs every time → **build the accumulating multi-hop SQLite
   graph** (§5). Nick explicitly asked for iterative multi-hop traversal that *persists* the network.
2. Track selection is popularity-biased (co-listening) and can't match a *sonic concept* → **build
   audio-DNA** (§6), the popularity-independent, version-specific signal that actually nails the
   concept. Nick promoted this from "low-leverage" to top priority.

**His taste compass (from his ~2958-track Apple library, read via `osascript`):** most-played =
Shakey Graves (529), Mac Miller, Slightly Stoopid, NOFX, Bob Marley, Ben Harper, Groundation,
Sublime, Rancid, NIN — reggae/punk/folk/hip-hop core. Curate *toward* these (compass), never
subtract them. Hard-reject mainstream pop (Katy Perry/Taylor Swift) unless teaching something
specific. First engine-made playlist delivered: "🎧 The Next Shakey Graves."

**THE FIRST REAL APPLICATION to build toward (Nick's words, 2026-07-02):** *"I want to create my own
riddims, and I need songs like that."* The sideloaded Scientist "Your Teeth in My Neck" **blew his
mind** — a track he'd been *skipping in Apple Music* until the real thing landed via sideload. So the
priority proof-of-the-finished-engine is a **deep dub/riddim reference pool to fuel his own
riddim-making** (EP-40, gym D3 / Stage). The `King Tubby + Scientist + Augustus Pablo` quorum
traversal is already a strong seed (it surfaced The Upsetters, Prince Jammy, The Aggrovators, Keith
Hudson, The Revolutionaries, Prince Far I, The Congos…). **"If it applies to the riddim it applies to
EVERYTHING"** — the engine is genre-agnostic by design; the riddim is just the proof case that hits
hardest. Make §7's done-test a dub/riddim concept.

---

## 5. Build FIRST — the accumulating SQLite music-graph

**Why first:** audio-DNA features get *stored in it*, and multi-hop traversal *reads from it*. It's
the substrate.

**Location:** `research-playlist/scripts/graph.py` + DB at `research-playlist/musicgraph.db`
(**gitignore it** — add to `research-playlist/.gitignore`).

**Schema (SQLite):**
```
nodes(id INTEGER PK, kind TEXT['artist'|'track'], name TEXT, mbid TEXT, artist TEXT,
      lastfm_playcount INT, discogs_styles TEXT(json), created_at TEXT, UNIQUE(kind,name,artist))
edges(src INTEGER, dst INTEGER, rel TEXT['similar_artist'|'similar_track'|'version_of'|'member_of'],
      source TEXT['listenbrainz'|'lastfm'|'musicbrainz'|'discogs'], weight REAL,
      UNIQUE(src,dst,rel,source))                          -- source column = quorum is queryable
dna(node_id INTEGER PK, features TEXT(json), extracted_at TEXT, method TEXT)   -- §6 writes here
```

**Behavior:**
- **Write-through:** `traverse.py` / `track_pool.py` / `discogs.py` should persist every node + edge
  they fetch (add a `--persist` path or a thin wrapper). An edge carries its `source`, so quorum
  = "≥2 distinct `source` rows for this edge."
- **Read-first:** before hitting an API for a node's neighbors, check the DB; only fetch what's
  missing. The graph gets richer + faster every run.
- **Multi-hop traversal:** `graph.py --seed "X" --hops 3 --novelty-filter` → BFS/weighted expansion
  from seed(s), accumulating the subgraph (fetch-and-persist unknown nodes as it walks), returning
  ranked candidates by (quorum, consensus weight, hop distance). This is the "iterate outward N
  times" Nick described. Rate-limit API fetches (MusicBrainz ~1/s; be polite to Last.fm/ListenBrainz).
- Fold in the existing novelty filter (drop artists already in his Apple library — the 411-artist
  set can be cached as a node attribute or a side table refreshed via `osascript`).

---

## 6. Build SECOND — audio-DNA (the concept-nailer)

### 6.1 What it is
Extract per-track acoustic features so we can match a **sonic concept** by the actual sound —
popularity-independent and **version-specific** (the Zula *acoustic* has different DNA than the
studio cut). This is what turns "a playlist he'd enjoy" into "a playlist that lands the exact thing
a lesson teaches."

### 6.2 Environment (heavy — flag before creating)
Named venv slot per the project convention (venvs live under `~/venv/`, `uv`-managed; **say so out
loud before creating**): create `~/venv/musicdna` and
`uv pip install --python ~/venv/musicdna/bin/python librosa soundfile numpy`. (librosa pulls
numba/scipy — that's why it's its own slot, not `~/venv/default`.) Essentia is optional/heavier;
librosa is enough for v1.

### 6.3 Two sources of DNA (prefer the free lookup before you compute)
1. **AcousticBrainz** — a **frozen but MBID-keyed** precomputed-feature dataset (Essentia low+high
   level: BPM, key/scale, danceability, timbre, etc.). Lets us get DNA **without downloading audio**,
   keyed by the MBID `ground_tracks.py` already resolves. *Verify it's still API-reachable* (frozen
   since ~2022; data historically at `acousticbrainz.org/api/v1/...`). Use it as the fast path.
2. **Local extraction (librosa)** — the fallback for anything not in AcousticBrainz. We already
   download the `.m4a` when we sideload, so extract then; or download-on-demand for candidates being
   ranked. Lossy YouTube audio is fine for a study-window match.

### 6.4 Feature set + what each concept-serves (librosa)
| feature | librosa | serves the concept… |
|---|---|---|
| tempo (BPM) | `beat.beat_track` | rhythmic-feel, tempo-matched ordering |
| key + mode | `feature.chroma_cqt` → Krumhansl-Schmuckler | harmonic concepts, harmonic-mixing order |
| onset density + regularity | `onset.onset_strength/detect` on HPSS-percussive | "even 16th hats," "one-drop," subdivision feel |
| spectral centroid **time-series** | `feature.spectral_centroid` | **brightness** — and its variance vs RMS |
| RMS energy **time-series** | `feature.rms` | dynamics (ghost notes, quiet↔loud); the "flat-loudness" reference for the FM brightness concept |
| chroma / tonnetz | `feature.chroma_cqt`, `feature.tonnetz` | "open fifth/octave," triad/chord-tone content |
| MFCCs (mean+var) | `feature.mfcc` | **timbre fingerprint** → "sounds like THIS version" |
| spectral flatness / ZCR | `feature.spectral_flatness`, `feature.zero_crossing_rate` | acoustic-vs-electronic, percussiveness |
| HPSS ratio | `effects.hpss` | sparse/acoustic-intimate vs dense/produced |

Store a normalized feature vector (json) in `dna.features`.

### 6.5 How it plugs into curation (the actual point)
Given a lesson concept, two ways to get a **target DNA**, then rank candidates by weighted distance:
- **Reference-track mode:** I name a track that nails the concept → compute its DNA → find candidates
  with nearest DNA in the concept-relevant subspace. (This is the Song-for-Zula move: seed = a track
  + version, find tracks that *feel* like it.)
- **Feature-target mode:** I decompose the concept into explicit feature constraints (my semantic
  job) → filter/rank candidates against them.
- **Weighting is per-concept:** for a *brightness* concept, weight `spectral_centroid` variance vs
  `rms` variance heavily; for *harmony*, weight chroma/tonnetz; for *groove*, weight onset
  pattern/tempo. Distance = weighted cosine/Euclidean over the chosen subspace.
- **Ordering bonus:** tempo + key give harmonic-mixing / energy-arc sequencing for free.

### 6.6 Worked concept → DNA mappings (build the tool to express these)
- **"even 16th-note hi-hat that doesn't lurch"** → HPSS-percussive onsets at 16th subdivision with
  **low variance in onset strength** (evenness) and steady tempo.
- **"brightness moves independent of loudness" (FM)** → **high variance in spectral-centroid
  time-series while RMS variance is low** (decorrelated centroid↔energy).
- **"open fifth / two notes that agree"** → chroma energy concentrated on root+fifth, low harmonic
  entropy (sparse).
- **"one-drop feel"** → beat-synchronous onset emphasis on beat 3, sparse beat 1.
- **"the stripped, aching intimacy of the Zula acoustic"** → low RMS, high harmonic/low percussive
  ratio, slow tempo, low spectral flatness (tonal/acoustic), sparse onsets, guitar-ish MFCC profile.

### 6.7 The tool
`research-playlist/scripts/audio_dna.py`:
- `--file X.m4a` → extract + print features json.
- `--mbid <id>` → AcousticBrainz lookup first, else needs `--file`.
- `--rank --target <ref.m4a|features.json> --candidates tracks.json --weights <concept-profile>` →
  rank candidates by distance to target in the weighted subspace.
- Write everything to `dna` table in `musicgraph.db` (keyed by node).
- Provide a few named `--weights` concept-profiles (brightness, groove-16th, sparse-intimate,
  open-harmony) as a starting library; extend per lesson.

### 6.8 Caveats
- Key detection is imperfect (~70-80%); treat as a soft signal, not gospel.
- Lossy rips slightly perturb high-freq features — fine for study-window matching, don't over-trust
  absolute spectral values; rely on *relative* distance.
- Extraction is CPU-seconds per track — cache in the DB (§5) so you never recompute.

---

## 7. Definition of done
- `musicgraph.db` accumulates nodes/edges with `source` (quorum queryable); multi-hop traversal
  reads-first, fetches-and-persists the rest.
- `audio_dna.py` extracts (AcousticBrainz-first, librosa-fallback), caches to the DB, and ranks
  candidates against a concept target with per-concept weighting.
- A test: take a real lesson concept (e.g. gym `024-fm` "brightness independent of loudness" or
  office `06-ma` "even 16th roll"), produce a candidate pool via multi-hop traversal, rank by
  audio-DNA to the concept, ground + sideload + verify, and confirm the tracks *audibly nail it*.
- Update `research-playlist/SKILL.md` roadmap (move these from "next" to "built") and append a memory.
```
```
