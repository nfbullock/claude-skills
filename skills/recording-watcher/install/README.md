# recording-watcher install

The autonomous-fire pieces of the skill: launchd job, fswatch driver, dispatch wrapper.

## Architecture

```
launchd (com.bullock.recording-watcher)
   └── /bin/bash watch-loop.sh                  (KeepAlive=true)
         └── fswatch --recursive JPR_DIR
               │ (one path per line on stdout)
               ↓
         dispatch.sh                            (sync loop, dedup via seen.txt)
               └── python3 watch.py <path>      (direct call, no outer claude -p)
                     └── lib/classify.py + handlers/add_to_things.py
                         use `claude -p --model opus` (OAuth) internally
```

**Why no outer `claude -p`?** Tested on the first real-recording run: a headless `claude -p "/recording-watcher <path>"` sits at a permission prompt waiting for a human to approve its Bash call (`python3 watch.py ...`), which fails the autonomous use case. Calling `watch.py` directly bypasses that — the model reasoning still happens via `claude -p` (OAuth) inside classify.py and add_to_things.py, where there's no agentic Bash to gate. Chat-invoked `/recording-watcher <file>` keeps the agent layer because there's a human in the loop to approve.

## Prerequisites

```bash
brew install fswatch        # not currently installed
```

## Install

```bash
# 1. Symlink (or copy) the plist into ~/Library/LaunchAgents/
ln -s "$HOME/Documents/sandbox/backstairs/recording-watcher/install/com.bullock.recording-watcher.plist" \
      "$HOME/Library/LaunchAgents/com.bullock.recording-watcher.plist"

# 2. Load the job (also starts it because RunAtLoad=true)
launchctl load "$HOME/Library/LaunchAgents/com.bullock.recording-watcher.plist"

# 3. Confirm it's running
launchctl list | grep recording-watcher
```

The job runs as your user (not root). It inherits the user keychain — same auth context as `claude` from a terminal — so `claude -p` should work without prompting.

## Logs

- `~/Library/Logs/recording-watcher/launchd.out` — fswatch event paths (the raw stream, since dispatch.sh reads them; useful when debugging "did fswatch see it?")
- `~/Library/Logs/recording-watcher/launchd.err` — fswatch and shell errors
- `~/Library/Logs/recording-watcher/dispatch.log` — one line per dispatched .m4a + the full `claude -p` JSON envelope
- `~/Library/Logs/recording-watcher/seen.txt` — dedup ledger (every path the dispatcher has fired on)
- `backstairs/recording-watcher/captures/log.md` — the skill's own activity log (one line per recording it processed)

## Manual smoke test (no launchd)

Before installing, you can prove the pipe works in the foreground:

```bash
bash /Users/dad/Documents/sandbox/backstairs/recording-watcher/install/watch-loop.sh
# In another terminal, drop or `touch` a .m4a inside the JPR dir.
# Watch dispatch.log for the fire.
# Ctrl-C to stop.
```

## Uninstall

```bash
launchctl unload "$HOME/Library/LaunchAgents/com.bullock.recording-watcher.plist"
rm "$HOME/Library/LaunchAgents/com.bullock.recording-watcher.plist"
```

To reset the dedup ledger (re-process everything currently in JPR):

```bash
rm ~/Library/Logs/recording-watcher/seen.txt
```

## Known caveats / things to verify after install

- **fswatch event types on iCloud.** iCloud sync produces a layered sequence (placeholder → download → finalize). `Created`/`Updated`/`Renamed` should cover it but the first real test will tell. `watch.py`'s `wait_for_sync_settled()` is the safety net — it waits for size to stabilize for 10s before transcribing.
- **`claude -p` from launchd context.** Should work because the job runs as the user, but the first dispatch is the real validation. If `claude -p` fails for auth reasons, fall back to invoking `python3 watch.py <file>` directly from `dispatch.sh` — the orchestration layer doesn't strictly require Claude reasoning.
- **Concurrent recordings.** Dispatch is synchronous on purpose (one recording at a time). If you record three things back-to-back, they'll classify in arrival order — totally fine for sparse use, would need rethinking for high-volume.
- **seen.txt grows unboundedly.** A line per recording forever. Acceptable for v1; rotate or trim if it ever matters.
