#!/bin/bash
# watch-loop.sh — long-lived fswatch driver for recording-watcher.
#
# Watches the Just Press Record iCloud directory and pipes every event
# path to dispatch.sh. Single-process so launchd's KeepAlive=true does
# the right thing (relaunches if fswatch dies).

set -euo pipefail

JPR_DIR="$HOME/Library/Mobile Documents/iCloud~com~openplanetsoftware~just-press-record"
HERE="$(cd "$(dirname "$0")" && pwd)"

exec /opt/homebrew/bin/fswatch \
    --recursive \
    --event Created \
    --event Updated \
    --event Renamed \
    "$JPR_DIR" \
  | "$HERE/dispatch.sh"
