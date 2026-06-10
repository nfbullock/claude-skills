---
name: things
description: Read and write Things 3 from any conversation. Things plays two roles only — capture device (raw inbox) and next-actions holder. Project work and knowledge live in the vault, not Things. Three workflows — (1) **triage pass**: dispose inbox items as KILL / NEXT-ACTION (with context tags + Things-project rule) / MOVE-TO-VAULT (with target file). (2) **discuss-a-task**: when Nick says "I want to talk about [task]," find it, walk him through context, then modify the task (title rewrite + notes append) AND generate something additional (vault file / subtasks / rich notes). (3) **capture**: raw add, no taxonomy. Auto-trigger on natural phrasing — Nick rarely says "skill."
status: active
---

# /things

The Things 3 surface for Claude. Two integration points:

- **Capture** — drop something into the inbox from anywhere, fast, raw, no taxonomy.
- **Triage** — periodically read the capture pile and decide where each item actually belongs (Things as next-action, vault as project material, or trash). The triage pass is the load-bearing workflow — it's how task management, project management, and knowledge base maintenance stay integrated.

## Things' role (and what it is NOT)

Things 3 holds **two kinds of items only**:

1. **Raw captures** in the inbox — random thoughts that haven't been triaged yet.
2. **Atomic next-actions** — single concrete doable things, with or without a project. Examples: "call X," "buy Y," "stage PR Z."

Things does **not** hold the full action set for any project. That lives in the vault (e.g., `projects/<name>/log.md`, lesson files, etc.). A project may have *one or two* of its next-actions surfaced in Things, but the bulk of project work is in the vault. This is intentional — Things stays small and operational; the vault stays canonical.

**Tags at disposition, not capture.** Capture is raw — never tag on `add`. Contexts get assigned when an item *survives triage* and becomes a NEXT-ACTION (i.e., it leaves Inbox for Today/Anytime). The vocabulary is GTD-style and intentionally small:

- `home` — at the house, hands-on
- `office` — needs the office (hybrid days)
- `errand` — physical-world, requires going somewhere
- `phone` — call to make
- `computer` — needs desk + machine
- `5min` — sub-5-minute quick win (use sparingly — only when the action is genuinely that short)
- `waiting` — waiting on someone else

Multiple tags are OK (e.g., `office, computer` for work coding). Don't mint new context tags — propose to Nick first if a real gap appears. The earlier vestigial set (`Errand / Home / Important / Pending`) was retired 2026-05-07.

## When to invoke

Auto-trigger on natural phrasing — Nick rarely names skills.

**Capture**
- "add a task: …"
- "remind me to …"
- "todo: …"
- "throw that in things"
- "queue that up"

**Read / triage**
- "help me organize my inbox" / "let's triage" → the headline workflow
- "what's in things for [topic]"
- "what's on my plate today / this week"
- "what's overdue"
- "what did I add recently"

If a phrase is ambiguous (Nick said "I should …" rather than "add this"), confirm before capturing.

## Capture path

```bash
~/venv/default/bin/python /Users/dad/Documents/sandbox/projects/claude_skills/things/things.py add \
    --title "..." [--when today|tomorrow|anytime|someday|YYYY-MM-DD] \
    [--deadline YYYY-MM-DD] [--notes "..."] [--dry-run]
```

Default behavior: **no tag, no list, no when**. The item lands in the Inbox raw. That's the point — capture should be friction-free, and the triage pass is where the thinking happens. Context tags get applied later, at disposition.

**Never pass `--when anytime` on capture.** Nick does not want captures landing in Anytime — that bucket is for items that have *survived triage*. A raw capture goes to Inbox, full stop. Omit `--when` entirely; do not "helpfully" route it to Anytime.

Override only when Nick explicitly says so:
- "schedule for Tuesday" → `--when 2026-05-12`
- "deadline Friday" → `--deadline 2026-05-08`
- Notes for context only when Nick provides them — don't invent.

## Triage path (the headline workflow)

Trigger: "help me organize my inbox," "let's triage," "process my captures."

### Steps

1. **Pull the pile**:
   ```bash
   ~/venv/default/bin/python .../things.py inbox
   ```
2. **Read every item**. Don't dump the JSON to Nick — synthesize.
3. **For each item, propose ONE of three dispositions**:

   **NEXT-ACTION** — atomic, doable, belongs in Things.
   - State the action concretely (rewrite the title if vague).
   - Suggest list/when if obvious ("this is a Today thing").
   - **Assign context tag(s)** from the vocabulary above (`home`, `office`, `errand`, `phone`, `computer`, `5min`, `waiting`). Multiple tags OK. This is the disposition step where contexts get applied.
   - **Things project assignment rule**:
     - If the item has a *vault-project home* (e.g., the action serves `formative identity/`, `health/`, `music/`, `food/`, `the great courses/`, etc.) → **no Things project**. The vault is its source of truth; Things just holds the action.
     - If the item is genuinely vault-orphaned (no vault project would house it) → assign to the appropriate Things project: `Atomic` for one-offs, `Work` for professional development, `house` for home maintenance.
     - Things projects are visual buckets for *Things-only* items, not mirrors of vault projects.
   - This is for *truly* atomic items. "Think about X" is never a next-action.

   **MOVE-TO-VAULT** — project material, idea, observation, reference. Belongs in the vault.
   - Name the target file: `projects/<name>/log.md`, a new doc under a project, or a known location.
   - State *what to write* (1–3 sentences, the kernel of the captured thought).
   - This is the painful step — it forces "which project does this serve?" and "what does this mean once filed?"

   **KILL** — noise, duplicate, dead idea, no longer relevant.
   - Just say so. One-line reason if it's not obvious.

4. **Present terse and grouped**, not as a JSON dump:
   ```
   Inbox triage — N items

   NEXT-ACTION (n)
     - "<rewritten title>" → today
     ...

   MOVE-TO-VAULT (n)
     - "<title>" → projects/formative identity/log.md
       Write: <one-line kernel>
     ...

   KILL (n)
     - "<title>" — <one-line reason or blank>
   ```

5. **Wait for Nick's call** before doing anything. He may accept all, override individual items, or reshape categories.

6. **Execute the accepted MOVE-TO-VAULT writes** (Edit/Write into the named files). Then tell Nick exactly which Things items to mark done in-app — `things.py` v1 has no update/delete, so you don't close the loop in Things automatically.

### Pattern guidance for the dispositions

- The five priorities are the routing lens: **formative-identity · music · family · consistency · health**. Items often map cleanly to one project; trust the mapping and check `projects/<name>/README.md` for the right log path if unsure.
- A capture older than ~30 days that hasn't been triaged is usually a KILL, not a MOVE. If it had a clear home, it would have moved by now.
- A capture phrased as a vague directive ("look into X," "think about Y") is rarely a next-action. Either MOVE it (the *content* is the value, not the doing) or rewrite it as a concrete first step.
- Duplicates: pick the better-phrased one, KILL the other.

## The discuss-a-task workflow

Trigger phrases — auto-fire on any of these:
- "I want to talk about [task / item from my todo / something in things]"
- "let's discuss [task]"
- "let's flesh out [task]"
- "tell me about [task in things]"
- "I want to think through [task]"

The workflow's contract: **a discussion always produces (a) a modification of the Things task and (b) something additional.** A discussion that ends without a write to Things is incomplete — Nick's signaling that the task is currently underspecified, and the conversation's job is to specify it.

### Steps

1. **Find the task.**
   ```bash
   ~/venv/default/bin/python .../things.py search "<keywords from Nick's phrasing>"
   ```
   If multiple matches, list them and ask which. If zero matches, broaden the query or ask Nick for more.

2. **Pull current state.** From the search result, you have title, notes, tags, project, age. Read the notes carefully — they often hold the kernel of why this task got captured.

3. **Walk through context.** Open conversation. Ask the questions that move the task from vague-to-concrete:
   - What's the actual outcome you want?
   - What's blocked / what's the first move?
   - Which project (vault) does this serve, if any?
   - Who else is involved?
   - What's the right context (`@home`, `@office`, etc.)?
   - Is this one task, or is it actually a sequence?

   Don't interrogate. Listen. Reflect back what you're hearing.

4. **At the end, do BOTH:**

   **a) Modify the task** via `things.py update`:
   - **Rewrite the title** for concreteness if the original was vague (e.g., "Stage PR Claude code prompt" → "Build `make stage-pr` for [repo] — Claude -p invocation that reviews staged PR and posts feedback").
   - **Append notes** with a tight summary of what the conversation surfaced (use `--add-notes`). Don't dump the whole transcript; capture the kernel: outcome, first move, constraints. 3–8 lines is right.
   - **Update tags / project** if the conversation changed where it belongs.

   ```bash
   ~/venv/default/bin/python .../things.py update --id <UUID> \
     --title "<rewritten title>" \
     --add-notes "<conversation kernel>" \
     --tag <ctx1> --tag <ctx2>
   ```

   **b) Generate something additional** — pick whichever fits what came out:
   - **Vault file**: if the conversation surfaced project material (a plan, a design, an idea worth persisting), write it to the right vault location. Examples: a sequence of sessions for `letter-to-dad/letter.md`; a design sketch in `someday/<project>.md` for a meta-project idea; an entry appended to `<project>/log.md`.
   - **Spawned subtasks**: if the conversation revealed a sequence (this isn't ONE task, it's three), `things.py add` the additional concrete actions. Original task becomes the orchestrating one.
   - **Rich notes only**: if the discussion was pure clarification with no project material to persist, the notes append + title rewrite IS the artifact. That's a valid "additional" — what was missing was just precision.

5. **Tell Nick what changed.** One paragraph: title before/after, what got added to notes, what additional artifact landed (file path, or new task UUIDs). He can redirect.

### Why this exists

Things' inbox + Today are full of items captured at low resolution — they're the residue of moments where Nick had a thought but no time to think it through. When he says "let's talk about X," he's making time. The workflow's job is to make sure the discussion *moves the work forward in the system*, not just in his head — so the next time he sees the task, it's specified, contextually placed, and either smaller (a clear next move) or bigger-but-decomposed (no longer a fog).

## Project-mode read

When Nick is working inside `projects/<name>/` and asks "what's in things for this," pull *only the items he's surfaced as next-actions for this work* — not "everything tagged X." Two paths:

- If a Things 3 project exists with a matching name: `things.py project "<Project Name>"`
- Otherwise: `things.py inbox` and `things.py today`, then filter mentally for items obviously related to the project context.

The vault is canonical for "what should I work on in this project." Things is just where one or two atomic next-actions get parked when they need to surface in Today.

## CLI shape (full reference)

All commands print JSON. Path:

```
~/venv/default/bin/python /Users/dad/Documents/sandbox/projects/claude_skills/things/things.py <cmd>
```

**Read** (sqlite, read-only — fast, no permission prompt, may lag in-app edits by a few seconds):

| Command | Returns |
|---|---|
| `inbox` | open tasks with `start = 0`, newest first |
| `today` | open tasks in the Today/Evening bucket |
| `anytime` | open tasks in the Anytime bucket |
| `someday` | open tasks in the Someday bucket |
| `overdue` | tasks with deadline before today |
| `recent --days N` | tasks created in the last N days (default 7) |
| `tag <name>` | open tasks with that tag |
| `project <name>` | open tasks in a Things 3 project (matches by title) |
| `search <query>` | fuzzy match across title + notes of all open tasks (used by the discuss-a-task workflow) |
| `tags` | list of all tag titles |
| `projects` | list of all open Things 3 project titles |

Each task record includes: title, notes, age in days, scheduled date, deadline, tags, project, area, created/modified date.

**Write** (URL scheme via `open` — instant, no permission prompt):

```bash
things.py add --title "..." [--tag X]... [--list ProjectName] \
              [--when today|tomorrow|anytime|someday|YYYY-MM-DD] \
              [--deadline YYYY-MM-DD] [--notes "..."] [--dry-run]
```

`--tag` exists for completeness but is not used by default. `--list` routes to a Things 3 project (case-sensitive title match in Things). `--dry-run` prints the URL without opening it.

**Update** (AppleScript wrapper, automation permission already granted):

```bash
things.py update --id <UUID> [--title "..."] [--add-notes "..."] [--notes "..."] [--tag X --tag Y]
```

`--add-notes` appends to existing notes (with a paragraph break); `--notes` replaces entirely. `--tag` is repeatable; passing any `--tag` replaces the whole tag list. Used by the discuss-a-task workflow.

For deletion, completion, and re-bucketing (which `things.py` doesn't yet wrap as subcommands), use the AppleScript patterns documented below.

### AppleScript patterns that work (reference for re-bucketing passes)

- **Complete a task**: `set status of to do id "..." to completed`
- **Trash a task**: `move to do id "..." to list "Trash"`
- **Set tags**: `set tag names of to do id "..." to "tag1, tag2"`
- **Assign to a Things project**: `set project of to do id "..." to project id "<project-uuid>"`
- **Detach from project (un-project)**: Things won't accept `missing value` directly. Two-step:
  1. `move to do id "..." to list "Inbox"` — detaches project
  2. `move to do id "..." to list "Today"` (or wherever it should land) — restores bucket
- **Restore from trash**: `move to do id "..." to list "Inbox"`

## What this skill does NOT do (yet)

- No update / delete / mark-done. AppleScript path. Add later if the friction is real.
- No recurring task creation (URL scheme limitation).
- No automatic action on triage suggestions in Things — Claude writes vault files when accepted, but you mark Things items done.

## Notes

- Sqlite DB: `~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/ThingsData-OQ3NJ/Things Database.thingsdatabase/main.sqlite`. Read-only via `?mode=ro&immutable=1`.
- Things 3 packs scheduled date / deadline as `(year<<16) | (month<<12) | (day<<7) | flags`. Decoder lives in `things.py`. Off-by-one is flag-bit noise, not a bug.
- `/projects-status` has a stale `things_today()` query in its `scan.py`. Once the new skill has soaked, swap that call to shell out to `things.py today`.

## Files

- `things.py` — the CLI. Read via sqlite, write via URL scheme.
- `SKILL.md` — this file.
