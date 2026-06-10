"""Developer Token (JWT) generation + credential loading."""
import json
import time
from pathlib import Path

import jwt  # pyjwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key

CRED_PATH = Path.home() / ".config" / "apple-music-skill" / "credentials.json"


def load_credentials() -> dict:
    if not CRED_PATH.exists():
        raise FileNotFoundError(
            f"No credentials at {CRED_PATH}. See README for setup."
        )
    with CRED_PATH.open() as f:
        creds = json.load(f)
    # Expand ~ in private_key_path
    creds["private_key_path"] = str(Path(creds["private_key_path"]).expanduser())
    return creds


def generate_developer_token(creds: dict, ttl_days: int = 180) -> str:
    """Generate an ES256-signed JWT for the Apple Music API.

    ttl_days max is 180 per Apple's spec. Regenerated in memory each call (~1ms),
    so the developer token is never persisted.
    """
    with open(creds["private_key_path"], "rb") as f:
        private_key = load_pem_private_key(f.read(), password=None)

    now = int(time.time())
    payload = {
        "iss": creds["team_id"],
        "iat": now,
        "exp": now + (ttl_days * 24 * 60 * 60),
    }
    headers = {"alg": "ES256", "kid": creds["key_id"]}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


def get_music_user_token(creds: dict) -> str:
    mut = creds.get("music_user_token")
    if not mut:
        raise ValueError(
            "No music_user_token in credentials. Run serve_bridge.py first."
        )
    return mut
