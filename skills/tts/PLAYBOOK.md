---
status: active
priorities: [music]
activity_log: mindmap/build
---

# Creating Podcasts — Working Playbook

A repeatable workflow for turning a written script into a finished two-voice podcast on a Mac Studio (M4 Max, 36 GB). Distilled from the flex internal podcast (3 acts + cold open, ~300 turns rendered Apr 2026).

## What's in this directory

```
podcast/
├── README.md            ← this file
├── renderer/
│   ├── chunker.py       ← Markdown -> turns.json (project-agnostic library)
│   └── render_vibevoice_perturn.py  ← turns.json -> .wav/.mp3
├── examples/            ← template to copy
│   ├── build_turns.py
│   ├── render.sh
│   └── scripts/episode.md
└── mindmap/             ← live project: 'The Page on May 1st' (5 eps)
    ├── README.md
    ├── build_turns.py
    ├── render.sh
    └── scripts/ep1..ep5.md
```

To start a new podcast: copy `examples/` to a new dir, edit `build_turns.py`
(speakers, pronunciation, script paths) and `render.sh` (voices, output path),
then run `./render.sh`.

---

## TL;DR — the stack that works

| Stage          | Tool                                                                  |
|----------------|-----------------------------------------------------------------------|
| Script format  | Markdown with `[HOST]` / `[ARCH]` (or any 2-tag) speaker prefixes     |
| TTS model      | `mlx-community/VibeVoice-Realtime-0.5B-fp16` via `mlx-audio`          |
| Voices         | `en-Mike_man` + `en-Carter_man` (both natural American male)          |
| Render mode    | **Per-turn single-speaker**, NOT multi-speaker                        |
| Stitch         | `ffmpeg concat` with explicit silence WAV between turns               |
| Mastering      | `ffmpeg loudnorm=I=-16:TP=-1.5:LRA=11` (single pass is fine)          |
| Output target  | `~/Library/Mobile Documents/com~apple~CloudDocs/tts/<show>/`          |

Render speed in this mode: ~1.2× realtime on M4 Max 36 GB. A 30-min episode is ~35 min of compute, fully unattended.

---

## 1. Script conventions

Write the script as one Markdown file per act. One speaker tag per turn at the start of a paragraph.

```markdown
[HOST] There's a sentence I keep coming back to.
[ARCH] Beautiful sentence.
[HOST] Right? And it tells you exactly what's broken about
the way we think about correlation today.
```

Rules that prevent grief later:
- **One tag, one paragraph.** Don't put two speakers on a line.
- **Avoid stage directions inside the spoken text.** Bracket directions like `[laughs]`, `[pause]` get stripped by the chunker but the model can hallucinate them as words. Strip them upstream.
- **Keep turns under ~200 words.** Longer turns drift in tone and can get truncated. The chunker auto-splits on sentence boundaries past that limit.
- **Spell out acronyms** the model will mangle: `ARM` → `A R M`, `API` → `A P I`. Build a per-project pronunciation table; apply it after parsing.
- **Markdown headers and `> quotable:` blocks** are fine — they get stripped.

---

## 2. Why per-turn instead of multi-speaker

VibeVoice (and most current TTS) supports a "multi-speaker" mode where you feed the whole script in one shot. Tested it. It's worse:

- Hand-offs glitch on short turns ("Beautiful sentence." → next speaker arrives before the period decays).
- You lose all control over pacing — the model decides inter-turn timing.
- One bad turn means re-rendering the whole episode.

**Per-turn mode** renders each `(speaker, text)` independently to a WAV, then `ffmpeg concat` stitches with a fixed silence WAV between turns. Costs ~20% in render time. Buys:

1. **Caching.** Re-running skips turns whose WAV already exists. Fix one line, re-render only that turn.
2. **Pacing control.** 400ms between turns is the sweet spot — natural dialog rhythm without dead air. Bump to 600–800ms across act boundaries.
3. **Voice isolation.** No cross-speaker bleed.

---

## 3. Voice selection — what to A/B test

Don't pick voices from the model card. Render the **same 60-second cold open** through every plausible voice combo and listen on the device you actually consume podcasts on (AirPods, car, whatever).

For the flex podcast, tested 5 combos:
- `en-Grace_woman` + `en-Frank_man` — Frank read British, killed it
- `en-Mike_man` + `en-Carter_man` — winner
- `en-Mike_man` + `en-Davis_man` — too similar in timbre
- `en-Mike_man` + `en-Frank_man` — Frank still British
- Orpheus `tara` + `leo` — less natural than VibeVoice for explanatory content

Rule of thumb: pick voices with **distinct timbre but similar register**. If you can't tell speakers apart in the first 5 seconds, the dialog reads as monologue.

**Avoid voice-cloning models** (Higgs Audio v2, anything requiring `ref_audio`). Preset voices are tuned, consistent, and one less variable when something sounds wrong. Prefer Kokoro / VibeVoice / Orpheus.

---

## 4. The chunker

Parses `[SPEAKER]` Markdown into ordered `(speaker, text)` tuples, strips noise, applies pronunciation tweaks, splits long turns. Reference implementation: `/Users/dad/src/viasat/flex/audio_build/chunker.py`.

Key responsibilities:
- Strip `#` headers, `> quotable:` lines, `[laughs]`-style stage directions
- Collapse whitespace
- Split turns over `max_words=200` on sentence boundaries
- Apply project-specific pronunciation regexes
- Emit `<group>.turns.json` — the artifact the renderer consumes

The renderer never reads Markdown directly. The JSON is the contract. This means you can hand-edit `turns.json` to fix one line without re-running the parser.

---

## 5. The renderer

Reference: `/Users/dad/src/viasat/flex/audio_build/render_vibevoice_perturn.py`.

```bash
~/.claude/skills-venv/bin/python render_vibevoice_perturn.py \
    --turns build/episode.turns.json \
    --voice HOST=en-Mike_man \
    --voice GUEST=en-Carter_man \
    --out ~/Library/Mobile\ Documents/com~apple~CloudDocs/<show>/episode.wav \
    --ddpm 80 \
    --cfg 1.5 \
    --gap_ms 400 \
    --mp3
```

`--voice` is repeatable — use one per speaker tag. Tags must match the
`SPEAKERS` tuple in your `build_turns.py`.

Settings worth keeping:
- `ddpm_steps=80` — quality plateau. 40 is rough, 120 is wasted compute.
- `cfg_scale=1.5` — higher gets robotic; lower gets mumbly.
- `gap_ms=400` — see above.
- `max_tokens=2048` — safety ceiling for a single turn.
- `loudnorm I=-16:TP=-1.5:LRA=11` — podcast-standard loudness, leaves headroom.

The renderer writes a `_pre_loudnorm.wav` then loudnorms in place. Keep the per-turn WAVs (`<show>_turns/turn_NNNN_SPEAKER.wav`) — they're the cache that makes iteration cheap.

---

## 6. Iteration loop

1. Listen to the rendered episode end-to-end on your target device.
2. Note timestamps of issues: mispronunciations, weird pacing, model artifacts.
3. For each issue:
   - **Wrong word** → fix the script, re-run chunker, delete the affected `turn_NNNN_*.wav`, re-render (only that turn renders).
   - **Bad delivery** → re-render the same turn (VibeVoice is non-deterministic; another roll often fixes it). Delete the WAV, re-run.
   - **Pacing** → adjust `gap_ms` for the stitch step only; no re-render needed.
4. Repeat until you stop wincing.

The cache makes this loop minutes, not hours. The first full render is the expensive one.

---

## 7. Output and distribution

- **WAV** is the master. Keep it.
- **MP3** (`-qscale:a 2`, ~190 kbps VBR) for actual listening / sharing.
- iCloud Drive (`~/Library/Mobile Documents/com~apple~CloudDocs/`) syncs to iPhone automatically — open in Files app, AirPods, done.
- For internal sharing at work: drop the MP3 in whatever your equivalent of a Slack channel is. Don't upload to public services if the content is internal.

---

## 8. What I'd do differently next time

- **Build the cold-open A/B harness first.** Voice selection is the highest-leverage decision and the cheapest to test. Don't render any acts until voices are locked.
- **Pronunciation table is project-specific and grows over time.** Start it on day one, append every time the model mangles a term.
- **Don't bother with multi-speaker mode.** The 20% time savings isn't worth the loss of control.
- **400ms gap is the default; tune from there.** Don't start at zero and add — start at 400 and trim.

---

## Reference: the original flex implementation

The flex internal podcast — the project this playbook was distilled from — lives at:

- Scripts: `/Users/dad/src/viasat/flex/script/{cold-open-hook,act1,act2,act3}.md`
- Build outputs: `/Users/dad/src/viasat/flex/audio_build/`
- Per-turn caches: `/Users/dad/src/viasat/flex/audio_build/act{1,2,3}_turns/`

The chunker and renderer in `renderer/` here are generalized versions of the
flex originals (project-agnostic speakers, no hardcoded paths or pronunciation
table).
