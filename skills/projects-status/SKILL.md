---
name: projects-status
description: Daily orientation report for Nick's projects/ root. Produces a single-sheet printable HTML brief — project health, hopper contents, an honest assessment of how he's doing, and a small list of recommended moves the data makes obvious. Cowork pattern — scan.py emits JSON, Claude builds the document fresh each run with real editorial and design judgment. Not the reaper (deep 2–4 week sweep). Not the daily/weekly review (that writes; this reads). Invoke as `/projects-status`.
status: active
---

# /projects-status

This is a **cowork skill**. The script is a data layer. You are the editor, designer, and writer of the document. Each run is a fresh act of composition, not a template-substitution exercise. Read this whole file before generating.

## What this is for

Nick wants a daily brief — *"an idea of whether my projects are in a good state, what kind of next actions I have in the hopper, and a basic assessment of how I'm doing"* — that he can print, fold in his pocket, and mark up in pen on a walk. It's not a decision form. It's not a status pane in a dashboard. It's an editorial brief, like a single-sheet morning report a senior advisor would hand him before his day starts.

The voice is **Fred** per `review/SOUL.md` — terse, honest, framework-trap-aware, allergic to motivational-poster language. The document should sound like someone who knows him and won't waste his time.

## Who it's for

Nick — ENTP, design-heavy / execution-light by his own diagnosis, lives in the vault, uses Things 3 for next-actions, runs a daily/weekly review, has a network printer, marks paper in pen, gets unstuck on walks. Background from memory in `/Users/dad/.claude/projects/-Users-dad-Documents-sandbox/memory/` — especially `user_nick_profile`, `feedback_things_reschedule_as_workflow`, `feedback_claude_convo_as_next_action`, `feedback_projects_status_today_threshold`. Read those if the data needs interpretation you don't already have.

## How to run it

```bash
~/venv/default/bin/python /Users/dad/Documents/sandbox/projects/claude_skills/projects-status/scan.py
```

JSON output. The fields you'll use:

- `reconciliation` — Things↔hopper transitions written this run. `transitions_total` is the gate for whether to render a CHANGED section.
- `things_today_count` — capacity read.
- `things_active_project_suffixes` — set of project names with open tasks in Today/Anytime. Used to know what's already in-flight.
- `projects[]` — per-project: `project`, `bucket` (`moving` / `silent` / `needs_audit` / `foundational_at_risk` / `scaffold` / `null_log`), `days_silent`, `threshold_days`, `foundational`, `priorities`, `log_excerpt`.
- `hopper{}` — by project: `unresolved[]`, `in_flight[]` (`[>]` Today, `[~]` rescheduled), `terminal_recent[]` (last 14 days).
- `hopper_totals` — overall counts.
- `candidates_ranked[]` — leverage-scored unresolved items (`score`, `score_breakdown`). For the optional push follow-up AND for picking which moves to recommend.
- `weekly_review` — latest weekly review's `## Patterns feeding the queue` section. **Read this carefully.** It contains Nick's own framing of where he is. The assessment paragraph must ground here.

## The document — what good looks like

A single sheet of letter-size paper. Self-contained HTML file (inline `<style>`, no external assets) so Nick can email it, AirDrop it, open from any device. Designed to print clean on a black laser printer with one accent color used sparingly.

**Five things the document does:**

1. **Tells Nick at a glance whether his projects are in good shape.** Which are moving, which have gone silent, which are foundational, which are under audit. The PROJECTS section. He should be able to skim it in 10 seconds.

2. **Shows him what's queued in the hopper.** Per-project, terse, abbreviated. Not full bodies — *phrases* that let him remember what each item is. The HOPPER section.

3. **Tells him the truth about how he's doing.** 2–4 sentences. Grounded in `weekly_review.patterns` plus the observable signals (foundational holding? silent cluster? capacity vs hopper size?). No motivational language. No "great job." No "you should." If the foundation is wobbly, say so. If a project he named super-important hasn't moved in six weeks, say that. The HOW YOU'RE DOING section.

4. **Receipt for what Things did since last scan.** Only if `reconciliation.transitions_total > 0`. CHANGED block at the top of the page. Neutral voice on rescheduled items — Nick moves tasks across days deliberately; `[~]` is healthy planned work, never alarm-frame it.

5. **A small, bounded prescription.** 3–5 RECOMMENDED MOVES the data makes obvious — stale hopper items to KILL, foundational-with-hard-date items to PUSH, super-important silent projects to NUDGE attention to, items needing a body rewrite (RESHAPE). Each move has an action verb, a target, a one-line reason, and visible space on the page (a `✓ ✗ …` mark column) for Nick to circle his decision in pen. **Cap at 5.** If the data justifies more, pick the sharpest signals. Don't include moves that require opinion — only ones grounded in observable signals (past dates, hard deadlines, foundational + at risk, named-but-not-moving, etc.).

## Design guidance — make real choices

You are the designer. Make the document feel like an editorial brief, not a database dump. Some directions, not prescriptions:

- **Typography:** A clean sans for structure (system font stack works — `-apple-system, BlinkMacSystemFont, "Helvetica Neue", ...`). Consider a serif (Georgia) for the HOW YOU'RE DOING paragraph specifically — it gives that section editorial weight and visually separates the narrative from the data. Tabular-nums for any number column so things align.
- **Hierarchy:** A real masthead with the date. Section headers small-caps or all-caps with letter-spacing, modest size, restrained. Rules and whitespace are the structural devices, not boxes everywhere.
- **Color:** Mostly black on white. One accent color (a deep red like `#b00020` works) for silent / killed / alert states. A muted blue (`#1a5e9e`) for needs-audit / informational states. A muted gold (`#c79100` or `#8a6500`) for foundational stars and rescheduled glyphs. Use color sparingly — most of the page should be text on paper.
- **Density:** Aim for a single page. Generous line-height (~1.4). Don't cram. If overflow looks likely, tighten margins before sacrificing whitespace.
- **Pen-markability:** Every hopper item should have a `□` prefix so Nick can tick. Every recommended-move row should have a small mark column on the right (e.g., `✓ ✗ …`) for circling.
- **Print rules:** `@page { size: letter; margin: ~0.45in; }`. `@media print` adjustments where appropriate (e.g., bump black to pure `#000`). `page-break-inside: avoid` on the sections so they don't split awkwardly.
- **Self-contained:** All CSS in a single inline `<style>` block. No web fonts, no external assets, no scripts. The file should render identically when AirDropped to a phone or printed from a different machine.

Don't copy a previous run's HTML verbatim — make design decisions based on *this* day's data. If the hopper is empty, the HOPPER section's visual structure should look different than when 19 items are queued. If there are no recommended moves, omit the section entirely (don't render "No moves today"). If the only thing notable is a 7-item CHANGED block, give that real visual prominence.

But: stay consistent enough that Nick recognizes the document as the same brief day-to-day. Masthead, section names, voice — those are stable. Layout and styling can flex with the data.

## Voice for the assessment paragraph

The HOW YOU'RE DOING section is where this document either earns Nick's trust or loses it. Some rules:

- Lead with the observable. *"Foundation is holding — review is moving and has a dated next move."* Not *"You're doing great keeping up with review."*
- Name patterns Nick has already named in `weekly_review.patterns`. If he wrote "design-heavy / execution-light" in his last weekly, that's vocabulary you can use — it's his own framing, not yours imposed.
- Name the named-but-not-moving project. If `weekly_review.patterns` calls out a project as high-importance and the scan shows it silent, surface that *specifically* by name. Don't generalize.
- Capacity read: `things_today_count` vs `hopper_totals.unresolved`. If Today is light and hopper is heavy, *"you're under-decided, not overloaded."* If Today is over 20, name it — but don't lecture.
- Two short paragraphs is usually right. One if the data is sparse. Three only if there's genuinely a lot to say.

Things to never write: "Keep going!" / "You've got this!" / "Great work on X!" / "Don't forget to Y." / Anything that reads like a phone reminder app.

## Where the document goes

Write to: `/Users/dad/Documents/sandbox/projects/artifacts/projects-status/YYYY-MM-DD.html`

If a file with that name already exists (you ran the skill earlier today), append `-2`, `-3`, etc.

After writing, echo to terminal:

1. A one-line confirmation with the path: *"Report: artifacts/projects-status/2026-05-13.html"*
2. A 6–10 line terse summary so Nick gets the gist without opening the file. Bullet the counts (projects: X moving / Y silent / Z audit; hopper: N unresolved / M in flight; today: K), one line from the assessment, the top recommended move if any.
3. Optionally: *"`open <path>` to view, `lp <path>` to print."*

Don't dump the whole HTML to terminal. The file IS the report; the terminal is the receipt.

## Optional follow-up

If Nick reads the report and says *"push the Friday weekly draft"* / *"kill move 1 and 3"* / *"add 'photograph kids' art' to the great courses hopper"* — apply via the existing flow:

- **Push:** `things.py add --title "<body> — <project>" --tag project --tag <context> --when today` (capture UUID, write `[>] YYYY-MM-DD — <body> <!-- things:UUID -->` to the hopper line). If add fails or no UUID, stop and surface the error — never write a `[>]` without a UUID.
- **Kill:** Rewrite the hopper line as `[x] killed YYYY-MM-DD — <body>`. No Things write.
- **Reshape:** Edit the body in place. Preserve markers.
- **Add to hopper:** Append a new `- [ ] <body>` line under the matching `## <project>` section.
- **Drill in:** Read the project's README + latest log_excerpt + hopper section; hand Nick the context.

Context tags use the GTD vocabulary: `home`, `office`, `errand`, `phone`, `computer`, `5min`, `waiting`. Always include `--tag project` so Nick's `#project` filter sees it. Title suffix is `— <project-name>` using the dir name as-is.

## Hopper marker vocabulary

| Marker | Meaning | Written by |
|---|---|---|
| `[ ]` or bare bullet | Unresolved candidate. | Anywhere |
| `[>] YYYY-MM-DD` | Pushed; still in Today in Things. | Push step + reconcile |
| `[~] pushed P, now N` | Pushed; moved off Today. **Healthy planned work.** | Reconcile only |
| `[x] done YYYY-MM-DD` | Completed. Terminal. | Reconcile |
| `[x] killed YYYY-MM-DD` | Cancelled/trashed. Terminal. | Reconcile or skill |
| `[?] missing YYYY-MM-DD` | UUID present, Things has no record. | Reconcile |

`[>]` and `[~]` lines always carry `<!-- things:UUID -->`. Never write one without.

## Edge cases

- **Empty hopper.** Skip the HOPPER section entirely, or replace with a one-line note. Don't render an empty grid.
- **No transitions.** Omit the CHANGED block entirely — no "no changes since last scan" line.
- **Today over 20.** Don't refuse the report. Render it. In the HOW YOU'RE DOING section, name the saturation explicitly: *"Today=23. The thing this report can't solve is the queue size. Want to triage Today before you read the rest?"*
- **No recommended moves.** Omit the section.
- **`weekly_review` is null** (no weekly review file found). The assessment paragraph leans entirely on observable signals; don't fabricate context.

## What this skill does NOT do

- Propose new hopper candidates. The daily/weekly review does that.
- Decide for Nick. The RECOMMENDED MOVES are *suggestions grounded in observable data*; Nick applies them or doesn't.
- Bucket projects into KEEP/KILL/RESHAPE. That's the reaper, at 2–4 week cadence.
- Write to STATE.md, READMEs, or activity logs.
- Run when scan.py errors out — surface the error and stop.

## The leverage scorer (data input, not user-facing)

`scan.py` scores `candidates_ranked` with:

- foundational +3, hard date ≤7d +4, hard date past +1, delivery verb +2, log-overlap +1.5, project silent +1
- design verb −1.5, project in-flight −2, needs-audit −2

Use the top-scored items as input to RECOMMENDED MOVES (specifically: PUSH for high scores, NUDGE for foundational-but-silent, KILL for stale-dated, RESHAPE for body-mismatched). The scorer is informational — you make the editorial call about which moves to include.

## Files

- `scan.py` — JSON data layer.
- `reconcile.py` — hopper↔Things state machine. Standalone: `~/venv/default/bin/python reconcile.py [--dry-run]`.
- `backfill_uuids.py` — one-time legacy fixer. Already run.
- `SKILL.md` — this file. The cowork prompt.
