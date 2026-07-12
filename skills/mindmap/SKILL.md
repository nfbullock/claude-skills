---
name: mindmap
description: Process a photo of a hand-drawn mindmap into structured markdown analysis — branches, subbranches, drawn-over emphasis, inferred parent/child relationships, vault-grounded interpretation. Output lands in projects/artifacts/mindmap/<date>.md. Currently a stub — the workflow exists in lineage (the 2026-05-01 example artifact) but is not yet implemented as a callable skill. Do not invoke until status flips from stub to active.
status: stub
---

# mindmap (stub)

**Status: stub. Not yet implemented. Do not invoke.**

This skill is a captured intent, not a working tool. The frontmatter declares it as `status: stub` so `/skills-status` can yell if the stub goes stale. Once the next-steps below are done and a first artifact ships, replace this file with the real SKILL.md and flip `status: active`.

## Shape (when developed)

- **Input** — a photo of a hand-drawn mindmap (HEIC/JPG/PNG). Spiral notebook, whiteboard, napkin, whatever.
- **Process** — vision-aware analysis. Identify branches, subbranches, drawn-over (emphasized) bubbles, marginalia, parent/child relationships inferred from drawn lines. Ground interpretation in Nick's vault material — recognize project names, archetypes, recurring concepts; don't analyze in a vacuum.
- **Output** — markdown analysis at `projects/artifacts/mindmap/<YYYY-MM-DD>.md`. Top-level branches as headers; subbranches as nested lists; drawn-over emphasis called out explicitly; honest notes about what's illegible or ambiguous.

## Reference artifact

`projects/artifacts/mindmap/2026-05-01.md` is the canonical example — Claude transcribed IMG_0072.HEIC into the structured form this skill should produce. That artifact predates the skill and was generated ad-hoc; the skill formalizes that workflow.

Read that artifact before implementing. Match its shape: top-level branches, drawn-over emphasis, "Other plans cluster" detail, honest "left uncircled because Nick had forgotten what he meant" notation.

## Downstream

A typical workflow chains forward: mindmap photo → mindmap skill → markdown analysis (artifact) → Nick uses the analysis as input to the next thing (could be a `/tts` invocation to make a dialectical podcast, could be feeding the structure into project planning, could be just reading it). The mindmap skill itself stops at the markdown — what happens downstream is invocation-specific.

## Next steps (to flip from stub to active)

- Pick the vision model. Likely a multimodal Claude API call (the Claude Code session can read the image directly via Read tool); confirm whether the skill needs anything beyond that.
- Codify the vault-grounding step: which directories should the model scan to recognize project names and recurring concepts? Probably reads `STATE.md` plus any project READMEs the names match against.
- Define the output filename convention. `<YYYY-MM-DD>.md` works if Nick draws ≤1 mindmap per day; otherwise add a slug suffix.
- Write the first real invocation against a fresh photo. Confirm output matches the 2026-05-01 reference shape.
- Replace this stub SKILL.md with the real one. Update the description to drop the "Currently a stub" sentence.

