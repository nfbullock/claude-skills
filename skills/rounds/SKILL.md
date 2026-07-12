---
name: rounds
description: Fred's pull-based weekly synthesis — replaces the weekly review AND /projects-status. Fires ONLY when Nick asks ("do the rounds", "Fred, do the rounds", "what moved this week"); never scheduled, never a launchd agent — reflection erupts, it is not assigned. Output is a printed duplex 2-pager — what moved, what stalled (re-entry cards), the open music-lesson list, then the week read back in prose with 3-5 concrete claims to push against (never open questions). Cowork pattern — scan.py emits deterministic JSON, Fred writes the pager with judgment, render.py prints it via shim-api. Nick's reaction to each rounds is standing input to the next (state/<date>/reactions.md).
status: active
---

# The rounds

Nick asks; Fred answers with one duplex sheet. This is the whole review
apparatus now — the weekly review and `/projects-status` both retired into it
(STATE.md, 2026-07-11). The re-entry cards survived; the ceremony did not.

**Pull-based only.** No launchd agent, no cron, no schedule, no reminder to run
it. Scheduling reflection at Nick is banned by law (the 07-10 ruling). If a
week passes without the rounds, that is Nick's business, not a gap to nag
about.

**Fred's artifact.** Read `backstairs/SOUL.md` and the auto-memory
`vault-deep-context.md` before writing a word. The voice is Fred's: direct,
concise, chaotic-useful, never moralizing, never therapist. And the shed law
applies to every stall you report: **never diagnose avoidance when the tool is
broken** — a stalled project's first question is "where's its printed unit and
its debrief, and is the tool between them broken?"

## Trigger phrases

"do the rounds" · "Fred, do the rounds" · "what moved this week" · "read the
week back to me". Nick never says skill names.

## The pipeline

1. **Scan** (deterministic, no judgment):

   ```bash
   ~/venv/default/bin/python /Users/dad/Documents/sandbox/backstairs/rounds/scan.py \
       --out /Users/dad/Documents/sandbox/backstairs/rounds/state/<YYYY-MM-DD>/scan.json
   ```

   Default window is 7 days (`--days` to widen — e.g. if the last run in
   `prior_rounds.runs` is older than a week, cover the whole gap).

2. **Read** the JSON, plus `prior_rounds.last_reactions` — Nick's markup of
   the previous rounds is standing input; honor it before anything else. Pull
   personal memory (memory_search) for anything the week's data touches.

3. **Write** the 2-pager in Fred's voice as markdown at
   `state/<YYYY-MM-DD>/rounds.md`, using the section contract below and the
   markdown subset documented at the top of `render.py`. Exactly one `---`
   page break.

4. **Render + print**:

   ```bash
   ~/venv/default/bin/python /Users/dad/Documents/sandbox/backstairs/rounds/render.py \
       state/<date>/rounds.md state/<date>/rounds.html state/<date>/rounds.pdf --print
   ```

   render.py HARD-FAILS above 2 pages. Cut prose until it passes; never
   loosen the budget. (Preview without paper: drop `--print`.)

5. **Seed next time**: write `state/<date>/reactions.md` as a stub —

   ```markdown
   # Reactions — rounds of <date>
   <!-- Nick's pushback on the claims, in his words or from the pen marks.
        Filled at or after the walkthrough; the next rounds reads this first. -->
   ```

   When Nick reacts — in session, or reading pen marks off the sheet — append
   his reactions here verbatim-ish. Claims he disputed, cards he waved off,
   anything he said the rounds got wrong. The next run's scan surfaces it.

## The section contract (the four sections, in order)

**Page 1:**

- `## What moved` — the wins, terse. Soil-level, not file-level; the scan's
  numbers back the claims, they don't appear as tables. Things completions in
  window belong here. Watcher findings land here too (model-watcher findings
  have NO other channel since push-notify died — see FLEET.md; if the scan
  shows a finding Nick hasn't been told about, the rounds carries it).
- `## What stalled — the doors back in` — re-entry cards (`###` blocks), one
  per stalled thing: **where it stopped / the likely snag / one physical next
  move**. Physical means physical — a thing done with hands, not "think
  about". Inherited straight from /projects-status.
- `## Music — open lessons (listen first)` — the current-lesson list: every
  open lesson from the scan (which delegates to music-loops), grouped by
  track/lane. Listen-first framing; a listen with the kids counts. This is a
  LIST, not a loop report — no aging, no guilt arithmetic.

**Page 2 (after the one `---`):**

- `## The week, read back` — PROSE. The week as Fred actually read it, a few
  short paragraphs.
- `## Claims to push against` — 3-5 numbered, concrete, declarative claims
  Nick can disagree with. **Never open questions.** "The gym queue at three
  means the printed unit stopped being the unit" — yes. "How do you feel
  about the gym queue?" — never.

## Content rules (from the 07-11 walkthrough — not optional)

- **No open questions, anywhere.** Concrete promptables only.
- **ACTIVE projects don't get their loops enumerated.** A project moving under
  Nick's hands needs no ledger of its remaining work.
- **Music gets a current-lesson list, not a loop report.**
- **"Eventually" items are heuristics, not loops** — don't surface them as
  debts.
- **Kids-Minecraft is invisible.** scan.py filters it; the prose never
  resurrects it. Pure play, never a loop/hazard/concern.
- **Sensitive soils (life-story, spiritual-coupledom) at process level only**
  — files moved yes/no, never names, never content. scan.py already strips
  them; the prose stays at "life-story moved this week" altitude.
- **someday/ and archive/ are never surfaced as stale.** They aren't scanned;
  don't reach around the scan to mention them.
- **Zero provenance on paper** — no file paths, scan keys, or JSON on the
  printed sheet. Nick reads a page, not a debug dump.

## State layout

```
backstairs/rounds/state/<YYYY-MM-DD>/
    scan.json      — the deterministic facts this run saw
    rounds.md      — the pager as written
    rounds.html    — rendered
    rounds.pdf     — what printed
    reactions.md   — Nick's pushback (stub at run time, filled after)
```

## What this skill does NOT do

- Run on a schedule. Ever. No plist exists and none may be created.
- Ask open questions or assign reflection homework.
- Edit any soil, STATE.md, Things, or anything outside `rounds/state/`.
- Replace the reaper — that's the deep 2-6-week blade with the ballot; the
  rounds is the weekly read. Same shed, different tools.

## Files

- `scan.py` — deterministic scan (soils/git/Things/debriefs/watchers/music/
  prior-rounds), JSON to stdout, `--out` to file. Stdlib only; every failed
  source degrades to `{"error": ...}`.
- `render.py` — markdown -> designed HTML -> PDF (Chromium headless), 2-page
  hard budget, `--print` posts to shim-api `/print` duplex (thin stdlib
  client, same pattern as money/pipeline/shim.py).
- `SKILL.md` — this file.
- `state/` — per-run history (created on first run).
