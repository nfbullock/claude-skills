# Local Audio Analysis

Nick has a Mac Studio (M4 Max, 36GB) and is interested in running local audio-analysis tools to feed this skill. This document explains how to detect such a tool when it's available, how to use it, and — for the future — what a good version of it would look like.

## Detection

At the start of a cover session, after reading `JOURNAL.md` and before quizzing Nick, check whether any MCP tool with a name suggesting audio analysis is available. Likely names (in order of likelihood):

- `mcp__audio-analysis__*` (e.g., `analyze_audio`, `compare_audio`, `extract_stems`)
- `mcp__librosa__*`, `mcp__essentia__*`, `mcp__madmom__*` (named after the underlying library)
- `mcp__op1-analyzer__*` or `mcp__songdeconstruct__*` (named after the project)

If any such tool is in the available tool list, the local analysis path is open. If not, the skill works fine without it — proceed with web lookup only.

## What to ask of it

The skill cares about three things, in priority order:

1. **`analyze_audio(path)`** — given an audio file, return a structured object with at least:
   - `tempo_bpm` (float; ideally with a confidence score)
   - `key` (e.g., "D minor"; ideally with a confidence score)
   - `time_signature` (e.g., "4/4", "12/8")
   - `sections` (list of `{label, start_seconds, end_seconds}` — intro, verse, chorus, etc.)
   - `chord_progression` (list of `{chord, start_seconds, end_seconds}` if available — chord recognition is the hardest of these and may be absent)

   This replaces or augments the WebSearch step in Step 4 of the SKILL. *Augments*, not replaces — keep the web lookup too. If the local analysis disagrees with the web (often does, especially on tempo when there's a halftime feel), that disagreement is itself the lesson: "SongBPM says 70, the analyzer says 140 — it's halftime feel; both are technically right."

2. **`compare_audio(reference_path, your_path)`** — given the original song and Nick's bounced cover, return a comparison: tempo delta, key match/mismatch (and by how many semitones), section-by-section structural alignment, where the energy curves diverge.

   This is for after a cover is done — but be careful with the framing. On *Constellation*'s method, the cover is the rig's version and is **not measured against the original** (see `feedback_covers_not_same_style` in project memory). So the comparison is **not** "where Nick succeeded or failed at matching the original" — most divergence is just the rig taking the song where the rig takes it, neither intentional-as-statement nor a miss. The comparison is useful for surfacing things Nick may not have noticed (the section he thought was 32 bars was actually 28; the key drifted between takes) — observations, not grades. Use it as an *ear-training opener*, not a feedback report. Don't ever frame divergence as deviation-from-target.

3. **`extract_stems(path)`** — given an audio file, return separated stems (drums, bass, vocals, other). Optional and slow (Demucs takes ~real-time on M4 Max). Useful when Nick is having trouble hearing one element in a busy mix; pull just the drums and listen alone.

If the available tool has a different shape (e.g., one big `analyze` that returns everything, or separate tools per task), adapt to it — the priority order above still holds.

## When to use it during the deconstruction

- **Before Step 1 (the quiz)**: silently run `analyze_audio` on the reference if Nick has the audio file. Now you have ground truth from the audio itself, not just secondhand from the web. *Still don't tell him.*
- **During Step 2 (the reveal)**: if the analyzer's tempo/key disagrees with the web, lean on the analyzer — it's measuring the actual file. Use the disagreement as a teaching moment.
- **During Step 3 (Layer 1)**: if Nick is struggling to hear the kick pattern in a dense mix, offer to extract stems and isolate the drums. Don't do this proactively — it's a tool to break through a stuck moment, not a default.
- **After the retrospective**: if Nick has bounced his cover to an audio file (which the OP-1 album bounce produces), `compare_audio` can be useful but only if Nick is curious. Don't frame divergences as "miss vs. intentional" — frame them as *observations about what the recording is*. ("Your version sat at 84 BPM; the original is at 92. You ended up about a half-step down. Anything you want to do with that, or is that just where it landed?") The conversation is about hearing what's there, not auditing it against a target.

## What the analyzer can NOT replace

The analyzer measures; it doesn't *interpret*. It can tell you the chord at second 47 is Ab major, but it can't tell you that Ab major is bVI in the key of C major and the song just did modal interchange. That interpretive step is yours. The analyzer is a faster, more accurate eye — but the producer's-ear narration is still your job, and Nick's training.

Don't ever just dump the analyzer's output at Nick. Use it as your private second opinion; deliver the deconstruction in the conversational, layered way the SKILL describes.

## Recommendations for the future analyzer (Nick is interested in building this)

If Nick is sketching what to build, here's the shape that would serve this skill well:

- **A single MCP server, running locally on the Mac Studio**, exposing the three tools above.
- **Underlying libraries (all free, all Apple Silicon native):**
  - `madmom` for beat and downbeat tracking — best-in-class accuracy, especially on tempo with halftime feel.
  - `essentia` for key, tempo (cross-check with madmom), chord recognition, and rhythmic feature extraction. Trickier to install (compiled C++) but the most accurate.
  - `MSAF` (Music Structure Analysis Framework) for sectional segmentation. Less accurate than human ears but a useful starting point.
  - `demucs` (Meta) for stem separation. Slow but state of the art. Run on demand only.
  - `librosa` as the connective tissue / fallback for anything the others don't cover.
- **Don't try to do chord recognition without essentia** — librosa's chord detection isn't great. If essentia is too painful to install, use `autochord` as a Python alternative.
- **Cache aggressively.** Analysis of a single 4-minute song takes 30s–2min depending on which features. Cache by file hash so re-analyzing the same song is instant.
- **Output JSON, not plots.** The MCP returns structured data; visualization can happen client-side if needed.

There is no commercial product that does this end-to-end well — Mixed In Key does keys, Hooktheory does crowdsourced harmony, Lalal.ai does cloud stems. None of them assemble into the "give me everything about this song" pipeline. The open-source Python stack is genuinely state of the art here, and a thin MCP wrapper is a weekend project for Nick.

For a v1, the priority is `analyze_audio` returning tempo/key/sections. Chord recognition is the hardest; it can wait. Stem separation is icing.
