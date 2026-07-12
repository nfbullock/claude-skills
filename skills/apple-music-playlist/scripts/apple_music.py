"""Apple Music API wrapper: search, create playlist, add tracks."""
import re
from typing import Optional
from urllib.parse import quote

import requests

API_BASE = "https://api.music.apple.com"

_PARENS = re.compile(r"[\(\[].*?[\)\]]")  # "(Original Version)", "[Remix]", etc.
_NONWORD = re.compile(r"[^\w\s]")


def _norm(s: str) -> str:
    """Lowercase, drop parenthetical asides and punctuation, collapse whitespace."""
    s = _PARENS.sub(" ", s.lower())
    s = _NONWORD.sub(" ", s)
    return " ".join(s.split())


def _tokens(s: str) -> set[str]:
    return set(_norm(s).split())


def _is_match(want_artist: str, want_title: str, attrs: dict) -> bool:
    """A candidate is a real match only if BOTH artist and title genuinely align.

    Guards against the failure mode where an unavailable dub track silently
    resolves to whatever Apple surfaced first (e.g. Bonnie Tyler for Scientist).
    """
    cand_artist = attrs.get("artistName", "")
    cand_title = attrs.get("name", "")

    # Title: normalized equality, or one is a clean substring of the other
    # (handles "Killa Dub" vs "Politician / Killa Dub", "X" vs "X - Single").
    nt_want, nt_cand = _norm(want_title), _norm(cand_title)
    title_ok = (
        nt_want == nt_cand
        or nt_want in nt_cand
        or nt_cand in nt_want
        or _tokens(want_title) <= _tokens(cand_title)
    )

    # Artist: token overlap in either direction. Featured-artist credits and
    # "& The Aggrovators" tails mean we can't demand exact equality, but we do
    # demand that the wanted artist's name actually appears.
    at_want, at_cand = _tokens(want_artist), _tokens(cand_artist)
    artist_ok = bool(at_want) and (at_want <= at_cand or at_cand <= at_want or len(at_want & at_cand) >= 1 and len(at_want) <= 2)
    # For multi-word artists require the full name to be present to avoid
    # one-token false positives ("Revolution" matching "Revolutionaries").
    if len(at_want) > 2:
        artist_ok = at_want <= at_cand

    return title_ok and artist_ok


class AppleMusicError(Exception):
    pass


class AuthRequired(AppleMusicError):
    """Raised on 401/403 from /me/* — signals MUT refresh needed."""


class AppleMusic:
    def __init__(self, developer_token: str, music_user_token: str, storefront: str = "us"):
        self.dev_token = developer_token
        self.mut = music_user_token
        self.storefront = storefront

    def _headers(self, include_user: bool = False) -> dict:
        h = {
            "Authorization": f"Bearer {self.dev_token}",
            "Content-Type": "application/json",
        }
        if include_user:
            h["Music-User-Token"] = self.mut
        return h

    def total_duration_ms(self, song_ids: list[str]) -> int:
        """Sum the runtime (ms) of the given catalog songs in one batched call."""
        if not song_ids:
            return 0
        url = f"{API_BASE}/v1/catalog/{self.storefront}/songs"
        r = requests.get(url, headers=self._headers(),
                         params={"ids": ",".join(song_ids)}, timeout=10)
        if r.status_code != 200:
            return 0
        return sum(
            s.get("attributes", {}).get("durationInMillis", 0)
            for s in r.json().get("data", [])
        )

    def search_song(self, artist: str, title: str, album: Optional[str] = None) -> Optional[str]:
        """Return the catalog song ID, or None if not found."""
        queries = []
        if album:
            queries.append(f"{artist} {title} {album}")  # album-qualified first, more precise
        queries.append(f"{artist} {title}")

        for q in queries:
            url = f"{API_BASE}/v1/catalog/{self.storefront}/search"
            params = {"term": q, "types": "songs", "limit": 25}
            r = requests.get(url, headers=self._headers(), params=params, timeout=10)
            if r.status_code in (401, 403):
                raise AuthRequired(f"catalog search {r.status_code}: {r.text}")
            if r.status_code != 200:
                continue
            songs = r.json().get("results", {}).get("songs", {}).get("data", [])

            # 1) Exact artist+title wins outright.
            for s in songs:
                a = s.get("attributes", {})
                if a.get("artistName", "").lower() == artist.lower() and \
                        a.get("name", "").lower() == title.lower():
                    return s["id"]
            # 2) Otherwise the first candidate that genuinely matches BOTH fields.
            #    NO blind fallback to songs[0] — a non-match returns None and is
            #    logged as skipped, never silently swapped for the wrong song.
            for s in songs:
                if _is_match(artist, title, s.get("attributes", {})):
                    return s["id"]
        return None

    def create_playlist(self, name: str, description: str, track_ids: list[str]) -> dict:
        """Create a library playlist with the given tracks. Returns {id, url}."""
        url = f"{API_BASE}/v1/me/library/playlists"
        body = {
            "attributes": {"name": name, "description": description},
            "relationships": {
                "tracks": {
                    "data": [{"id": tid, "type": "songs"} for tid in track_ids]
                }
            },
        }
        r = requests.post(url, headers=self._headers(include_user=True), json=body, timeout=15)
        if r.status_code in (401, 403):
            raise AuthRequired(f"create playlist {r.status_code}: {r.text}")
        if r.status_code not in (200, 201):
            raise AppleMusicError(f"create playlist {r.status_code}: {r.text}")
        data = r.json()["data"][0]
        return {"id": data["id"], "url": self._playlist_url(data)}

    def _playlist_url(self, playlist_data: dict) -> str:
        """Build a shareable URL.

        Library playlists carry a global catalog id in
        attributes.playParams.globalId when available; that yields a public,
        shareable link. Otherwise we fall back to the library id, which only
        resolves in Nick's own signed-in browser.
        """
        attrs = playlist_data.get("attributes", {})
        global_id = attrs.get("playParams", {}).get("globalId")
        if global_id:
            slug = quote(attrs.get("name", "playlist").lower().replace(" ", "-"))
            return f"https://music.apple.com/{self.storefront}/playlist/{slug}/{global_id}"
        return f"https://music.apple.com/library/playlist/{playlist_data['id']}"

