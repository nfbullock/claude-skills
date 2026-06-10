#!/usr/bin/env bash
# Render pull-learning chapters as single-voice spoken-word audiobook.
# Usage: ./render.sh [chapter-slug]
# Default chapter: 00-topology
#
# Layout convention (only MP3 syncs to iCloud; .tts is dot-prefixed so Obsidian Sync ignores it):
#   LOCAL  projects/artifacts/.tts/pull-learning/<chapter>.wav            (master)
#          projects/artifacts/.tts/pull-learning/<chapter>_turns/...wav   (per-turn cache)
#   iCloud ~/Library/Mobile Documents/com~apple~CloudDocs/tts/pull-learning/<chapter>.mp3
# (cache stays local so iteration on one bad line is cheap)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
RENDERER_DIR="$(cd "$PROJECT_DIR/../renderer" && pwd)"
VENV="$HOME/venv/tts"

CHAPTER="${1:-00-topology}"
NARRATOR_VOICE="en-Mike_man"  # proven from flex podcast / PLAYBOOK §3
LOCAL_DIR="$HOME/Documents/sandbox/projects/artifacts/.tts/pull-learning"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/tts/pull-learning"

mkdir -p "$LOCAL_DIR" "$ICLOUD_DIR"

echo "==> Building turns from script..."
"$VENV/bin/python" "$PROJECT_DIR/build_turns.py"

echo "==> Rendering ${CHAPTER} (single voice: $NARRATOR_VOICE) -> local..."
"$VENV/bin/python" "$RENDERER_DIR/render_vibevoice_perturn.py" \
    --turns "$PROJECT_DIR/build/${CHAPTER}.turns.json" \
    --voice "NARRATOR=$NARRATOR_VOICE" \
    --out "$LOCAL_DIR/${CHAPTER}.wav" \
    --ddpm 80 \
    --cfg 1.5 \
    --gap_ms 400 \
    --mp3

echo "==> Copying MP3 to iCloud for phone sync..."
cp "$LOCAL_DIR/${CHAPTER}.mp3" "$ICLOUD_DIR/${CHAPTER}.mp3"

echo "==> Done."
echo "    MP3 (synced):  $ICLOUD_DIR/${CHAPTER}.mp3"
echo "    WAV (local):   $LOCAL_DIR/${CHAPTER}.wav"
