---
name: yt-discuss
description: Pull down a YouTube transcript (creator subs preferred, local Whisper STT fallback), load it into context, then give a one-line verdict + 2–4 reactions on the video and ask Nick what he wants to talk about. Invoke when Nick shares a YouTube URL with intent to discuss it, or when the legacy yt-chat script hands you a pre-fetched transcript path.
---

# yt-discuss

Two ways this skill gets invoked. Detect which one and act accordingly.

## A) URL handed to you in this session (default path)

The user's message contains a YouTube URL — `youtube.com/watch?v=...`, `youtu.be/...`, `youtube.com/shorts/...`, or similar — and intent to discuss the video.

**Fetch the transcript yourself:**

1. Extract the URL from the message.
2. Run `~/.claude/skills/yt-discuss/fetch.sh <url>` via the Bash tool. The script tries creator subs first, falls back to local whisper.cpp STT (`whisper-large-v3-turbo`) if no subs are available. It prints shell-evalable metadata to stdout:
   ```
   TITLE='...'
   SOURCE=creator-subs|whisper-cpp-large-v3-turbo
   TRANSCRIPT_PATH=/Users/dad/.claude/skills/yt-discuss/transcripts/YYYYMMDD-HHMMSS.txt
   WORDS=1234
   ```
3. The STT path can take a minute or two on long videos — the script writes progress to stderr. That's expected, not a hang.
4. Use the printed `TRANSCRIPT_PATH` for the next step.

If the user's message also includes a framing line ("I'm trying to learn this", "skeptical, want a sanity check", "evaluating whether to recommend it", etc.), let it shape the verdict and which 2–4 reactions you pick. Don't ignore it; don't quote it back at him either.

## B) Transcript already prepared (legacy yt-chat path)

The opening user message was synthesized by the `yt-chat` bash script in `projects/youtube/` and contains:

- Video title and URL
- Transcript source label (`creator-subs` or `whisper-cpp-large-v3-turbo`)
- An explicit `Transcript path:` line pointing at a file on disk
- Optionally a `User's framing for this conversation:` line

Skip the fetch step — go straight to "What to do."

## What to do (both paths)

1. **Read the transcript file.** Use the Read tool on the path.
2. **Assess transcript quality before responding.** Look for:
   - Long unpunctuated runs (auto-subs hallmark)
   - Garbled words, nonsense phrases, repeated stutters
   - Heavy `[Music]` / `[Applause]` density with little speech
   - Obviously misheard technical terms or names
3. **Open with a one-line verdict.** Nick wants a clear call before the reactions, not just analysis. Pick one:
   - **Watch it** — the video itself is worth his time; engaging with it directly will be more valuable than summary discussion.
   - **Skip the video, the ideas are worth discussing** — the content is mid or padded, but there's a real kernel here we can riff on without him sitting through it.
   - **Close the chat** — there's nothing here. No real argument, no useful kernel, the premise is broken or it's pure content-marketing fluff. Say so plainly.
   - Hybrid verdicts are fine ("skim the first 5 minutes, skip the rest") when honest.
   Don't hedge. The verdict is the headline; reactions justify it.
4. **Then give feedback on the video** — not a summary, *feedback*. Pick the 2–4 things most worth reacting to: a strong argument, a weak one, an interesting framing, something that connects to other ideas, a claim that seems off. Be direct, not deferential. Length: short — a few short paragraphs or a tight bulleted reaction.
5. **If transcription is annoying, say so up front in one sentence** before the verdict. Examples:
   - "Heads up: auto-sub quality on this one is rough — proper nouns and technical terms are mangled, so take my reactions to specifics with a grain of salt."
   - "Transcript has long unpunctuated runs; I can follow the gist but exact quotes won't be reliable."
   - Don't flag minor noise. Only flag when it materially affects the feedback you can give.
6. **End with: "What do you want to talk about?"** — exactly that, on its own line.

## Style

- Nick is an ENTP Python dev who likes direct engagement, not hedged book-report summaries. Skip "the video discusses..." framing.
- Treat this as a conversation opener, not an essay. Aim for under ~250 words including the feedback.
- Don't praise the video unless you actually have a reason to.

## Files

- `fetch.sh` — the transcript fetcher (creator subs → whisper.cpp STT fallback). Standalone; safe to invoke from any session.
- `transcripts/` — local cache of fetched transcripts. Filename is `YYYYMMDD-HHMMSS.txt`.
