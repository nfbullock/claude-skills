---
status: plan
parent: backstairs/recording-watcher/
created: 2026-05-09
---

# recording-watcher — build plan

The build plan for the universal voice-capture endpoint. Spun out of `review/daily/PLAN.md` on 2026-05-09 because the watcher has its own gravity: multiple consumers (review, things, future), agentic routing, infrastructure-shaped lifecycle.

## Decisions (locked from 2026-05-09 scoping)

| Decision | Choice |
|---|---|
| Trigger surfaces | (a) launchd + `fswatch` on JPR iCloud dir (autonomous); (b) `/recording-watcher <file>` (manual / testable) |
| Classification | Claude **Opus 4.7** reasoning over the transcript. Not config dispatcher; not regex. |
| Routes (v1) | `review_recording`, `add_to_things`, `unknown`. **Watcher does NOT decide review cadence** — that's the review factory's job (`review/handle.py`). Watcher just recognizes "this is a review" vs "this is a task." |
| Self-declaration | Nick will often start a recording with "this is my daily review" / "this is my weekly review" / "remind me to..." This is a strong classification signal but not required. Classifier should look for it first; fall back to content-shape heuristics if absent. |
| Ownership boundaries | **Watcher owns:** file watch, STT (whisper), classification (3 buckets), dispatch. **Watcher does NOT own:** TTS (lives in `review/`), cadence-specific handlers (live in each cadence's dir). |
| Transcription | `whisper-large-v3-turbo.bin` at `/Volumes/NewSamsung/models/standalone/stt/` (whisper.cpp ggml; cohere-transcribe as fallback) |
| Inference posture | Take all the time it needs. Async pipeline; no user waiting; quality > speed. |
| Watch dir | `~/Library/Mobile Documents/iCloud~com~openplanetsoftware~just-press-record/` |
| Sync-settled check | File size stable for 10s before processing (handles iCloud partial writes) |
| Handler invocation | Skill calls handler scripts as subprocesses with the transcript + metadata; handlers own their write paths |
| Activity log | `captures/log.md` (one line per dispatch); `captures/unknown.log` (triage queue) |
| Headless invocation | `claude -p "/recording-watcher <file-path>"` from launchd-fired wrapper script (or Agent SDK if cleaner) |

## Architecture

```
─── trigger ────────────────────────────────────────────────────
  (a) fswatch new .m4a → launchd job → claude -p "/recording-watcher <file>"
  (b) chat: /recording-watcher <file>
                  ↓
─── inside the skill ──────────────────────────────────────────
  wait_for_sync_settled(file)
                  ↓
  transcript = transcribe(file)         # whisper-large-v3-turbo
                  ↓
  {route, confidence, reasoning} = classify(transcript)   # Opus
                  ↓
  match route:
    review_recording → review/handle.py (the review factory)
                       (factory reads transcript, detects daily/weekly/monthly/etc.,
                        dispatches to that cadence's handle.py)
    add_to_things    → handlers/add_to_things.py
                       (Opus → title + clarity + description; things.py add)
    unknown          → captures/unknown.log
                  ↓
  append captures/log.md
  archive original audio (route-specific destination)
```

## Build phases

### Phase 1 — manual end-to-end on one real recording

Goal: process one real audio file by hand, validate the path. No automation.

1. `lib/transcribe.py` — wrapper around `whisper.cpp` invocation. CLI: `python -m lib.transcribe <file>` → prints transcript.
2. `lib/classify.py` — takes transcript text, calls Opus with the classification prompt, prints `{route, confidence, reasoning}` JSON.
3. `handlers/add_to_things.py` — takes transcript + metadata, runs Opus for title/clarity/description, calls `things.py add`. CLI: `python handlers/add_to_things.py <transcript-file>`.
4. `watch.py` — wires it together. CLI: `python watch.py <m4a-file>` runs transcribe → classify → dispatch. For `review_recording` route, calls out to `review/handle.py` (built in the parallel review-side plan).
5. Manually invoke `python watch.py <recording.m4a>` on a real test recording (one for each route type). Validate end-to-end.

**Phase 1 success** = three test recordings (one review-shaped, one task-shaped, one unknown) all dispatched correctly with one manual command each.

### Phase 2 — skill plumbing + manual chat invocation

7. Write the SKILL.md prompt body so Claude can invoke `/recording-watcher <file>` from a chat and produce the same outcome as `python watch.py`.
8. Verify symlink at `projects/.claude/skills/recording-watcher` (or wherever symlinks live per the shared-skills convention).
9. Test from a fresh chat: `/recording-watcher <file>` → same outcome as the script.

**Phase 2 success** = the skill is callable from any conversation; classification + dispatch happens via Claude reasoning, not just script execution.

### Phase 3 — automate the watcher

10. Write `install/im.bullock.recording-watcher.plist` — launchd job that runs an `fswatch -o` loop on the JPR dir; on event, fires `claude -p "/recording-watcher <new-file>"`.
11. Install the plist (`launchctl load`).
12. Test: drop a recording into JPR via phone, walk away, come back, verify dispatch happened.

**Phase 3 success** = "just press record" → outcome lands in the right place with zero manual steps.

### Phase 4 — polish

13. `unknown.log` review surface: a `/recording-watcher triage` invocation that walks unprocessed unknowns and asks Nick what to do with each.
14. Confidence threshold: if classification confidence is below X, route to `unknown` instead of acting on a guess.
15. Re-process surface: `/recording-watcher reprocess <file-or-date>` for when classification was wrong.
16. Promote SKILL.md `status: stub → active` once Phase 3 has run end-to-end on real recordings for a week without manual intervention.

## Open risks / unknowns

- **Just Press Record filename + folder behavior.** First test recording will reveal the actual filename pattern. If JPR can route to subfolders by tag/category, that's a useful signal *in addition to* Opus classification (not a replacement — the goal is "just press record," not "remember which folder you're in").
- **iCloud sync latency.** If recordings take >5 min to appear locally, the "fire-and-forget" feel breaks. Acceptable for v1 but measure during Phase 1.
- **Claude headless invocation.** `claude -p` semantics — does it inherit the right working dir / permissions / skills? Validate during Phase 3 install. Falling back to Agent SDK is fine if the CLI path is fiddly.
- **Classification ambiguity.** A recording that's both "I had a thought during the walk + remind me to fix the gate" — does it route as review with action_items, or as add_to_things with context? Default: prefer review_recording when there's any reflective content; pure imperative captures route to add_to_things.
- **Recordings during a Friday weekly review.** Subsumption rule says no daily review on Fridays. If Nick walks Friday and records a response, what happens? Default: still classify; if route is review_recording on a subsumed day, write to `review/daily/<date>.md` anyway (Friday becomes both — no data loss).

## Hopper section

`projects/next-actions.md` gets a `## recording-watcher` section. First entry will be the Phase 1 build kickoff.

