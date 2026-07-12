# Reaper — Second Pass (Reorganization)

*Rebased 2026-07-12 for the two-layer output (ledger + ballot, adopted 2026-07-10)
and the flat vault. The second pass reorganizes the LEDGER, then RE-AUTHORS the
ballot curation and re-renders the printed ballot. The ledger itself is NEVER
printed.*

This is a re-runnable prompt for cleaning up a reaper sweep that has become disorganized. Run it after a fresh `PROMPT.md` sweep, especially when:

- The first pass produced supplements (e.g., from a late-arriving source like a claude.ai export, or a folder the first-pass agent missed)
- Classifications drifted as new context arrived mid-pass
- The ledger exceeded ~80 loops and the ballot's curation stopped reflecting it (rocks reading like a to-do list is the tell)
- The same loop appears in three or more sections via cross-references
- A new bit of context (illness, deadline, life event) reframes how prior loops should be read

**To re-run:** drop into a fresh Claude window with file access. Paste everything below the line. Hit go. Don't read this prompt to "get ready." The reading is the work the second pass does, not you.

---

# Reaper Second Pass — Run Instructions

You are running a one-shot reorganization pass over the most recent reaper output for me (Nick). The deliverable is TWO layers, same as the first pass: a reorganized v2 LEDGER (machine/audit layer — never printed) and a re-authored + re-rendered v2 BALLOT (the only paper; ≤8 pages duplex). The v2 ballot supersedes the prior print for pen markup.

This is **not a new sweep.** Do not re-scan the vault, Claude history, Things 3, claude.ai exports, or any other source. The first pass already did the externalization; this pass is about making the output usable on paper.

If you catch yourself wanting to add a loop you "noticed" or to surface new findings from your own knowledge — stop. That belongs in the next first-pass sweep, two-to-four weeks from now.

## Input

Read the most recent first-pass file in:
**`/Users/dad/Documents/sandbox/artifacts/reaper/`**

Outputs are organized as `<YYYY-MM-DD>/reaper_<YYYY-MM-DD>.md` (with `_v2`, `_v3` suffixes for reorganizations). Pick the freshest dated subdirectory and read the file with no `_v2`, `_v3` suffix. Read it in full, including any supplements appended at the bottom. Also read that sweep's `ballot_curation.json` (the ballot's editorial layer — you will re-author it after the ledger settles). Read `/Users/dad/Documents/sandbox/backstairs/reaper/RUN_LOG.md` for run history.

If `artifacts/reaper/` is empty or no first-pass file exists, output a single line saying "No first-pass output found. Run PROMPT.md first." and stop.

## Operating sequence — moves in order

The moves are sequential. Each one assumes the prior one is done. Don't dedup before integrating supplements; don't tag domains before re-classifying.

### 1. Integrate supplements first

If the doc has appended sections (Supplement A, B, etc., usually from late-arriving sources or first-pass misses), fold each loop in those supplements back into its natural class section. Drop the supplement scaffolding entirely. The supplements are a chronological artifact of how the sweep ran; they should not survive into the printable. Do this *before* dedup so you're working with one corpus.

### 2. Consolidate same-loop-different-name across sources

If two captures across sources are clearly the same loop under different names (e.g., a Things task and a vault-file section that describe the same intended action), merge them into one entry. Preserve both source pointers in the `Sources:` line. The first pass over-splits because each source is read in isolation; the second pass is the first time you can see the same loop appear twice.

### 3. Re-classify after the full read

A loop's classification can change once all the others are visible. A STALE item that turns out to be a sub-loop of a larger named parent is NESTED. A VAGUE item with an explicit dated ask in a parent doc is ZOMBIE. A ZOMBIE that has gone fully cold is just STALE. **A class of re-classification worth watching:** a loop is upgraded from STALE/VAGUE to ZOMBIE because a freshly-discovered parent doc names a deadline or escalates the ask. Update the class. Note the change in "What changed in v2."

### 4. Dedup to a single home — precedence rule

Each loop has exactly one home. When a loop fits multiple classes, pick the most action-pressing one in this order:

**Section 0 (DEADLINE) > ZOMBIE > NESTED > ECHO > VAGUE > STALE > WIDOWED > PRINCIPLE**

A DEADLINE-class loop *also* appears in Section 0 (intentional redundancy for safety) but its primary home is its action class. Where removing the cross-listing would lose signal, leave a one-line `Cross-ref:` note. The first pass intentionally cross-listed loops to avoid losing them; the second pass picks the single best home and trusts the cross-ref to do the rest.

**Exception worth honoring:** ECHO is a multiplicity-of-captures signal. If a loop is genuinely ECHO *and* a sub-loop of a NESTED parent, keep it in ECHO with a cross-ref to NESTED — the "I keep re-externalizing this" pattern is its own diagnostic and shouldn't be hidden inside a cluster.

**After dedup, re-number globally.** First-pass output uses sequential global `#1..#N` numbering. After dedup/consolidation in v2, re-number from #1 so the new doc has a clean continuous sequence. Preserve the original numbers in a `was: #47, #62 (merged)` note for traceability where merging happened. The walkthrough references items by v2 number, so v2 numbers must be unique and gap-free.

### 5. Extract Section 0 — Deadlines

Pull any loop with an external clock — passport before a wedding, tax deadline, return window, registration cutoff, delivery window, an explicit "this week" ask in a dated document, anything with a date the world enforces — into a new **Section 0 — Deadlines** at the very front. Order by closeness. **Expired deadlines also belong here** with the deadline marked as "already passed (resolve filed/extension/late?)" — they need resolution, not deferral.

### 6. Tag domains; build Section 8 — Domain index

Each loop in Sections 0–7 carries an inline `Domain:` tag. Domains: Music & Creative · Family & Marriage · Home & Errands · Health & Body · Work & Career · Tooling & Agents · Practices & Self-Authorship · Misc.

The domain index at the back lists loops by primary domain (allow secondary domain listings for genuinely cross-domain loops). Use class abbreviations in the index for density: **D=Deadline, E=Echo, Z=Zombie, S=Stale, V=Vague, W=Widowed, N=Nested, P=Principle**. This lets the print be spread across the desk and worked through one domain at a time without losing the by-class view.

### 7. Surface decision burden per cluster

For each NESTED cluster and each ECHO cluster where one decision disposes of multiple items, name the single decision that disposes of it, and put it in a "Single decision that disposes of this cluster:" line under the cluster header. A single-decision line can also span multiple related ECHO entries (e.g., Camping ECHO + Weekend-getaway ECHO are the same wish under two names — one decision settles both). Examples:

- "Health project (8 items): decide once whether to schedule a 30-minute health-admin block this week. If yes, all 8 dispose to NEXT-ACTION. If no, all 8 KILL or DEFER."
- "Apr-22 home punchlist (28 items): promote to project, triage to top-5, or kill all. Don't decide 28 times."
- "Camping + weekend-getaway (2 ECHOs): decide once whether monthly outdoor weekends are a 2026 commitment."

For NESTED clusters, give the cluster header its own checkbox row keyed to the single decision (e.g., `[ ] PROMOTE   [ ] TRIAGE   [ ] KILL ALL   [ ] DEFER`) above the per-item rows. This protects against re-deciding the same thing per item.

### 8a. Verify priority lens on every KEEP

The five priorities are **formative-identity · music · family · consistency · health**. Every KEEP in v2 must declare which priority (or priorities, max two) it serves. Inherit declarations from v1 where present. For any KEEP that v1 left without a priority, attempt to infer from sources; if no priority connects, flag explicitly: `KEEP? — does not connect to any of the five priorities. Reconsider as KILL or RESHAPE.`

This is a verification pass, not new analysis. The goal is that no KEEP makes it into v2 without a stated relationship to the lens.

### 8b. Foundational projects at risk

If v1 surfaced a project marked `foundational: true` (frontmatter) as STALE or with empty/stale activity log, hoist that finding to the very front of v2 — above Section 0 — under a heading "Foundational project at risk." Foundational projects are load-bearing for the rest of the corpus; their stalls are not just one entry among many.

### 9. Surface contradictions — Section 10

List places where the corpus tells contradictory things about the same loop. Brief — one line each. Examples:
- A vault file says "active priority high" and the same loop is 87 days stale in Things.
- A daily-practice doc commits to a protocol; no source has a status surface.
- Two sources give different next-actions for the same loop.
- A strategic review told you to cut X N days ago; X is still present.

The reader resolves these in pen.

## Pen-friendliness audit (apply throughout, but verify after Section 8)

The ledger's item format doubles as a renderer contract: keep the `#NN` item
markers, `Title:` field, `Last moved:` dates, and `## Section N — NAME` headers
exactly as PROMPT.md specifies, or `render_ballot.py` breaks. The pen ultimately
lands on the BALLOT, but the ledger keeps these affordances for the post-pen
walkthrough. Each item needs:
- A checkbox row: `[ ] KEEP   [ ] KILL   [ ] RESHAPE   [ ] DEFER`
- A Title line
- Source / class / domain / last-activity metadata as appropriate to the class
- A Notes line with two underscored blanks, minimum
- Generous vertical whitespace; long inline lists (e.g., a 28-item NESTED) are acceptable as a single dense line *only* if the cluster has its own decision row above

**For PRINCIPLE items**, add a `Status:  [ ] running  [ ] stalled  [ ] never started  [ ] killed` row alongside the standard checkbox. Principles are easy to ignore on paper because they don't *look* like tasks. The status row gives the pen something to do per principle. For a multi-practice principle (e.g., a daily protocol with 8 sub-practices, or a weekly cadence with 4 days), give each sub-practice its own status row.

**Reorganization can reveal a new NESTED parent.** If your full read uncovers that several items v1 framed as orphans are sub-loops of a single previously-unnamed parent (a master doc, a project, a thread), name the parent and create a new NESTED cluster for it. This is the highest-value structural finding the second pass can produce. Note it in "What changed in v2" and in Patterns.

## What this pass does NOT do

- No re-scanning of sources. The corpus is frozen as of the first-pass file.
- No new loops surfaced from your own knowledge or pattern-matching.
- No interpretive coaching ("you should consider…"). Reorganize, don't advise. The PRINCIPLE section can recommend a destination for a loop, but never the disposition (KEEP/KILL).
- No removing loops because they look low-value. The author is the only one who decides KILL. The pen does the killing.
- No collapsing distinct loops just because they share a topic. ECHO is a multiplicity of identical-shape captures; if two loops are different asks within the same domain, they stay separate.
- No emoji, tables, or fancy formatting. Same plain-paper constraints as the first pass.

## Output

Save to:
**`/Users/dad/Documents/sandbox/artifacts/reaper/<original_date>/reaper_<original_date>_v2.md`**

Where `<original_date>` matches the source file's date (not today's date). If `_v2` already exists, use `_v3`, etc. Never overwrite.

Ledger constraints, identical to the first-pass sweep:

- Page breaks (`\n\n---\n\n`) before each `## Section N` header.
- No emoji. No tables. No bold paragraphs. Plain text inside sections.
- Generous vertical whitespace; Notes line is two underscored blanks per item, minimum.
- No truncation by default. ECHO listed exhaustively; STALE/ZOMBIE may be capped at 100 with the cap noted.

### Then re-author and re-render the ballot

The v2 ledger re-numbers items, so the old `ballot_curation.json` is invalid by
construction. Author `ballot_curation_v2.json` in the same dated directory,
mapping EVERY v2 ledger item exactly once (big rock / project group / auto-KILL
strip / ledger-only), following the curation rules in PROMPT.md's "The ballot"
section — rocks ordered by stake, one physical line per sub-item, group-mark
precedence, no fabricated ages. Render:

`~/venv/default/bin/python <skill>/scripts/render_ballot.py <ledger_v2.md> <ballot_v2.html> <ballot_v2.pdf> --curation <ballot_curation_v2.json>`

and print duplex via shim-api `/print`. The ≤8-page budget and the 07-11
content rules (no open questions; active projects' loops not enumerated; music
as current-lesson list; kids-Minecraft invisible) bind the v2 ballot exactly as
they bind a first-pass ballot.

### Document structure

```
# Reaper Sweep — [original date] (v2, reorganized [today's date])

## Sources read
[Inherit from v1; trim trivia but keep the source list complete. These were not re-scanned.]

## Counts
[Re-tally after dedup. Show the delta from v1 in parentheses, e.g., "STALE: 47 (was 60)".]

## What changed in v2
[3-7 bullets. Supplements integrated, dedup, re-classifications, new NESTED parent if any, deadline section, domain tags, contradictions section. Brief.]

---

## Section 0 — Deadlines (loops with an external clock)
[Order by closest first; expired deadlines included. Each item also lives in its action-class section below; this section is intentional redundancy.]

---

## Section 1 — ECHO   (recurring across sources)
[Each item carries `Domain:` inline. ECHO clusters with a shared decision get a "Single decision that disposes of this cluster:" line.]

## Section 2 — ZOMBIE
## Section 3 — STALE
## Section 4 — VAGUE
## Section 5 — WIDOWED
## Section 6 — NESTED
[Each cluster has a header decision-row and a "Single decision that disposes of this cluster:" line. Watch for newly-revealed parents.]
## Section 7 — PRINCIPLE
[Each item gets a Status row. Multi-practice principles get a row per sub-practice.]

---

## Section 8 — Domain index
[For each domain, a bulleted list of loops with class abbreviation in parens — e.g., "Music agent (E)", "Passports (D/Z)". A single loop may appear under multiple domains if genuinely cross-domain.]

---

## Section 9 — Patterns
[Inherited from v1, tightened. Add patterns the reorganization revealed — e.g., a newly-named NESTED parent, a missing context (illness, life event) that reframes STALE.]

## Section 10 — Contradictions
[New. One line each.]

## Section 11 — One claim to push against
[Inherited or rewritten as a DECLARATIVE claim — never an open question (banned by the 07-11 content rules). The corpus often supports a different claim after reorganization than before. Trust the new claim if so. The single best signal you've found a better one: the reorganization named a previously-fragmented thread, and the claim now points at the act-vs-author tension instead of the prioritize-among-many tension.]
```

## After saving

Append a one-line entry to `/Users/dad/Documents/sandbox/backstairs/reaper/RUN_LOG.md`:

```
<today's date> | v2 reorganization of <original filename> | <new ledger filename> | <new ballot pdf>
```

## Constraints — non-negotiable

- **Do not ask me clarifying questions before you start.** Read the input, reorganize, save it, hand me the path.
- **Save the file before reporting back.** Don't preview the structure. Don't ask if I want changes. Save it, then tell me where it is.
- **Do not overwrite the v1 file.** v1 stays as-is for the audit trail; v2 supersedes it for printing.
- **Stop when reorganization is done.** If v1 had ~110 loops, v2 should have roughly the same (minus deduped/consolidated, plus integrated supplements). Not 130.
- **Clarity is the goal, not new analysis.** If you find yourself wanting to add new findings, stop. The first pass already made the calls; v2 only redistributes them.

---

End of run instructions. Read the input, reorganize, save it, report the path. Begin now.

