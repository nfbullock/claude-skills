"""ntfy sender — push a notification to Nick's phone via ntfy.

ntfy needs no Apple developer app: Nick installs the ntfy iOS/Mac app, subscribes to a
secret topic, and any HTTP POST to that topic shows up as a push. Plain HTTPS, no HTTP/2,
no JWT. Self-hostable on the Studio for full privacy; defaults to the public ntfy.sh.
"""
import json

import requests


class NtfyError(Exception):
    pass


def push(server: str, topic: str, message: str, *, title: str = "", priority: str = "default",
         tags: str = "", click: str = "", actions: list[dict] | None = None,
         attach: str = "", markdown: bool = False, auth_token: str = "") -> dict:
    """Publish one notification. Returns {status, id}.

    priority: min|low|default|high|urgent (or 1..5)
    tags:     comma-separated emoji shortcodes, e.g. "musical_note,girl"
    click:    URL opened when the notification is tapped
    actions:  ntfy action buttons, e.g. [{"action":"view","label":"Open","url":"..."}]
              or [{"action":"http","label":"Approve","url":"https://.../approve/123",
                   "method":"POST"}]  — this is how the "ask dad" approve/deny unlock works.
    """
    url = f"{server.rstrip('/')}/{topic}"
    headers = {}
    if title:
        headers["Title"] = title
    if priority:
        headers["Priority"] = str(priority)
    if tags:
        headers["Tags"] = tags
    if click:
        headers["Click"] = click
    if attach:
        headers["Attach"] = attach
    if markdown:
        headers["Markdown"] = "yes"
    if actions:
        # ntfy accepts a JSON actions array via the X-Actions header (as a JSON string).
        headers["Actions"] = json.dumps(actions)
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    r = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=10)
    if r.status_code != 200:
        raise NtfyError(f"{r.status_code}: {r.text}")
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    return {"status": r.status_code, "id": body.get("id", "")}
