#!/usr/bin/env python3
"""
transcribe.py — local STT via ffmpeg + whisper.cpp.

CLI:
    python -m lib.transcribe <audio-file>

Prints the transcript to stdout. Logs go to stderr.

whisper-cli only ingests flac/mp3/ogg/wav, so .m4a (Just Press Record's default)
is decoded to a 16kHz mono wav in a tempdir before invoking whisper-cli.
"""
from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WHISPER_MODEL = Path(
    "/Volumes/NewSamsung/models/standalone/stt/whisper-large-v3-turbo.bin"
)
WHISPER_BIN = "whisper-cli"
FFMPEG_BIN = "ffmpeg"


def _ensure_tools() -> None:
    for tool in (WHISPER_BIN, FFMPEG_BIN):
        if shutil.which(tool) is None:
            sys.exit(f"transcribe: missing required binary: {tool}")
    if not WHISPER_MODEL.exists():
        sys.exit(f"transcribe: whisper model not found at {WHISPER_MODEL}")


def _to_wav(src: Path, dst: Path) -> None:
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-loglevel", "error",
            "-i", str(src),
            "-ar", "16000", "-ac", "1",
            str(dst),
        ],
        check=True,
    )


def collapse_repetition_loops(text: str, threshold: int = 3) -> str:
    """whisper-large hallucinates by looping the same line 5-50 times on quiet
    or ambient audio. Collapse any run of `threshold+` consecutive identical
    (whitespace-stripped) non-empty lines down to one occurrence + a count
    marker. Two repetitions can be legitimate emphasis; three+ is almost
    always the model failing."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        j = i
        key = lines[i].strip()
        while j < len(lines) and lines[j].strip() == key:
            j += 1
        run = j - i
        if run >= threshold and key:
            out.append(lines[i])
            out.append(f"[whisper repetition loop collapsed — {run} occurrences]")
        else:
            out.extend(lines[i:j])
        i = j
    return "\n".join(out)


def transcribe(audio: Path) -> str:
    _ensure_tools()
    if not audio.exists():
        sys.exit(f"transcribe: file not found: {audio}")

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        wav = tdp / "audio.wav"
        _to_wav(audio, wav)

        out_stem = tdp / "out"
        subprocess.run(
            [
                WHISPER_BIN,
                "-m", str(WHISPER_MODEL),
                "-l", "en",
                "-np",
                # -mc 0: don't carry text context between 30s windows. Without this,
                # if a window predicts a benign phrase ("That's really cool") and the
                # next window has quiet audio, the model self-prompts into an infinite
                # loop and abandons the rest of the audio. Cost us 16 of 17 minutes
                # of Nick's 2026-05-10 walk recording before the flag was added.
                "-mc", "0",
                "-otxt",
                "-of", str(out_stem),
                str(wav),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        raw = (out_stem.with_suffix(".txt")).read_text().strip()
        return collapse_repetition_loops(raw)


def main() -> int:
    p = argparse.ArgumentParser(prog="lib.transcribe")
    p.add_argument("audio", type=Path)
    args = p.parse_args()
    print(transcribe(args.audio))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

