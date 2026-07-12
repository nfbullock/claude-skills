#!/usr/bin/env bash
# Render formative-identity chapters as single-voice spoken-word audiobook.
# Usage: ./render.sh [chapter-slug]
# Default chapter: 01-configuration-attachment
#
# Layout convention (only MP3 syncs to iCloud; .tts is dot-prefixed so Obsidian Sync ignores it):
#   LOCAL  ~/Documents/sandbox/artifacts/.tts/formative-identity/
#          <chapter>.wav                                  (master, ~900 MB)
#          <chapter>_turns/turn_NNNN_NARRATOR.wav         (per-turn cache for iteration)
#          <chapter>.concat.txt + silence_400ms_24000.wav (build artifacts)
#   iCloud ~/Library/Mobile Documents/com~apple~CloudDocs/tts/formative-identity/
#          <chapter>.mp3                                  (~30 MB, the phone-sync copy)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
RENDERER_DIR="$(cd "$PROJECT_DIR/../renderer" && pwd)"
VENV="$HOME/venv/tts"

CHAPTER="${1:-01-configuration-attachment}"
NARRATOR_VOICE="en-Mike_man"  # proven from flex podcast / PLAYBOOK §3
LOCAL_DIR="$HOME/Documents/sandbox/artifacts/.tts/formative-identity"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/tts/formative-identity"

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
echo "    MP3 (synced):   $ICLOUD_DIR/${CHAPTER}.mp3"
echo "    WAV (local):    $LOCAL_DIR/${CHAPTER}.wav"
echo "    Cache (local):  $LOCAL_DIR/${CHAPTER}_turns/"
