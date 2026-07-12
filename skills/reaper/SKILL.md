---
name: reaper
description: The recurring open-loop sweep — externalizes everything Nick has committed to (or implicitly hung onto) across the vault, Claude history, and Things 3, classifies each loop, and hands back a two-layer artifact — an exhaustive LEDGER on disk (never printed) and a designed HTML BALLOT (≤8 pages, printed duplex) marked up in pen with KEEP/KILL/RESHAPE/DEFER. The sweep is ~1 hour of orchestrated parallel readers; the budget that matters is Nick's ≤30 pen-minutes. Cadence is every 2–4 weeks; the prompt refuses to run inside 14 days without explicit confirmation. Invoke as /reaper or when Nick asks to run the reaper or do a deep sweep.
status: active
---

# reaper

**This is a deep operation, not a quick skill.** A single run sweeps the entire vault, recent Claude conversation history, and Things 3 — roughly an hour of orchestrated parallel readers plus composition (the 2026-07-10 run used 37 readers; the old "7–9 hours" estimate predates orchestration). Don't fire it inside other work. Open a fresh Claude Code window dedicated to the sweep. The budget that actually matters is on the other side of the paper: **Nick's pen pass is ≤ 30 minutes by design.**

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

1. **Stage claude.ai exports if recent.** If there's been claude.ai activity worth sweeping in the last sweep window: claude.ai → Settings → Privacy → Export data → wait for email → drop the zip into `~/Documents/sandbox/backstairs/reaper/sources/claude_ai_exports/`. The prompt picks up the freshest zip automatically. If you skip this, the reaper still runs over Claude Code / Cowork history; you just won't get claude.ai threads.

2. **Read `PROMPT.md` and follow it end-to-end.** It is the first-pass sweep prompt. Don't paraphrase, don't summarize — execute.

3. **Output lands in `~/Documents/sandbox/artifacts/reaper/<YYYY-MM-DD>/`.** Two layers, strictly separated:
   - `reaper_<date>.md` — **the LEDGER.** Exhaustive, full provenance, globally numbered. The walkthrough and the next sweep's diff read it. **Never printed.**
   - `ballot_<date>.{html,pdf}` + `ballot_curation.json` — **the BALLOT.** The designed decision surface (≤ 8 pages, system rulings + big rocks on page 1, project groups, auto-KILL strip). The only paper Nick touches. Numbering is identical to the ledger.

   Append a line to `RUN_LOG.md` with the run timestamp.

4. **Print the BALLOT duplex (shim-api `/print`). Mark it up with a pen.** This is the binding step. The pen converts surfaced loops into KEEP / KILL / RESHAPE / DEFER decisions. Mark precedence is printed on the ballot: line beats group; blank = undecided.

## Regenerating or re-cutting a ballot (no re-sweep)

The ballot is a pure function of the ledger + curation. To re-render (or re-cut the grouping) at any time:

```bash
~/venv/default/bin/python scripts/render_ballot.py \
  artifacts/reaper/<date>/reaper_<date>.md \
  artifacts/reaper/<date>/ballot_<date>.html \
  artifacts/reaper/<date>/ballot_<date>.pdf \
  --curation artifacts/reaper/<date>/ballot_curation.json
```

The renderer parses the ledger format directly, validates that the curation accounts for every ledger item exactly once, and hard-fails past 8 pages. Edit the curation JSON to re-group; never touch the ledger. PDF renders via a headless Chromium-family browser (Brave on this machine; `BALLOT_CHROMIUM` overrides). `--redline notes.md` appends a design-notes page; `--no-pdf` for HTML-only. Without `--curation` it falls back to classification-grouping — correct coverage, uncurated.

## How to run — second pass (reorganization) — LEGACY

`PROMPT_SECOND_PASS.md` predates the two-layer contract (it reorganized a messy printed v1). Kept for lineage. If a ballot reads badly, the fix is now a curation edit + re-render, not a v2 document.

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

- `PROMPT.md` — the first-pass sweep prompt (run this every 2–4 weeks). Includes the two-layer output contract and the ballot-curation rules.
- `scripts/render_ballot.py` — deterministic ledger→ballot renderer (HTML + PDF, coverage-validated, ≤8-page gate). Stdlib + a headless Chromium for PDF.
- `PROMPT_SECOND_PASS.md` — legacy reorganization prompt (pre-ballot lineage; superseded by curation edits).
- `RUN_LOG.md` — one line per run; the prompt reads this to enforce cadence.
- `sources/` — out-of-band inputs (claude.ai exports). See `sources/README.md`.

Outputs do **not** live here — they live in `projects/artifacts/reaper/<date>/` per the artifacts convention.

