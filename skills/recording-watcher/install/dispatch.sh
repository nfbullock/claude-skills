#!/bin/bash
# dispatch.sh — fswatch event handler for recording-watcher.
#
# Reads file paths from stdin (one per line, as fswatch emits them),
# filters to new .m4a files, dedups via seen.txt, and fires
# `claude -p "/recording-watcher <path>"` for each.
#
# Sync (not backgrounded) on purpose:
#   - Recordings are sparse; serial dispatch keeps logs and reasoning sane.
#   - The async pipeline lives inside watch.py / claude -p — there's no
#     UX advantage to parallelism here.
#
# Invoked by watch-loop.sh; not meant to run standalone (no stdin → exits).

set -euo pipefail

LOG_DIR="$HOME/Library/Logs/recording-watcher"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/dispatch.log"
SEEN="$LOG_DIR/seen.txt"
touch "$SEEN"

WATCHER_DIR="/Users/dad/Documents/sandbox/projects/claude_skills/recording-watcher"

while IFS= read -r path; do
  case "$path" in
    *.m4a) ;;
    *) continue ;;
  esac

  if grep -Fxq "$path" "$SEEN"; then
    continue
  fi

  echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] dispatch: $path" >> "$LOG"

  # Only mark seen if processing succeeds. A transient failure (e.g. iCloud
  # placeholder not yet materialized when fswatch fires) needs to remain
  # eligible for retry on the next fswatch event — see watch.py's
  # wait_for_sync_settled and the 2026-05-10 walking-review incident.
  if ( cd "$WATCHER_DIR" && "$HOME/.claude/skills-venv/bin/python" watch.py "$path" ) >> "$LOG" 2>&1; then
    printf '%s\n' "$path" >> "$SEEN"
  else
    echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] watch.py failed for $path (not marking seen; will retry on next fswatch event)" >> "$LOG"
  fi
done
