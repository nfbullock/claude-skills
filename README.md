# claude-skills

Single source of truth for Claude Code skills across all of Nick's machines.
Skill content lives here; each host installs a selective subset by symlinking
into `~/.claude/skills`, driven by `manifest.json`.

## Layout

```
manifest.json      # categories of skills + per-host selection
bin/skills-sync    # bootstrap / sync / status (python3 stdlib only)
skills/<name>/     # one directory per skill (SKILL.md + tooling)
```

## How selection works

`manifest.json` defines named **categories** (lists of skills) and **hosts**.
A host's skill set is the union of its categories, plus `add`, minus `remove`:

```json
{
  "categories": {
    "core": ["sync-skills"],
    "mac": ["yt-discuss"],
    "server": []
  },
  "hosts": {
    "studio": {"categories": ["core", "mac"], "add": [], "remove": []}
  }
}
```

Hosts are keyed by `hostname -s` lowercased (override: `SKILLS_HOST=<name>`).
Every host should include `core` so it gets the `sync-skills` meta-skill.

## New host

```sh
git clone <this repo> && cd <repo>
bin/skills-sync bootstrap
```

Bootstrap records the repo path in `~/.claude/skills-sync.json` and applies
the manifest. If the host isn't in the manifest yet, it prints the JSON entry
to add — add it, commit, rerun.

## Day to day

Say **"sync skills"** to Claude — the `sync-skills` meta-skill (itself managed
here, in `core`) pulls this repo and reapplies the manifest. Or by hand:

```sh
bin/skills-sync sync      # pull + apply
bin/skills-sync status    # show desired vs installed, no changes
```

`sync` only ever removes symlinks that point into this repo; hand-made skill
directories in `~/.claude/skills` are never deleted. If one shadows a managed
skill, `sync --adopt` moves it aside as `.<name>.pre-sync.bak` first.

## Notes

- Skills are **symlinked**, not copied — `git pull` is the whole update, and
  edits made in `~/.claude/skills/<name>` flow back here for committing.
- Runtime artifacts skills write next to themselves (e.g. `transcripts/`)
  therefore land in this working tree; keep them in `.gitignore`.
- The script is stdlib-only on purpose: it must run on a fresh host's system
  python3 (3.9+) before any venv exists.
