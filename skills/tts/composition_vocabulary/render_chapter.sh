#!/usr/bin/env bash
# Render one chapter. Usage: ./render_chapter.sh chapter_00_motif
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
RENDERER_DIR="$(cd "$PROJECT_DIR/../renderer" && pwd)"
VENV="$HOME/.claude/skills-venv"

NAME="${1:?usage: ./render_chapter.sh chapter_NN_slug}"
VOICE="en-Mike_man"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/tts/composition_vocabulary"
# .tts is dot-prefixed so Obsidian Sync ignores the bulky WAV master + per-turn cache.
LOCAL_DIR="$HOME/Documents/sandbox/projects/artifacts/.tts/composition_vocabulary"

mkdir -p "$ICLOUD_DIR" "$LOCAL_DIR"

# Render master + per-turn cache LOCAL; only the MP3 is copied to iCloud below.
"$VENV/bin/python" "$RENDERER_DIR/render_vibevoice_perturn.py" \
    --turns "$PROJECT_DIR/build/${NAME}.turns.json" \
    --voice "NARRATOR=$VOICE" \
    --out "$LOCAL_DIR/${NAME}.wav" \
    --ddpm 80 \
    --cfg 1.5 \
    --gap_ms 400 \
    --mp3

cp "$LOCAL_DIR/${NAME}.mp3" "$ICLOUD_DIR/${NAME}.mp3"
