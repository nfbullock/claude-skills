---
name: model-check
description: Check whether open-weights SOTA has leapt past the local AI models Nick keeps on disk, across all four domains (LLM, STT, TTS, image). Detects the real Mac Studio hardware profile at runtime and researches LIVE from Hugging Face + Reddit + leaderboards — never from training data. Invoke as /model-check (all domains) or /model-check <llm|stt|tts|image> for one. Also runs autonomously every Monday 9am via launchd, staying silent unless something actually leapt, and pushing Nick's phone when it does. Trigger when Nick asks whether his local models are still the best, what's new in local AI, or "should I be running something better."
status: active
---

# model-check

"Am I still playing with the best local models available, for every domain?"

This is the skill version of `~/.local/bin/model_watcher.py`. The engine lives at
`scripts/model_watcher.py` in this directory; `~/.local/bin/model_watcher.py` is a
symlink to it.

## The non-negotiables

1. **Never answer from training data.** The whole point is to catch releases that
   postdate any model's knowledge. Every verdict must come from pages actually
   fetched *now* — Hugging Face trending + leaderboards, the relevant subreddit,
   image/TTS arenas. If you can't load fresh sources, say so and declare no leap.
2. **Hardware is detected, not assumed.** The script reads `system_profiler` each
   run. Don't hardcode "M4 Max / 36 GB" — let the profile speak.
3. **Be stingy about "leap."** A leap is something Nick would *notice in daily use*
   — a new family, a new architecture, a model newly fitting the memory envelope.
   Not a 2-point benchmark bump, not a finetune, not a same-family size variant.

## Domains

`llm` · `stt` · `tts` · `image`. The four subfolders under
`/Volumes/NewSamsung/models/standalone/`.

## Interactive run (Nick typed /model-check)

1. `~/venv/default/bin/python <this>/scripts/model_watcher.py --print-context`
   → JSON with `hardware`, `envelope`, per-domain `inventory`, the curated
   `domains` source list, and the last-saved `state`.
2. For each requested domain, do the research **yourself** with WebSearch/WebFetch,
   hitting the sources named in `domains[d].sources`. Ground every claim in a URL
   you actually read.
3. Present a tight table: domain · on-disk · current frontier · leap? · what to pull.
4. Persist each domain's new frontier so the autonomous run has fresh state:
   `echo '{"domain":"llm","frontier":"..."}' | python .../model_watcher.py --save`
5. If anything genuinely leapt, offer to update the `reference_local_models.md`
   memory note and/or drop a next-action in Things to download it.

## Autonomous run (launchd, Mondays 9am)

`launchctl` loads `com.bullock.model-watcher.plist`. It runs
`model_watcher.py` with no args → loops all four domains via `claude -p` (live
web/HF/Reddit research), saves state, and **stays silent unless something leapt**.
On a leap it prints to the log *and* pushes Nick's phone via the push-notify skill.

- Logs: `~/Library/Logs/model-watcher/launchd.{out,err}`
- State: `~/.model_watcher/state.json` (per-domain frontier + last_run)
- Reload after edits: `launchctl unload ... && launchctl load ~/Library/LaunchAgents/com.bullock.model-watcher.plist`

## Notes

- The inventory is read straight from disk, so it self-corrects when Nick adds or
  removes a model. Don't trust the memory note's snapshot over the live listing.
- `llm/` on disk may be empty — Nick runs LLMs via Ollama, not as standalone
  folders. Treat "empty" as "tell me what the best option *would* be," not an error.
