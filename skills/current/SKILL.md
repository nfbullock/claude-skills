---
name: current
description: Ingest a real-life situation Dahlia is going through (a rough patch, a fear, a lesson she needs — e.g. she was rude to an adult who asked her to stop) and distill it into an ABSTRACT, de-identified story-theme ("a current") that surfaces reflectively in her cyoa/camp adventures — never named, never tied to the real event, so she works through it without feeling lectured or watched. Writes profiles/<kid>.currents.toml in the dahlias_laptop repo. Invoke when Dad says "she's dealing with X and I want the stories to gently work it" / "add a current" / "what's she being worked on right now" / "retire that current". NOT for changing tools or content — only for authoring/listing/retiring reflective themes.
status: active
---

# current — reflective theme channel for Dahlia

Dad witnesses something in real life and wants her *stories* to help her work the underlying theme —
**reflectively, not referentially.** The magic word is *mirror at an angle*: the story holds up the
theme, never points at the event. If she could ever trace a scene to "that thing yesterday," the trust
that makes the whole system work is broken. Your job in this skill is the delicate part: turn what Dad
saw into a theme so abstracted it reveals nothing, get his sign-off, and ship it.

This is the INGEST + DISTILL half. The runtime half (weaving it into her play, decay, the "it surfaced"
readout) already exists — see `homeschool-tui/homeschool/currents.py` and `tools/camp/README.md`. You
only author the `profiles/<kid>.currents.toml` file; the deploy + storyteller do the rest.

## The one hard rule (non-negotiable)

**No real events reach the file. Ever.** No names, places, dates, "yesterday", or specifics that could
identify what happened. Only a *transferable theme* + *in-world scene hooks*. The distilled current must
read like ordinary storyteller seasoning — a classic story trope — even to Dahlia if she ever opened the
file. The raw thing Dad tells you stays in the live chat and is never written anywhere.

Two more lines (they mirror the great-courses no-label rule the storyteller already enforces):
- **Never a moral.** Encode the theme as a *situation with consequences she chooses her way through* —
  never "the lesson is…". The story makes the point; nobody states it.
- **Occasional.** Default `budget = 3` (rides ~3 adventures, then retires). Don't stack many loud
  currents at once — a drumbeat is detectable. One or two quiet currents is the texture you want.

## Default flow: author a current

1. **Listen.** Let Dad describe the situation freely. Ask only what you need to find the *transferable*
   theme (what's the durable thing she should feel/learn, stripped of this instance?).
2. **Distill** into:
   - `id` — short kebab slug (`respect-the-overlooked`).
   - `label` — Dad-facing, abstract, one line (what this is, for his tracking — still event-free).
   - `theme` — the storyteller instruction: a *kind of moment* she meets + how the *consequence* plays
     out, abstract and reusable across worlds. Second person about "a character"/"her", not real life.
   - `hooks` — 2–3 concrete IN-WORLD ways it could show up (a ferryman, a cook, a gatekeeper…).
   - `budget` — default 3; raise only if Dad wants it to ride longer.
3. **Show Dad the distilled current and the leak-check.** Explicitly confirm it names no real event and
   reveals nothing. Iterate until he approves. **Do not write until he says yes.**
4. **Append** the `[[current]]` block to `profiles/<kid>.currents.toml` in the dahlias_laptop repo
   (default kid: `dahlia`). Create the file from the existing one's header if it's missing.
5. **Deploy** (offer): commit + push, then `deploy/deploy.sh` renders it to `/opt/homeschool/currents.toml`
   and her next adventure can pick it up. (It rides only FRESH adventures, occasionally, per budget.)

## The format

```toml
[[current]]
id = "respect-the-overlooked"
label = "how she treats people who seem beneath her notice"
budget = 3
theme = """
Sometimes a character crosses someone easy to look down on … let her CHOOSE how she treats them, then
let that choice quietly matter later … never say any of this; let the consequence land on its own.
"""
hooks = [
  "a gruff ferryman or gatekeeper controls passage she'll need later",
  "someone she's tempted to brush off quietly remembers how she spoke to them",
]
```

## Subcommands

- **`list`** — show the active currents in `profiles/<kid>.currents.toml` with each one's surfaced count
  (read the ledger: SSH the laptop and read `~dahlia/.homeschool/currents-ledger.json`, or note it's
  laptop-only state). This is Dad's "what's she being worked on / has it landed" view. The bus also
  carries a `current_surfaced` event per surfacing (visible in `homeschool-observe`).
- **`retire <id>`** — remove that `[[current]]` block (or set `budget = 0`), then deploy. Use when the
  real-life thing has resolved or Dad wants it to stop.

## Boundaries

- Only ever touch `profiles/<kid>.currents.toml` (+ commit/deploy). Don't edit worlds, tools, or the
  runtime. Don't invent currents Dad didn't ask for. One real-life input → one well-abstracted current.
- If Dad's situation is really two themes, propose splitting into two currents and let him pick.
- When unsure whether something is too identifying, cut it. Abstraction is the safety margin.
