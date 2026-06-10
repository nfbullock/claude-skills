---
name: skills-status
description: Lightweight status scan over the centralized skills repo (the cross-host home of all Claude skills). Reads SKILL.md frontmatter for each skill, buckets by status (active / stub / stale stub / deprecated / no metadata), surfaces stubs that haven't moved past the staleness threshold, and shows each skill's manifest category (uncategorized = no host receives it). Invoke as /skills-status for the sweep, or `/skills-status <skill>` to scope a single-skill conversation that auto-routes to bootstrap / develop / refine / cleanup. Sibling to /projects-status — same shape, different domain.
status: active
---

# /skills-status

Status check for the skills ecosystem. Active skills stay quiet; stubs that haven't been developed get yelled about.

## What this skill does

1. Walks `<skills repo>/skills/*/SKILL.md` (the scan script lives in the
   repo and derives the root from its own location — no host paths).
2. Reads frontmatter (`name`, `status`, `description`) and each skill's
   manifest category.
3. Computes `days_since_touched` from git history (last commit touching the
   skill); uncommitted edits count as today and set `dirty: true`.
4. Buckets each skill:
   - **active** — `status: active`. Working skill. Show count + name only, no fuss.
   - **stub** — `status: stub`, touched within threshold. Surface so it stays on radar.
   - **stale stub** — `status: stub`, untouched for >30d. Yell. Either develop it, retire it, or relax expectations.
   - **deprecated** — `status: deprecated`. Suggest cleanup.
   - **no status / no frontmatter** — SKILL.md exists but doesn't declare status. Retrofit needed.
   - **no SKILL.md** — directory in claude_skills/ but missing SKILL.md. Broken.

## How to invoke

When Nick types `/skills-status`, run the scan and report. The repo path is
in `~/.claude/skills-sync.json` (key `repo`); the scanner is stdlib-only, so
plain `python3` works on any host:

```bash
python3 "<repo>/skills/skills-status/scan.py"
```

It prints JSON. Format the output for Nick like this (terse, scannable):

```
skills/ status — YYYY-MM-DD

ACTIVE (n)
  - skill — last touched Xd ago
  ...

STUB (n)
  - skill — Xd since touched — develop, retire, or relax expectations
  ...

STALE STUB (n)  ← stub > 30d, hasn't moved
  - skill — Xd silent — yell-louder bucket
  ...

NO STATUS (n)  ← SKILL.md exists, status field missing
  - skill — retrofit frontmatter
  ...

NO SKILL.md (n)  ← directory exists, SKILL.md missing
  - skill — broken
  ...
```

Skip empty buckets. If everything is `active`, just print:

```
skills/ status — YYYY-MM-DD

ACTIVE (n)
  - skill — Xd ago
  ...

(no stubs, no retrofit needed)
```

## Parameterized mode — `/skills-status <skill>`

When Nick invokes the skill with an arg, scope the conversation to that one skill. Same intent as `/projects-status <project>` — single-command entry point that auto-routes.

Run the scan with the target as a positional arg:

```bash
python3 "<repo>/skills/skills-status/scan.py" "<skill name>"
```

Returns:

- `name_resolution`: `{ input, resolved, candidates, ambiguous, not_found }`
- `route`: one of `bootstrap_greenfield` | `bootstrap` | `develop` | `refine` | `cleanup`
- `confidence`: `confident` | `borderline`
- `reasons`: short list explaining the route
- `frontmatter`, `skill_md_text`, `file_listing`, `scan_py_preview` (if present), `days_since_touched`

### Step 1 — handle the resolution result

- **`not_found: true`** with no candidates → confirm Nick wants a brand-new skill, then run **bootstrap-greenfield**.
- **`not_found: true`** with fuzzy candidates → ask "did you mean &lt;X&gt;?" before doing anything.
- **`ambiguous: true`** → ask which substring match Nick meant.
- **`resolved`** set → proceed.

### Step 2 — confirm the route if borderline

If `confidence: confident`, announce in one line and proceed. If `borderline`, name the route + reason in one sentence and confirm before executing.

### Step 3 — run the matching sub-flow

#### Route: `bootstrap_greenfield` (skill doesn't exist yet)

Nick is starting a new skill.

1. Ask: what does the skill do, in one sentence? What triggers it (slash command only, or natural-language phrasing)? Does it need a `scan.py` / helper, or is it pure prose?
2. Create `<repo>/skills/<name>/` (`make new NAME=<name>` scaffolds it) and write a minimal `SKILL.md` with frontmatter:
   ```yaml
   ---
   name: <name>
   description: <one-sentence description that doubles as trigger guidance>
   status: stub
   ---
   ```
   plus a "What this skill does" stub body and a "Files" footer.
3. If a helper is needed, create an empty `scan.py` (or equivalent) so the directory has the shape the skill will eventually have.
4. Add the skill to a manifest category (`bin/categorize <name>` or edit `manifest.json`) — uncategorized skills install nowhere — then commit and run sync.
5. Remind Nick the skill is a `stub` — it'll surface in `/skills-status` until status flips to `active`.

#### Route: `bootstrap` (directory exists, SKILL.md missing or no frontmatter)

Same as greenfield but in-place — read what's there, fill in the missing pieces, write the frontmatter.

#### Route: `develop` (status: stub)

The skill exists but isn't done.

1. Read the full `skill_md_text` (already in payload) and any helper-script preview.
2. Two questions:
   - **What's still missing to flip this to `active`?** (Could be: prose workflow, helper script, trigger conditions tightened, an output-format decision.)
   - **What's the smallest concrete delivery that closes the gap?**
3. Implement the smallest delivery — edit SKILL.md, write/edit the helper. Don't over-build; one increment at a time.
4. If Nick decides the increment is enough to flip to `active`, update the `status:` field. Otherwise leave as `stub`.

#### Route: `refine` (status: active)

Open-ended conversation about a working skill — what's not working, what should change, what edge cases have come up. Nick is the driver here; just hold the context and react. Read `skill_md_text` and any helper preview to ground the conversation.

If a refinement lands, edit SKILL.md or the helper. Don't change `status:`.

#### Route: `cleanup` (status: deprecated)

The skill is on its way out. Ask: delete entirely, archive (move somewhere, leave a tombstone), or revive? Apply the decision — and if revive, flip to `stub` and route to `develop`.

### When to stop

If the route turns out wrong (e.g., Nick says "no, I want to refine, not develop"), pivot. The classifier is a starting point.

## What this skill does NOT do

- It does not write to anything. Read-only.
- It does not flip status fields automatically. Nick decides when a stub graduates to active.
- It does not invoke other skills.
- It does not yell about active skills going stale by mtime — an active skill that hasn't been touched in 6 months can be perfectly fine. Only stubs are surfaced for staleness.

## Sibling tool

`/projects-status` does the same thing for `projects/` root. Same general shape (scan → bucket → terse report), different domain. If both are showing the same items three weeks running, the reaper is overdue.

## Files

- `scan.py` — the scan script. Reads frontmatter, walks skill dirs, outputs JSON.
- `SKILL.md` — this file.
