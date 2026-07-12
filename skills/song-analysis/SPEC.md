# SPEC — song-analysis (the practice-artifact grader)

> **STATUS: DESIGN — 2026-07-10.** Written at the end of a design session with Nick so a future
> build session can construct this without re-deriving anything. Research inputs:
> 1. music-07 Gemini DR (assessment science, groove quantification, feedback pedagogy) —
>    **INGESTED 2026-07-10**, numbers folded into §4/§5/§6; final pair at `research/prompts/music/`.
>    Load-bearing figures (tolerance windows, JND asymmetry, guidance-hypothesis feedback
>    schedules, variance-as-skill-signal) cross-check against the known literature; the
>    BKT/MPKT/SingPAD specifics were not independently verified (non-load-bearing — v2 idea only).
> 2. Tool-verification report — **DONE 2026-07-10**, folded into §4.5 and reflected in §1/§3.

---

## 0. Orientation — what this is and why

**Project:** `~/Documents/sandbox/music/` — Nick's four-track practice umbrella
(gym / field / Stage / office). Read `music/CLAUDE.md` and `music/SOUL.md` first, always.

**The moment that created this:** field lesson 10 (`field/lessons/10-ear-leg-dub-bassline.md`)
— the first ear-leg. Its output is a bounced dub groove with *fully specified* targets: A minor,
~70 BPM, bass notes A→C→E→A on beats 1/3/1/3 ("let them ring"), one-drop drums (beat 1 empty,
kick+snare on 3), 16 bars, two tracks. Nick realized: **the artifact is analyzable, and the
lesson is already the spec.** No artifacts exist yet — capture is part of what this spec designs.

**The double duty (Nick's framing, load-bearing):** every analysis is read at two moments by
two postures —
1. **At debrief** — feedback *to Nick*, woven into Sylvia's coach prose (no charts, no report
   file — his explicit choice).
2. **At next-lesson generation** — input *to Sylvia*. The longitudinal ledger (§6) sits beside
   `JOURNAL.md`: the journal says what Nick *felt*, the ledger says what the tape *shows*. The
   next lesson's constraint rotation is picked against both. This is the "next-lesson design
   guardrails" payoff.
   **Cross-track (Nick, 2026-07-10):** the ledger measures the *musician*, not the track.
   Metrics are keyed by skill dimension (timing variance, pitch accuracy, dynamics control…)
   with track/lesson as provenance, and Sylvia reads it in **every mode** at lesson-generation
   time — a timing-stability trend observed in field artifacts legitimately shapes a gym,
   office, or voice lesson. This is shared observational state (like memories), NOT a
   coordination layer: no track gates, blocks, or routes work to another (coupling stays
   forbidden per `projects/CLAUDE.md`). Voice remains excluded as an analysis *subject*; its
   lesson design may still read the ledger — gently, the no-push rule holds.

**The core design insight:** this is a **grader that reads the lesson, not a generic analyzer.**
Generic MIR ("this is 71 BPM in A minor") is useless. Lesson-aware analysis ("your E landed
~40ms early on every pass; your notes rang 1.8 beats instead of hanging into the next; beat 1
stayed genuinely empty — the one-drop held") is coaching material.

**Pattern:** the established cowork pattern — deterministic Python emits JSON receipts, Sylvia
interprets with judgment. Same shape as `/music-status`, `/money`, and the playlist engine.

**What already exists (don't rebuild):**
- `~/venv/musicdna` — librosa 0.11 / soundfile / numpy (uv-managed). Extend it or add a slot
  per the `projects/CLAUDE.md` venv convention (**say so out loud before creating**).
- `backstairs/research-playlist/` — `audio_dna.py` + `musicgraph.db`: precedent for cached
  feature extraction into a gitignored SQLite in the skill dir.
- `recording-watcher` skill — proven watched-folder → transcribe → classify → dispatch pattern,
  if capture ever wants to go automatic. v1 does NOT need it.
- Hardware: Mac Studio M4 Max, 36 GB — everything runs local, including neural models.

**v1 scope (Nick's choice):** **field-first, engine track-agnostic.** Prove the loop on field
artifacts (lesson 10's groove is the ideal first test case); structure targets and profiles so
gym A/Bs and office `ma` plug in later without rework (§8).

---

## 1. The loop (product design)

```
lesson written ──► Nick practices ──► bounce to album ──► OFFLOAD (new gesture)
                                                              │
        ~/Library/Mobile Documents/com~apple~CloudDocs/practice-artifacts/<track>/<name>.wav
                                                              │
debrief: "I recorded an artifact from this lesson: field-lesson-10.wav"
                                                              │
                    skill fires: extract ──► grade vs lesson targets ──► append ledger
                                                              │
             Sylvia reads Nick's retro FIRST, then the receipts ──► coach prose in the debrief
                                                              │
             …later: "give me my next lesson" ──► Sylvia reads JOURNAL.md + ledger trends
```

**Capture home (Nick's choice):** iCloud, like tts output —
`~/Library/Mobile Documents/com~apple~CloudDocs/practice-artifacts/<track>/`. Phone-visible,
drop-from-anywhere, outside the vault (no Obsidian Sync weight). Naming convention:
`<track>-lesson-NN[-<take>].wav` (e.g. `field-lesson-10.wav`, `field-lesson-10-take2.wav`).

**Capture becomes part of the field finish line.** The lesson's "bounce to album" gesture grows
a sibling step: offload the file. **Verified (§4.5 Q1):** the OP-1 Field exposes the four tape
tracks as separate stereo WAV files *and* the album sides — but **over MTP only** (plain disk
mode shows just synth/drum folders). On macOS that means TE's **Field Kit** utility (or an MTP
client) — a one-time setup step for Nick. The offload gesture grabs *both* the album bounce
(the master — the only file carrying mix/EQ/master-FX) and the `tape/` tracks (**true stems —
no neural separation needed for field artifacts**, a massive accuracy and simplicity win; note
per-track files carry no mix FX). One landmine: Field tape WAVs are **44.1 kHz 32-bit *integer*
PCM**, which trips several toolchains — ingest must convert (e.g. `ffmpeg -c:a pcm_s24le`)
before analysis. Exact filenames unverified — glob, don't hardcode, and confirm on-device once.
Field lessons from v1 onward should name the offload step explicitly, in lesson voice, ~one
sentence.

**Trigger:** Nick names an artifact during a debrief (or asks "analyze field-lesson-10.wav").
No cron, no watcher in v1. SKILL.md description should catch natural phrasings: "I recorded an
artifact", "analyze the bounce", "here's the wav from lesson NN".

---

## 2. Lesson targets — the lesson is the spec

**Going forward:** when Sylvia writes a lesson on an analyzable track, she ALSO emits a
machine-readable target block — a fenced YAML block at the bottom of the lesson file (coach-
facing, like the retro template; Nick can ignore it). Fields:

```yaml
# targets (coach-facing — read by song-analysis)
key: A minor
tempo_bpm: 70          # with tolerance, e.g. ±8%
form_bars: 16
stems:
  bass:
    notes:              # pitch, beat position (bar.beat), expected min duration in beats
      - {pitch: A2, at: 1.1, ring: 2}
      - {pitch: C3, at: 1.3, ring: 2}
      - {pitch: E3, at: 2.1, ring: 2}
      - {pitch: A2, at: 2.3, ring: 2}
    loop_bars: 2
  drums:
    grid: {kick: [3], snare: [3], hat: offbeats-optional}
    empty_beats: [1]    # the one-drop — absence is a target too
graded_dimensions:      # ONLY these get graded, each with weight + tolerance
  - {dim: pitch_accuracy, weight: high}
  - {dim: note_duration, weight: high, note: "the ring IS the lesson"}
  - {dim: space, weight: high, note: "beat 1 empty; no third voice"}
  - {dim: timing_precision, weight: low, note: "dub lives a hair off the beat — feel, not grid"}
ungraded: [timing_micro_offset_direction]   # measured + logged, never fed back as error
```

**The `graded_dimensions` block is the pedagogical firewall.** Lesson 10 says "match the feel,
not perfection" — so timing precision is measured loosely and duration/space heavily. An office
`ma` lesson inverts the weights. The grader never scores a dimension the lesson didn't name.

**Back-catalog / target-less artifacts:** Sylvia derives the target block on demand from the
lesson text at analysis time (she wrote the lesson; the extraction is reliable). Free-play
artifacts with no lesson get descriptive analysis only — never graded.

---

## 3. Extraction pipeline (deterministic, local, cached)

Stages (each emits JSON, cached keyed by file hash — never recomputed):

1. **Ingest/normalize** — accept wav/m4a/aif; **convert OP-1F 32-bit integer PCM to 24-bit on
   ingest** (`ffmpeg -c:a pcm_s24le` or soundfile); loudness measurement (LUFS + RMS
   time-series); duration sanity.
2. **Stems** — fast path: OP-1F true tape-track stems offloaded alongside the master (§1).
   Fallback for single-file artifacts and future non-field tracks: `audio-separator`
   (RoFormer-class models, MPS-accelerated — §4.5 Q2). **Defer installing until actually
   needed** — v1 field artifacts shouldn't require it.
3. **Beat grid** — `beat-this` (CPJKU, ISMIR 2024, on PyPI — beats + downbeats, CPU is fine at
   lesson lengths); fallback `librosa.beat.beat_track` **with the target tempo as prior**
   (`start_bpm` from the lesson) — sparse 70 BPM dub octave-fools untuned trackers, and we
   always know the intended tempo. Skip madmom entirely (unmaintained, §4.5 Q4).
4. **Note events per pitched stem** — monophonic lines (most OP-1 lesson material): **penn** (or
   torchcrepe) f0 + crepe-notes-style segmentation → (pitch, onset, duration). Polyphonic
   passes: **basic-pitch** (CoreML backend on macOS) — needs a **Python 3.11** venv (§4.5 Q3).
5. **Drum events** — **band-split heuristics first** (librosa onset_detect on the drum stem;
   classify by band energy: kick <150 Hz, snare 150 Hz–2 kHz broadband, hats >5 kHz + centroid).
   Deterministic, zero model weights, sufficient for sparse known-pattern dub. ADTOF-pytorch in
   reserve if hat/snare confusion appears on real artifacts (§4.5 Q5).
6. **Dynamics/timbre descriptors** — per-stem RMS envelope, spectral centroid series (reuses
   audio_dna feature code where sensible).

**Venvs (two slots, announce before creating per the projects convention):** extend
`~/venv/musicdna` (py3.14, librosa already there) with penn/beat-this/soxr for the main
pipeline; a **py3.11 slot only if/when basic-pitch's polyphonic pass is actually needed**
(basic-pitch caps at py3.11 — documented compatibility constraint, which is the named-slot
justification the convention requires). v1 monophonic grading may never need the second slot.

---

## 4. The grader

Deterministic comparison of extracted events vs the target block:

- **Alignment:** DTW over note-event sequences (pitch+time), so a dropped or extra note doesn't
  cascade misalignment. Per-note verdicts: matched / wrong-pitch / missing / extra.
- **Timing:** signed onset deviation per matched note relative to the beat grid — **mean =
  feel (ahead/behind), variance = stability.** Report both; they mean different things. Tempo
  drift curve across the take.
- **Duration:** played duration vs `ring:` target (lesson 10's "toll, don't play" is literally
  this ratio).
- **Space/absence:** energy in beats the target declares empty; count of voices vs allowed
  tracks (lesson 10: "add nothing" is a graded constraint).
- **Structure:** section boundaries vs the arrangement table (novelty-based segmentation),
  loop-length verification.
- **Dynamics:** range and envelope vs the lesson's intent where named.

Output: one `analysis.json` per artifact (receipts, stored beside the ledger), including the
ungraded-but-logged measurements. **Numbers are receipts, never the deliverable.**

**Tolerance windows (music-07, ingested 2026-07-10):**
- Beginner "on the note" ≈ **±50–100 ms** (Melodics-class practice apps), scaled by tempo and
  lesson difficulty.
- Windows are **asymmetric**: listeners are sharply sensitive to *early* notes, tolerant of
  *late* ones. A bass sitting **+10–40 ms behind** the drums' perceived beat is the laid-back
  pocket — stylistic, never an error; beyond **~+80 ms** the compound sound segregates into
  sloppiness. Percussive elements are tighter (±20–40 ms shifts are audible/disruptive).
- Perceived beat ≠ acoustic onset (P-center): sharp sounds (kick, hat) carry narrow beat bins,
  soft/slow-attack sounds (sub bass, pads) wide ones. v1 approximation: asymmetric per-stem
  windows; true P-center estimation is v2 at most.
- **Normalize before judging:** subtract the take's mean offset before computing variance — a
  consistent shifted mean is a *groove*, high variance is a *struggle*; conflating them is the
  classic invalid-feedback failure mode.
- **Confidence gate:** when beat-tracking confidence is low (sparse slow dub is the known
  case), grade relative inter-onset intervals instead of absolute grid positions — never
  report grid errors off a corrupted grid.

### 4.5 Tool verification report (web-verified 2026-07-10)

**Q1 — OP-1 Field file layout.** Four tape tracks ARE separate files, **over MTP only** (disk
mode shows just synth/drum). macOS: TE **Field Kit** or an MTP client. Tape format: 44.1 kHz
**32-bit integer PCM stereo WAV** (not the original OP-1's AIFF; not float — several tools
mis-decode it → convert to 24-bit on ingest). Per-track files carry **no mix/EQ/master-FX** —
the album mixdown (side A/B, 6 min each) is "what Nick actually heard." *Unverified:* exact
filenames (original OP-1 used `tape/track_1.aif`, `album/sideA.aif`) — glob, confirm on-device
once. Sources: teenage.engineering/guides/mtp; op-forums.com/t/22729, /t/24840, /t/22624.

**Q2 — Source separation.** facebookresearch/demucs **archived 2025-01-01**. Current local
route: **`audio-separator`** (pip; wraps UVR model zoo incl. BS/Mel-RoFormer — the SDR leaders —
plus htdemucs_ft; explicit MPS support). MLX-native alternative: `mlx-audio-separator` (~1.85×
faster median on M4). Mostly unnecessary here given Q1 true stems — install only when an
album-side-only or non-field artifact needs it. Sources: github.com/facebookresearch/demucs;
pypi.org/project/audio-separator; github.com/nomadkaraoke/python-audio-separator;
github.com/ssmall256/mlx-audio-separator.

**Q3 — Transcription.** **basic-pitch** semi-abandoned (0.4.0, Aug 2024; **py3.8–3.11 only**;
CoreML backend on macOS) — still the pragmatic polyphonic pick. Monophonic (most lesson
material): **penn** (fast on CPU, 5-cent bins) or torchcrepe, + **crepe-notes** (PyPI) for
f0→note segmentation. Transkun v2 is maintained but piano-trained (wrong prior for OP-1
engines); MT3-class = research-grade installs, skip. SwiftF0 (2025) promising, install story
unverified. Sources: pypi.org/project/basic-pitch; github.com/spotify/basic-pitch issues
#159/#188; github.com/maxrmorrison/torchcrepe; pypi.org/project/crepe-notes;
arxiv.org/html/2508.18440v1.

**Q4 — Beat tracking.** madmom effectively unmaintained (PyPI wheel needs py≤3.9; skip).
**`beat-this`** (CPJKU, ISMIR 2024) is on PyPI: beats + downbeats, `File2Beats` API, madmom-DBN
optional and off by default; CPU fine at lesson lengths (MPS param unverified). librosa
beat_track acceptable **only with the lesson's tempo as prior** — octave-doubles sparse slow dub
otherwise (expert judgment, not benchmarked). Sources: github.com/CPJKU/beat_this (+issue #9);
pypi.org/project/madmom.

**Q5 — Drum classification.** No maintained lightweight pretrained package (ADTLib/OaF-Drums are
TF1-dead). **Band-split heuristics are sufficient** for a clean drum stem with a known sparse
pattern: onset_detect + band-energy classification (kick <150 Hz, snare 150 Hz–2 kHz, hats
>5 kHz) + centroid. Reserve: ADTOF-pytorch inference port (install flow unverified — check
github.com/MZehren/ADTOF). Source: arxiv.org/html/2509.24853v1 (2025 SOTA recipe = stem
separation → CRNN — overkill here).

**Q6 — Prior art.** **MusicCritic** (MTG-UPF) is exactly this shape but closed SaaS. Read before
building the grader: **Lerch et al., Music Performance Analysis survey** (ISMIR 2019 +
TISMIR 10.5334/tismir.53) for the assessment-parameter taxonomy; **LadderSym**
(arxiv.org/pdf/2510.08580, 2025) — practice *error detection* via align-then-diff, the closest
published analog to §4; **MAST** datasets (github.com/barisbozkurt/MASTmelody_dataset) for
pitch/rhythm grading style. Melodics scores via **MIDI, not audio** — an argument for keeping
audio grading target-informed and simple. No public Yousician audio-engine write-ups found.

**Cross-cutting:** the 32-bit-PCM landmine (Q1) is the one ingest gotcha; python-version split
(basic-pitch 3.11 vs everything-else 3.12+) is why the venv plan in §3 defers the second slot.

---

## 5. Longitudinal ledger — where deficit-identification lives

`backstairs/song-analysis/practice.db` (SQLite, **gitignored**, sibling precedent:
`musicgraph.db`).

```
artifacts(id, track, lesson, take, path, recorded_at, analyzed_at, target_source)
metrics(artifact_id, stem, dimension, value REAL, detail TEXT(json))
observations(artifact_id, author TEXT['sylvia'], note TEXT, created_at)  -- coach notes worth keeping
```

One artifact describes one night. Twenty artifacts describe *Nick*: "timing variance on bass
notes has halved since lesson 10", "he consistently lands ahead of the beat under tension",
"dynamics range widens when the lesson names it, collapses when it doesn't." Trend queries are
the input to next-lesson design (§0 double duty — read by ALL Sylvia modes, dimension-keyed).

**Trend metrics (music-07):** **variance is the skill signal.** Timing-variance reduction
(after mean-offset normalization) is the most robust objective marker of motor consolidation —
and it's precisely the thing self-report can't perceive, i.e. the ledger's unique contribution
over the journal. Skill follows an ordered progression: stability first, expression later —
once a dimension's variance stabilizes (literature landmark for timing: onset SD < ~15 ms),
unlock *expression* metrics so deliberate swing/rubato is rewarded, not flagged. v2 idea, not
v1: concept-keyed mastery probabilities (Bayesian Knowledge Tracing / MPKT-style adaptive
sequencing); rolling per-dimension stats are enough until the ledger is deep.

---

## 6. Sylvia integration — the feedback constitution

These are constitution, not implementation detail:

1. **Retro first, always.** Sylvia reads Nick's subjective retro *before* the receipts, and the
   debrief conversation happens in that order too — self-assessment before objective data is
   empirically supported (improves retention and internal error-detection; music-07 §5).
2. **The retro stays primary.** Analysis is a second opinion that sharpens the debrief, never
   a grade that replaces it. If receipts and retro disagree, that disagreement is the
   interesting finding — name it gently.
3. **PB&J applies to feedback.** Max one or two focal observations per debrief, chosen for the
   next lesson's leverage. The rest goes to the ledger silently.
4. **Grade only what the lesson names as the point.** The `graded_dimensions` firewall (§2). A
   system that dings a dub lesson for loose timing is worse than no system.
5. **Per-track posture.** Field: warm, feel-first (this spec's v1). Office `ma`/`ml`: lean in
   with hard numbers — that track wants them (memory `feedback_office_build_to_hard`). Voice
   (`vx`): **out of scope entirely** — the recording gate and no-push rule
   (memory `feedback_voice_recording_gate_no_l6max_yet`) exclude it until Nick reopens that door.
6. **Never homework-ify.** No score displayed as a score, no streaks, no red marks. Findings
   arrive as coach observations in Sylvia's voice. (music-07 §6 confirms: gamified per-note
   feedback shifts the goal from "making music" to "satisfying the algorithm.")
7. **Silence is feedback (bandwidth rule).** Within tolerance → no corrective commentary at
   all; the guidance hypothesis shows dense external feedback breeds dependence and degrades
   retention. Speak about the *playing*, not the score (knowledge-of-performance over
   knowledge-of-results), and frame success-forward — error-focused framing predicts
   adult-hobby dropout (music-07 §5).

**Wiring (build session):** `field/CLAUDE.md` gets two short additions — (a) in the
retrospective flow: "if Nick names a recorded artifact, run song-analysis before responding to
the retro"; (b) in lesson generation: "read the practice ledger's trend view alongside
JOURNAL.md"; plus the target-block emission rule in the lesson format. Keep each addition to a
few lines; this SPEC holds the detail.

---

## 7. What v1 is NOT

- No watcher/cron ingestion (recording-watcher pattern exists if wanted later).
- No visual reports, charts, or printables (Nick chose coach prose only).
- No reference-track comparison for covers (natural v2: same engine, target = the original
  song's extracted events — pairs with cover skills and audio-DNA).
- No voice-lane analysis (gated, see §6.5).
- No coordination layer between tracks (forbidden — `projects/CLAUDE.md`).

## 8. Later track profiles (design now, build later)

- **Office `ma` (finger drumming):** the highest-value hard-numbers case — micro-timing per
  beat position against a click, subdivision evenness, limb independence proxies. Daily
  cadence = fastest-accumulating ledger. Likely v2.
- **Gym A/Bs:** a different question — not "did you play it right" but "did the variable change
  what you think it changed": spectral comparison of take A vs take B (centroid, envelope,
  harmonic content). Reuses audio-DNA feature code directly.
- **Stage:** performance-oriented; probably descriptive only (energy arc, dub-throw detection)
  — retros are optional there, keep analysis optional too.

## 9. Definition of done (build session)

1. Drop zone exists; lesson 10 (or the next field lesson) performed, bounced, offloaded —
   **first real artifact.**
2. Extraction pipeline runs on it end-to-end locally; `analysis.json` receipts cached.
3. Target block derived from lesson 10's text; grader emits per-note verdicts + the four
   graded dimensions.
4. Ledger row written; a trend query returns sane output (even with n=1).
5. Sylvia debrief on the real artifact: retro first, ≤2 focal observations, field posture.
6. SKILL.md written (status: active), `field/CLAUDE.md` wired (§6), memory appended,
   `/skills-status` clean.
7. Both research inputs (music-07 response + tool report) ingested and their deltas applied
   to tolerances, trend metrics, and tool choices.

## 10. Open questions (carry into the build)

- Confirm exact OP-1F tape/album filenames on-device (5-minute check; ingest globs regardless),
  and get Field Kit (or an MTP client) installed + the offload gesture actually walked once.
- When to unlock expression metrics per dimension (the SD < ~15 ms landmark covers timing;
  other dimensions need coach judgment as the ledger deepens).
- Whether the target block lives in the lesson file (current design) or a sidecar
  `targets/NN.yaml` — lesson-file-embedded preferred (one artifact, lesson-is-the-spec), revisit
  only if the YAML grows ugly.
