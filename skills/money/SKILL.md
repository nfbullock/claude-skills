---
name: money
description: Run the household spending review — the one-time bootstrap (3–6 month history) or a weekly check-in. Nick drops bank CSV exports in money/dumps/, then invokes this. Deterministic Python computes the EXACT numbers; Claude (in-session, no local model) writes the briefing; it renders a printable PDF and sends it to the Brother laser via shim-api /print; turns agreed cuts into Things tasks; schedules the next money date on the calendar; and records week-to-week state so the next run compares against targets and last week. Invoke as /money, or on "money review", "run the spending sheet", "weekly money", "do the 6-month review", or after dropping CSVs in dumps/.
status: active
---

# /money

The spending review for Nick + his wife. The whole point is a **shared, low-conflict ritual**:
exact numbers on a printed sheet, framed as *leverage and teamwork — never blame or shame*.
Behavioral thesis: *if you're paying attention, you spend less.*

**Division of labor (load-bearing):** the **dollar figures are deterministic Python** and are
never model-generated. **Claude writes only the narrative** and categorizes the tail — there is
**no local model** in this flow. Outward actions (print, Things, calendar) go through `shim-api`
and are **confirmed with Nick before firing.**

Paths: project `~/Documents/sandbox/money` (run everything from here); interpreter
`~/venv/default/bin/python`; outside world via `pipeline/shim.py` (the studio shim-api client).

**Reference — read `research/REVIEW-REFERENCE.md` before writing the briefing.** Distilled from
Nick's Deep Research, tailored to his profile (family of 4, Carlsbad/San Diego, ~$250k MFJ): the
**benchmark table** (where each category lands vs p25/p50/p75 + HIGH trip-wires), the **money-date
playbook** (agendas, de-escalation + blame→teamwork scripts), and the **target-setting + recurring
triage** method with **fair-price anchors**. (Raw reports in `research/raw/`; both gitignored.)

## Procedure

### 1. Pick the mode
- **bootstrap** — first run, or no `state/history.jsonl` yet. The consequential 3–6 month review.
- **weekly** — history exists. A check-in against targets + last week. Use `--since` if asked.
If unsure, check `state/history.jsonl`; absent → bootstrap.

### 2. Run the deterministic engine (rules-only — no local model)
```
~/venv/default/bin/python -m pipeline.run <bootstrap|weekly> --source dumps --no-llm
```
Read the **Preflight** block it prints (per-file rows · $in · $out · range):
- If it **REFUSES** an inverted credit-card file, tell Nick to copy `accounts.yaml.template` →
  `accounts.yaml` and set `flip_sign: true` for that account, then re-run. Do not proceed.
- Eyeball each file: a card/checking should read mostly **out**; flag anything that looks wrong.

It writes `reports/<label>-<mode>-analysis.md`. Read it.

### 3. Fix the categorization tail (Claude does this — no model call)
The analysis ends with **"Uncategorized merchants."** For each, add a substring → category line
to `categories.yaml` (durable + diffable; prefer this over the learned cache). Confirm the
non-obvious ones with Nick. Then **re-run step 2** so the numbers reflect the fixes. Repeat until
the uncategorized list is empty or trivial.

### 4. Write the briefing (in-session)
Compose the narrative yourself, in markdown, grounded in the analysis. Rules:
- Address them as a team ("you two"); never assign blame to one person.
- **Lead with leverage:** the 2–3 changes that free the most money for the least pain. Name
  specific recurring charges and their monthly cost (the forgotten/duplicate subs are the gold).
- Be concrete and numeric; no lectures, no shame, no hedging; short enough to read aloud.
- **Benchmark each category** against the table in `research/REVIEW-REFERENCE.md` — say where they
  land vs the SD/$250k p25/p50/p75 ranges and flag any HIGH trip-wire (e.g. groceries >$1,760,
  dining >$1,200, utilities >$700). This is what makes the numbers *mean* something on a first read.
  (Watch the category-bleed caveat: superstore charges miscoded as groceries inflate that line.)
- **bootstrap:** propose first-draft monthly **targets** per major category using the target-setting
  method in the reference (start from the benchmark, set a realistic negotiable target — not p25 in
  every category at once; housing/utilities are fixed, the elastic valves are dining/groceries-tier/
  subscriptions/entertainment). After Nick + wife agree, write them to `state/targets.yaml`
  (via `pipeline.state.save_targets`).
- **weekly:** load `pipeline.state.last_snapshot()` and `state.load_targets()`; report how the
  week went **vs target and vs last week**, and what to watch. Check `state.load_decisions()` and
  note follow-through on prior cuts.
Save the briefing to `reports/briefing.md`.

### 5. Render the sheet
```
~/venv/default/bin/python -m pipeline.run <mode> --source dumps --no-llm --briefing reports/briefing.md
```
Writes the HTML and a printable **PDF** (with a Target/Δ column if `targets.yaml` exists).

### 6. Outward actions — PROPOSE, then CONFIRM, then fire (via shim-api)
Run the conversation from the **money-date playbook** in `research/REVIEW-REFERENCE.md` — the 15-min
agenda for the first month, 30-min later; keep the de-escalation protocol and blame→teamwork scripts
on hand. Show Nick the plan and get a yes before each action:
- **Print:** `python -c "from pipeline import shim; print(shim.print_pdf('reports/<label>-<mode>.pdf'))"`
  → double-sided to the Brother.
- **Things (cuts → action):** run the recurring table through the reference's **cancel/keep/renegotiate
  triage**, using the **fair-price anchors** to flag above-market bills (internet/mobile/insurance) as
  *renegotiate* candidates. For each agreed cut, e.g.
  `shim.create_task("Cancel ANYTIME FITNESS — $49/mo (second gym)", tags=["money"], notes="From the <date> review.")`
  Use Nick's Things conventions (a `project`/tags as appropriate). Record each with
  `state.record_decision(merchant, "cancel"|"renegotiate"|"keep", monthly=..., on_date="<today>")`.
- **Calendar (next money date):** writable calendars are `Nick, Family, Xander, Dahlia` — default
  to **Family** (or Nick) for a money date; confirm. `shim.create_event("Money date", calendar,
  start, end, notes=...)` with ISO datetimes. Default cadence weekly; confirm day/time. Cadence is
  the #1 adoption risk — make the next one exist.

### 7. Persist state
Append the snapshot so trends accrue:
```
python -c "from pipeline import ingest,categorize,analyze,state as S; t=ingest.load('.','dumps'); categorize.categorize(t,'.',use_llm=False); a=analyze.analyze(t); S.append_snapshot(S.make_snapshot(a,'<label>'))"
```
Then append a one-line entry to `log.md` (and `weekly.md` for weekly runs).

## Notes
- **Privacy:** real CSVs (`dumps/`), `reports/`, `state/`, `research/` (holds the income/location-
  tailored benchmarks), `accounts.yaml`, the learned cache are all gitignored. Financial figures
  never leave the machine; only the printed sheet and Things/calendar titles (you control) go anywhere.
- **shim-api** must be up (`python -c "from pipeline import shim; print(shim.health())"`). It runs
  as a launchd service on this Mac Studio. The client is HTTP today; if an MCP facade lands,
  only `pipeline/shim.py` changes.
- See `RUNBOOK.md` for the first-real-run checklist. Prompts live in `prompts/review/` (conversation)
  and `prompts/service/` (tuning the tool); the completed Deep Research that fed
  `research/REVIEW-REFERENCE.md` is archived raw in `research/raw/`.

