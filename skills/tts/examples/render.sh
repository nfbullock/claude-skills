#!/usr/bin/env bash
# Example render driver. Edit the variables, then `./render.sh`.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
RENDERER_DIR="$(cd "$PROJECT_DIR/../renderer" && pwd)"
VENV="$HOME/venv/tts"

NAME="episode"
HOST_VOICE="en-Mike_man"
GUEST_VOICE="en-Carter_man"
# Bulky master + per-turn cache stay LOCAL under .tts (dot-prefixed → Obsidian Sync
# ignores it, and it never churns iCloud). Only the final MP3 is copied to iCloud.
LOCAL_DIR="$HOME/Documents/sandbox/projects/artifacts/.tts/${NAME}"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/tts/${NAME}"

mkdir -p "$LOCAL_DIR" "$ICLOUD_DIR"

# 1. Build turns from script.
"$VENV/bin/python" "$PROJECT_DIR/build_turns.py"

# 2. Render audio (master + per-turn cache land in LOCAL_DIR).
"$VENV/bin/python" "$RENDERER_DIR/render_vibevoice_perturn.py" \
    --turns "$PROJECT_DIR/build/${NAME}.turns.json" \
    --voice "HOST=$HOST_VOICE" \
    --voice "GUEST=$GUEST_VOICE" \
    --out "$LOCAL_DIR/${NAME}.wav" \
    --ddpm 80 \
    --cfg 1.5 \
    --gap_ms 400 \
    --mp3

# 3. Only the MP3 syncs to iCloud for phone listening.
cp "$LOCAL_DIR/${NAME}.mp3" "$ICLOUD_DIR/${NAME}.mp3"
