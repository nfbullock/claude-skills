#!/usr/bin/env bash
# Render weekly-review touchstones as single-voice spoken-word audio.
# Usage: ./render.sh [date-slug]   e.g. ./render.sh 2026-05-15
# Default: latest entry in build_turns.py ENTRIES dict.
#
# Layout convention (only MP3 syncs to iCloud; .tts is dot-prefixed so Obsidian Sync ignores it):
#   LOCAL  ~/Documents/sandbox/projects/artifacts/.tts/weekly-review/
#          <date>.wav                                  (master)
#          <date>_turns/turn_NNNN_NARRATOR.wav         (per-turn cache for iteration)
#          <date>.concat.txt + silence_400ms_24000.wav (build artifacts)
#   iCloud ~/Library/Mobile Documents/com~apple~CloudDocs/tts/weekly-review/
#          <date>.mp3                                  (the phone-sync copy)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
RENDERER_DIR="$(cd "$PROJECT_DIR/../renderer" && pwd)"
VENV="$HOME/.claude/skills-venv"

DATE="${1:-2026-05-15}"
NARRATOR_VOICE="en-Mike_man"  # Fred's voice — proven from formative-identity / PLAYBOOK §3
LOCAL_DIR="$HOME/Documents/sandbox/projects/artifacts/.tts/weekly-review"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/tts/weekly-review"

mkdir -p "$LOCAL_DIR" "$ICLOUD_DIR"

echo "==> Building turns from script..."
"$VENV/bin/python" "$PROJECT_DIR/build_turns.py"

echo "==> Rendering ${DATE} (single voice: $NARRATOR_VOICE) -> local..."
"$VENV/bin/python" "$RENDERER_DIR/render_vibevoice_perturn.py" \
    --turns "$PROJECT_DIR/build/${DATE}.turns.json" \
    --voice "NARRATOR=$NARRATOR_VOICE" \
    --out "$LOCAL_DIR/${DATE}.wav" \
    --ddpm 80 \
    --cfg 1.5 \
    --gap_ms 400 \
    --mp3

echo "==> Copying MP3 to iCloud for phone sync..."
cp "$LOCAL_DIR/${DATE}.mp3" "$ICLOUD_DIR/${DATE}.mp3"

echo "==> Done."
echo "    MP3 (synced):   $ICLOUD_DIR/${DATE}.mp3"
echo "    WAV (local):    $LOCAL_DIR/${DATE}.wav"
echo "    Cache (local):  $LOCAL_DIR/${DATE}_turns/"
