#!/usr/bin/env python3
"""Audio-DNA — the concept-nailer (SPEC-audio-dna.md §6).

Popularity-biased signals (co-listening, top-tracks, tags) always drift to the hits.
Audio-DNA is the counterweight: per-track acoustic features that match a *sonic concept*
by the actual sound — popularity-independent and version-specific (the Zula *acoustic*
has different DNA than the studio cut). This is what turns "a playlist he'd enjoy" into
"a playlist that lands the exact thing a lesson teaches" ([[feedback_lesson_playlist_nail_the_concept]]).

Two extractors populate ONE canonical feature schema (so ranking works across sources):
  1. AcousticBrainz — a frozen but MBID-keyed precomputed-feature dataset (Essentia).
     The FAST path: no audio download. Coverage is sparse + per-exact-recording, so we
     try ALL candidate recording MBIDs for a track before giving up. (Verified reachable
     2026-07-02; ~1 in 5 MBIDs has data.)
  2. librosa — the workhorse fallback, computed on the .m4a we already sideload. Also the
     ONLY source for time-series features (centroid<->loudness correlation, beat-3
     emphasis) that AB's summary stats can't give.

The ranker takes a concept (a named weight-profile, or a custom one), a target (a
reference track that nails it, OR explicit feature targets/directions), and a candidate
pool, and ranks candidates by weighted distance in the concept-relevant subspace.
Everything caches into musicgraph.db's `dna` table so you never recompute.

Design guarantees (2026-07 adversarial review):
  - VERSION-SPECIFIC cache: dna rows are keyed (node, version) — 'mbid:<id>' or
    'file:<sha1-16>' — so the Zula acoustic never answers for the studio cut.
  - DOWNLOAD-ON-DEMAND (SPEC §6.3): in --rank mode, candidates with no cached DNA, no
    file, and no AcousticBrainz hit are fetched from YouTube into .dna-cache/ and
    extracted, ON BY DEFAULT (--no-fetch to disable). Without this, only popular /
    already-catalogued tracks get scored and the ranking quietly leans popular.
  - PER-METHOD normalization: z-scores are computed within each extractor's sub-pool
    (AB and librosa scales differ per-feature), falling back to pool-wide when a
    method group is too small. Cross-method comparisons are flagged, not hidden.
  - Ranking honesty: each ranked row carries the raw feature values and a
    wrong_direction list, so "best of a bad pool" is visible instead of silent.

RUN UNDER: ~/venv/musicdna/bin/python  (librosa + numpy live there; numba pins it to 3.12).

Usage:
  # single-track extraction
  audio_dna.py --file "Scientist - Your Teeth in My Neck.m4a" --artist Scientist --title "Your Teeth in My Neck"
  audio_dna.py --mbid b522c65f-4b63-4ff5-9d04-8627ab329e67
  audio_dna.py --artist Nirvana --title "Smells Like Teen Spirit"        # AB fast-path, tries all MBIDs

  # rank a candidate pool against a concept
  audio_dna.py --rank --weights dub-riddim \
      --target "Scientist - Your Teeth in My Neck.m4a" \
      --candidates /tmp/pool.json
  audio_dna.py --rank --weights brightness-fm --candidates /tmp/pool.json   # feature-target mode (no ref track)

  audio_dna.py --list-profiles
"""
import argparse
import hashlib
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

UA = "NickMusicResearch/0.1 (nick@bullock.im)"
MB_REC = "https://musicbrainz.org/ws/2/recording/"
AB_ROOT = "https://acousticbrainz.org/api/v1"
MB_SLEEP = 1.1   # anonymous MusicBrainz ~1 req/sec
AB_SLEEP = 0.3
CACHE_DIR = Path(__file__).resolve().parent.parent / ".dna-cache"   # gitignored
SIBLING_SCRIPTS = (Path(__file__).resolve().parent.parent.parent
                   / "apple-music-playlist" / "scripts")

# The canonical schema — every field either extractor tries to fill. Fields marked
# (librosa-only) need the time series AB doesn't expose; (AB-only) are AB's classifiers.
SCALAR_FEATURES = [
    "tempo", "key", "mode", "key_strength",
    "onset_density", "onset_regularity",
    "centroid_mean", "centroid_var", "centroid_cv",
    "rms_mean", "rms_var", "rms_cv", "dynamic_range",
    "centroid_rms_corr",           # librosa-only (time-series correlation)
    "chroma_entropy",
    "spectral_flatness", "zcr_mean", "rolloff_mean",
    "hpss_ratio",                  # librosa-only
    "beat3_emphasis",              # librosa-only (one-drop)
]
VECTOR_FEATURES = ["chroma", "tonnetz", "mfcc_mean", "mfcc_var"]

NOTE_TO_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
              "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

# Krumhansl-Schmuckler key profiles
KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


# ============================ librosa extractor =================================

def extract_librosa(path, sr=22050, max_seconds=180):
    """Extract the canonical feature vector from an audio file. The workhorse."""
    import librosa
    y, sr = librosa.load(path, sr=sr, mono=True, duration=max_seconds)
    y, _ = librosa.effects.trim(y, top_db=40)
    if y.size < sr:  # < 1s of signal
        raise ValueError(f"too little audio after trim: {y.size} samples")
    dur = librosa.get_duration(y=y, sr=sr)
    f = {}

    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    f["tempo"] = float(np.atleast_1d(tempo)[0])

    y_h, y_p = librosa.effects.hpss(y)
    e_h, e_p = float(np.sum(y_h ** 2)), float(np.sum(y_p ** 2))
    f["hpss_ratio"] = e_h / (e_h + e_p + 1e-9)          # 1=harmonic, 0=percussive

    onset_env = librosa.onset.onset_strength(y=y_p, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units="time")
    f["onset_density"] = float(len(onsets) / dur) if dur > 0 else 0.0
    if len(onsets) > 3:
        ioi = np.diff(onsets)
        cv = float(np.std(ioi) / (np.mean(ioi) + 1e-9))
        f["onset_regularity"] = float(1.0 / (1.0 + cv))  # steady -> ~1, lurching -> ~0
    else:
        f["onset_regularity"] = None

    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    f["centroid_mean"] = float(np.mean(cent))
    f["centroid_var"] = float(np.var(cent))
    f["centroid_cv"] = float(np.std(cent) / (np.mean(cent) + 1e-9))

    rms = librosa.feature.rms(y=y)[0]
    f["rms_mean"] = float(np.mean(rms))
    f["rms_var"] = float(np.var(rms))
    f["rms_cv"] = float(np.std(rms) / (np.mean(rms) + 1e-9))
    f["dynamic_range"] = float(np.max(rms) - np.min(rms))

    m = min(len(cent), len(rms))                          # brightness<->loudness (FM)
    if m > 8:
        cc = np.corrcoef(cent[:m], rms[:m])[0, 1]
        f["centroid_rms_corr"] = float(cc) if np.isfinite(cc) else None
    else:
        f["centroid_rms_corr"] = None

    chroma = librosa.feature.chroma_cqt(y=y_h, sr=sr)     # harmonic component = cleaner
    cmean = np.mean(chroma, axis=1)
    f["chroma"] = [float(x) for x in cmean]
    p = cmean / (np.sum(cmean) + 1e-9)
    f["chroma_entropy"] = float(-np.sum(p * np.log2(p + 1e-12)) / np.log2(12))  # 0..1

    k, mode_i, strength = _krumhansl(cmean)
    f["key"], f["mode"], f["key_strength"] = k, mode_i, strength

    tonn = librosa.feature.tonnetz(y=y_h, sr=sr)
    f["tonnetz"] = [float(x) for x in np.mean(tonn, axis=1)]

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    f["mfcc_mean"] = [float(x) for x in np.mean(mfcc, axis=1)]
    f["mfcc_var"] = [float(x) for x in np.var(mfcc, axis=1)]

    f["spectral_flatness"] = float(np.mean(librosa.feature.spectral_flatness(y=y)[0]))
    f["zcr_mean"] = float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))
    f["rolloff_mean"] = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)[0]))
    f["beat3_emphasis"] = _beat3_emphasis(onset_env, beats)
    return f


def _krumhansl(chroma_mean):
    x = chroma_mean - np.mean(chroma_mean)
    best = (-2.0, 0, 1)
    for mode_i, profile in ((1, KS_MAJOR), (0, KS_MINOR)):
        pc = profile - np.mean(profile)
        for k in range(12):
            rolled = np.roll(pc, k)
            denom = np.linalg.norm(x) * np.linalg.norm(rolled) + 1e-9
            corr = float(np.dot(x, rolled) / denom)
            if corr > best[0]:
                best = (corr, k, mode_i)
    corr, k, mode_i = best
    return int(k), int(mode_i), round((corr + 1) / 2, 4)   # strength normalized 0..1


def _beat3_emphasis(onset_env, beats):
    """One-drop signal: mean onset strength on beat 3 of 4 vs beat 1. >0.5 => beat-3 lean."""
    if beats is None or len(beats) < 8:
        return None
    idx = np.clip(np.asarray(beats), 0, len(onset_env) - 1)
    strengths = onset_env[idx]
    n = (len(strengths) // 4) * 4
    if n < 8:
        return None
    grid = strengths[:n].reshape(-1, 4).mean(axis=0)
    b1, b3 = float(grid[0]), float(grid[2])
    return float(b3 / (b1 + b3 + 1e-9))


# ========================== AcousticBrainz extractor ============================

def _http_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _ab_get(mbid, level):
    try:
        return _http_json(f"{AB_ROOT}/{mbid}/{level}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None


def resolve_recording_mbids(artist, title, limit=8, min_score=85):
    q = f'artist:"{artist}" AND recording:"{title}"'
    url = MB_REC + "?" + urllib.parse.urlencode({"query": q, "fmt": "json", "limit": limit})
    try:
        recs = _http_json(url).get("recordings", [])
    except Exception:
        return []
    return [r["id"] for r in recs if r.get("score", 0) >= min_score]


def ab_lookup_any(artist=None, title=None, mbid=None):
    """AB fast-path: try the given MBID, else resolve candidate recording MBIDs and try
    each until one has data (AB coverage is sparse + per-exact-recording)."""
    mbids = [mbid] if mbid else resolve_recording_mbids(artist or "", title or "")
    for i, m in enumerate(mbids):
        if i:
            time.sleep(AB_SLEEP)
        ll = _ab_get(m, "low-level")
        if ll:
            hl = _ab_get(m, "high-level")
            feats = map_acousticbrainz(ll, hl)
            feats["_mbid"] = m
            return feats
    return None


def _stat(d, k):
    return float(d[k]) if isinstance(d, dict) and d.get(k) is not None else None


def _cv(d):
    if isinstance(d, dict) and d.get("mean") not in (None, 0) and d.get("var") is not None:
        return float(math.sqrt(max(d["var"], 0.0)) / (abs(d["mean"]) + 1e-9))
    return None


def _fold_hpcp(mean36):
    """Fold AB's 36-bin HPCP into 12. NOTE: bin 0 is not guaranteed C-aligned, so this
    12-vector is NOT directly comparable to librosa's C-indexed chroma_cqt across sources
    — use key/mode/chroma_entropy scalars for cross-source harmony instead."""
    v = np.asarray(mean36, dtype=float)
    if v.size != 36:
        return None
    return [float(x) for x in v.reshape(12, 3).sum(axis=1)]


def map_acousticbrainz(ll, hl=None):
    """Map an AcousticBrainz low-level (+ optional high-level) blob into the canonical schema."""
    rhythm = ll.get("rhythm", {}) or {}
    tonal = ll.get("tonal", {}) or {}
    low = ll.get("lowlevel", {}) or {}
    f = {k: None for k in SCALAR_FEATURES}
    f["tempo"] = float(rhythm["bpm"]) if rhythm.get("bpm") is not None else None
    f["onset_density"] = float(rhythm["onset_rate"]) if rhythm.get("onset_rate") is not None else None
    # regularity proxy: how concentrated the tempo histogram's first peak is (a stats dict)
    f["onset_regularity"] = _stat(rhythm.get("bpm_histogram_first_peak_weight"), "mean")
    key, scale = tonal.get("key_key"), tonal.get("key_scale")
    f["key"] = NOTE_TO_PC.get(key) if key else None
    f["mode"] = 1 if scale == "major" else (0 if scale == "minor" else None)
    f["key_strength"] = float(tonal["key_strength"]) if tonal.get("key_strength") is not None else None
    f["centroid_mean"] = _stat(low.get("spectral_centroid"), "mean")
    f["centroid_var"] = _stat(low.get("spectral_centroid"), "var")
    f["centroid_cv"] = _cv(low.get("spectral_centroid"))
    f["rms_mean"] = _stat(low.get("spectral_rms"), "mean")
    f["rms_var"] = _stat(low.get("spectral_rms"), "var")
    f["rms_cv"] = _cv(low.get("spectral_rms"))
    f["dynamic_range"] = (float(low["dynamic_complexity"])
                          if low.get("dynamic_complexity") is not None else None)  # proxy
    f["centroid_rms_corr"] = None                        # no time series in AB
    # AB hpcp_entropy is bits over 36 bins; librosa's is fraction-of-max over 12.
    # Normalize both to 0..1 fraction-of-max so the scalar is roughly comparable
    # (per-method z-normalization in rank() covers the residual scale gap).
    ce = _stat(tonal.get("hpcp_entropy"), "mean")
    f["chroma_entropy"] = (ce / math.log2(36)) if ce is not None else None
    f["spectral_flatness"] = _stat(low.get("spectral_flatness_db"), "mean")
    if f["spectral_flatness"] is None:                   # AB often nulls this; fall back
        f["spectral_flatness"] = _stat(low.get("barkbands_flatness_db"), "mean")
    f["zcr_mean"] = _stat(low.get("zerocrossingrate"), "mean")
    f["rolloff_mean"] = _stat(low.get("spectral_rolloff"), "mean")
    # vectors
    f["chroma"] = _fold_hpcp(low_or_tonal_hpcp(tonal))
    f["tonnetz"] = None
    mfcc = low.get("mfcc", {})
    f["mfcc_mean"] = mfcc.get("mean") if isinstance(mfcc, dict) else None
    f["mfcc_var"] = _mfcc_var_from_cov(mfcc)
    f["hpss_ratio"] = None
    f["beat3_emphasis"] = None
    if hl and isinstance(hl.get("highlevel"), dict):     # AB-only semantic classifiers
        f["_highlevel"] = {k: {"value": v.get("value"), "probability": v.get("probability")}
                           for k, v in hl["highlevel"].items() if isinstance(v, dict)}
    return f


def low_or_tonal_hpcp(tonal):
    h = tonal.get("hpcp")
    return h.get("mean") if isinstance(h, dict) else None


def _mfcc_var_from_cov(mfcc):
    if not isinstance(mfcc, dict):
        return None
    cov = mfcc.get("cov")
    if isinstance(cov, list) and cov and isinstance(cov[0], list):
        return [float(cov[i][i]) for i in range(len(cov))]
    return None


# =============================== the ranker =====================================

# §6.6 concept profiles — each term names a canonical feature + a weight + how to score
# it: `direction` high/low (reward high/low across the pool), `target` (a specific value
# to sit near), or neither (reference-track mode: match the --target track's value).
# `abs: true` scores |value| (used for "correlation near zero").
PROFILES = {
    "brightness-fm": {
        "desc": "FM brightness moves independent of loudness — decorrelated centroid<->energy",
        "terms": [
            {"feature": "centroid_rms_corr", "weight": 3.0, "direction": "low", "abs": True},
            {"feature": "centroid_cv", "weight": 2.0, "direction": "high"},
            {"feature": "rms_cv", "weight": 2.0, "direction": "low"},
        ],
    },
    "groove-16th": {
        "desc": "even 16th-note percussion that doesn't lurch — steady, dense, regular onsets",
        "terms": [
            {"feature": "onset_regularity", "weight": 3.0, "direction": "high"},
            {"feature": "onset_density", "weight": 1.5, "direction": "high"},
        ],
    },
    "sparse-intimate": {
        "desc": "the stripped acoustic intimacy of the Zula acoustic — quiet, harmonic, slow, tonal, sparse",
        "terms": [
            {"feature": "rms_mean", "weight": 2.0, "direction": "low"},
            {"feature": "hpss_ratio", "weight": 2.5, "direction": "high"},
            {"feature": "tempo", "weight": 1.0, "direction": "low"},
            {"feature": "spectral_flatness", "weight": 1.5, "direction": "low"},
            {"feature": "onset_density", "weight": 1.5, "direction": "low"},
        ],
    },
    "open-harmony": {
        "desc": "open fifth / two notes that agree — sparse harmony, low harmonic entropy",
        "terms": [
            {"feature": "chroma_entropy", "weight": 3.0, "direction": "low"},
        ],
        "vectors": [{"feature": "chroma", "weight": 1.5}],   # reference-mode: match target chroma shape
    },
    "one-drop": {
        "desc": "one-drop feel — onset emphasis on beat 3, sparse beat 1, roots tempo",
        "terms": [
            {"feature": "beat3_emphasis", "weight": 3.0, "direction": "high"},
            {"feature": "tempo", "weight": 1.0, "target": 72},
        ],
    },
    "dub-riddim": {
        "desc": "deep dub/riddim reference — harmonic space, sparse steady percussion, "
                "moderate-slow tempo, tonal, that breathes (Nick's first application, SPEC §0)",
        "terms": [
            {"feature": "hpss_ratio", "weight": 2.0, "direction": "high"},
            {"feature": "onset_regularity", "weight": 2.0, "direction": "high"},
            {"feature": "onset_density", "weight": 1.5, "direction": "low"},
            {"feature": "tempo", "weight": 1.5, "target": 75},
            {"feature": "spectral_flatness", "weight": 1.0, "direction": "low"},
            {"feature": "dynamic_range", "weight": 1.0, "direction": "high"},
        ],
    },
}


def _cosine_distance(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.size != b.size or a.size == 0:
        return None
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return None
    return float(1.0 - np.dot(a, b) / (na * nb))          # 0=identical, 2=opposite


def _fold_tempo(bpm, target):
    """Fold a detected tempo into the target's octave class. Beat trackers octave-err
    systematically — reggae/dub reads 2x (the skank), DnB can read half — so a 146 BPM
    detection of a 73 BPM riddim must count as NEAR 73, not far from it."""
    if not bpm or not target or bpm <= 0:
        return bpm
    best = bpm
    for mult in (0.25, 0.5, 1.0, 2.0, 4.0):
        cand = bpm * mult
        if abs(cand - target) < abs(best - target):
            best = cand
    return best


def rank(profile, candidates, target=None):
    """Rank candidates (list of {name, features, method, ...}) by weighted distance to
    the concept. Z-normalizers are computed PER EXTRACTION METHOD (AB vs librosa scales
    differ per-feature) with a pool-wide fallback when a method group is too small.
    Missing features are skipped per-candidate and their weight removed from that
    candidate's denominator — but coverage is reported, raw values are echoed, and
    direction terms flag candidates on the wrong side of their group mean, so a
    "least-bad of an off-concept pool" ranking is visible instead of silent."""
    terms = profile.get("terms", [])
    vecs = profile.get("vectors", [])

    # ---- per-(feature, method) normalizers, pool-wide fallback --------------------
    def _vals(feat, use_abs, meth=None):
        out = []
        for c in candidates:
            if meth is not None and c.get("method") != meth:
                continue
            v = (c.get("features") or {}).get(feat)
            if isinstance(v, (int, float)) and math.isfinite(v):
                out.append(abs(v) if use_abs else float(v))
        return np.asarray(out, dtype=float)

    def _mknorm(feat, use_abs, meth):
        arr = _vals(feat, use_abs, meth)
        if arr.size < (3 if meth is not None else 1):
            return None      # method group too small to normalize on its own
        mean, std = float(np.mean(arr)), float(np.std(arr))
        std = std if std > 1e-9 else 1.0
        z = (arr - mean) / std
        return (mean, std, float(np.min(z)), float(np.max(z)), use_abs)

    methods = sorted({c.get("method") for c in candidates if c.get("method")})
    norm = {}
    for t in terms:
        feat, use_abs = t["feature"], t.get("abs", False)
        norm[(feat, None)] = _mknorm(feat, use_abs, None)
        for m in methods:
            norm[(feat, m)] = _mknorm(feat, use_abs, m)

    def zscore(feat, raw, meth):
        """Returns (z, normalizer, used_pool_fallback). Fallback = this candidate's
        method group was too small, so it was normalized against the MIXED pool —
        cross-extractor scale skew can leak in; callers surface it, never hide it."""
        n = norm.get((feat, meth))
        fallback = False
        if n is None:
            n = norm.get((feat, None))
            fallback = meth is not None and len(methods) > 1
        if n is None or not isinstance(raw, (int, float)) or not math.isfinite(raw):
            return None, None, False
        mean, std, _, _, use_abs = n
        v = abs(raw) if use_abs else float(raw)
        return (v - mean) / std, n, fallback

    tfeat = target.get("features") if target else None

    ranked = []
    for c in candidates:
        cf = c.get("features") or {}
        meth = c.get("method")
        num, den, used, missing, wrongdir, fellback = 0.0, 0.0, [], [], [], []
        for t in terms:
            feat, w = t["feature"], float(t["weight"])
            zc, n, fb = zscore(feat, cf.get(feat), meth)
            if zc is None:
                missing.append(feat)
                continue
            if fb:
                fellback.append(feat)
            _, _, zmin, zmax, _ = n
            if "target" in t:
                if feat == "tempo":
                    # octave-fold, then measure RELATIVE distance in raw BPM space
                    # (z-space would re-inject the pool's octave errors); 25% off
                    # the target ~ one z-unit of cost
                    folded = _fold_tempo(cf.get(feat), t["target"])
                    d = abs(folded - t["target"]) / (0.25 * t["target"])
                else:
                    zt, _, _ = zscore(feat, t["target"], meth)
                    d = abs(zc - (zt if zt is not None else 0.0))
            elif t.get("direction") == "high":
                d = zmax - zc                 # distance from the group's most
                if zc < -1e-9:                # epsilon: float noise on a constant
                    wrongdir.append(feat)     # feature must not flag the whole pool
            elif t.get("direction") == "low":
                d = zc - zmin
                if zc > 1e-9:
                    wrongdir.append(feat)
            elif tfeat is not None and isinstance(tfeat.get(feat), (int, float)):
                # reference-track mode: place the target's raw value in the
                # CANDIDATE's normalization group so cross-method scale skew
                # can't masquerade as sonic distance
                zt, _, _ = zscore(feat, tfeat.get(feat), meth)
                if zt is None:
                    missing.append(feat)
                    continue
                d = abs(zc - zt)
            else:
                missing.append(feat)
                continue
            num += w * d
            den += w
            used.append(feat)
        # vector terms only work in reference-track mode
        for vt in vecs:
            feat, w = vt["feature"], float(vt["weight"])
            if tfeat is None or not tfeat.get(feat) or not cf.get(feat):
                missing.append(feat)
                continue
            cd = _cosine_distance(tfeat[feat], cf[feat])
            if cd is None:
                missing.append(feat)
                continue
            num += w * cd
            den += w
            used.append(feat)

        total_w = sum(float(t["weight"]) for t in terms) + sum(float(v["weight"]) for v in vecs)
        score = (num / den) if den > 0 else None
        cross = bool(target and target.get("method") and meth
                     and target["method"] != meth)
        values = {}
        for t in terms:
            v = cf.get(t["feature"])
            values[t["feature"]] = round(v, 4) if isinstance(v, float) else v
        ranked.append({
            "name": c.get("name"),
            "artist": c.get("artist"),
            "title": c.get("title"),
            "method": meth,
            "score": round(score, 4) if score is not None else None,
            "coverage": round(den / total_w, 3) if total_w else 0.0,
            "values": values,
            "wrong_direction": wrongdir,
            "pool_norm_fallback": fellback,   # scored vs the MIXED pool (small method group)
            "used_features": used,
            "missing_features": sorted(set(missing)),
            "cross_method_vs_target": cross,
        })
    scored = [r for r in ranked if r["score"] is not None]
    unscored = [r for r in ranked if r["score"] is None]
    scored.sort(key=lambda r: (r["score"], -r["coverage"]))
    return scored + unscored


# ============================ feature resolution ================================

def _get_graph():
    try:
        from graph import Graph
        return Graph()
    except Exception:
        return None


def _file_key(path):
    h = hashlib.sha1(Path(path).read_bytes()).hexdigest()[:16]
    return f"file:{h}"


def _fname(s):
    """Filename-safe component — '/' in an artist/title must not become a directory."""
    import re
    return re.sub(r"[/\\:]+", "-", s or "").strip()


def _safe_extract(path, quarantine_cache=True):
    """extract_librosa that cannot kill a whole --rank run. A corrupt/truncated file in
    .dna-cache is deleted so the next run re-fetches instead of cache-hitting the corpse."""
    try:
        return extract_librosa(str(path))
    except Exception:
        p = Path(path)
        if quarantine_cache and str(p).startswith(str(CACHE_DIR)):
            p.unlink(missing_ok=True)
        return None


def _fetch_audio(artist, title, cache_dir=CACHE_DIR):
    """Download-on-demand (SPEC §6.3): pull the track's audio from YouTube into the
    local DNA cache so librosa can score tracks nobody scrobbles / AB never indexed.
    Reuses the sideload tool's search/rank/download; never touches Music.app."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    expected = cache_dir / f"{_fname(artist)} - {_fname(title)}.m4a"
    if expected.exists():
        return expected, None
    sys.path.insert(0, str(SIBLING_SCRIPTS))
    try:
        from sideload_tracks import search_candidates, pick_best, download_and_tag
    except Exception as e:
        return None, f"sideload import failed: {e}"
    cands = search_candidates(f"{artist} {title}")
    best = pick_best(cands, artist, title)
    if not best:
        return None, "no_candidate"
    return download_and_tag({"artist": _fname(artist), "title": _fname(title)},
                            best["id"], cache_dir)


def _cache_dna(g, artist, title, mbid, feats, method, version_key=""):
    if g is None or not (title or mbid):
        return
    try:
        stored = {k: v for k, v in feats.items() if k != "_mbid"}   # key carries the mbid
        nid = g.upsert_node("track", title or (mbid or "?"), artist=artist, mbid=mbid)
        g.put_dna(nid, stored, method, version_key=version_key)
        g.commit()
    except Exception:
        pass


def resolve_features(g, item, method="auto", fetch_missing=False):
    """Resolve one item's canonical features. item: {artist,title,file?,mbid?,features?}.
    Returns (features, method, version_key) — version_key is 'mbid:<id>' / 'file:<hash>'
    so the acoustic cut and the studio cut never answer for each other.
    Order: explicit features -> DB cache (version-exact when the item names a version)
    -> librosa on the file -> AcousticBrainz -> download-on-demand (if fetch_missing)."""
    if item.get("features"):
        return item["features"], item.get("method", "provided"), ""
    artist, title, mbid = item.get("artist"), item.get("title"), item.get("mbid")
    fpath = item.get("file")
    file_ok = bool(fpath) and Path(fpath).exists()

    vkey = None                       # None = version-agnostic (accept latest cached)
    if mbid:
        vkey = f"mbid:{mbid}"
    elif file_ok:
        vkey = _file_key(fpath)

    if g is not None and title:
        node = g.find_node("track", title, artist)
        if node:
            d = g.get_dna(node["id"], version_key=vkey)
            if d and (method == "auto" or d["method"] == method):
                return d["features"], d["method"], d.get("version_key", "")

    if file_ok and method in ("auto", "librosa"):
        feats = _safe_extract(fpath)              # a bad file falls through, not crashes
        if feats:
            vk = vkey or _file_key(fpath)
            _cache_dna(g, artist, title, mbid, feats, "librosa", vk)
            return feats, "librosa", vk

    if method in ("auto", "acousticbrainz"):
        feats = ab_lookup_any(artist, title, mbid)
        if feats:
            ab_mbid = feats.get("_mbid", mbid)
            vk = f"mbid:{ab_mbid}" if ab_mbid else ""
            _cache_dna(g, artist, title, ab_mbid, feats, "acousticbrainz", vk)
            return feats, "acousticbrainz", vk

    if file_ok:                                   # AB missed; extract what we have
        feats = _safe_extract(fpath)
        if feats:
            vk = vkey or _file_key(fpath)
            _cache_dna(g, artist, title, mbid, feats, "librosa", vk)
            return feats, "librosa", vk

    if fetch_missing and artist and title and method in ("auto", "librosa"):
        path, err = _fetch_audio(artist, title)
        if path:
            feats = _safe_extract(path)           # quarantines a corrupt download
            if feats:
                vk = _file_key(path)
                _cache_dna(g, artist, title, mbid, feats, "librosa", vk)
                return feats, "librosa", vk

    return None, None, None


def _target_from_arg(g, target_arg, method, fetch_missing=False):
    """--target may be a file, a features.json, 'mbid:XXX', or 'Artist :: Title'."""
    if not target_arg:
        return None
    p = Path(target_arg)
    if p.exists() and p.suffix.lower() in (".m4a", ".mp3", ".wav", ".flac", ".aac", ".ogg"):
        return {"name": p.stem, "features": extract_librosa(str(p)), "method": "librosa"}
    if p.exists() and p.suffix.lower() == ".json":
        d = json.loads(p.read_text())
        return {"name": target_arg, "features": d.get("features", d), "method": d.get("method", "provided")}
    if target_arg.startswith("mbid:"):
        feats = ab_lookup_any(mbid=target_arg[5:])
        return {"name": target_arg, "features": feats, "method": "acousticbrainz"} if feats else None
    if "::" in target_arg:
        a, t = [s.strip() for s in target_arg.split("::", 1)]
        feats, m, _ = resolve_features(g, {"artist": a, "title": t}, method,
                                       fetch_missing=fetch_missing)
        return {"name": f"{a} - {t}", "features": feats, "method": m} if feats else None
    return None


# ================================== CLI =========================================

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="audio file -> extract canonical features (librosa)")
    ap.add_argument("--mbid", help="AcousticBrainz lookup by recording MBID")
    ap.add_argument("--artist")
    ap.add_argument("--title")
    ap.add_argument("--rank", action="store_true", help="rank a candidate pool against a concept")
    ap.add_argument("--weights", help="concept profile name (see --list-profiles) or path to a profile json")
    ap.add_argument("--target", help="reference track: file | features.json | mbid:XXX | 'Artist :: Title'")
    ap.add_argument("--candidates", help="tracks.json (create_playlist schema; each track may carry file/mbid)")
    ap.add_argument("--method", default="auto", choices=["auto", "librosa", "acousticbrainz"],
                    help="how to resolve features when not cached")
    ap.add_argument("--no-cache", action="store_true", help="do not read/write musicgraph.db")
    ap.add_argument("--no-fetch", action="store_true",
                    help="disable download-on-demand for unresolved --rank candidates "
                         "(fetching is ON by default: you can't rank what you can't hear)")
    ap.add_argument("--list-profiles", action="store_true")
    args = ap.parse_args()

    if args.list_profiles:
        print(json.dumps({k: {"desc": v["desc"],
                              "terms": v.get("terms", []), "vectors": v.get("vectors", [])}
                          for k, v in PROFILES.items()}, indent=2))
        return

    g = None if args.no_cache else _get_graph()

    # ---- ranking mode ----
    if args.rank:
        if not args.weights or not args.candidates:
            ap.error("--rank needs --weights and --candidates")
        if Path(args.weights).exists():
            profile = json.loads(Path(args.weights).read_text())
        elif args.weights in PROFILES:
            profile = PROFILES[args.weights]
        else:
            ap.error(f"unknown profile '{args.weights}'. --list-profiles to see the library.")
        data = json.loads(Path(args.candidates).read_text())
        tracks = data["tracks"] if isinstance(data, dict) else data
        fetch = not args.no_fetch
        target = _target_from_arg(g, args.target, args.method, fetch_missing=fetch)

        resolved, unresolved = [], []
        for tr in tracks:
            feats, m, vk = resolve_features(g, tr, args.method, fetch_missing=fetch)
            if feats is None:
                unresolved.append(f"{tr.get('artist')} - {tr.get('title')}")
                continue
            resolved.append({"name": f"{tr.get('artist')} - {tr.get('title')}",
                             "artist": tr.get("artist"), "title": tr.get("title"),
                             "features": feats, "method": m, "version_key": vk})
        ranked = rank(profile, resolved, target=target)
        if g:
            g.close()
        # an unscored fraction this large means the ranking mostly reflects coverage,
        # not the concept — refuse to let it pass silently as a curation verdict
        unresolved_frac = len(unresolved) / max(1, len(tracks))
        out = {
            "concept": args.weights,
            "desc": profile.get("desc"),
            "target": (target or {}).get("name"),
            "mode": "reference-track" if target else "feature-target",
            "resolved": len(resolved), "unresolved": unresolved,
            "ranking_valid_for_curation": unresolved_frac <= 0.2,
            "ranked": ranked,
        }
        if unresolved_frac > 0.2:
            out["warning"] = (f"{len(unresolved)}/{len(tracks)} candidates unscored "
                              f"({unresolved_frac:.0%}) — do NOT curate from this ranking; "
                              "re-run without --no-fetch or supply files/mbids")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    # ---- single-track extraction modes ----
    out = None
    if args.file:
        feats = extract_librosa(args.file)
        vk = f"mbid:{args.mbid}" if args.mbid else _file_key(args.file)
        _cache_dna(g, args.artist, args.title, args.mbid, feats, "librosa", vk)
        out = {"source": "librosa", "file": args.file, "version_key": vk,
               "artist": args.artist, "title": args.title, "features": feats}
    elif args.mbid or (args.artist and args.title):
        feats = ab_lookup_any(args.artist, args.title, args.mbid)
        if feats:
            ab_mbid = feats.get("_mbid", args.mbid)
            vk = f"mbid:{ab_mbid}" if ab_mbid else ""
            _cache_dna(g, args.artist, args.title, ab_mbid, feats, "acousticbrainz", vk)
            out = {"source": "acousticbrainz", "mbid": ab_mbid, "version_key": vk,
                   "artist": args.artist, "title": args.title, "features": feats}
        else:
            out = {"source": "acousticbrainz", "artist": args.artist, "title": args.title,
                   "features": None, "note": "no AcousticBrainz data for any candidate MBID; "
                   "pass --file to extract with librosa"}
    else:
        ap.error("need --file, --mbid, --artist/--title, or --rank")
    if g:
        g.close()
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
