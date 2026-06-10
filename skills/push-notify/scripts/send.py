#!/usr/bin/env python3
"""Entry point: push a notification to Nick's phone via ntfy.

Usage:
  ~/.claude/skills-venv/bin/python send.py --title "Render done" --message "Dahlias batch finished"
  ~/.claude/skills-venv/bin/python send.py --title "Dahlia's song session" \
      --message "Her take on 'Here Comes the Sun' is ready" --click "obsidian://..." --tags "musical_note"
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import load_config
from ntfy import push, NtfyError


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", default="")
    p.add_argument("--message", required=True)
    p.add_argument("--priority", default="default")
    p.add_argument("--tags", default="")
    p.add_argument("--click", default="", help="URL opened on tap")
    p.add_argument("--topic", default="", help="override the config topic")
    p.add_argument("--markdown", action="store_true")
    args = p.parse_args()

    try:
        cfg = load_config()
    except FileNotFoundError as e:
        print(json.dumps({"status": "config_required", "reason": str(e)}))
        sys.exit(0)

    try:
        result = push(
            cfg["server"], args.topic or cfg["topic"], args.message,
            title=args.title, priority=args.priority, tags=args.tags,
            click=args.click, markdown=args.markdown, auth_token=cfg.get("auth_token", ""),
        )
    except NtfyError as e:
        print(json.dumps({"status": "error", "reason": str(e)}))
        sys.exit(1)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
