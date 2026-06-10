---
name: push-notify
description: Push a notification to Nick's phone (and Mac) via ntfy — a short title + message, optional tap-to-open link, tags, and action buttons. Use when a long-running task finishes, an event fires that Nick should know about, or a project needs to hand him something (e.g. the dahlias-laptop project pushing "Dahlia's song session is ready" with a link to the saved artifact). Works from any machine including Dahlia's Linux laptop — plain HTTPS POST, no Apple developer app required. Nick installs the ntfy app once and subscribes to a secret topic.
status: active
---

# push-notify

Send a push to Nick's phone via **ntfy**. General-purpose: any project can call it to notify him.

> **One-time setup required before first use** — see README. Install the ntfy app, pick a secret
> topic, write `~/.config/push-notify/config.json`. After that this is live.

## Invocation
```bash
~/venv/default/bin/python \
  /Users/dad/Documents/sandbox/projects/claude_skills/push-notify/scripts/send.py \
  --title "Render done" --message "The dahlias batch finished" [--click "<url>"] [--tags "white_check_mark"]
```
Output: `{"status": 200, "id": "..."}` on success, or `{"status":"config_required"|"error", ...}`.

## What it carries
- `--title`, `--message` (required), `--priority` (min|low|default|high|urgent), `--tags`
  (emoji shortcodes), `--click` (URL opened on tap — e.g. an `obsidian://` link straight to a
  vault note), `--markdown`. Action buttons (approve/deny, open) are supported in `ntfy.py` for
  programmatic callers.

## Patterns
- **Task-done ping:** a long render/sweep/research run finishes → `--title "Done" --message "…"`.
- **Hand Nick an artifact:** save the artifact to the vault, then push a short summary with
  `--click` set to an `obsidian://`/file link straight to the note.
- **Approve/deny gate:** `ntfy.py push(...)` takes an `actions=[...]` list — an
  `{"action":"http","label":"Approve","url":".../approve/<id>","method":"POST"}` button hits a
  caller-owned endpoint. The notification is the *signal*; the consuming project owns any lock/state
  and treats it as fail-closed (never make the push the security boundary).

This skill is just the notification *verb*. Project-specific workflows that use it (e.g. the
dahlias-laptop song-interviewer) own their own design and live in their project — see
`projects/dahlias laptop/song-session-design.md`.

## Notes
- ntfy.sh topics are public-by-obscurity — use a long random topic, or self-host ntfy on the
  Studio (set `server` in config) for true privacy. Self-hosted supports `auth_token`.
- No HTTP/2, no JWT, no `.p8`. (Earlier draft of this skill used APNs; abandoned because receiving
  APNs requires building and distributing an iOS app — ntfy removes that entirely.)
