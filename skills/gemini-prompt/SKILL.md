---
name: gemini-prompt
description: Courier for ad-hoc Gemini Deep Research (DR) prompts. Stages prompts in research/requested/, moves them to the final project bucket on ingest. Invoke when Nick wants a deep-research/DR/Gemini prompt for whatever project he's in, when he says he pasted/ran a response, or asks what DR prompts are still outstanding. NOT the multi-chapter `research` arc skill — this is the single-prompt courier.
status: active
---

# gemini-prompt

The fix for "my Deep Research prompts are scattered and I lose the thread." One canonical home for the **raw research** (the prompt + Gemini's raw output), keyed by the project it serves, written wherever Nick happens to be when he asks.

**What these prompts ARE.** Every `.prompt.md` is an artifact you author **for an external system — Google/Gemini Deep Research.** It is the *input side of an integration*: Nick pastes it into Google DR, which does the actual multi-source research and returns a report he pastes back into the paired `.response.md`. So write each prompt as a self-contained external input (no Claude-side context assumed), and **never confuse authoring-the-prompt with doing-the-research-yourself** — Google DR runs the research; you write its brief. Your own deep-research ability has exactly one role here: *downstream*, to validate or extend a report after it returns (see Workflow B). You cannot stand in for Google DR, and a "round-trip test" where you fake a response is meaningless.

## Routing — read first

- **This skill** = a single ad-hoc DR prompt for an ordinary project ("give me a deep research prompt on X", "write me a DR/Gemini prompt", "I pasted the response", "ingest the research", "what DR prompts are outstanding?"). The courier.
- **The `research` skill** = a multi-chapter research *arc* — parallel sub-agents, synthesis, audiobook. "Do a research arc on X", "build me a vocabulary for Y". If Nick wants an arc, defer to that skill. Arcs keep their own internal `source-material/prompts/`; do not route them here.

When ambiguous, ask one sentence: "One-off DR prompt, or a full arc?"

## The architecture (where things live)

Two-stage flow: prompts are written to `requested/` (staging), then moved to the final bucket on ingest.

```
research/requested/<project>/      ← STAGING: prompt written, waiting on Gemini
  NN-slug.prompt.md                  the DR prompt — what Nick pastes INTO Gemini
  NN-slug.response.md                stub until Nick pastes the response back

research/<bucket>/                 ← FINAL: response filled, moved here on ingest
  NN-slug.prompt.md
  NN-slug.response.md
  <arc-dir>/                         full research arcs live alongside prompt files

research/adhoc/<topic>/            ← FINAL for ad-hoc topics (not tied to a project)
  NN-slug.prompt.md
  NN-slug.response.md

<project>/.../synthesis/           ← stays in the project (work done ON the raw)
```

Current buckets: `music`, `life-story`, `food`. Add a bucket to `PROJECT_BUCKETS` in `hub.py` when a project's research graduates from adhoc.

Two hard principles:
1. **Raw research is centralized.** Prompt + raw response always live under `research/requested/<project>/` while pending, then `research/<bucket>/` (project-tied) or `research/adhoc/<topic>/` (ad-hoc) once complete. Same place, every time, regardless of which directory the session was launched from.
2. **Synthesis stays home.** When a project distills the raw into something it uses, that synthesis lives in the project, not the hub. The hub holds raw material only.

Paired-adjacent naming (`.prompt.md` / `.response.md`, one stem) means the prompt and its response always sort next to each other. Nick always knows: the prompt is `.prompt.md`; the response goes in the `.response.md` beside it — and it's already created for him.

## Directory-awareness — how it knows the project

Resolve the target project from the current working directory using the helper:

```
~/venv/default/bin/python <skill>/hub.py resolve
```

It prints the path segment immediately under `projects/` (e.g. cwd inside `projects/music/...` → `music`). It prints **empty** when cwd is the `projects/` root or inside `research/` itself — no unambiguous project. In that case, ask Nick which project, or infer it from the conversation topic, then proceed.

## Workflow A — write a prompt

1. **Resolve the project** (above). Confirm it out loud ("→ research/requested/music-NN-slug").
2. **Check the queue first** — `memory_search` (personal-memory) tag `deep-research-prompt`, and/or `hub.py outstanding <project>`, so you don't collide a number and can remind Nick what's already pending.
3. **Allocate + pre-create** the response stub:
   ```
   ~/venv/default/bin/python <skill>/hub.py new <project> <slug>
   ```
   This prints two paths inside `research/requested/<project>/`: the `.prompt.md` (you fill it) and the `.response.md` (already stubbed — Nick pastes into it).
4. **Write the prompt** into the `.prompt.md`. It MUST be self-contained — pasteable cold into Gemini Deep Research with no outside context. Follow the established register (see the existing files under `research/food/` and `research/life-story/`): a **Profile** block (who it's for — do not research the person), **Standing instructions** (format, citation rigor, length), the **research question**, numbered **sub-questions each requesting citations**, and **source guidance**. Carry a defer-guard if the project has a prior corpus not to re-pave.
5. **Register it pending** — `memory_store`: content `"Pending Gemini DR prompt: research/requested/{project}-NN-slug.prompt.md — <one-line topic>"`, tags `["deep-research-prompt", "<project>", "pending"]`, metadata `{project, slug, prompt_path, response_path, status: "awaiting-run"}`.
6. **Hand off** — tell Nick the exact prompt path to copy into Gemini and the response path to paste the output into. Nothing for him to create or name.

## Workflow B — ingest responses

1. **Resolve the project.**
2. **Find filled responses** — `hub.py outstanding <project>` lists prompts in `requested/` still awaiting a response. Anything in `requested/<project>/` whose `.response.md` has content past the stub is freshly filled. Read those `.response.md` files into context.
3. **Treat the response as external + unverified.** It came from Google/Gemini Deep Research, not from you — so it may carry hallucinations, stale figures, or thin citations. When it matters (or when Nick asks), use **your own** deep research to **validate or extend** it: web-search / the `deep-research` skill to fact-check load-bearing claims, flag or correct anything unsupported, and add fresher or missing sources. This is the one place Claude-side research belongs — *downstream* of the external report, never as a substitute for running the prompt in Google DR.
4. **Do the work** Nick asked for (synthesize, draft, answer), now grounded in the validated/extended material. Any synthesis output lands in the **project**, not the hub.
5. **Move to final bucket** — `hub.py complete <project> <stem>` moves the pair from `requested/<project>/` to the final bucket (`research/<bucket>/` or `research/adhoc/<topic>/`). Prints the two final paths.
6. **Close the loop** — `memory_delete` the matching pending entry (the filled `.response.md` is now in the final bucket, so the memory queue stays a clean "what's still outstanding" list).

## Workflow C — what's outstanding

`memory_search`/`memory_list` tag `deep-research-prompt`, optionally narrowed by project tag. Cross-check with `hub.py outstanding` (filesystem truth: a `.prompt.md` whose `.response.md` is still just the stub). Report the queue grouped by project.

## The helper — hub.py

Stdlib, run via `~/venv/default/bin/python`. Owns the fiddly mechanics so they aren't model-guesswork:
- `resolve [cwd]` → project name from cwd (empty if none).
- `new <project> <slug>` → allocate next zero-padded `NN`, make the dir, pre-create the `.response.md` stub, print both paths.
- `outstanding [project]` → prompts whose response is still unfilled.

Claude owns prompt prose and ingestion; the helper owns paths/numbering/touching; personal-memory owns the cross-session queue.

## Project exceptions (don't relocate these)

Some projects deliberately keep their DR research **project-local** and must NOT be moved into the central hub:

- **`money`** — its `research/` is **gitignored (private)** and the `/money` skill reads `research/REVIEW-REFERENCE.md` + `research/raw/` at runtime in several places. money keeps its own `prompts/review|service/` + `research/raw/` + distilled `REVIEW-REFERENCE.md` pipeline. For money, **index don't move**: register outstanding prompts in the personal-memory queue (pointing at the in-project paths), but write new prompts and read responses in money's own layout — never under `research/requested/money/` or `research/money/`. When resolving a project, if it's `money`, use its project-local layout.

The rule of thumb: if a project's research is gitignored or a skill consumes it at a fixed path, leave it in place and only index it.

## Project discoverability

Each project that has central raw research carries a `raw` symlink pointing at its hub folder, so the raw is visible from inside the project without duplication. When you first centralize a project's research, create that symlink (`ln -s` — matches Nick's symlink-for-skills convention) and update any in-project corpus docs (e.g. `INGESTION.md`, `SEED-INDEX.md`) to note that prompts + raw now live centrally and are surfaced via `raw/`.
