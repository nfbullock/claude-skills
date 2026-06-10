# Quiz Calibration

This is the rule that makes the skill *adaptive over time*. Read it before Step 2 of the deconstruction.

The principle Nick gave: **start at a crawl, pick up the pace.** Be explanatory at first, then withhold more, then eventually challenge inference. It's a layering problem — early you're teaching cues by naming them; later you're testing whether he can name them himself.

---

## The signal: per-domain skill counts

The signal is the entries under **"Listening skills learned"** in `playground/JOURNAL.md` — but counted **per domain**, not as one lump. Each entry carries a domain tag (the lesson template's Section 10 emits it): one of

**rhythm | harmony | melody | form | lyric | timbre**

— matching the six passes of the producer's-ear walkthrough (`listening-layers.md`).

**Compute the difficulty level PER DOMAIN.** Nick's ear does not develop uniformly: a strong melodic ear and a weak rhythmic ear means hard melody questions and gentle rhythm questions *in the same session*. One global difficulty number flattens exactly the differences that matter.

Legacy entries without a tag: assign a best-guess domain as you read them (most early ones are rhythm or harmony). Don't rewrite the journal to add tags unless you're already in there appending.

---

## Difficulty levels

The levels are unchanged — what changed is that the count that places him in a level is **the count for the domain you're currently quizzing.**

### Level 0 — Crawl mode (0–1 skills learned in this domain)

Maximum explanation, zero withholding.

- Reveal the answer immediately when he guesses anything.
- Even when he's right, *spell out* the cue he used: "You heard the snare on 2 and 4, which is why you got the tempo right."
- Volunteer cues he didn't ask about: "By the way, the reason this song *feels* like it's in major even though it's actually in minor is the IV chord — when minor songs use a IV instead of a iv, the brightness gets borrowed back in."
- Use plain language exclusively. Defer all theory naming to Layer 2 if he opts in.

The goal at this level: he's building a *library of cues*. Don't make him work for any of them. Hand them over.

### Level 1 — Walk mode (2–4 skills learned in this domain)

He has some cues in this domain but not many. Start asking him to *try again* before revealing.

- When he gets something wrong, give a directional hint and one re-guess: "Tempo's faster than you said — try counting the hi-hat between snare hits and tell me what you get."
- After his second guess (right or wrong), reveal and name the cue.
- When he gets something right, ask him *what cue he used* before validating: "Yes — what made you hear it as minor?" If he can't articulate, name it for him.
- You can start using formal terms in Layer 1, but always paired with the plain-language version: "This is a halftime feel — the snare on 3 makes the song feel half-speed."

The goal at this level: he's starting to *connect cues to outcomes*. The hint is what teaches him the cue applies *here*.

### Level 2 — Run mode (5–9 skills learned in this domain)

Real ear training accumulated in this domain. Now you're testing inference — can he recognize a cue he learned in *another* song?

- Withhold the answer and ask leading questions: "Listen to the bridge again. What cue from your past lessons applies here?"
- Reference his own learned skills explicitly: "Two lessons ago you learned to spot modal interchange. Try that lens on the chorus."
- When he gets it: "Right. You just transferred the cue from [previous song]. That's the actual skill — pattern recognition across songs."
- When he doesn't: name the cue, name the song he learned it in, and connect them: "This is the same move as [song] — modal interchange to bVI. Your ear missed it because [the surface element was different — different tempo, different instrument, etc.]."
- Theory vocabulary by default in Layer 1, with plain language only when a new term comes up.

The goal at this level: he's building *inference*. He has the cues; the skill now is applying them under unfamiliar surface conditions.

### Level 3 — Sprint mode (10+ skills learned in this domain)

He's becoming a producer — in this domain. Quiz hard.

- Don't volunteer answers. Ask, wait, ask harder.
- Sometimes set him up to be wrong — pick a song that uses a cue *similar to but different from* one he knows, and see if he overgeneralizes. ("You said this was modal interchange to bVI, but listen again — the bass moved with it. That's not interchange, that's a key change.") This is how he learns the *limits* of cues.
- Skip Layer 2 by default; ask if he wants it. He probably has the vocabulary already and the theory pass is now redundant.
- The deconstruction can become more peer-to-peer: "What do *you* think is essence here? Walk me through your reasoning."

The goal at this level: he's developing *judgment*. The skill is no longer transferring cues; it's calibrating his confidence.

---

## Wrong answers are gold — we deliberately reject "errorless learning"

Naming this explicitly because an external report once imported clinical memory-rehab doctrine here — minimize errors, never let the learner guess wrong — and we refused it. That doctrine is for impaired memory systems; this is deliberate-practice ear training, and **productive failure is the engine.** A wrong guess followed by the cue that explains the miss is worth more than ten correct guesses he can't articulate.

So: keep treating his wrong answers as the most valuable thing in the session. Keep the Level-3 set-him-up-to-be-wrong move — overgeneralizing a cue and getting caught is how he learns the cue's *limits*. Never soften a quiz to protect him from a miss.

---

## Two light mechanisms on top of the levels

### Spaced re-testing

A cue logged in the journal isn't a cue retained. Every **2–3 covers**, pull one *previously learned* cue from the journal and re-quiz it in the current song ("you've got halftime in your kit already — is this one?"). On success, **stretch the interval** — next re-test of that cue comes after more covers, not fewer. On a miss, the cue goes back into short rotation. One re-test per session, woven into the walkthrough; this is seasoning, not a unit test.

### Transfer tests — the real proficiency instrument

Recognition in **unfamiliar material** is what proves a cue became a skill. The mechanism: play Nick a song he doesn't know in the same genre — the lesson's **reference playlist** is the delivery vehicle; seed it with one stranger — and ask him to spot the learned cue cold. No setup, no hint: "somewhere in this track is a move you already know. Name it."

Spotting a cue in the song you taught it on is memory. Spotting it in a song nobody analyzed for him is the skill. Log transfer-test results (hit or miss, domain) in **Notes for the coach** so the trail accumulates.

---

## The Cover-phase flip — operational criterion

The `Cover phase` flip from `recipe` to `deconstruct` (watched by `song-recipe` via the lesson template's graduation-signal watch) now has an operational trigger: **consistent transfer-test success across domains** — Nick spotting learned cues in unfamiliar songs not just in his strongest domain but across several of the six. That's the signal that fires the *suggestion*.

But the criterion only governs when you raise it. **Graduation remains a promotion Nick accepts, never a test he passes.** Frame it that way, and Nick decides.

---

## How to read the journal

Open `playground/JOURNAL.md`. Find the section header `## Listening skills learned`. Count the bullet lines under it **per domain tag** (ignore the line `(populated once cover lessons begin)` if it's still there from the template).

If the section doesn't exist yet (first cover ever), treat every domain as Level 0.

The counts are approximate — what matters is *which level* they put him in per domain, not the exact numbers. Use judgment. If the **Notes for the coach** section says "Nick struggles to hear chord changes," knock the harmony level down even if the harmony count is high. Notes-for-the-coach observations and transfer-test misses both outrank the raw count.

---

## What the levels are *not*

This is not a "respect his ability" rule. It's a *teaching cadence* rule. Even at Level 3 in one domain, you should still volunteer cues for domains he hasn't built yet (e.g., a song that introduces an entirely new technique he's never encountered). The level only governs how you handle the cues he's already in process of acquiring — domain by domain.

If you're ever unsure, default *down* a level. A too-easy quiz is mildly annoying; a too-hard quiz makes him stall and lose the session.
