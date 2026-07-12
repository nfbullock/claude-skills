#!/bin/bash
# recording-watcher-watch-loop.sh
#
# launchd entry-point. Real file lives here (outside ~/Documents/) so
# launchd-spawned bash isn't blocked by TCC at script-open time. The
# canonical version lives at:
#   ~/Documents/sandbox/backstairs/recording-watcher/install/watch-loop.sh
# Keep them in sync.

set -euo pipefail

JPR_DIR="$HOME/Library/Mobile Documents/iCloud~com~openplanetsoftware~just-press-record"
REVIEWS_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/reviews"

exec /opt/homebrew/bin/fswatch \
    --recursive \
    --event Created \
    --event Updated \
    --event Renamed \
    "$JPR_DIR" \
    "$REVIEWS_DIR" \
  | /Users/dad/.local/bin/recording-watcher-dispatch.sh
