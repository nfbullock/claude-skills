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
    "work": [],
    "personal": ["yt-discuss"],
    "studio-only": []
  },
  "hosts": {
    "studio": {"categories": ["core", "work", "personal", "studio-only"], "add": [], "remove": []}
  }
}
```

Categories are composable slices, and device classes are compositions of
them — a skill added to `work` reaches every host that includes `work`:

| device class | categories |
|---|---|
| work laptop | `core, work` |
| dev box | `core, work, personal` |
| studio | `core, work, personal, studio-only` |

Hosts are keyed by `hostname -s` lowercased (override: `SKILLS_HOST=<name>`).
Every host should include `core` so it gets the `sync-skills` meta-skill.

After applying, sync also reports drift in both directions: repo skills not
selected for this host, and local-only skills in `~/.claude/skills` the repo
doesn't know about (import candidates — the sync-skills meta-skill offers to
fold them in).

## New host

```sh
git clone <this repo> && cd <repo>
bin/skills-sync bootstrap            # prompts for device class if host is new
bin/skills-sync bootstrap --class dev-box   # non-interactive
```

Bootstrap records the repo path in `~/.claude/skills-sync.json`. If the host
(keyed by `hostname -s`) isn't in the manifest, it registers it under the
chosen device class — the `classes` block maps class → categories — commits
the manifest change, pushes so the other machines see it, and installs.
Mac and Linux only; no Windows handling.

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
