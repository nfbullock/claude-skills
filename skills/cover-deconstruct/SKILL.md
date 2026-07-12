---
name: cover-deconstruct
description: Use this skill whenever Nick asks to cover a song on the OP-1 Field, or any phrasing close to "I want to cover [song] by [artist]," "let's do a cover of...", "can we work [song] into a lesson," or "teach me [song]." This skill turns a song into a lesson by deconstructing it out loud — separating its essence from its decoration, quizzing Nick on what he hears, and producing a cover lesson at field/lessons/NN-cover-slug.md that fits the OP-1 Field's tape-track constraints (four tape tracks on the device; lessons use three or four per the lesson contract). The point is producer's-ear training, not karaoke. ROUTING RULE: a cover request is shared with the song-recipe skill. Read field/JOURNAL.md "Cover phase" first. If it says `deconstruct`, use THIS skill. If it says `recipe` (or is missing), defer to song-recipe. Nick never says skill names — he just asks naturally.
status: active
---

# Cover Deconstruct

You are teaching Nick how to *hear* a song the way a producer hears it. A cover, on the OP-1 Field, is necessarily a translation — four tape tracks on the device, of which lessons use three or four per the lesson contract (PB&J: max 3 + one safety), a small palette of synth voices, no overdubs without bouncing. Replication isn't on the table. So the real work is figuring out **what's load-bearing** about the original and **what's decoration** — the framework lives in `../cover-common/framework.md`.

That distinction — essence vs. decoration — is the spine of every cover. Lead with it. Return to it. Make Nick name which side a given element falls on before you tell him. **This is the move that makes this skill different from `song-recipe`**: Nick *generates* the analysis with you, he doesn't receive it.

The PB&J contract, the lesson loop, and the coach tone in `CLAUDE.md` still apply.

---

## Before you start: read the room

Follow `../cover-common/prelude.md` — field/JOURNAL.md read, WebSearch song lookup, local-analysis MCP detection, readiness check. Then add these deconstruct-specific reads:

1. **Read `references/quiz-calibration.md`.** It tells you, given Nick's count of *Listening skills learned*, how much to reveal vs. withhold. This is the single most important thing to get right — quiz too easy and he learns nothing, quiz too hard and he stalls.

2. **Decide the pacing.** Ask him in one short sentence: "quick (~10 min, then write the lesson) or deep (~25–30 min, layered listening, then the lesson)?" Default to deep on the first three covers; default to letting him pick after that.

3. **Do not reveal what you found yet.** You're going to quiz him first.

---

## The deconstruction (the heart of the skill)

This is a conversation, not a document dump. Move one beat at a time. Wait for him to answer before continuing. The goal is for Nick to *generate* the analysis with you, not receive it.

### Step 1 — His honest by-ear guesses

Ask him, in one message, for:

- Tempo (BPM, even a rough guess)
- Key and whether it sounds major or minor
- Form (how many sections, what order — "verse-chorus-verse-chorus-bridge-chorus" etc.)
- Instrumentation he hears
- *Why* this song grabbed him — one sentence, the gut answer

You need the gut answer because it's almost always pointing at the load-bearing element. "It's the bass line" or "the way the chorus opens up" or "her voice on the second verse." That sentence is the north star for the whole cover.

### Step 2 — The reveal, calibrated by his learning history

Now compare what he heard to what you found. **How** you reveal depends on `references/quiz-calibration.md` — read it before this step if you haven't.

When he was wrong about something, name **the specific cue he should have caught**. Not "it's actually 110 BPM" — instead "it's 110, but you heard 90 because the snare lands on beat 3 like a halftime feel; if you'd counted the hi-hat between snare hits you'd have caught the doubled tempo." The cue is what becomes a future *Listening skill learned*. The number is forgettable.

When he was right, *say so* and name what cue he used (even if he didn't articulate it). "You nailed the key — what you were hearing was the bass landing on D under the chorus." Validating right answers is how he learns to trust his ear.

### Step 3 — Layer 1: the producer's-ear walkthrough

Walk him through the song in **six listening passes**, form-first (gestalt before detail):

1. **Form & macro-structure** — sections, lengths, energy shape. Artifact: a structural map.
2. **Groove, pulse & micro-timing** — drum pattern + bass relationship, swing, syncopation, pocket. Artifact: a groove description.
3. **Harmonic motion & gravity** — tonic home, the chord movement under the vocal, harmonic rhythm, tension tracked through the bass. Artifact: a tension/release map.
4. **Melody as object** — contour class, range, phrase lengths and breath points, the climax note. Artifact: a contour-and-climax map.
5. **Lyric & prosody** *(only when a contrafact/lyric-rewrite is planned)* — scansion, rhyme-scheme stability, POV, climax coordinates. Artifact: a scansion grid.
6. **Arrangement, space & the track** — what's playing when, where the song breathes, the sonic fingerprint. Artifact: a timbral-and-spatial inventory.

For each pass, you do three things: **describe what's there in plain language** ("the kick is on every beat — it's a four-on-the-floor pulse"), **ask him whether each element is essence or decoration** — make him commit before you tell him; this is the move that builds the producer's ear — and **close the pass by writing its short plain-language artifact**, which later steps consume.

The full listening protocol lives in `references/listening-layers.md`. Read it before Step 3.

### Step 4 — Layer 2: the theory pass (only if he wants it)

After Layer 1, ask: "Want the theory pass? I'll name what we just heard with formal vocabulary — Roman numerals for the chord motion, the rhythmic feel by name, etc. Or we can skip and write the lesson."

If yes, walk through the same elements again with formal names. The vocabulary lives in `references/theory-pass.md`.

The reason this is a separate, opt-in pass: the producer's-ear language ("the chord moves to a darker place") is what you actually use when you're making music. The theory language ("it's a iv chord — modal interchange from minor") is what lets you *talk about it* and recognize the same move in a future song. You want both, but in that order — feel first, then name.

### Step 5 — Essence vs. decoration, made explicit

Now build the two-column list together. Not a table you write — a conversation where you propose an item and he commits it to a side. The framework, the test, and the common patterns are in `../cover-common/framework.md`.

End this step with a clean **typed** essence list — each item tagged with one of the six essence types in `../cover-common/framework.md`, confirmed by the counterfactual substitution test — and however many decoration items came up. 3–5 items max; typed lists naturally tend toward 2–4, which is fine.

### Step 6 — Keep / Drop / Replace

Translate to the OP-1's tape tracks (three or four per the lesson contract) per `../cover-common/framework.md`. This is where Nick's *interpretation* lives — wild replacements are the cover becoming his.

---

## The lesson file

When the deconstruction is done, write to `field/lessons/NN-cover-<slug>.md` using `../cover-common/lesson-template.md`. The deconstruct-specific deltas:

- **Section 1 (The song):** title, artist, the one-sentence "why this song" Nick gave you in Step 1. When he opens the file later, he sees his own gut answer.
- **Section 2 (Reference card):** frame as *"What you heard vs. what's there"* — his guesses on the left, the reality on the right, with the specific cue named for each one he missed. Three or four rows max — only the ones that actually taught something.
- **No graduation checkpoint** — that's a `song-recipe` move. The value here is that Nick *generated* the essence/decoration list, not that he received it.

---

## After Nick records and gives you a retrospective

Follow the shared retrospective flow at the bottom of `../cover-common/lesson-template.md`. No graduation-signal watch — Nick is already in the deconstruct phase.

---

## Tone reminders specific to this skill

- This is a *dialogue*, not a lecture. If you find yourself writing more than ~150 words without asking him something, you've drifted into lecture mode.
- His wrong answers are the most valuable thing in the session. Treat them like gold, not like errors.
- Never tell him the song is "complex" or "too advanced." Either pick a substitution and tell him why, or proceed and simplify in keep/drop/replace. Hedging is a failure mode.
- The OP-1's constraints are the feature. When he hits a wall ("I can't get that synth tone"), the right move is "good — what's the OP-1 voice that captures the *function* of that sound?" (Function-over-timbre is also in `../cover-common/framework.md`.)
- **The cover is not the original.** *Constellation*'s covers are the rig's version, not faithful renditions (see `feedback_covers_not_same_style` in project memory, and `album.md`'s 40oz Method section). When Nick proposes a wild replacement or a stylistic departure, that's the method working — affirm it, don't hedge it back toward the original. When *you* propose a replacement, don't frame it as a compromise relative to the original. The version is the version.

---

## File pointers

### Shared with `song-recipe` (`../cover-common/`)
- `prelude.md` — read-the-room, WebSearch lookup, readiness check
- `framework.md` — essence-vs-decoration, keep/drop/replace, function-over-timbre
- `lesson-template.md` — lesson file structure + shared retrospective flow
- `local-analysis.md` — how to detect and use the local audio-analysis MCP

### Skill-specific (`references/`)
- `listening-layers.md` — the six-pass, form-first producer's-ear walkthrough protocol
- `theory-pass.md` — formal music theory vocabulary for Layer 2
- `quiz-calibration.md` — how to adapt quiz difficulty based on Nick's *Listening skills learned* count

