---
name: research
description: Multi-prompt agentic research arc. Given a topic and a set of focused sub-questions, spawn parallel sub-agents to produce a corpus of standalone essays, then synthesize them into a final document. Optionally reframe and render as an audiobook via the tts skill. Output is configuration — markdown is always the canonical, audio is downstream via tts. Invoke when Nick wants to build deep working vocabulary on a topic (composition, philosophy, a specific domain), not for quick lookups or one-shot answers.
status: active
---

# research

Take a topic → produce a corpus of essays + a synthesis + optionally an audiobook. Multi-agent, parallel, with a defined phase ordering. The hard-won lesson is that prompt-response shape and audiobook shape are different shapes; if the output is going to TTS, schedule the reframe pass.

## When to invoke

- "I want to build a real vocabulary for X"
- "Let's do a research arc on Y"
- "Help me work through [topic] deeply"
- "Make me an audiobook on Z"

Not for: quick factual lookups, one-shot questions, code research, vault searches. This skill is for sustained learning arcs where Nick wants to come out the other side with a working mental model and ideally an audiobook to keep listening to.

**Not this skill:** a single ad-hoc Gemini Deep Research prompt for some other project ("give me a DR prompt for this", "I pasted the response") → that's the **`gemini-prompt`** skill, the lightweight courier that stages prompts in `research/requested/` and moves them to the final bucket on ingest. Arcs keep their own internal `source-material/prompts/`; don't route those through `gemini-prompt`.

## Phase-by-phase shape

### Phase 0 — Scope the pull

Before defining anything, negotiate the shape. The same skill runs three different sizes; conflating them produces immersion-sized work for essay-sized pulls.

Three shapes:

- **Essay** — one focused prompt, one chapter, ~20 min of audio, render same day (~30 min compute). Right when Nick has a single specific question and wants something on his walk tomorrow. Pipeline collapses to Phase 1 (one prompt) → Phase 2 (one sub-agent) → Phase 6 (reframe) → Phase 7 (TTS). No synthesis, no gap-fill, no reordering.
- **Mini-arc** — 3–5 prompts, ~80 min total audio, 1–2 days end-to-end. Right when a topic has a few clean sub-questions but doesn't deserve a fractal treatment. Phase 1 (3–5 prompts) → Phase 2 (parallel) → Phase 4 (light synthesis or single coda essay) → Phase 6 → Phase 7. Gaps and reordering usually skipped.
- **Immersion** — 10–15 prompts, several hours of audio, multi-day. Right when Nick wants to live inside a topic and build fractal vocabulary. Full pipeline (Phases 1–7).

The negotiation axis is **importance × information availability**. High importance + lots of information → immersion. Mid importance or focused question → mini-arc. Specific question + tight time window → essay.

Do not default to immersion. The composition arc was an immersion; most pulls won't be. Ask Nick which shape this is before scoping prompts. If unclear, propose a shape with one sentence of reasoning and let him redirect.

If Nick wants to scope but not run an arc right now, write the result as a parked seed: `projects/research/<slug>.md` with the proposed shape, draft prompts, and reasoning. See directory layout below for the file-vs-folder convention.

### Phase 1 — Define the arc

Nick names a topic. Together you scope:

1. **A research directory** at `projects/research/<bucket>/<topic_slug>/` for project-tied topics, or `projects/research/adhoc/<topic_slug>/` for ad-hoc topics. The bucket matches the project name (music, life-story, food); if no bucket fits, use adhoc. See Directory layout below.
2. **A `CLAUDE.md`** in that directory. This is the contract the sub-agents read before working. It declares:
   - Project context (the why, the framing hypothesis)
   - How to work (deep engagement vs. encyclopedic coverage, when to web-search vs. trust training, honesty about uncertainty, register and tone)
   - Output format (filename convention, length range, markdown style, TTS-friendliness if audiobook is downstream)
3. **A `prompts.md`** listing N focused prompts. Each prompt has a stable structure:
   - **Goal:** one sentence
   - **Current understanding:** **what Nick actually knows pre-arc, not what the arc hopes he'll know post-arc.** State his literature exposure honestly (read, name-aware, novice) and his practice exposure honestly. If he has an existing working theory, state the components he has named — not the developed version the arc will produce. Nick reviews and corrects these sections before agents fire. Projecting post-arc outputs onto the pre-arc current-understanding section makes the chapter self-confirmatory and weakens the corpus.
   - **What I want:** numbered sub-questions (typically three)
   - **Go deeper hook:** the open question at the edge of the topic
4. N is set by Phase 0 — 1 for essay, 3–5 for mini-arc, 8–12 for immersion. Don't override Phase 0's call here without a reason.
5. **Identify source-grounded chapters and pre-write Deep Research prompts.** Some chapters depend on primary-source material a sub-agent's training memory cannot reliably supply: **lineage chapters** (specific thinkers' actual passages with page references), **empirical-evidence chapters** (real studies with citations and methodology), and **steelman/skeptic chapters** (the critics' verbatim words and cited evidence). For each such chapter, write a Deep Research prompt during scoping and save it to `<arc>/source-material/prompts/NN-name.md`. Nick runs the prompt manually in Gemini Deep Research (Ultra plan covers the consumer app) and pastes the cited output to `<arc>/source-material/NN-name.md` before Phase 2 fires. The chapter's entry in `prompts.md` should include a **Before firing** line directing the sub-agent to use the source-material file as raw citations to draw from, *not* as a draft to recapitulate (Deep Research's voice is encyclopedic; the sub-agent must rewrite in the arc's register). See `projects/research/pull-learning/source-material/` for the worked example.

Not every arc has source-grounded chapters. Pure-conceptual arcs — those centered on the user's own working theory, on a topology they already inhabit, or on argumentative/synthetic moves rather than source-fetching — may skip this step entirely. The decision is **per-chapter, not per-arc**: a single mini-arc may have one source-grounded chapter and three conceptual ones. The synthesis chapter should evaluate per-arc whether the pre-step earned its keep and propose adjustments to this convention.

### Phase 2 — Parallel execution

Spawn N sub-agents in a single message, one per prompt. Each agent:
- Reads the project `CLAUDE.md`
- Writes to its assigned numbered file (`00-<slug>.md`, `01-<slug>.md`, etc.)
- Operates in isolated context — does not see other prompts or other agents' outputs

Run in background. They take 60–150 seconds each. By the time the slowest finishes you have the whole corpus.

### Phase 3 — Identify and fill gaps (optional but usually needed)

After the corpus exists and is being synthesized (or after Nick reads it), gaps become visible that weren't visible from the outset. Examples of gaps from the composition arc: rhythm and groove, mix and space, voice as instrument, genre as structural pressure. Each gap becomes a new prompt in the same shape. Spawn parallel agents for the gap-fillers.

Gap-filler prompts should reference the original arc and name what gap they fill, so the sub-agent knows the synthesis context.

### Phase 4 — Synthesis

Spawn one synthesis sub-agent (single agent, not parallel) with a precise brief:
- Read the entire corpus as one document
- Identify cross-cutting motifs (typically 3–6)
- Identify productive tensions (typically 2–3)
- Construct a throughline / structural argument — not "here's what each prompt said" but a real claim with stakes
- Surface gaps the research didn't address
- Translate insight into operational form if Nick has a downstream practice
- **For arcs claiming behavior-change relevance (most arcs), produce a falsifiable bet as a named section in the synthesis.** Specific external criteria — counts, named instances, observable artifacts — that distinguish actual change from articulate explanation of why change did not happen. Typical window: 2 years for the full bet, with **interim checkpoints at 6 months and 1 year** so failure modes get caught before the full window elapses. The bet is the corpus's claim to do work; without it, the synthesis cannot be distinguished from articulate confirmation theater. The bet should be wired into something that will actually fire on the named dates (a Things task, a scheduled remote agent, a calendar entry) — otherwise the bet is itself theatre.

The synthesis should embody the principles it discusses — motifs that recur transformed across sections, transitions that connect, a coda that earns its return. This is itself a fractal move: do at the synthesis level what the topic does at its level.

Editorial pass after — the parent agent fixes pronoun ambiguities, factual hedges, tightens length.

### Phase 5 — Reorder and rename (if gap-fillers exist)

After gap-fillers are integrated into the synthesis, the original filename numbering reflects research order, not logical reading order. Renumber the files so the canonical sequence reflects the audiobook flow:
- Gap-fillers slot in next to their natural siblings (groove next to duration, voice next to mix, etc.)
- Synthesis becomes the final numbered chapter
- Old synthesis (v1) preserved as `synthesis-v1.md` if needed

### Phase 6 — Reframe for audiobook (only if rendering to audio)

**Critical learning.** The research prompts were written in prompt-response shape ("Your working definition is already most of the way there", "Now the second question", "What I want from you"). When played as audio, this is jarring — the listener can't hear the prompt and the essay reads as mid-conversation with no introduction.

Before rendering, spawn N parallel reframe agents, one per chapter. Each agent's brief:
- Add an opening (1–2 paragraphs) naming the topic and stakes
- Define key terms cleanly before deploying them
- Remove all prompt-response phrasings ("now the second question", "what I want from you", etc.)
- Smooth numbered sub-question transitions into organic essay flow
- Preserve all substantive analysis, examples, uncertainty flags
- Close cleanly — name what the listener should carry forward

The synthesis usually needs less work because it was already written as standalone, but it should still be scanned for research-process metadata ("this research arc," "the four new prompts filled the gaps") that doesn't belong in the audiobook.

### Phase 7 — TTS render

Hand off to the `tts` skill. Each chapter becomes its own audio file. Audiobook output lands in `~/Library/Mobile Documents/com~apple~CloudDocs/tts/<topic_slug>/` per the tts skill's convention.

Render chapter 00 first as the validation chapter. Listen on AirPods. Iterate on pronunciation table and pacing. Once chapter 00 is good, fire the rest in batch (~4–5 hours unattended for a 15-chapter arc).

## Directory layout

```
projects/research/
├── <bucket>/                 ← project-tied research (music, life-story, food, …)
│   ├── <topic_slug>/         ← active or completed arc
│   │   ├── CLAUDE.md
│   │   ├── prompts.md
│   │   ├── source-material/
│   │   │   ├── prompts/
│   │   │   │   └── NN-name.md
│   │   │   └── NN-name.md
│   │   ├── 00-<slug>.md
│   │   ├── ...
│   │   └── NN-synthesis.md
│   ├── NN-slug.prompt.md     ← ad-hoc DR prompt (gemini-prompt skill output)
│   └── NN-slug.response.md
├── adhoc/                    ← research not tied to any project
│   └── <topic_slug>/         ← arc or prompt cluster
│       ├── CLAUDE.md         (if arc)
│       ├── 00-<slug>.md …    (if arc)
│       └── NN-slug.{prompt,response}.md   (if DR prompts only)
└── CLAUDE.md
```

**Routing rule.** A topic belongs in `research/<bucket>/` if it serves a project that has a bucket (currently: music, life-story, food). Everything else lands in `research/adhoc/`. When a new project accumulates research, add its bucket name to `PROJECT_BUCKETS` in `gemini-prompt/hub.py`.

**Status by filesystem shape.** A parked arc seed is a `<slug>.md` file inside the relevant bucket (or `adhoc/`) — a scoped proposal (shape, draft prompts, reasoning) that Nick has decided to do later. When activated, promote it to a folder; the seed file can be moved inside as `SEED.md` for lineage or folded into `CLAUDE.md`.

Research lives at the projects root, alongside `someday/`, `archive/`, `artifacts/`, and `claude_skills/`.

After Phase 7, TTS audio lives in iCloud per the tts skill convention. The vault holds the canonical markdown; iCloud holds the listening copy.

## Configuration is the format

The skill's stub-era observation still holds. The same workflow produces:
- `.md` — vault canonical, always written first
- `.wav` / `.mp3` — audiobook, downstream via tts skill
- `.epub` — possible future format; not yet implemented

Markdown is the source of truth. Other formats are renders of it. If a chapter needs to change, change the markdown; downstream formats follow.

## Hard-won lessons

- **Scope before scoping.** Phase 0 is load-bearing. The same skill produces a 20-min essay, an 80-min mini-arc, or a multi-hour immersion — and the wrong shape wastes either Nick's time or the topic. Negotiate importance × information-availability up front.
- **Prompt structure matters.** The current-understanding section anchors agents in Nick's mental model so they don't waste words on basics he already knows. The numbered sub-questions force focused coverage. The go-deeper hook stops agents from stopping at the surface.
- **Audiobook needs reframing.** Prompt-response prose works on the page; on audio it sounds like overheard dialogue. Schedule the reframe pass before rendering.
- **Parallel sub-agents need a contract.** The project CLAUDE.md is the contract. Without it, fifteen agents produce fifteen voices. With it, they sound like one author.
- **Gaps become visible at corpus scale.** Plan for a gap-fill phase. The first prompts.md is rarely complete.
- **Synthesis is its own discipline.** Do not let the synthesis agent default to "here's a summary of each chapter." Brief it to construct an argument with stakes, identify motifs and tensions, and produce something that embodies the topic's own principles.
- **Editorial pass is the parent agent's job.** Don't delegate the final polish. Fact-checks, hedge removal, tightening — do these yourself before declaring done.
- **Source-grounded chapters want Deep Research pre-steps.** When a chapter centers on specific thinkers' primary texts, real empirical studies, or steelmanning a literature the arc doesn't otherwise engage, sub-agents working from training memory will hallucinate citations, reconstruct passages they can't actually verify, and produce plausible-sounding but unreliable source claims. Pre-write a Deep Research prompt during Phase 1, have Nick run it manually in Gemini Deep Research, and feed the cited output to the sub-agent as raw material. Decide per-chapter, not per-arc — most arcs will have a mix.
- **The "current understanding" section is where confirmation theater enters arcs.** If the prompt's current-understanding section projects post-arc conclusions onto the user's pre-arc position, the chapter agent will write to validate the projection. Nick must review these sections before agents fire and correct them down to actual epistemic position. Honest novice + practice-rich is fine; projecting "Nick already has the developed theory" when he has only named the components is the failure mode.
- **Behavior-change arcs need falsifiable bets.** Without specific external criteria committed in advance, the synthesis cannot be distinguished from articulate explanation of why behavior did not change. Two-year window with interim checkpoints; the bet should consist of counts, named instances, or observable artifacts the user can verify or fail to verify on the named dates. Wire the bet into a system that will actually fire on the dates — Things, scheduled agent, calendar — or the bet is theatre on a longer timeline.

## Lineage

Per reaper #50 — descended from the dead "Fred research-paper" agent. Fred died; the research-and-produce shape survived. First active execution was the 15-chapter composition vocabulary arc in May 2026 (see `projects/research/composition_vocabulary/` for the worked example, including the iteration where the reframe pass was added after the first audiobook render exposed the prompt-response problem).

**2026-05-12 — Deep Research pre-step convention added.** Emerged during the scoping conversation for `projects/research/pull-learning/`. The arc's literature-novice / practice-rich shape made it clear that lineage and skeptic chapters needed real citations rather than reconstructions from training memory. Phase 1 now explicitly includes a source-grounded-chapter identification step with Deep Research pre-prompts; the directory layout grows a `source-material/` sub-tree. See `projects/research/pull-learning/source-material/` for the first worked example of the pattern.

**2026-05-12 — Synthesis-pass amendments from pull-learning arc.** The synthesis chapter of `projects/research/pull-learning/` (08-synthesis.md) produced six concrete amendments to this skill per the metacognitive job in its arc-specific CLAUDE.md. Four were piloted in the arc itself and now codified above: the recursive-reference-data section convention, the mandatory skeptic chapter for sympathetic-framing arcs, the Deep Research pre-step, and the substitution-not-compression word-target calibration for DR-pre-loaded chapters (3,500–5,000 words preserving DR's quoted passages 1:1 rather than compressing past them). Two were new findings, now embedded above: **the "current understanding" section must state pre-arc epistemic position honestly** (projecting post-arc outputs onto it produces self-confirmatory chapters), and **arcs claiming behavior-change relevance must produce a falsifiable two-year bet** with interim checkpoints in the synthesis (specific external criteria; wire into Things or scheduled-agent so the bet actually fires).
