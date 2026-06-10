#!/usr/bin/env bash
# fetch.sh <youtube-url>
#
# Fetches a YouTube transcript: creator subtitles preferred, local Whisper STT
# fallback. Stashes the result in a stable cache and prints metadata to stdout
# in shell-evalable KEY=VALUE form. All progress noise goes to stderr.
#
# Output (stdout):
#   TITLE='...'
#   SOURCE=creator-subs|whisper-cpp-large-v3-turbo
#   TRANSCRIPT_PATH=/abs/path/to/transcript.txt
#   WORDS=1234
#
# Designed to be called by the yt-discuss SKILL.md via Bash. Standalone — no
# claude exec, no session spawning. Caller decides what to do with the path.

set -euo pipefail

usage() {
  echo "usage: fetch.sh <youtube-url>" >&2
  exit "${1:-1}"
}

URL="${1:-}"
[[ -n "$URL" ]] || usage

WHISPER_MODEL="/Volumes/NewSamsung/models/standalone/stt/whisper-large-v3-turbo.bin"
CACHE_DIR="$HOME/.claude/skills/yt-discuss/transcripts"
mkdir -p "$CACHE_DIR"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

echo "fetch.sh: fetching metadata..." >&2
TITLE="$(yt-dlp --get-title --no-warnings "$URL" 2>/dev/null || echo "(unknown title)")"

echo "fetch.sh: checking for creator subtitles..." >&2
yt-dlp --write-subs --sub-langs "en.*" --skip-download \
       --convert-subs srt --no-warnings \
       -o "vid.%(ext)s" "$URL" >/dev/null 2>&1 || true

SOURCE=""
if compgen -G "vid*.srt" > /dev/null; then
  SRT="$(ls vid*.srt | head -1)"
  awk '
    /^[0-9]+$/      { next }
    /-->/           { next }
    /^[[:space:]]*$/{ next }
    { print }
  ' "$SRT" > transcript.txt
  SOURCE="creator-subs"
else
  echo "fetch.sh: no creator subs — downloading audio for local transcription..." >&2
  yt-dlp -x --audio-format wav --no-warnings \
         -o "audio.%(ext)s" "$URL" >/dev/null 2>&1

  ffmpeg -hide_banner -loglevel error -y \
         -i audio.wav -ar 16000 -ac 1 audio16k.wav

  echo "fetch.sh: transcribing with whisper.cpp (large-v3-turbo)..." >&2
  whisper-cli -m "$WHISPER_MODEL" -f audio16k.wav \
              --output-txt -of transcript >/dev/null 2>&1

  SOURCE="whisper-cpp-large-v3-turbo"
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
TRANSCRIPT_PATH="$CACHE_DIR/${STAMP}.txt"
cp transcript.txt "$TRANSCRIPT_PATH"

WORDS="$(wc -w < "$TRANSCRIPT_PATH" | tr -d ' ')"
echo "fetch.sh: transcript ready ($WORDS words, source: $SOURCE)" >&2

# Shell-evalable output. Single-quote TITLE to survive most punctuation; replace
# any embedded single quotes with the standard '"'"' escape.
TITLE_ESC="${TITLE//\'/\'\"\'\"\'}"
printf "TITLE='%s'\n" "$TITLE_ESC"
printf "SOURCE=%s\n" "$SOURCE"
printf "TRANSCRIPT_PATH=%s\n" "$TRANSCRIPT_PATH"
printf "WORDS=%s\n" "$WORDS"
