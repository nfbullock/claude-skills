---
name: reaper
description: The recurring open-loop sweep — externalizes everything Nick has committed to (or implicitly hung onto) across the vault, Claude history, and Things 3, classifies each loop, and hands back a printable document to mark up in pen with KEEP/KILL/RESHAPE/DEFER decisions. Heavy operation (7–9 hours of sweep work). Cadence is every 2–4 weeks; the prompt refuses to run inside 14 days without explicit confirmation. Invoke as /reaper or when Nick asks to run the reaper or do a deep sweep.
status: active
---

# reaper

**This is a deep operation, not a quick skill.** A single run is a 7–9 hour sweep over the entire vault, recent Claude conversation history, and Things 3. Don't fire it inside other work. Open a fresh Claude Code window dedicated to the sweep.

## Why this exists

Nick has memory issues, ENTP-style appetite for new threads, and a life that keeps generating distractions. He cannot trust his head to remember what he committed to. Without externalization, loops accumulate silently and eat cognition.

The reaper is the periodic sweep that brings every loop to the surface, classifies it, and forces a binary decision (KEEP / KILL / RESHAPE / DEFER) per loop with a pen.

This skill is the operational arm of the "program? reapers (tasks?)" bubble in `projects/artifacts/mindmap/2026-05-01.md`.

## When to invoke

- "Run the reaper"
- "Time for a deep sweep"
- "/reaper"
- Anything that signals "do the periodic open-loop externalization"

The cadence is **every 2–4 weeks**. `RUN_LOG.md` tracks history; `PROMPT.md` refuses to run inside 14 days without explicit override. Don't run it more often.

## How to run — first pass

1. **Stage claude.ai exports if recent.** If there's been claude.ai activity worth sweeping in the last sweep window: claude.ai → Settings → Privacy → Export data → wait for email → drop the zip into `~/Documents/sandbox/projects/claude_skills/reaper/sources/claude_ai_exports/`. The prompt picks up the freshest zip automatically. If you skip this, the reaper still runs over Claude Code / Cowork history; you just won't get claude.ai threads.

2. **Read `PROMPT.md` and follow it end-to-end.** It is the first-pass sweep prompt. Don't paraphrase, don't summarize — execute.

3. **Output lands in `~/Documents/sandbox/projects/artifacts/reaper/<YYYY-MM-DD>/`.** First-pass file is `reaper_<date>.md`; supplements (if any) appear as `reaper_<date>_supplement_*.md`. Append a line to `RUN_LOG.md` with the run timestamp.

4. **Print the output on letter paper. Mark it up with a pen.** This is the binding step. The pen converts surfaced loops into KEEP / KILL / RESHAPE / DEFER decisions.

## How to run — second pass (reorganization)

When a first pass gets messy — supplements bolted on, the same loop appearing in three sections, deadlines buried inside long STALE lists — read and execute `PROMPT_SECOND_PASS.md`. It does NOT re-scan sources; it integrates supplements, dedups to a single home per loop, pulls deadlines into a Section 0, adds a domain index, and names the single decision that disposes of each cluster.

Output: `projects/artifacts/reaper/<original_date>/reaper_<original_date>_v2.md`. The v1 stays as the audit trail; the v2 supersedes it for printing.

You only need a v2 when v1 is hard to read on paper. A clean v1 doesn't need a v2.

## After the print-out

The reaper produces the document. Follow-through is Nick's:

- **KILL** → delete the loop from its source (vault file, Things task, chat thread).
- **KEEP** → assign a concrete next action.
- **RESHAPE** → re-scope the loop (smaller, different framing, different home).
- **DEFER** → assign a date and create a calendar event.

If the print-out gets marked up but the follow-through doesn't happen within 7 days, the next sweep will surface every "kept" loop again as still-stale. The pen marks don't change the world; the actions after do.

## When to update the prompts themselves

If a run produces supplements (Supplement A, B, etc.), that's a smell — the first-pass prompt missed a source or a folder. Don't just live with the supplement: figure out what the prompt should have caught, and fold the fix back into `PROMPT.md` before the next run. The 2026-05-02 run added a hard scan-roster requirement to the vault step and moved claude.ai exports into `sources/`, both for this reason.

## Numbering convention

Every decision item in reaper output gets a sequential global `#NN` prefix so Nick can walk through them by number with Claude after marking up the print. The numbering survives reorganizations (a loop's `#NN` stays the same in v1, v2, v3 supplements). PROMPT.md enforces this.

## Files

- `PROMPT.md` — the first-pass sweep prompt (run this every 2–4 weeks).
- `PROMPT_SECOND_PASS.md` — the reorganization prompt (run this against a messy v1).
- `RUN_LOG.md` — one line per run; the prompt reads this to enforce cadence.
- `sources/` — out-of-band inputs (claude.ai exports). See `sources/README.md`.

Outputs do **not** live here — they live in `projects/artifacts/reaper/<date>/` per the artifacts convention.
