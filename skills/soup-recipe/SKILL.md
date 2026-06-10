---
name: soup-recipe
description: On-demand soup recipe generator in the Alton Brown register — small batches, simple ingredients, science-aware technique notes. Invoke from food/ project when Nick wants a specific soup or to brainstorm what to do with what's in the kitchen.
status: active
---

# soup-recipe

Soup-on-demand skill. Alton Brown register: practical, science-aware, small-batch, no fluff.

## When to invoke

- Nick says "give me a soup recipe" or "what can I do with [ingredients] for soup."
- Active inside the `food/` project's meal-planning workflow.

## Status

Scaffold (placeholder). Per reaper #18 — Alton Brown soup agent reshaped from Things task into a skill. Real content/recipe library not yet authored. Nick will flesh out when the food/ project starts running.

## What still needs to be written

- Recipe-generation prompt (Alton Brown voice, technique-aware framing).
- Optional `references/` subdir with canonical soup-technique notes.
- Integration with `food/`'s meal-plan rhythm (does the skill fire weekly? on-demand only?).
