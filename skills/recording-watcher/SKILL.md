---
name: recording-watcher
description: Universal voice-capture endpoint. Watches the Just Press Record iCloud directory for new audio files; transcribes with local whisper; uses Claude (Opus) to classify the recording (review_recording | add_to_things | unknown); dispatches to the matching handler (write to review/daily/, push to Things via things.py, etc.). Acts both as an autonomous folder watcher (via launchd + fswatch) and a callable skill (`/recording-watcher <file>` for testing or manual processing). Designed so Nick can "just press record" anywhere and the system figures out where it belongs.
status: stub
activity_log: captures/
---

# /recording-watcher

The voice-capture endpoint. One press of the record button on the phone, anywhere; the system figures out where it belongs.

## Invocation

```
/recording-watcher <audio-file-path>
/recording-watcher <audio-file-path> --dry-run
```

When invoked, run the orchestrator:

```bash
~/venv/default/bin/python /Users/dad/Documents/sandbox/projects/claude_skills/recording-watcher/watch.py <audio-file-path>
```

Default behavior:
- If the path is inside `~/Library/Mobile Documents/iCloud~com~openplanetsoftware~just-press-record/`, omit `--skip-settle` (the file may still be syncing from the phone).
- If the path is anywhere else (a local test file, a re-process), pass `--skip-settle`.
- Pass `--dry-run` if Nick asked for one, or if you're not confident about the route — `add_to_things` will print the planned task without pushing to Things.

After the run, summarize for Nick in 2–4 lines: route, confidence, and either the synthesized Things title (for `add_to_things`) or the log path (for `review_recording` / `unknown`). The orchestrator already prints a JSON summary; pull from it, don't re-run inference.

`watch.py` does the heavy lifting (whisper transcription, Opus classification, handler dispatch). Don't reach into `lib/` or `handlers/` directly — let the orchestrator own the pipeline so the chat-invoked path matches the launchd-fired path.

## What this skill does

1. Triggered by either:
   - **fswatch** (launchd-managed) detecting a new `.m4a` in `~/Library/Mobile Documents/iCloud~com~openplanetsoftware~just-press-record/`
   - **Manual** invocation: `/recording-watcher <path>` from a chat (testing, reprocessing, ad-hoc)
2. Waits for iCloud sync to settle (file size stable for 10s).
3. Transcribes locally with `whisper-large-v3-turbo.bin` (whisper.cpp ggml format) at `/Volumes/NewSamsung/models/standalone/stt/whisper-large-v3-turbo.bin`.
4. Sends transcript to Claude (Opus 4.7) with the classification prompt → `{route, confidence, reasoning}`. Routes (v1):
   - `review_recording` — reflective content. Nick will often self-declare ("this is my daily review", "this is my weekly review") at the start; the review factory uses that downstream to pick the cadence handler. Classifier just needs to recognize "this is a review."
   - `add_to_things` — task / capture / "remind me to" / "I need to" shape
   - `unknown` — too short, ambient noise, off-topic; leave for triage
5. Dispatches to the matching handler:
   - `review_recording` → `review/handle.py` (the **review factory** — owns the daily/weekly/monthly/quarterly/annual dispatch based on Nick's spoken declaration). Watcher's job ends here; review system takes over.
   - `add_to_things` → `handlers/add_to_things.py` — Opus generates `{best_title, clarity: clear|needs_research, description}`; calls `things.py add` with title + notes (description if any + transcript verbatim); archives audio
   - `unknown` → write a line to `captures/unknown.log` so Nick can review later
6. Appends a one-line entry to `captures/log.md` for every dispatched recording: `<timestamp> | <route> | <confidence> | <one-liner>`.

## Inference posture

**Take all the time it needs.** This pipeline is async — there's no user waiting on the result. Use Opus 4.7 for classification and for handler-side reasoning (title generation, daily-review categorization). Quality is the deliverable, not throughput.

## Why "skill that masquerades as folder watcher"

The watch component (launchd + fswatch) is install glue, not the intelligence. The intelligence is Claude reasoning over the transcript. Treating it as a skill means:

- Same code path runs whether it's auto-fired by fswatch or manually invoked from a chat
- The skill is callable from any conversation (`/recording-watcher /path/to/file.m4a`) for testing, reprocessing, or one-off use
- Lifecycle (active / stub / deprecated) tracked by `/skills-status` like every other skill

## Files

```
claude_skills/recording-watcher/
├── SKILL.md                              this file
├── PLAN.md                               build plan (decisions + phases)
├── watch.py                              launchd entry → invokes the skill headless
├── lib/
│   ├── transcribe.py                     whisper.cpp wrapper
│   └── classify.py                       Opus classifier
├── handlers/
│   └── add_to_things.py                  Opus → title/clarity/description → things.py add
│                                         (review_recording dispatches directly to
│                                         review/handle.py — the review factory owns
│                                         cadence routing, so no local handler needed)
├── install/
│   └── im.bullock.recording-watcher.plist
└── captures/                             activity log
    ├── log.md                            one line per dispatched recording
    └── unknown.log                       triage-needed recordings
```

## Status

**Stub.** Phases 1 (manual end-to-end) and 2 (chat invocation) are built — `watch.py` processes a real recording and dispatches correctly, and `/recording-watcher <file>` is wired here. Still pending: Phase 3 (launchd + fswatch autonomous fire) and `review/handle.py` (the parallel review factory; for now `review_recording` just appends to `captures/pending-review.log`). Promote `status: stub → active` once Phase 3 has fired correctly on real recordings for a week without manual intervention.
