# Reaper — Open Loop Sweep Prompt

This is a re-runnable prompt. Drop it into a fresh Claude Code window (or claude.ai with file/MCP access) any time you need to externalize the open loops your brain is currently carrying. The reaper exists because of memory issues, ENTP novelty pull, and a life that keeps interrupting itself. Externalize, classify, hand back a printable document.

**To re-run:** open a new Claude window with file access, paste everything below the line, hit go. Don't read the prompt to "get ready." The reading is the work the reaper does, not you.

---

# Reaper Sweep — Run Instructions

You are running a one-shot open-loop reaper for me (Nick). The deliverable is a single printable markdown document I will mark up with a pen. This is a comprehensive sweep, not a sample. Be exhaustive within the sources you have, and be organized so the exhaustiveness is usable rather than overwhelming.

I have memory issues, an ENTP-style appetite for new threads, and a life that keeps generating distractions. I cannot trust my head to remember what I committed to. The reaper is one of the externalization tools I depend on. Treat this with the seriousness of cognitive infrastructure, not a tidy-up chore.

## What an open loop is, for this sweep

An open loop, in David Allen's sense, is anything I have either explicitly committed to or implicitly hung onto, that has not been completed and has not been formally declined. It uses cognitive load even when I'm not looking at it.

A loop is *not* the same as an active project. An active project that is moving forward on its own does not need the reaper's attention. The reaper is interested in: stale projects, abandoned-but-not-archived files, half-written specs, recurring "I should…" thoughts that show up in chat history, Things 3 tasks older than 60 days that haven't moved, notes that have been edited once and never touched again, and intentions I've voiced multiple times across sources without converting them into action.

If you are uncertain whether something is a loop, surface it. The cost of a false positive (I cross it off in pen) is trivial. The cost of a false negative (the loop keeps eating cognition) is high.

## Sources to read — exhaustive

In priority order. Read all of them. If a source isn't accessible, note that clearly in the output and proceed.

### 0. STATE.md — read this first

Before any other source, read **`/Users/dad/Documents/sandbox/projects/STATE.md`** in full. It is the orientation surface: what's active, what's foundational, what's on the shelf, what's been killed, and the Things 3 CRUD recipe Claude has access to. The reaper's first job is to know the map before it starts walking.

The reaper itself is responsible for keeping STATE.md current. At the end of the run, update STATE.md to reflect any structural changes the sweep surfaces — new projects, projects promoted/demoted, projects archived, lifecycle moves. STATE.md is the agent-facing doppelgänger of the printable output; it survives between runs while the printable is consumed.

**Inter-reaper updates section.** STATE.md has an `## Inter-reaper updates` section near the top where Claude appends material changes between reaper runs (new skills, new conventions, structural rules). At the end of *this* run, **fold those entries into the canonical body of STATE.md** (move skill notes into the skills section, lifecycle moves into the active/someday/archive sections, etc.) and **clear the Inter-reaper updates section** so it's empty for the next inter-run window. The append-only outlet exists so STATE.md doesn't drift between sweeps; the reaper's job at run-end is to integrate and reset.

### 1. Obsidian vault

Root: `/Users/dad/Documents/sandbox/projects/`

Read the **entire vault**, not just one subdirectory. **Hard requirement, in this order:**

1. **First**, run `ls /Users/dad/Documents/sandbox/projects/` and capture the exact list of top-level entries. Names with spaces are real — `formative identity/` and `the great courses/` count.
2. **Second**, before producing the final document, you MUST output a one-line scan-roster of the form:
   `Vault top-level: [a, b, c, ...]   Walked: [a, b, c, ...]   Skipped: [name — reason]`
   The two lists must match, or every entry in `Skipped` must have a written reason. A scan that lists fewer entries in `Walked` than `ls` returned, with no `Skipped` accounting, is an incomplete scan and you must redo it before continuing. This step is non-negotiable; past sweeps have missed `formative identity/` despite this prompt and produced a Supplement B to recover. The roster step exists to make that failure mode impossible.
3. **Third**, walk every entry in the roster.

Within each top-level folder:

- Every `README.md` in every folder.
- Every single-file `.md` at any depth.
- Every `TODO.md`, `PLAN.md`, `FUTURE_PROJECTS.md`, `LEARNINGS.md`, `state.md`, `JOURNAL.md`, or similarly-named planning artifact.
- Mind map photo transcriptions if present (e.g., `mindmap_*.md` in the root).
- For folders that look like deep multi-file projects (10+ markdown files all on one theme — e.g., `formative identity/`, `the great courses/`, `music/op1f/`), read the master/playbook/index file in full, not just the headline. Action items and dated commitments often live three files deep.

The strategic-review document at `inbox/reference/projects-strategic-review-2026-04-13.md` is **context, not gospel**. It is one prior pass at this same problem. Read it to see what was previously flagged for cut/archive — if something it flagged is still alive, that's a loop the previous sweep failed to close, which is high-signal. Do not defer to it.

#### Lifecycle and frontmatter awareness

The vault uses lifecycle folders (`inbox/`, `someday/`, `archive/`, `reference/`) plus per-project frontmatter as a first-class signal. The reaper must respect both.

- **Skip every file inside `someday/` and `archive/`.** Also skip any markdown file whose frontmatter contains `status: someday` or `status: archived`. These are deliberately on the shelf — surfacing them as STALE is noise. Mention once at the top of the output that these folders were skipped.
- **Read `activity_log:` frontmatter from each project's README.** Shape:
  ```yaml
  ---
  status: active
  priorities: [music, family]
  activity_log: lessons/
  activity_threshold: 30d
  foundational: true   # optional
  ---
  ```
  Before flagging a project as STALE, check the `activity_log:` path. If any file under that path was modified within `activity_threshold` (default 30 days), the project is **active** regardless of how stale individual files look. "Active project with stale subfiles" is a separate flag, not a STALE finding.
- **If a project has no `activity_log:` declared**, eyeball recent file mtimes across the directory before flagging stale. Default to a 30-day mtime check across the whole directory.
- **`reference/` is not a project tree.** No activity log expected. Don't surface reference docs as STALE for being old; staleness is a property of intent-to-act, not of reference material.
- **Foundational projects (frontmatter `foundational: true`)** get extra scrutiny. If a foundational project's activity log is empty or stale, that is load-bearing news, not a footnote. Surface it near the top of the output with a clear "foundational project at risk" flag.

### 2. Claude conversation history

Standard locations on macOS to check (read whichever exist):

- `~/Library/Application Support/Claude/` — Claude desktop app data, sessions, transcripts.
- `~/Library/Application Support/Claude/local-agent-mode-sessions/` — Cowork mode session transcripts (these are richest, since they include tool calls and file edits).
- `~/.claude/projects/` and `~/.claude/history/` — Claude Code conversation history (one JSONL file per session, named by project path).
- `~/.config/claude/` and `~/.local/share/claude/` — alternate config locations.
- **`/Users/dad/Documents/sandbox/projects/claude_skills/reaper/sources/claude_ai_exports/`** — manual claude.ai exports. Read the **freshest `.zip` by mtime** (older zips are kept for audit but only the latest is scanned). If the directory is empty, note that the user has not done a recent claude.ai export and proceed.
- `~/Downloads/` only as a fallback if `sources/claude_ai_exports/` is empty — any `*conversations*.json` or `*claude*export*` files I may have downloaded from claude.ai but not yet moved into `sources/`.

For each readable transcript, scan for any sentence I (the user side, not Claude) said matching: "I should", "I need to", "I want to build", "I keep meaning to", "remind me to", "let me know when", "follow up on", "TODO", "I'll come back to", "next time", "eventually", "one of these days", "I've been meaning to", "I keep saying I'll", or any future-tense first-person commitment. Pull the surrounding 3–5 lines so the context is reconstructable.

Also scan for **abandoned threads** — conversations where I started a real piece of work and never returned (e.g., a project bootstrap that never got a follow-up session, a script we drafted that I never asked for again). Those are a different kind of loop and they belong in the sweep.

### 3. Things 3

Standard path: `~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/ThingsData-*/Things Database.thingsdatabase/main.sqlite`

If sqlite is hard, fall back to the Things URL scheme (`things:///show?id=...`) or AppleScript (`tell application "Things3"`) to dump tasks programmatically.

**Skip the Things "Recurring" project entirely.** Recurrence is its own status surface; surfacing car-wash tasks as stale is noise. Mention once at the top of the output that Recurring was skipped, and proceed.

For every task in **Inbox, Today, Upcoming, Anytime, Someday, Logbook (only the last 30 days for context), and every Project/Area**, capture: title, area/project name, created date, last-modified date, due date, completion status, notes field, and tag list.

The Logbook scan is for context only — if a task was just completed, it's not a loop. But its presence helps you recognize patterns (e.g., recurring loops I keep completing instances of without retiring the parent intention).

### 4. Memory files (if accessible)

`~/Library/Application Support/Claude/local-agent-mode-sessions/*/spaces/*/memory/MEMORY.md` and the individual memory files it indexes. These contain prior cross-session context — sometimes including loops I've explicitly asked to be remembered.

## Cross-source dedup

Many loops will appear in multiple sources. "Build a music agent" might be a Things task, a vault folder, AND a chat history thread. Treat that as **one loop with three pointers**, not three loops. The cross-reference is itself signal — multi-source loops are higher-priority for surfacing.

## Priority lens

The five priorities are **formative-identity · music · family · consistency · health**. They are the lens, not the taxonomy.

- For every KEEP, name which priority (or priorities, max two) it serves.
- KEEPs that don't connect to any of the five get flagged explicitly: `KEEP? — does not connect to any of the five priorities. Reconsider as KILL or RESHAPE.`
- Project-level `priorities: [...]` frontmatter declares which lenses a project sits under. Use those declarations as primary; infer for loose loops.
- The lens is queryable, not directory-shaped. A loop can serve `[music, family]` simultaneously without belonging to a single home. Don't force a primary domain when the loop genuinely sits across two.

## Classification taxonomy

Assign exactly one classification to each loop. The classification controls which section of the print-out it lives in.

- **STALE** — was once active, hasn't been touched in 60+ days, no clear blocker. The default classification for most surfaced loops. Candidate for reaping or revival.
- **ZOMBIE** — has been "in progress" for 6+ months, with periodic activity but no completion. Worse than stale because it's masquerading as alive. The activity is performance, not progress.
- **VAGUE** — exists as a loop but the next action is undefined. Either I write a next action in pen or it gets killed.
- **WIDOWED** — the original person, project, or context the loop was attached to no longer exists or is no longer relevant. The loop hasn't been told.
- **NESTED** — actually a sub-loop of a larger loop I haven't named explicitly. Group these by inferred parent.
- **PRINCIPLE** — not a task at all. A recurring intention I keep restating in different forms across sources. These belong in a principles or north-star file, not on a task surface. The reaper evicts them from the task list and recommends a destination.
- **ECHO** — appears identically in 3+ sources, indicating I keep externalizing the same thought without acting. These need their own attention because the re-externalization is the symptom of an avoided decision.

**ALIVE** loops (recent activity, currently being worked on, moving forward) do **not** appear in the print-out unless they are at risk of stalling — in which case classify as STALE with a note.

## Output format

A single markdown document. Save to:
**`/Users/dad/Documents/sandbox/projects/artifacts/reaper/<YYYY-MM-DD>/reaper_<YYYY-MM-DD>.md`**

Create the dated artifacts directory if it doesn't exist. If a file with today's date already exists, append `_v2`, `_v3`, etc. — never overwrite a prior sweep.

Designed for printing on letter paper and pen markup. Plain formatting only. No emoji. No tables (they print poorly with pen markup). Generous whitespace.

### Document structure

```
# Reaper Sweep — [YYYY-MM-DD]

## Sources read
- Vault: [path] — N folders, M markdown files scanned, K loops surfaced
- Claude history: [paths checked, which existed, N conversations scanned, K loops surfaced]
- Things 3: [path or method, N tasks scanned across which lists, K loops surfaced]
- Memory: [path, status]
- Skipped: [anything that was unreachable, with the reason]

## Counts
- Total loops surfaced: N
- STALE: N | ZOMBIE: N | VAGUE: N | WIDOWED: N | NESTED: N | PRINCIPLE: N | ECHO: N
- Cross-source loops (appear in 2+ sources): N

---

## Section 1 — ECHO  (recurring across sources — the thoughts I keep re-externalizing)

[List ECHO loops first because they're the most diagnostic. For each:]

  [ ] KEEP   [ ] KILL   [ ] RESHAPE   [ ] DEFER

  Title:           ___________________________________________
  Sources:         [list all locations — vault path, Things project, chat date]
  Times restated:  N
  Original frame:  [one line]
  What I keep saying about it: [one line summarizing the recurring phrasing]

  Notes: ________________________________________________________
         ________________________________________________________

  ---

## Section 2 — ZOMBIE  (active but never finishing)
[same item format]

## Section 3 — STALE  (60+ days, no clear blocker)
[same item format]

## Section 4 — VAGUE  (exists, no next action)
[same item format, plus a "Next action if kept:" line for me to fill in]

## Section 5 — WIDOWED  (orphaned context)
[same item format, plus a "Original context:" line]

## Section 6 — NESTED  (sub-loops of unnamed parents)
[Group by inferred parent. Each group gets a header that names the parent. Then list the sub-loops underneath in the standard item format.]

## Section 7 — PRINCIPLE  (not tasks — evict to where?)
[same item format, plus a "Suggested destination:" line — e.g., a specific principles file in the vault]

---

## Section 8 — Patterns I noticed across the corpus

Brief prose. 4–8 observations max. Things to surface:
- Recurring themes across sources (what kinds of loops keep showing up?)
- Topics where I keep promising action but the action never arrives
- Areas where the vault has a folder but Things 3 has no tasks (or vice versa) — i.e., places where my externalization stack is internally inconsistent
- Loops that point to a missing project, a missing principle, or a real-world change I haven't named yet
- Anything that surprised you while reading the corpus

## Section 9 — Comparison with prior sweeps

If `/Users/dad/Documents/sandbox/projects/artifacts/reaper/` already contains prior reaper outputs, do a brief diff:
- Which loops from the last sweep are still here, unchanged?
- Which were resolved (no longer present in any source)?
- Which are new since the last sweep?

If this is the first sweep, say so and skip this section.

## Section 10 — One question to sit with

A single open question for me, in pen-friendly format with five blank lines underneath. Not a prescription. The question the corpus seems to be asking me right now.
```

## Numbering and homogenization

- **Number every decision item sequentially and globally** (`#1..#N`). Continue the numbering through every section. Walkthroughs after the sweep reference items by number, so the numbers must be unique across the document. Restart from #1 each new sweep.
- **Surface duplicates with their canonical home up front, with the duplicate marked KILL by default.** Format example:
  > #47 KILL (duplicate of #1) — "Find a therapist" Things task. Canonical home: #1 IFS consult.
  Do not require the user to re-decide a duplicate. The first instance is canonical; subsequent matches are auto-KILL with a pointer.
- **Cross-source loops still get one entry**, per the existing dedup rule. Numbering and dedup interact: a multi-source loop has one number; a same-text-different-task duplicate has its own number marked KILL.

## Constraints — non-negotiable

- **Page breaks before each section header.** I want to spread the print-out across a desk and work on one section at a time. Use markdown's standard convention: `\n\n---\n\n` before each `## Section N` header (these will translate to page breaks in most PDF/print renderers; if the renderer needs explicit `<div style="page-break-before: always;"></div>`, include those instead).
- **No truncation by default.** I asked for exhaustive. If a section has 80 items, list 80 items. If it has 200, list 200. The exception: ECHO loops should be listed exhaustively no matter how many; STALE/ZOMBIE can be capped at 100 per section if absolutely necessary, with the cap noted.
- **Cross-reference, don't duplicate.** A loop that appears in three sources gets one entry with three source pointers, not three entries.
- **Be honest about uncertainty.** If you can't tell whether something is STALE or ZOMBIE, mark it STALE and note the ambiguity in the Notes line. Better to surface than to mis-classify silently.
- **No emoji. No tables. No bold paragraphs. Plain text inside sections.** The document must be readable as printed paper, not just as rendered markdown on screen.
- **Generous vertical whitespace.** Each loop needs room for me to write notes in pen. The Notes line is two underscored blank lines minimum.
- **Do not ask me clarifying questions before you start.** Read the sources, build the document, save it, hand me the path. The reaper is not interactive.
- **Save the file before reporting back.** Don't preview the structure. Don't ask if I want changes. Save it, then tell me where it is.
- **At the end, append a one-line `last_run` entry to `/Users/dad/Documents/sandbox/projects/claude_skills/reaper/RUN_LOG.md`** — date, total loops surfaced, output path. Create the file if it doesn't exist. This is so I can see the rhythm of how often I'm running the reaper.
- **Do NOT produce supplements (Supplement A, B, etc.).** If you discover mid-sweep that you missed a source or a folder, go back and fold those loops into the appropriate class sections before producing the final document. The supplement format is a smell — it means the first pass left work for the second pass to do. The vault scan-roster step (above) is designed to make the most common cause of this impossible. If something else slips through, integrate it; do not append it.

## What the reaper is NOT

- Not a planner. Don't propose an order or priority for what to work on after.
- Not a coach. Don't suggest I "consider" anything. Surface, classify, hand back.
- Not a system migration. Don't tell me to move things from Things 3 to Obsidian or vice versa. Sort what's there.
- Not an inbox triage. The Things 3 inbox is one source among several, not the focus.
- Not a daily habit. The reaper should not be run more than every 2–4 weeks. If the RUN_LOG shows it was run within the last 14 days, output a single line saying "Last sweep was N days ago. Are you sure?" and stop, unless I confirm.
- Not exhaustive *of conversation* — exhaustive *of loops*. If a chat thread has eight forward commitments and they're all the same loop, that's one entry, not eight.

## Companion to the mind map

This sweep is the operational arm of the "program? reapers (tasks?)" bubble in the mind map at `/Users/dad/Documents/sandbox/projects/mindmap_2026-05-01.md`. When I bring a marked-up print-out back, the loops marked KILL get killed (deleted from sources), KEEP gets a next-action assigned, RESHAPE gets re-scoped, DEFER gets a date and a calendar event. That follow-through is mine, not yours.

---

End of run instructions. Read the sources, build the document, save it, report the path. Begin now.
