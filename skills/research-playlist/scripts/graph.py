#!/usr/bin/env python3
"""The accumulating music-graph — the persistent substrate under discovery + audio-DNA.

Why this exists (SPEC-audio-dna.md §5): discovery used to be one hop and re-queried the
APIs every single run. This mirrors the network into a local SQLite graph that gets
richer + faster every time it's walked:

  - WRITE-THROUGH: every node + edge a fetch touches is persisted, tagged with its
    `source` (so "quorum" = "how many distinct sources vouch for this edge" is a query,
    not a heuristic). THREE similarity sources: ListenBrainz (session co-listening),
    Last.fm (scrobble co-occurrence), Discogs (label-adjacency — artists sharing the
    seed's home labels; in scene-based music the label IS the studio/house band).
  - READ-FIRST with a SLOW CLOCK: before hitting an API for a node's neighbors, check
    the DB — but expansions age out (default 120 days), so neighborhoods refresh and
    new artists can enter. A frozen graph is a stagnant graph (2026-07 adversarial
    review, finding: "expansions freeze every neighborhood at first fetch").
  - MULTI-HOP: BFS outward from seed(s) N hops, accumulating the subgraph as it walks.
    Candidate ranking is SCOPED TO THIS WALK (not the whole historical edge table) so
    hub artists don't accumulate cross-run gravity (the rich-get-richer finding), uses
    mean edge weight (not raw sum), demotes artists served in recent playlists (ledger)
    and — with --novelty-filter — DEMOTES rather than drops artists in Nick's library.
    Artist-level bans are forbidden by design: the exclusion unit is the worn TRACK,
    never the artist (the RHCP rule). --exclude-library exists only for explicit
    "only new artists" discovery runs.

audio_dna.py writes acoustic features into the `dna` table keyed by (node, version) —
the Zula acoustic and the Zula studio cut are different rows by design.

Usage:
  graph.py --seed "King Tubby" --seed "Scientist" --hops 2
  graph.py --seed "Augustus Pablo" --hops 3 --novelty-filter --skip-head 6
  graph.py --seed "Phosphorescent" --sources listenbrainz,lastfm --max-age-days 30
  graph.py --refresh-library        # rebuild the Apple-library artist set (osascript)
  graph.py --node "Scientist"       # inspect a persisted node + its neighbors
  graph.py --stats                  # node / edge / dna / library counts
"""
import argparse
import json
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# sibling imports (traverse.py) must work both as-script and when imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

DB_PATH = Path(__file__).resolve().parent.parent / "musicgraph.db"
CREDENTIALS = Path(__file__).resolve().parent.parent / "credentials.json"
# the sibling skill's playlist ledger — used to demote already-served artists
USED_TRACKS = (Path(__file__).resolve().parent.parent.parent
               / "apple-music-playlist" / "used_tracks.jsonl")

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes(
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,                 -- 'artist' | 'track'
  name TEXT NOT NULL,
  mbid TEXT,
  artist TEXT NOT NULL DEFAULT '',    -- track: performer; artist-node: '' (NULLs break UNIQUE)
  lastfm_playcount INTEGER,
  discogs_styles TEXT,                -- json list
  created_at TEXT,
  UNIQUE(kind, name, artist)
);
CREATE TABLE IF NOT EXISTS edges(
  src INTEGER NOT NULL,
  dst INTEGER NOT NULL,
  rel TEXT NOT NULL,                  -- 'similar_artist'|'similar_track'|'version_of'|'member_of'
  source TEXT NOT NULL,              -- 'listenbrainz'|'lastfm'|'musicbrainz'|'discogs'
  weight REAL,
  created_at TEXT,
  UNIQUE(src, dst, rel, source)       -- source column => quorum is queryable
);
CREATE TABLE IF NOT EXISTS dna(
  node_id INTEGER NOT NULL,
  version_key TEXT NOT NULL DEFAULT '',  -- 'mbid:<id>' | 'file:<sha1-16>' | '' (unversioned)
  features TEXT,                      -- json canonical feature vector (audio_dna.py)
  extracted_at TEXT,
  method TEXT,                        -- 'acousticbrainz' | 'librosa'
  PRIMARY KEY(node_id, version_key)   -- version-specific: acoustic != studio cut
);
CREATE TABLE IF NOT EXISTS expansions(
  node_id INTEGER NOT NULL,
  rel TEXT NOT NULL,
  source TEXT NOT NULL,
  fetched_at TEXT,
  PRIMARY KEY(node_id, rel, source)   -- "this node's neighbors for (rel,source) are fetched"
);
CREATE TABLE IF NOT EXISTS library_artists(
  name TEXT PRIMARY KEY,              -- lowercased Apple-library artist (novelty signal)
  refreshed_at TEXT
);
CREATE TABLE IF NOT EXISTS feedback(
  node_id INTEGER NOT NULL,
  verdict TEXT NOT NULL,              -- 'love' | 'skip'
  context TEXT NOT NULL DEFAULT '',   -- playlist/lesson it was heard in
  noted_at TEXT,
  PRIMARY KEY(node_id, verdict, context)  -- Nick's ears, one row per listen-context
);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src, rel);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst, rel);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(kind, name);
"""

REL_SIMILAR_ARTIST = "similar_artist"
REL_SIMILAR_TRACK = "similar_track"
DEFAULT_SOURCES = ("listenbrainz", "lastfm", "discogs")
DEFAULT_REFRESH_DAYS = 120   # expansions older than this re-fetch (slow-clock freshness)

DISCOGS_SEARCH = "https://api.discogs.com/database/search"
UA = "NickMusicResearch/0.1 (nick@bullock.im)"

# labels so broad that label-mates carry no similarity signal (conglomerate noise)
_MEGA_LABELS = {
    "columbia", "columbia records", "warner bros. records", "emi", "rca", "rca records",
    "atlantic", "atlantic records", "capitol records", "island records", "polydor",
    "epic", "mercury", "virgin", "universal", "universal music group", "warner music group",
    "sony music", "interscope records", "reprise records", "elektra", "mca records",
    "parlophone", "decca", "geffen records", "not on label", "self-released",
}


class Graph:
    """Thin, write-through persistence layer over the SQLite music-graph.

    All node writes funnel through upsert_node (case-insensitive dedup); all edge
    writes through add_edge (idempotent on UNIQUE(src,dst,rel,source), keeping the max
    weight seen). Callers commit() when done (or the CLI/traversal commits as it walks).
    """

    def __init__(self, path=DB_PATH):
        self.path = Path(path)
        self.db = sqlite3.connect(str(self.path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=8000")
        self.db.executescript(SCHEMA)
        self._migrate_dna_version_key()
        self.db.commit()

    def _migrate_dna_version_key(self):
        """Early DBs keyed dna by node_id only (version-blind — the Zula-acoustic bug)."""
        cols = {r[1] for r in self.db.execute("PRAGMA table_info(dna)")}
        has_orphan = self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dna_old'").fetchone()
        if "version_key" in cols:
            if has_orphan:   # a prior migration died mid-flight — recover its rows
                self.db.execute(
                    "INSERT OR IGNORE INTO dna(node_id,version_key,features,extracted_at,method) "
                    "SELECT node_id,'',features,extracted_at,method FROM dna_old")
                self.db.execute("DROP TABLE dna_old")
            return
        self.db.execute("ALTER TABLE dna RENAME TO dna_old")
        self.db.executescript(SCHEMA)
        self.db.execute(
            "INSERT INTO dna(node_id,version_key,features,extracted_at,method) "
            "SELECT node_id,'',features,extracted_at,method FROM dna_old")
        self.db.execute("DROP TABLE dna_old")

    # -- helpers -----------------------------------------------------------------
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def commit(self):
        self.db.commit()

    def close(self):
        self.db.commit()
        self.db.close()

    # -- nodes -------------------------------------------------------------------
    def upsert_node(self, kind, name, artist=None, mbid=None,
                    lastfm_playcount=None, discogs_styles=None):
        """Insert-or-enrich a node. Dedups case-insensitively on (kind,name,artist).
        Never clobbers an existing value with None (fields only fill forward)."""
        name = (name or "").strip()
        artist = (artist or "").strip()
        row = self.db.execute(
            "SELECT * FROM nodes WHERE kind=? AND lower(name)=lower(?) "
            "AND lower(artist)=lower(?)", (kind, name, artist)).fetchone()
        if row:
            nid = row["id"]
            sets, params = [], []
            if mbid and not row["mbid"]:
                sets.append("mbid=?"); params.append(mbid)
            if lastfm_playcount is not None:
                sets.append("lastfm_playcount=?"); params.append(int(lastfm_playcount))
            if discogs_styles is not None:
                sets.append("discogs_styles=?"); params.append(json.dumps(discogs_styles))
            if sets:
                params.append(nid)
                self.db.execute(f"UPDATE nodes SET {','.join(sets)} WHERE id=?", params)
            return nid
        cur = self.db.execute(
            "INSERT INTO nodes(kind,name,artist,mbid,lastfm_playcount,discogs_styles,created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (kind, name, artist, mbid,
             int(lastfm_playcount) if lastfm_playcount is not None else None,
             json.dumps(discogs_styles) if discogs_styles is not None else None,
             self._now()))
        return cur.lastrowid

    def get_node(self, node_id):
        r = self.db.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
        return dict(r) if r else None

    def find_node(self, kind, name, artist=None):
        artist = (artist or "").strip()
        r = self.db.execute(
            "SELECT * FROM nodes WHERE kind=? AND lower(name)=lower(?) "
            "AND lower(artist)=lower(?)", (kind, (name or "").strip(), artist)).fetchone()
        return dict(r) if r else None

    def set_mbid(self, node_id, mbid):
        if mbid:
            self.db.execute("UPDATE nodes SET mbid=? WHERE id=? AND (mbid IS NULL OR mbid='')",
                            (mbid, node_id))

    # -- edges -------------------------------------------------------------------
    def add_edge(self, src, dst, rel, source, weight=None):
        if src == dst:
            return
        self.db.execute(
            "INSERT OR IGNORE INTO edges(src,dst,rel,source,weight,created_at) VALUES(?,?,?,?,?,?)",
            (src, dst, rel, source, weight, self._now()))
        # keep the strongest weight seen for this exact edge
        self.db.execute(
            "UPDATE edges SET weight=MAX(ifnull(weight,0),?) WHERE src=? AND dst=? AND rel=? AND source=?",
            (weight or 0.0, src, dst, rel, source))

    def neighbors(self, node_id, rel, min_quorum=1):
        """Persisted neighbors of a node, aggregated with quorum + consensus weight."""
        rows = self.db.execute(
            "SELECT e.dst AS dst, n.name AS name, n.kind AS kind, n.artist AS artist, "
            "       COUNT(DISTINCT e.source) AS quorum, "
            "       GROUP_CONCAT(DISTINCT e.source) AS sources, "
            "       SUM(ifnull(e.weight,0)) AS wsum "
            "FROM edges e JOIN nodes n ON n.id = e.dst "
            "WHERE e.src=? AND e.rel=? "
            "GROUP BY e.dst HAVING quorum >= ? "
            "ORDER BY quorum DESC, wsum DESC", (node_id, rel, min_quorum)).fetchall()
        return [dict(r) for r in rows]

    # -- read-first bookkeeping (with a slow clock) --------------------------------
    def is_expanded(self, node_id, rel, source, max_age_days=None):
        """True if this node's neighbors were fetched recently enough. An expansion
        older than max_age_days counts as NOT expanded — re-fetch merges safely because
        add_edge is idempotent. None = never expires (raw cache check)."""
        row = self.db.execute(
            "SELECT fetched_at FROM expansions WHERE node_id=? AND rel=? AND source=?",
            (node_id, rel, source)).fetchone()
        if not row:
            return False
        if max_age_days is None:
            return True
        try:
            fetched = datetime.fromisoformat(row["fetched_at"])
            age_days = (datetime.now(timezone.utc) - fetched).days
        except (TypeError, ValueError):
            return False
        return age_days < max_age_days

    def mark_expanded(self, node_id, rel, source):
        self.db.execute(
            "INSERT OR REPLACE INTO expansions(node_id,rel,source,fetched_at) VALUES(?,?,?,?)",
            (node_id, rel, source, self._now()))

    # -- dna (audio_dna.py writes; ranker reads) — version-specific ----------------
    def put_dna(self, node_id, features, method, version_key=""):
        self.db.execute(
            "INSERT OR REPLACE INTO dna(node_id,version_key,features,extracted_at,method) "
            "VALUES(?,?,?,?,?)",
            (node_id, version_key or "", json.dumps(features), self._now(), method))

    def get_dna(self, node_id, version_key=None):
        """Exact version when version_key given; else the most recent row of any version."""
        if version_key is not None:
            r = self.db.execute(
                "SELECT features, method, extracted_at, version_key FROM dna "
                "WHERE node_id=? AND version_key=?", (node_id, version_key)).fetchone()
        else:
            r = self.db.execute(
                "SELECT features, method, extracted_at, version_key FROM dna "
                "WHERE node_id=? ORDER BY extracted_at DESC LIMIT 1", (node_id,)).fetchone()
        if not r:
            return None
        return {"features": json.loads(r["features"]), "method": r["method"],
                "extracted_at": r["extracted_at"], "version_key": r["version_key"]}

    # -- novelty signal (Apple-library artist set) ---------------------------------
    def refresh_library_artists(self):
        """Pull the distinct artist set from Nick's Apple Music library via osascript.
        Uses a linefeed delimiter so artist names containing commas survive."""
        import subprocess
        script = (
            'tell application "Music"\n'
            '  set od to AppleScript\'s text item delimiters\n'
            '  set AppleScript\'s text item delimiters to (ASCII character 10)\n'
            '  set out to (artist of every track of library playlist 1) as text\n'
            '  set AppleScript\'s text item delimiters to od\n'
            '  return out\n'
            'end tell')
        r = subprocess.run(["osascript", "-e", script],
                           capture_output=True, text=True, timeout=240)
        if r.returncode != 0:
            raise RuntimeError(f"osascript failed: {r.stderr.strip()[:200]}")
        names = {a.strip().lower() for a in r.stdout.split("\n") if a.strip()}
        now = self._now()
        self.db.execute("DELETE FROM library_artists")
        self.db.executemany(
            "INSERT OR IGNORE INTO library_artists(name,refreshed_at) VALUES(?,?)",
            [(n, now) for n in names])
        self.db.commit()
        return len(names)

    def in_library(self, name):
        return self.db.execute(
            "SELECT 1 FROM library_artists WHERE name=?",
            ((name or "").strip().lower(),)).fetchone() is not None

    # -- taste ledger (the debrief's "loved it / skipped it" lands here) -----------
    def add_feedback(self, artist, title, verdict, context=""):
        """One line of Nick's ear: he loved or skipped this track in this context.
        Loves become traversal seeds and DNA reference targets; skips correct the
        profiles. The single highest-signal input the engine has."""
        nid = self.upsert_node("track", title, artist=artist)
        self.db.execute(
            "INSERT OR REPLACE INTO feedback(node_id,verdict,context,noted_at) VALUES(?,?,?,?)",
            (nid, verdict, context or "", self._now()))
        self.commit()
        return nid

    def loved_tracks(self):
        return [dict(r) for r in self.db.execute(
            "SELECT n.artist, n.name AS title, f.context, f.noted_at, "
            "       (SELECT COUNT(*) FROM dna d WHERE d.node_id=n.id) AS dna_versions "
            "FROM feedback f JOIN nodes n ON n.id=f.node_id "
            "WHERE f.verdict='love' ORDER BY f.noted_at DESC")]

    def skipped_tracks(self):
        return [dict(r) for r in self.db.execute(
            "SELECT n.artist, n.name AS title, f.context, f.noted_at "
            "FROM feedback f JOIN nodes n ON n.id=f.node_id "
            "WHERE f.verdict='skip' ORDER BY f.noted_at DESC")]

    def loved_artist_set(self):
        return {r[0].strip().lower() for r in self.db.execute(
            "SELECT DISTINCT n.artist FROM feedback f JOIN nodes n ON n.id=f.node_id "
            "WHERE f.verdict='love' AND n.artist != ''")}

    def library_meta(self):
        row = self.db.execute(
            "SELECT COUNT(*) c, MAX(refreshed_at) m FROM library_artists").fetchone()
        age_days = None
        if row["m"]:
            try:
                age_days = (datetime.now(timezone.utc)
                            - datetime.fromisoformat(row["m"])).days
            except (TypeError, ValueError):
                age_days = None
        return {"count": row["c"], "age_days": age_days}

    def stats(self):
        def c(sql):
            return self.db.execute(sql).fetchone()[0]
        return {
            "nodes": c("SELECT COUNT(*) FROM nodes"),
            "artists": c("SELECT COUNT(*) FROM nodes WHERE kind='artist'"),
            "tracks": c("SELECT COUNT(*) FROM nodes WHERE kind='track'"),
            "edges": c("SELECT COUNT(*) FROM edges"),
            "edges_quorum2": c(
                "SELECT COUNT(*) FROM (SELECT src,dst,rel FROM edges "
                "GROUP BY src,dst,rel HAVING COUNT(DISTINCT source)>=2)"),
            "edges_quorum3": c(
                "SELECT COUNT(*) FROM (SELECT src,dst,rel FROM edges "
                "GROUP BY src,dst,rel HAVING COUNT(DISTINCT source)>=3)"),
            "dna": c("SELECT COUNT(*) FROM dna"),
            "expansions": c("SELECT COUNT(*) FROM expansions"),
            "library_artists": c("SELECT COUNT(*) FROM library_artists"),
            "db_path": str(self.path),
        }


# --- similarity fetchers -----------------------------------------------------------

def _discogs_token():
    try:
        return json.loads(CREDENTIALS.read_text())["discogs"].get("personal_token") or None
    except Exception:
        return None


def discogs_label_neighbors(artist_name, token, max_labels=3, polite=1.1):
    """Third similarity vote: artists sharing this artist's most-frequent home labels.
    Strong for scene-based music (dub/reggae/punk: the label IS the studio/house band);
    noisy for conglomerate rock — mega-labels are skipped and the quorum requirement
    filters the residual noise (a discogs-only neighbor never outranks a quorum-2 one)."""
    import urllib.parse
    import urllib.request

    def search(params):
        url = DISCOGS_SEARCH + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Authorization": f"Discogs token={token}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    d = search({"artist": artist_name, "type": "release", "per_page": 75})
    label_counts = Counter()
    for rel in d.get("results", []):
        lbs = rel.get("label") or []
        if lbs and lbs[0] and lbs[0].lower() not in _MEGA_LABELS:
            label_counts[lbs[0]] += 1

    neighbors = Counter()
    me = artist_name.lower()
    for lb, _ in label_counts.most_common(max_labels):
        time.sleep(polite)
        try:
            dl = search({"label": lb, "type": "release", "per_page": 75})
        except Exception:
            continue
        for rel in dl.get("results", []):
            title = rel.get("title") or ""       # Discogs format: "Artist - Release Title"
            if " - " not in title:
                continue
            a = title.split(" - ", 1)[0].strip()
            a = re.sub(r"\s*\(\d+\)$", "", a)    # strip Discogs "(2)" disambiguation
            if a and a.lower() not in ("various", me):
                neighbors[a] += 1
    # >=2 appearances on a shared label — filters one-off compilation guests
    return [name for name, cnt in neighbors.most_common(60) if cnt >= 2]


# --- multi-hop traversal ---------------------------------------------------------

def _ensure_artist_node(g, name, resolve_mbid, polite):
    """Upsert an artist node and (rate-limited) resolve its MBID if missing."""
    node = g.find_node("artist", name)
    nid = node["id"] if node else g.upsert_node("artist", name)
    node = g.get_node(nid)
    if not node.get("mbid"):
        try:
            r = resolve_mbid(name)
            if r:
                g.set_mbid(nid, r["mbid"])
        except Exception:
            pass
        time.sleep(polite)
    return nid


def _fetch_and_persist_similar(g, node_id, name, source, ctx, per_node_limit):
    """Fetch one source's similar-artist list and write the edges through. Returns count.
    A RAISED fetch (timeout/429) does NOT mark the expansion — a transient outage must
    not freeze the neighborhood for the whole TTL. A successful fetch retires the old
    (src,rel,source) edge set first, so a refresh is a true refresh, not add-only."""
    names = []
    try:
        if source == "listenbrainz":
            node = g.get_node(node_id)
            mbid = node.get("mbid")
            if not mbid:
                r = ctx["resolve_mbid"](name)
                mbid = r["mbid"] if r else None
                if mbid:
                    g.set_mbid(node_id, mbid)
            if mbid:
                names = ctx["lb_similar"](mbid)
    except Exception:
        return 0
    try:
        if source == "lastfm":
            names = ctx["lastfm_similar"](name, ctx["lastfm_key"])
        elif source == "discogs":
            names = discogs_label_neighbors(name, ctx["discogs_token"])
    except Exception:
        return 0
    g.db.execute("DELETE FROM edges WHERE src=? AND rel=? AND source=?",
                 (node_id, REL_SIMILAR_ARTIST, source))
    n = len(names) or 1
    for rank, nm in enumerate(names[:per_node_limit]):
        if not nm or nm.lower() == name.lower():
            continue
        dst = g.upsert_node("artist", nm)
        g.add_edge(node_id, dst, REL_SIMILAR_ARTIST, source, weight=round(1.0 - rank / n, 4))
    g.mark_expanded(node_id, REL_SIMILAR_ARTIST, source)
    g.commit()
    return len(names)


def served_artist_counts(window=15):
    """Artist appearance counts over the last `window` delivered playlists (ALL domains),
    from the sibling skill's used_tracks.jsonl ledger. Used to demote — never ban —
    artists the engine has already served, so repeat seeds walk progressively deeper."""
    counts = Counter()
    if not USED_TRACKS.exists():
        return counts, False
    entries = []
    try:
        for line in USED_TRACKS.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(e, dict):
                entries.append(e)
    except OSError:
        return counts, False
    for e in entries[-window:]:
        for t in (e.get("tracks") or []):
            if isinstance(t, dict) and t.get("artist"):
                counts[t["artist"].strip().lower()] += 1
    return counts, True


def traverse(g, seeds, hops=2, sources=DEFAULT_SOURCES,
             novelty_filter=False, exclude_library=False, per_node_limit=100,
             polite=1.1, limit=80, refresh_days=DEFAULT_REFRESH_DAYS, skip_head=6):
    """BFS outward from seeds, read-first (slow clock)/fetch-and-persist, ranking the
    reached artists by (quorum, demotion-adjusted mean weight, hop). Scoped to THIS
    walk's edges so historical runs don't pile popularity gravity onto hub artists."""
    from traverse import resolve_mbid, lb_similar, lastfm_similar, _lastfm_key
    ctx = {
        "resolve_mbid": resolve_mbid,
        "lb_similar": lb_similar,
        "lastfm_similar": lastfm_similar,
        "lastfm_key": _lastfm_key(),
        "discogs_token": _discogs_token(),
    }
    warnings = []

    # novelty signal wants a live library snapshot — auto-refresh when empty/stale
    if novelty_filter or exclude_library:
        meta = g.library_meta()
        if meta["count"] == 0 or meta["age_days"] is None or meta["age_days"] > 7:
            try:
                n = g.refresh_library_artists()
                warnings.append(f"library_artists auto-refreshed ({n} artists)")
            except Exception as e:
                warnings.append(f"library refresh FAILED ({str(e)[:80]}) — "
                                f"novelty signal uses stale/empty snapshot")

    before = g.stats()
    api_fetches = 0

    seed_ids = {}
    for s in seeds:
        nid = _ensure_artist_node(g, s, resolve_mbid, polite)
        seed_ids[nid] = s

    reached_hop = {nid: 0 for nid in seed_ids}   # node_id -> shortest hop distance
    queue = [(nid, seed_ids[nid], 0) for nid in seed_ids]
    enqueued = set(seed_ids)

    while queue:
        node_id, name, depth = queue.pop(0)
        if depth >= hops:
            continue
        for source in sources:
            if source == "lastfm" and not ctx["lastfm_key"]:
                continue
            if source == "discogs" and not ctx["discogs_token"]:
                continue
            if not g.is_expanded(node_id, REL_SIMILAR_ARTIST, source,
                                 max_age_days=refresh_days):
                _fetch_and_persist_similar(g, node_id, name, source, ctx, per_node_limit)
                api_fetches += 1
                time.sleep(polite)
        for nb in g.neighbors(node_id, REL_SIMILAR_ARTIST, min_quorum=1):
            dst = nb["dst"]
            nd = depth + 1
            if dst not in reached_hop or nd < reached_hop[dst]:
                reached_hop[dst] = nd
            if dst not in enqueued:
                enqueued.add(dst)
                queue.append((dst, nb["name"], nd))

    # ---- rank the reached artists, SCOPED to this walk's edges -------------------
    g.db.execute("DROP TABLE IF EXISTS _walk")
    g.db.execute("CREATE TEMP TABLE _walk(id INTEGER PRIMARY KEY)")
    g.db.executemany("INSERT OR IGNORE INTO _walk(id) VALUES(?)",
                     [(nid,) for nid in reached_hop])

    served, ledger_found = served_artist_counts()
    loved = g.loved_artist_set()

    candidates = []
    for nid, hop in reached_hop.items():
        if nid in seed_ids:
            continue
        agg = g.db.execute(
            "SELECT COUNT(DISTINCT e.source) q, COUNT(DISTINCT e.src) breadth, "
            "COUNT(*) n_edges, SUM(ifnull(e.weight,0)) w, "
            "GROUP_CONCAT(DISTINCT e.source) srcs "
            "FROM edges e JOIN _walk wk ON wk.id = e.src "
            "WHERE e.dst=? AND e.rel=?", (nid, REL_SIMILAR_ARTIST)).fetchone()
        if not agg["q"]:
            continue
        node = g.get_node(nid)
        in_lib = g.in_library(node["name"])
        if exclude_library and in_lib:
            continue    # only on explicit "new artists ONLY" runs — never the default
        key = node["name"].strip().lower()
        served_n = served.get(key, 0)
        in_loved = key in loved
        mean_w = (agg["w"] or 0.0) / (agg["n_edges"] or 1)
        # demote, don't drop: served artists sink; library artists sink on novelty
        # runs; artists Nick LOVED a track by get a modest, transparent lift
        factor = 1.0 / (1.0 + 0.5 * served_n)
        if novelty_filter and in_lib:
            factor *= 0.35
        if in_loved:
            factor *= 1.25
        candidates.append({
            "name": node["name"],
            "mbid": node.get("mbid"),
            "quorum": agg["q"],
            "sources": sorted((agg["srcs"] or "").split(",")) if agg["srcs"] else [],
            "breadth": agg["breadth"],            # walked nodes pointing here
            "consensus_weight": round(mean_w, 4),  # mean edge weight within this walk
            "effective_weight": round(mean_w * factor, 4),
            "hop": hop,
            "in_library": in_lib,
            "served_recently": served_n,
            "loved_artist": in_loved,
        })
    candidates.sort(key=lambda c: (c["quorum"], c["effective_weight"], -c["hop"]),
                    reverse=True)
    for rank, c in enumerate(candidates):
        c["deep_zone"] = rank >= skip_head   # fish past the obvious head

    after = g.stats()
    return {
        "seeds": list(seeds),
        "hops": hops,
        "sources": [s for s in sources
                    if not (s == "lastfm" and not ctx["lastfm_key"])
                    and not (s == "discogs" and not ctx["discogs_token"])],
        "novelty_filter": novelty_filter,
        "exclude_library": exclude_library,
        "refresh_days": refresh_days,
        "skip_head": skip_head,
        "served_ledger_found": ledger_found,
        "library": g.library_meta(),
        "api_fetches_this_run": api_fetches,
        "graph_growth": {
            "nodes": [before["nodes"], after["nodes"]],
            "edges": [before["edges"], after["edges"]],
        },
        "reached": len(reached_hop) - len(seed_ids),
        "warnings": warnings,
        "candidates": candidates[:limit],
    }


# --- CLI -------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", action="append", default=[])
    ap.add_argument("--hops", type=int, default=2)
    ap.add_argument("--sources", default=",".join(DEFAULT_SOURCES),
                    help="comma list of similarity sources to walk "
                         "(listenbrainz,lastfm,discogs)")
    ap.add_argument("--per-node-limit", type=int, default=100)
    ap.add_argument("--limit", type=int, default=80, help="max ranked candidates returned")
    ap.add_argument("--skip-head", type=int, default=6,
                    help="candidates ranked above this are flagged deep_zone=false")
    ap.add_argument("--max-age-days", type=int, default=DEFAULT_REFRESH_DAYS,
                    help="re-fetch a node's neighbors when its expansion is older than this")
    ap.add_argument("--novelty-filter", action="store_true",
                    help="DEMOTE artists already in Nick's Apple library (discovery runs; "
                         "auto-refreshes the library snapshot when stale)")
    ap.add_argument("--exclude-library", action="store_true",
                    help="hard-drop library artists — ONLY for explicit 'new artists only' "
                         "requests; never a curation default (the RHCP rule)")
    ap.add_argument("--polite", type=float, default=1.1, help="seconds between API fetches")
    ap.add_argument("--refresh-library", action="store_true",
                    help="rebuild the Apple-library artist set (osascript) then exit")
    ap.add_argument("--node", help="inspect a persisted artist node + its neighbors, then exit")
    ap.add_argument("--stats", action="store_true", help="print graph stats and exit")
    ap.add_argument("--love", action="append", default=[], metavar="'ARTIST :: TITLE'",
                    help="taste ledger: Nick loved this track (debrief ingest; repeatable)")
    ap.add_argument("--skip-track", action="append", default=[], metavar="'ARTIST :: TITLE'",
                    help="taste ledger: Nick skipped this track (repeatable)")
    ap.add_argument("--context", default="", help="playlist/lesson the feedback came from")
    ap.add_argument("--taste", action="store_true",
                    help="print the taste ledger (loves + skips) and exit")
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()

    g = Graph(args.db)

    if args.love or args.skip_track:
        noted = {"loved": [], "skipped": []}
        for spec, verdict, bucket in ((args.love, "love", "loved"),
                                      (args.skip_track, "skip", "skipped")):
            for s in spec:
                if "::" not in s:
                    print(json.dumps({"error": f"feedback needs 'Artist :: Title', got: {s}"}))
                    return
                a, t = [x.strip() for x in s.split("::", 1)]
                g.add_feedback(a, t, verdict, context=args.context)
                noted[bucket].append(f"{a} — {t}")
        print(json.dumps({"noted": noted, "context": args.context,
                          "loved_total": len(g.loved_tracks())}, indent=2, ensure_ascii=False))
        return

    if args.taste:
        print(json.dumps({"loved": g.loved_tracks(), "skipped": g.skipped_tracks()},
                         indent=2, ensure_ascii=False))
        return

    if args.refresh_library:
        try:
            n = g.refresh_library_artists()
            print(json.dumps({"library_artists_loaded": n, "db": str(g.path)}, indent=2))
        except Exception as e:
            print(json.dumps({"error": f"library refresh failed: {e}"}, indent=2))
        return

    if args.stats:
        print(json.dumps(g.stats(), indent=2))
        return

    if args.node:
        node = g.find_node("artist", args.node) or g.find_node("track", args.node)
        if not node:
            print(json.dumps({"error": f"node not found: {args.node}"}, indent=2))
            return
        nbrs = g.neighbors(node["id"], REL_SIMILAR_ARTIST, min_quorum=1)
        print(json.dumps({
            "node": node,
            "neighbor_count": len(nbrs),
            "neighbors": nbrs[:60],
        }, indent=2, ensure_ascii=False))
        return

    if not args.seed:
        ap.error("need --seed (repeatable), or --refresh-library / --stats / --node")

    out = traverse(g, args.seed, hops=args.hops,
                   sources=tuple(s.strip() for s in args.sources.split(",") if s.strip()),
                   novelty_filter=args.novelty_filter,
                   exclude_library=args.exclude_library,
                   per_node_limit=args.per_node_limit, polite=args.polite,
                   limit=args.limit, refresh_days=args.max_age_days,
                   skip_head=args.skip_head)
    g.close()
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
