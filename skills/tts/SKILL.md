---
name: tts
description: Turn text into audio. Two formats: spoken-word (single voice, audiobook/narration) or dialog (multi-voice, podcast-shaped with [SPEAKER] tags). Uses VibeVoice via mlx-audio with per-turn rendering for cache-friendly iteration. Final audio lands in ~/Library/Mobile Documents/com~apple~CloudDocs/tts/<name>/ so it syncs to Nick's phone; per-turn caches stay in projects/artifacts/.tts/<name>/ (dot-prefixed so Obsidian Sync ignores them). Invoke when Nick asks to TTS something, narrate something, make a podcast, or generate audio of any text.
status: active
---

# tts

Take text → produce audio. Working pipeline. The full producer-grade reference (voice A/B testing, loudnorm settings, pacing rules, why per-turn over multi-speaker) is in `PLAYBOOK.md` — read that before invoking on a new project. This file is the operational shape; the playbook is the why.

## When to invoke

- "TTS this script"
- "Narrate this to audio"
- "Make a podcast from this"
- "Audio version of these notes"
- "Turn this into a spoken-word piece"

Triggered by intent to produce audio output from text. If the intent isn't clear (Nick describing audio, not asking for it), don't fire.

## Two formats

The skill handles two shapes, picked from input:

| Format | Input shape | Voices | Use case |
|---|---|---|---|
| **dialog** | Markdown with `[SPEAKER]` tags (or any 2-tag prefix) | Two distinct voices, e.g. `en-Mike_man` + `en-Carter_man` | Podcast, dialectical conversation, two-host explainer |
| **spoken-word** | Plain markdown / prose | One voice, e.g. `en-Mike_man` | Audiobook, narrated piece, briefing, single-voice playbook reading |

Detect format by scanning input: if `[A-Z]+]` speaker tags appear at line starts, dialog; else spoken-word.

## Pipeline

1. **Read input.** Confirm format.
2. **Pronunciation table.** Ask Nick if there are project-specific terms the model will mangle (acronyms, names). Stage as regex pairs in the build script.
3. **Voices.** For new projects, run the cold-open A/B harness (PLAYBOOK §3) before committing — pick voices with distinct timbre but similar register. For continuations of existing projects, reuse the locked voice block.
4. **Chunk.** `renderer/chunker.py` parses the markdown to `<name>.turns.json`. Strips headers, stage directions, applies pronunciation regexes, splits long turns on sentence boundaries.
5. **Render.** `renderer/render_vibevoice_perturn.py` renders each `(speaker, text)` turn to a WAV, then `ffmpeg concat` stitches with silence between turns. Default `gap_ms=400`.
6. **Master.** `loudnorm I=-16:TP=-1.5:LRA=11` (single pass).
7. **Output.** Render WAV + per-turn cache + build artifacts to local `~/Documents/sandbox/projects/artifacts/.tts/<name>/` so iteration on one bad line is cheap and the master stays accessible. The `.tts` dir is **dot-prefixed on purpose**: it sits inside the Obsidian vault, and Obsidian Sync (like iCloud) ignores dot-folders, so the bulky regeneratable WAVs never travel either sync surface. Then `cp` the final MP3 to `~/Library/Mobile Documents/com~apple~CloudDocs/tts/<name>/<name>.mp3` so it syncs to Nick's phone (AirPods + Files app). **Only the MP3 leaves the local hidden dir** — never point `--out` at iCloud, or the master + cache get dumped where they don't belong.

## Render command

```bash
cd ~/Documents/sandbox/projects/claude_skills/tts
LOCAL="$HOME/Documents/sandbox/projects/artifacts/.tts/<name>"   # dot-prefixed: Obsidian Sync ignores it
ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs/tts/<name>"
mkdir -p "$LOCAL" "$ICLOUD"

~/venv/tts/bin/python renderer/render_vibevoice_perturn.py \
    --turns build/<name>.turns.json \
    --voice HOST=en-Mike_man \
    --voice GUEST=en-Carter_man \
    --out "$LOCAL/<name>.wav" \
    --ddpm 80 \
    --cfg 1.5 \
    --gap_ms 400 \
    --mp3

cp "$LOCAL/<name>.mp3" "$ICLOUD/<name>.mp3"
```

The renderer writes WAV + per-turn cache + build artifacts (`<name>_turns/`, `<name>.concat.txt`, `silence_400ms_24000.wav`) next to `--out`, so pointing `--out` at the local hidden `.tts` dir keeps everything bulky off **both** sync surfaces — Obsidian Sync (the vault) and iCloud. The post-render `cp` puts only the MP3 in iCloud for phone sync. **Never set `--out` to the iCloud path** — that dumps the master and per-turn cache straight into iCloud.

Settings worth keeping (PLAYBOOK §5):
- `ddpm_steps=80` — quality plateau
- `cfg_scale=1.5` — natural; higher gets robotic
- `gap_ms=400` — natural dialog rhythm
- Avoid voice-cloning models — preset voices only

## Iteration

After first render, listen end-to-end on AirPods. For each issue:
- **Wrong word** → fix script, re-run chunker, delete affected `turn_NNNN_*.wav`, re-render (only that turn)
- **Bad delivery** → re-render same turn (model is non-deterministic; another roll often fixes it)
- **Pacing** → adjust `gap_ms` for the stitch step; no re-render needed

The per-turn cache makes this loop minutes, not hours.

## Starting a new project

Copy `examples/` to a working dir, edit `build_turns.py` (speakers, pronunciation, script paths) and `render.sh` (voices, output path under `~/Library/Mobile Documents/com~apple~CloudDocs/tts/<name>/`), then run `./render.sh`.

## Output convention

**Local (the master + everything bulky):** `~/Documents/sandbox/projects/artifacts/.tts/<name>/`
- `<name>.wav` — the loudnormed master (~900 MB for a 35-min chapter)
- `<name>_turns/turn_NNNN_<SPEAKER>.wav` — per-turn cache; required for cheap iteration on a single bad line
- `<name>.concat.txt`, `silence_400ms_24000.wav` — build artifacts

The `.tts` parent is **dot-prefixed deliberately**. This dir lives inside the Obsidian vault (`projects/artifacts/`), and Obsidian Sync — like iCloud — never indexes or syncs dot-folders at any depth. Without the dot, every render dumped hundreds of MB of WAVs into the synced vault and broke sync. Keep the cache (it makes single-line re-renders cheap), just keep it hidden. This is the skill cleaning up after itself: bulky regeneratable output never enters a sync surface.

**iCloud (only the phone-sync copy):** `~/Library/Mobile Documents/com~apple~CloudDocs/tts/<name>/<name>.mp3`

Point `--out` at the local `.tts` path; the renderer writes WAV + cache + build artifacts there. Then `cp` only the MP3 to iCloud. Nick listens to the MP3 on AirPods via the Files app — no need to sync the 900MB WAV or the dozens of cache WAVs.

## Files

- `renderer/chunker.py` — markdown → turns.json
- `renderer/render_vibevoice_perturn.py` — turns.json → wav/mp3
- `examples/` — starting template (copy this, don't edit in place)
- `PLAYBOOK.md` — full producer reference (read before invoking on a new project)
- `pyproject.toml`, `uv.lock` — manifest for the deps (mlx-audio, soundfile, numpy) that live in `~/venv/tts/`. Model is `mlx-community/VibeVoice-Realtime-0.5B-fp16` (HuggingFace cache).

## Hardware

Designed for M4 Max 36 GB. Render speed ~1.2× realtime — 30-min episode = ~35 min compute, fully unattended. Don't run on smaller machines without re-validating memory headroom.
