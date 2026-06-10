---
name: skylight-calendar
description: Push events, chores, and meal-plan items to the Skylight family calendar via its programmatic interface. Invoke when a project (token_economics/, food/, etc.) needs to put something in front of the family on the wall calendar.
status: active
---

# skylight-calendar

Programmatic interface to the Skylight family calendar.

## What this skill does

- Authenticates against the Skylight API.
- Pushes calendar events, chore items, and meal-plan entries from project-side content (e.g., `food/meal-prep.md`, `token_economics/magnificent-seven.md`).

## When to invoke

Any time a project needs something on the family's wall calendar. The skill is the *plumbing*; the projects are what generate the content.

## Files

- `verify.py` — auth verification.
- `package.json` / `node_modules/` — Node-side MCP wrapper (`skylight-mcp` binary).

## Status

Per reaper #11 — small but active tool. Promoted out of `projects/skylight/` (which mixed skill code with project content) into the proper skill location.
