"""Config loader for the ntfy push skill."""
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "push-notify" / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"No config at {CONFIG_PATH}. See README.")
    with CONFIG_PATH.open() as f:
        cfg = json.load(f)
    cfg.setdefault("server", "https://ntfy.sh")
    cfg.setdefault("auth_token", "")
    if not cfg.get("topic"):
        raise FileNotFoundError(f"No 'topic' set in {CONFIG_PATH}.")
    return cfg
