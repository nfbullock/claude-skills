#!/usr/bin/env python3
"""
watch.py — orchestrator for the recording-watcher pipeline.

CLI:
    python watch.py <audio-file>
    python watch.py <audio-file> --skip-settle      # don't wait for iCloud sync
    python watch.py <audio-file> --dry-run          # don't push to Things, don't move files

Pipeline:
    1. wait_for_sync_settled (file size stable for 10s)
    2. transcribe via lib.transcribe (whisper-large-v3-turbo)
    3. classify via lib.classify (Opus 4.7 → {route, confidence, reasoning})
    4. dispatch:
         review_recording → captures/pending-review.log (date-stamped queue;
                            the rounds — backstairs/rounds/scan.py — drains it.
                            review/ was killed 2026-07-11; no cadence handlers)
         add_to_things    → handlers/add_to_things.py
         unknown          → captures/unknown.log
    5. append one line to captures/log.md

Phase 1 of the build plan (backstairs/recording-watcher/PLAN.md). Designed
to be invoked manually for now; Phase 3 wraps this in launchd + fswatch.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

JPR_DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FLAT_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[ _]\d{2}_\d{2}_\d{2}\.[A-Za-z0-9]+$", re.IGNORECASE)

ROOT = Path(__file__).resolve().parent
CAPTURES = ROOT / "captures"
LOG = CAPTURES / "log.md"
PENDING_REVIEW = CAPTURES / "pending-review.log"
UNKNOWN_LOG = CAPTURES / "unknown.log"
TRANSCRIPTS_DIR = CAPTURES / "transcripts"

SETTLE_SECONDS = 10
SETTLE_POLL_SECONDS = 2
SETTLE_TIMEOUT_SECONDS = 600


def wait_for_sync_settled(path: Path) -> None:
    """Wait until the file is fully on-disk (not just an iCloud placeholder)
    and its size has been stable for SETTLE_SECONDS.

    `st_size` alone is unsafe: iCloud Drive presents dataless placeholders
    with the server-side size populated but `st_blocks == 0`. Reads against
    those placeholders race the on-demand fetch and fail with EDEADLK
    ("Resource deadlock avoided") — which is exactly what bit the walking
    review on 2026-05-10."""
    if not path.exists():
        sys.exit(f"watch: file does not exist: {path}")

    # Ask iCloud to materialize the file. brctl is undocumented but
    # universally available; ignore exit code — we verify via st_blocks below.
    subprocess.run(["/usr/bin/brctl", "download", str(path)],
                   check=False, capture_output=True)

    deadline = time.monotonic() + SETTLE_TIMEOUT_SECONDS
    last_size = -1
    stable_since: float | None = None

    while time.monotonic() < deadline:
        st = path.stat()
        size = st.st_size
        materialized = st.st_blocks > 0
        now = time.monotonic()
        if materialized and size == last_size and size > 0:
            if stable_since is None:
                stable_since = now
            elif now - stable_since >= SETTLE_SECONDS:
                return
        else:
            stable_since = None
            last_size = size
        time.sleep(SETTLE_POLL_SECONDS)

    sys.exit(f"watch: file did not settle within {SETTLE_TIMEOUT_SECONDS}s: {path}")


def _run_child(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """subprocess.run with stderr surfaced on failure. Avoids the silent-failure
    mystery from 2026-05-10 where lib.transcribe died and watch.py just logged
    'returned non-zero exit status 1' with no clue why."""
    try:
        return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        if e.stderr:
            sys.stderr.write(e.stderr)
        raise


def transcribe(audio: Path) -> str:
    proc = _run_child([sys.executable, "-m", "lib.transcribe", str(audio)], cwd=ROOT)
    return proc.stdout.strip()


def classify(transcript_file: Path) -> dict:
    proc = _run_child([sys.executable, "-m", "lib.classify", str(transcript_file)], cwd=ROOT)
    return json.loads(proc.stdout.strip())


def dispatch_add_to_things(transcript_file: Path, audio: Path, dry_run: bool) -> dict:
    cmd = [
        sys.executable, str(ROOT / "handlers" / "add_to_things.py"),
        str(transcript_file),
        "--audio", str(audio),
    ]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"raw": proc.stdout.strip()}


def _infer_recording_date(audio: Path) -> str | None:
    """Just Press Record uses two layouts: older recordings nest under a date
    dir (`…/Documents/YYYY-MM-DD/HH-MM-SS.m4a`), newer ones are flat files at
    the Documents root (`YYYY-MM-DD_HH_MM_SS.wav`). Just Press Record drops flat files too,
    with a space between date and time (`YYYY-MM-DD HH_MM_SS.mp3`). Honor all
    three. Return None otherwise so the queue falls back to today (manual
    ad-hoc files)."""
    if JPR_DATE_DIR_RE.match(audio.parent.name):
        return audio.parent.name
    m = FLAT_FILE_RE.match(audio.name)
    if m:
        return m.group(1)
    return None


def dispatch_review(audio: Path, transcript_file: Path, classification: dict,
                    dry_run: bool) -> dict:
    """Queue the recording for the rounds. review/ was killed 2026-07-11 —
    there are no daily/weekly cadence handlers anymore; the rounds
    (backstairs/rounds/scan.py) reads pending-review.log and drains it.
    `recording_date` comes from the filename, so the entry is stamped with
    the day Nick recorded, not the day the pipeline ran."""
    entry = {
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "recording_date": _infer_recording_date(audio) or dt.date.today().isoformat(),
        "audio": str(audio),
        "transcript_file": str(transcript_file),
        "classification": classification,
    }
    if dry_run:
        return {"dry_run": True, "would_queue": entry}

    PENDING_REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with PENDING_REVIEW.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"queued_for_rounds": str(PENDING_REVIEW),
            "recording_date": entry["recording_date"]}


def dispatch_unknown(audio: Path, transcript: str, classification: dict) -> dict:
    UNKNOWN_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "audio": str(audio),
        "transcript": transcript,
        "classification": classification,
    })
    with UNKNOWN_LOG.open("a") as f:
        f.write(line + "\n")
    return {"queued_for_triage": str(UNKNOWN_LOG)}


def append_log(audio: Path, route: str, confidence: float, transcript: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    one_liner = " ".join(transcript.split())[:120]
    ts = dt.datetime.now().isoformat(timespec="seconds")
    with LOG.open("a") as f:
        f.write(f"{ts} | {route} | conf={confidence:.2f} | {audio.name} | {one_liner}\n")


def save_transcript(audio: Path, transcript: str) -> Path:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out = TRANSCRIPTS_DIR / f"{audio.stem}.txt"
    out.write_text(transcript + "\n")
    return out


def process(audio: Path, *, skip_settle: bool, dry_run: bool) -> dict:
    if not skip_settle:
        wait_for_sync_settled(audio)

    print(f"[watch] transcribing {audio.name}", file=sys.stderr)
    transcript = transcribe(audio)
    if not transcript:
        # Empty transcript — route to unknown without bothering the classifier.
        result = dispatch_unknown(audio, "", {"route": "unknown", "confidence": 1.0,
                                              "reasoning": "empty transcript"})
        append_log(audio, "unknown", 1.0, "")
        return {"route": "unknown", "result": result}

    transcript_file = save_transcript(audio, transcript)

    print(f"[watch] classifying ({len(transcript)} chars)", file=sys.stderr)
    classification = classify(transcript_file)
    route = classification["route"]
    confidence = float(classification.get("confidence", 0.0))
    print(f"[watch] route={route} confidence={confidence:.2f}", file=sys.stderr)

    if route == "review_recording":
        result = dispatch_review(audio, transcript_file, classification, dry_run)
    elif route == "add_to_things":
        result = dispatch_add_to_things(transcript_file, audio, dry_run)
    else:
        result = dispatch_unknown(audio, transcript, classification)

    append_log(audio, route, confidence, transcript)
    return {"route": route, "confidence": confidence,
            "classification": classification, "result": result}


def main() -> int:
    p = argparse.ArgumentParser(prog="watch")
    p.add_argument("audio", type=Path)
    p.add_argument("--skip-settle", action="store_true",
                   help="Skip the iCloud sync-settled wait (for local test files)")
    p.add_argument("--dry-run", action="store_true",
                   help="Pass --dry-run to handlers; don't actually push to Things")
    args = p.parse_args()

    out = process(args.audio, skip_settle=args.skip_settle, dry_run=args.dry_run)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

