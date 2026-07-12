#!/bin/bash
# recording-watcher-dispatch.sh
#
# launchd-side stdin handler. Real file lives here (outside ~/Documents/)
# so launchd-spawned bash isn't blocked by TCC. Canonical version at:
#   ~/Documents/sandbox/backstairs/recording-watcher/install/dispatch.sh
# Keep them in sync.
#
# Sync (not backgrounded) on purpose: recordings are sparse; serial dispatch
# keeps logs and reasoning sane. Invoked by watch-loop.sh; not meant to run
# standalone (no stdin → exits).

set -euo pipefail

LOG_DIR="$HOME/Library/Logs/recording-watcher"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/dispatch.log"
SEEN="$LOG_DIR/seen.txt"
touch "$SEEN"

WATCHER_DIR="/Users/dad/Documents/sandbox/backstairs/recording-watcher"

while IFS= read -r path; do
  case "$path" in
    *.m4a|*.mp3|*.wav) ;;
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
  if ( cd "$WATCHER_DIR" && /Users/dad/venv/default/bin/python watch.py "$path" ) >> "$LOG" 2>&1; then
    printf '%s\n' "$path" >> "$SEEN"
  else
    echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] watch.py failed for $path (not marking seen; will retry on next fswatch event)" >> "$LOG"
  fi
done
