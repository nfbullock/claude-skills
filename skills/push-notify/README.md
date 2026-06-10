# push-notify — setup (ntfy)

Push notifications to Nick's phone/Mac from any machine. No Apple developer account, no app build.

## One-time setup
1. **Install the ntfy app** on your iPhone (App Store) and/or Mac. Free.
2. **Pick a secret topic** — a long random string, e.g. `dad-7f3a9c2e1b4d`. Anyone who knows the
   topic on `ntfy.sh` can publish to it, so treat it like a password. (Or self-host — see below.)
3. **Subscribe** to that topic in the ntfy app (Subscribe → type the topic).
4. **Config:**
   ```bash
   mkdir -p ~/.config/push-notify && chmod 700 ~/.config/push-notify
   cp config.example.json ~/.config/push-notify/config.json
   # set "topic" to your secret string
   chmod 600 ~/.config/push-notify/config.json
   ```
5. **Deps:** `requests` only (already in ~/venv/default from the music skill). Nothing else.
6. **Test:**
   ```bash
   ~/venv/default/bin/python scripts/send.py --title "Test" --message "hello from push-notify" --tags "wave"
   ```
   `{"status": 200, ...}` and a buzz on your phone = working.

## On Dahlia's Linux laptop
Same `config.json` + the ntfy publish is just an HTTPS POST, so `send.py` (or a direct `curl
-d "msg" ntfy.sh/<topic>`) works from Linux unchanged. Nothing Apple-specific touches her machine.

## Self-hosting (full privacy)
Run ntfy on the always-on Mac Studio (`brew install ntfy`, `ntfy serve`), set `"server"` in config
to the Studio's address, enable access control, and put the token in `"auth_token"`. Then topics
aren't world-publishable.

## Approve/deny action buttons
`ntfy.py push(...)` takes an `actions=[...]` list — an `{"action":"http","label":"Approve",
"url":".../approve/<id>","method":"POST"}` button hits a caller-owned endpoint. The consuming
project owns the lock/state; the push is only the signal. (Example consumer: the dahlias-laptop
song-session — design lives in that project at `song-session-design.md`, not here.)

# topic
dad-85ba0c6acd12da4d0753