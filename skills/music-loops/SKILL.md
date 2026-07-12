---
name: music-loops
description: Open-loops check for Nick's music lessons — every generated lesson still awaiting practice + debrief/retro, across all four tracks (gym per-lane, office per-lane, field), each paired with its reference playlist and a listen-first nudge. Exists because the playlist is the half of the lesson Nick skips when he's manic — the report leads with LISTEN FIRST, not with the lesson. Invoke as /music-loops, or when Nick asks "what are my open loops", "what lessons are open", "what am I supposed to be practicing", "which playlists do I owe a listen". Read-only; never generates a lesson. Sibling to /music-status (this is the narrow fast cut; that's the full orientation).
status: active
---

# /music-loops

What's open right now — the lessons generated and waiting, and the playlists that come *before* them. The fast, narrow cut: `/music-status` tells you where the whole project stands; this tells you what you owe your own curriculum tonight.

**Read-only.** Never generates a lesson, never builds a playlist, never edits a track file.

## Why this skill leads with playlists

Nick asked for this skill for two reasons (2026-07-01): he loses track of which lessons are open, and — his words — he's not listening to every playlist he should. The playlist is the pre-lesson gate on every track; a lesson read before it's heard is half a lesson. So the report's unit is not "lesson with a playlist attached" — it's **listen → practice → debrief**, three steps of one loop, in that order.

One reframe to honor: Nick uses these playlists to play music for his kids ("the ultimate music exposure tool for children"). **A listen with the kids counts.** Never frame the playlist as homework he's behind on — frame it as the thing he already loves doing, pointed at the right playlist.

## How to run

```bash
~/venv/default/bin/python /Users/dad/Documents/sandbox/backstairs/music-loops/scan.py
```

The scan emits JSON: `loops` (each with track, lane, id, title, file, playlist URL, and the listening.md log line as listen-first material), plus `stage` counts and the per-track `gates` reference.

## Building the report

Keep it to one screen. Group by track; within gym and office, name the lane — **lanes never block each other**, so a `home-lab` and a `voice` loop (or a `ma` and an `ml`) are parallel, not a pile-up. For each loop, three lines of substance max:

1. **🎧 Listen first** — playlist name, runtime, URL, and a *one-phrase* what-to-listen-for distilled from the `listen_line` (don't paste the whole log line). If `carried_over` is true, say so ("same playlist as NNN — it carries over"). If `playlist` is null, check the `status_excerpt` and the lesson file before declaring it playlist-less; if it genuinely has none, say "no playlist for this one" and move on (some lessons legitimately skip — the request-not-a-wall rule).
2. **The lesson** — id, title, file path, one phrase on what it drills.
3. **The gate it holds** — what stays blocked until its debrief lands (e.g. "gates the next keys lesson, nothing else").

### Judgment to apply

- **Ask about listened-state, don't assume it.** The scan can't know what Nick's ears have done. If it matters, ask him which playlists he's actually heard — his answer is the real data, and it feeds the next lesson's framing.
- **Field loops get the soft touch.** Field is pull-based and allowed to sit quiet; an open field lesson is a warm invitation, not a debt. Cross-track utility lessons (e.g. sample-prep for the office) may carry no retro on purpose — reconcile against `field/JOURNAL.md` "Notes for the coach" before calling one open.
- **Stage never appears as a loop.** Optional retros by design.
- **No manufactured urgency.** If a loop has sat for a week, that's a fact, not a failing — the practice meets him and doesn't punish him (SOUL.md). The report's job is orientation, not guilt. If everything's closed, celebrate in one line and stop.
- **End with the shortest true sentence about tonight:** given the open loops, what's the one obvious "if you've got 40 minutes" move (usually: the playlist that's been heard least + its lesson).

## What this skill does NOT do

- Generate lessons, playlists, or debrief prompts (those are asks routed through the mode CLAUDE.md files).
- Write to any file.
- Replace `/music-status` — that's the full four-track orientation with sources and cover pulls; this is the loop ledger.
