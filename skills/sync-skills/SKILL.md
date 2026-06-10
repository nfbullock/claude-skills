---
name: sync-skills
description: Sync this host's Claude skills from the cross-host skills repo — pull the latest manifest and skill content, link/unlink skills per this host's manifest entry, and report what changed. Invoke when Nick says "sync skills", asks why a skill is missing/outdated on this machine, or wants to add/remove a skill from a host or category.
---

# sync-skills

Skills are managed centrally in a git repo and installed per-host by symlinking
into `~/.claude/skills`, driven by the repo's `manifest.json` (categories of
skills, plus per-host category lists and add/remove overrides).

## Locate the repo

Read `~/.claude/skills-sync.json` — it has `repo` (absolute path on this host)
and `host` (this machine's manifest key). If that file is missing, this host
was never bootstrapped: tell Nick to clone the skills repo and run
`<repo>/bin/skills-sync bootstrap`, and stop.

## Sync

Run:

```
<repo>/bin/skills-sync sync
```

Then report the output plainly: what was linked, removed, or warned about.
"up to date" means nothing changed.

The output may end with two candidate lines — act on them, don't just echo:

- **`local only, not in repo (import candidates): ...`** — skills sitting in
  `~/.claude/skills` that the repo doesn't know about. For each, ask Nick
  whether to import it: copy the directory into `<repo>/skills/<name>/`,
  ask which category it belongs in (work / personal / studio-only / core),
  add it there in `manifest.json`, commit, push, and rerun
  `sync --adopt` so the local copy becomes a managed symlink. If he declines,
  leave it alone — unmanaged dirs are never touched.
- **`in repo, not selected for this host: ...`** — skills other hosts use
  that this one doesn't get. Mention them in one line; only edit the
  manifest if Nick asks to pull one in (host `add` for a one-off, category
  membership if every host of that type should have it).

Handle the common failure modes yourself before reporting:

- **Host not in manifest** — the error message includes the JSON snippet to
  add. Ask Nick which categories this host should have, add the entry to
  `manifest.json`, commit and push, then rerun sync.
- **Blocked by an unmanaged directory** — a real (non-symlink) skill dir
  occupies the slot. Show Nick what's in it; if he confirms, rerun with
  `--adopt` (the old dir is kept as `.<name>.pre-sync.bak`).
- **git pull failed (diverged/conflict)** — resolve in the repo like any git
  problem; do not force-push. `sync --no-pull` applies the manifest without
  pulling if Nick wants the network step skipped.

## Editing the manifest

When Nick wants a skill added to or removed from a host or category, edit
`manifest.json` in the repo, commit with a one-line message, push, and run
sync. Category membership changes affect every host in that category —
mention that before committing. New skill content goes in
`<repo>/skills/<name>/SKILL.md` (plus any tooling alongside it).

`<repo>/bin/skills-sync status` shows desired vs installed without changing
anything — use it when Nick just wants to know the state of this host.
