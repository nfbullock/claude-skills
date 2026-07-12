---
name: music-status
description: Orientation report for Nick's music project — the four-track umbrella (gym, field, Stage, office). Shows where each track stands (lesson counts, phase, what's next, retro/playlist blocks), the active cover pulls, and the state of the source reservoir (syntheses, holes, open requests). Cowork pattern — scan.py emits deterministic JSON, Claude writes the report with judgment. Invoke as /music-status. Read-only. Sibling to /projects-status and /skills-status.
status: active
---

# /music-status

Where am I across the four practice tracks, and what's the state of the material I generate lessons from? This is the repeatable version of the start-of-session orientation — run it any time you want the lay of the land.

It is **read-only**. It never generates a lesson, never edits a track file, never builds a playlist. It tells you where you are and what the obvious next moves are; you decide what to actually do.

## What this skill does

1. Runs `scan.py`, which deterministically reads:
   - Each track's lesson count, newest lesson, and how long since it moved.
   - **Gym**: current phase, rotation "next suggested", count of queued-but-not-practiced lessons (from `gym/state.md`).
   - **Field**: current phase, cover phase (recipe vs deconstruct), songs finished, and the active cover pulls (from `JOURNAL.md`).
   - **Sources**: synthesis count, holes (raw source with no matching synthesis), open Tier-1 requests (from `sources/raw/REQUESTED.md`).
2. Claude reads the JSON and writes a single scannable report with editorial judgment — see "Building the report" below.

## How to invoke

```bash
~/venv/default/bin/python /Users/dad/Documents/sandbox/backstairs/music-status/scan.py --json
```

(Drop `--json` for a quick human-readable dump if you just want to eyeball it without Claude formatting.)

## Building the report

The scan gives facts. Your job is to turn them into orientation. Keep it tight — this is the lightweight version, not a 200-line audit (that's the reaper). Aim for a one-screen report.

Structure it as **four track lines + a sources line + a short "obvious next moves" list.**

### Per-track judgment to apply

- **Retro/playlist gate (gym + field only).** Both block their next lesson on (a) the prior lesson having a retrospective, and (b) a reference playlist being built. If gym shows `queued_lessons > 0`, the next lesson is *already generated and waiting to be practiced* — the move isn't "generate a lesson," it's "practice 010-ep / 011-gk, then retro." Say that. Don't suggest generating a new gym lesson when printed ones are unpracticed.
- **Stage + office never block.** Their retros are optional. Don't flag them as "missing a retro." A long silence on Stage/office is not a problem to surface — these are pull-based and allowed to sit quiet (so is field; see below).
- **Field is pull-based and allowed to be quiet.** If field hasn't moved in weeks, that's not staleness — per the project's own framing, Nick's energy flows toward office/gym for stretches and the field sits quiet by design. Note the active cover pulls (they're the warm pulls waiting), but don't nag.
- **Cover pulls are warm leads, not a backlog.** List them; if one has a notable hook (e.g. the McHugh "Go Don't Stop" grief-lyric-rewrite), name it in a few words. Don't imply they're overdue.

### Sources judgment to apply

- **A "hole" from the scan is raw-source-with-no-synthesis. Cross-check it against `sources/raw/REQUESTED.md` before reporting it as a gap.** Some holes are *deliberate skips* documented there (e.g. `pattison-songwriting-essential-guide` is a scanned EPUB Nick chose not to OCR — redundant with Writing Better Lyrics). Report those as "intentionally skipped," not as an open gap. A genuine hole is raw material that *should* be synthesized and isn't.
- **`tier1_open_requests > 0`** means there's a source biting *right now* that needs ingesting — surface it. Zero is the healthy state.
- Don't list all 22 synthesis slugs. Give the count and only call out anything noteworthy (a just-added source, a genuine hole).

### Tone

Same register as `/skills-status` and `/projects-status`: terse, scannable, honest. Celebrate what's moving, name what's blocked, and end with the 2–4 moves the data makes obvious. If everything's healthy, say so in a line and stop — don't manufacture concern.

## What this skill does NOT do

- It does not write to any track file, `state.md`, `JOURNAL.md`, or source.
- It does not generate lessons or build playlists — it points at where those are due. Generating a lesson is a separate, explicit ask routed through the relevant mode's CLAUDE.md.
- It does not run the reaper or a deep sweep. This is the daily-orientation altitude, not the periodic deep audit.
- It does not flag Stage/office/field as stale by mtime — those tracks are pull-based by design.

## Sibling tools

`/projects-status` (the whole `projects/` root) and `/skills-status` (the skills directory) are the same shape — scan → judgment → terse report. This one is scoped to the music project's internals, one altitude below `/projects-status` (which sees `music/` as a single project).

## Files

- `scan.py` — deterministic scan. Reads each track + the sources reservoir, emits JSON (`--json`) or a human-readable dump (default). Makes no qualitative calls.
- `SKILL.md` — this file.

