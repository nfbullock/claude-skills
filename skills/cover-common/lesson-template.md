# Cover lesson file — shared template

Shared by `cover-deconstruct` and `song-recipe`. Both skills write to `playground/lessons/NN-cover-<slug>.md` (next number, kebab-case slug from the song title). The sections below are the shared core; each skill's SKILL.md notes its mode-specific deltas (extra sections, different framings).

---

## 1. The song

Title, artist. One sentence anchoring why this song.

- `cover-deconstruct`: Nick's gut "why this song" answer from Step 1.
- `song-recipe`: one sentence on the original, one sentence on what your version will do differently.

## 2. The reference card

Three or four bullets — the form, the key, the progression, the feel. This is what Nick looks at while recording.

- `cover-deconstruct` calls this *"What you heard vs. what's there"* — a two-column list of his guesses vs. the reality with the specific cue named for each miss. Three or four rows max — only the ones that taught something.
- `song-recipe` calls this *"The breakdown (in brief)"* — pulled from the inline breakdown in chat.

## 3. The skeleton / essence vs. decoration

The load-bearing parts. The two-column essence/decoration list from `framework.md` — each essence item **typed** with one of the six essence types (Melodic Hook / Harmonic Loop / Groove-Riddim / Lyric-Prosodic Narrative / Timbral Signature / Structural Gesture). So Nick knows what he's holding onto, what he's letting go, and what *kind* of thing each held item is.

## 4. Keep / Drop / Replace

The three columns from `framework.md`. Be specific about replacements — name the OP-1 engine and the exact notes.

## 5. Tempo and key

Pick exact values. If you're shifting tempo or key from the original (common — the OP-1's keyboard starts at F, so transposing to a key that fits the keyboard is often useful), say so and explain why.

## 6. Section-by-section build

For each section: which tape track, which synth engine, exact notes (absolute, e.g., "C3, Eb3, G3"), how many bars, the section's job in the song. Same internal format as a regular Phase 1 lesson.

## 7. The arrangement

A table with columns **Bars / Section** showing the literal layout on tape.

## 8. The new OP-1 technique (if any)

Max one new technique per cover. If this cover doesn't introduce one, say so.

## 9. Rules and constraints

What NOT to do, narrowed for this song. Always include:

- Hold the spirit, not the recording.
- If a part is too hard, simplify; if a chord is too complex, drop to root + fifth or root only.
- Three or four tape tracks total.
- Finishable in one sitting.

## 10. What this cover trains your ear for

One paragraph. Name **the specific listening skill** this song forces you to develop. This is what compounds, and what gets appended to `playground/JOURNAL.md` *Listening skills learned* after the retrospective — **with a domain tag**, one of `rhythm | harmony | melody | form | lyric | timbre`, leading the entry. Quiz calibration (`cover-deconstruct/references/quiz-calibration.md`) reads these tags to set difficulty per domain, so the tag is load-bearing, not decoration.

Examples:

- *"[rhythm] Hearing halftime feel — the snare lands on 3 instead of 2 and 4, so the song sounds slow even though the hi-hat is at the actual tempo."*
- *"[form] Hearing arrangement-as-dynamics — this song never gets louder, it just adds and removes layers."*
- *"[harmony] Hearing the iv-chord borrow — the bridge drops to a minor IV, a chord borrowed from the parallel minor key."*

## 11. Bounce to album

Confirm the finish line.

## 12. The 48-hour blind audit (optional — never blocks)

A post-bounce step, staged explicitly as **"retro now, audit later."** The retrospective happens on its usual schedule; this audit trails it by design and **never blocks the next lesson** — if it doesn't happen, nothing downstream waits on it.

The procedure: bounce, then set the recording aside for **at least 48 hours** (the gap defeats demo-love — the glow that makes everything you just made sound finished). Then listen to **the new recording only — the original is never played.** Two checks:

1. **Typed essence checklist, binary Y/N per item.** For each typed essence item from Section 3, one question: is it clearly audible in the new recording under the re-coloring? (*"Is the chorus contour clearly audible?" "Does the groove still lag the downbeat?"*) Y or N, no grading scale.
2. **One standalone-cohesion check.** Does it work as its own piece — no mud, no clashing parts, no prosodic seams where new words fight the contour?

This is not a fidelity test — the original stays unplayed, and the checklist audits *Nick's own essence list*, not resemblance. Any N goes to **Notes for the coach** as an observation, not a failure.

---

## Mode-specific deltas

- **`song-recipe` only:** optional *Graduation checkpoint* — at one moment in the recipe (usually a keep/drop/replace decision or a reimagining-direction choice), drop a small italic note: *"Graduation checkpoint: in a future cover, you could try to call this yourself — listen for [cue] and ask whether it's essence or decoration."* Max one per recipe. Skip if nothing in the recipe naturally lends itself.

- **`cover-deconstruct` only:** no extra sections — the value is that *Nick generated* the essence/decoration list, not received it. The lesson file is the artifact of his work, not a recipe handed to him.

---

## After Nick records and gives a retrospective

Same flow as a regular lesson retrospective (see `CLAUDE.md` in the project), with these additions both skills share:

1. Append to `playground/JOURNAL.md` *Listening skills learned* the skill named in Section 10, **with its domain tag** (`rhythm | harmony | melody | form | lyric | timbre`). This is the entry that calibrates `cover-deconstruct` quiz difficulty later — per domain, so the tag matters.

2. If the retrospective surfaced a *new* listening pattern Nick noticed while making it ("I noticed the bass and kick lock up at the section change, not just on the downbeat"), add it to **Notes for the coach**.

3. If a local-analysis tool is available and Nick has bounced his cover to audio, offer to run the same analysis on his version. Frame any comparison with the original as *observations about what the recording is*, not as a feedback report — divergence is the rig taking the song where the rig takes it, not deviation-from-target. See `local-analysis.md` for the framing.

4. Remind Nick the 48-hour blind audit (Section 12) is open — retro now, audit later. Don't chase it, don't block on it; if he brings audit findings back later, fold them into **Notes for the coach**.

`song-recipe` adds one more: **watch for graduation signal.** The operational criterion is **consistent transfer-test success across domains** (see `cover-deconstruct/references/quiz-calibration.md`): Nick spotting learned cues in *unfamiliar* songs — delivered via the lesson's reference playlist — across several of the six domains, not just his strongest one. Softer corroborating signs still count: predicting the breakdown before reading it, naming chords or feels you didn't tell him, questioning a keep/drop/replace call you made. When the signal is there — suggest flipping `Cover phase` to `deconstruct`. Frame as a promotion Nick accepts, never a test he passes. Nick decides.
