"""Per-turn VibeVoice rendering with controlled silence + loudnorm stitch.

Single-speaker mode per turn, then ffmpeg concat with explicit silence and
two-pass loudnorm. Slower than multi-speaker mode but eliminates handoff
glitches and gives us control over inter-turn pacing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf

from mlx_audio.tts.utils import load_model


def render_turn(model, text: str, voice: str, max_tokens: int, cfg: float, ddpm: int) -> tuple[np.ndarray, int]:
    chunks = []
    sample_rate = None
    for result in model.generate(
        text=text,
        voice=voice,
        max_tokens=max_tokens,
        cfg_scale=cfg,
        ddpm_steps=ddpm,
        verbose=False,
    ):
        if result.audio is not None:
            arr = np.array(result.audio)
            if arr.ndim > 1:
                arr = arr.squeeze()
            chunks.append(arr)
            sample_rate = result.sample_rate
    if not chunks:
        raise RuntimeError(f"no audio for turn: {text[:60]}...")
    return np.concatenate(chunks), sample_rate


def stitch(turn_wavs: list[Path], gap_ms: int, sample_rate: int, out_path: Path) -> None:
    list_file = out_path.parent / f"{out_path.stem}.concat.txt"
    silence_path = out_path.parent / f"silence_{gap_ms}ms_{sample_rate}.wav"
    if not silence_path.exists():
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=r={sample_rate}:cl=mono",
                "-t", f"{gap_ms / 1000:.3f}",
                str(silence_path),
            ],
            check=True, capture_output=True,
        )
    with list_file.open("w") as fh:
        for i, w in enumerate(turn_wavs):
            fh.write(f"file '{w.resolve()}'\n")
            if i < len(turn_wavs) - 1:
                fh.write(f"file '{silence_path.resolve()}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out_path)],
        check=True, capture_output=True,
    )


def loudnorm(in_path: Path, out_path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(in_path), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(out_path)],
        check=True, capture_output=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", required=True)
    ap.add_argument(
        "--voice",
        action="append",
        required=True,
        metavar="SPEAKER=VOICE",
        help="Map a speaker tag to a voice. Repeat for each speaker. "
             "Example: --voice HOST=en-Mike_man --voice GUEST=en-Carter_man",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="mlx-community/VibeVoice-Realtime-0.5B-fp16")
    ap.add_argument("--ddpm", type=int, default=80)
    ap.add_argument("--cfg", type=float, default=1.5)
    ap.add_argument("--gap_ms", type=int, default=400)
    ap.add_argument("--max_tokens", type=int, default=2048)
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--mp3", action="store_true")
    args = ap.parse_args()

    turns = json.loads(Path(args.turns).read_text())
    voices_for: dict[str, str] = {}
    for spec in args.voice:
        if "=" not in spec:
            raise SystemExit(f"--voice expects SPEAKER=VOICE, got: {spec}")
        speaker, voice = spec.split("=", 1)
        voices_for[speaker.strip()] = voice.strip()
    missing = {sp for sp, _ in turns} - voices_for.keys()
    if missing:
        raise SystemExit(f"No --voice mapping for speakers: {sorted(missing)}")

    out_path = Path(args.out)
    workdir = Path(args.workdir) if args.workdir else out_path.parent / f".{out_path.stem}_turns"
    workdir.mkdir(parents=True, exist_ok=True)

    print(f"Loading model: {args.model}")
    t0 = time.time()
    model = load_model(args.model)
    print(f"  loaded in {time.time() - t0:.1f}s")

    print(f"Rendering {len(turns)} turns -> {workdir}")
    voice_summary = "  ".join(f"{sp}={v}" for sp, v in voices_for.items())
    print(f"  voices: {voice_summary}")
    print(f"  ddpm={args.ddpm}  cfg={args.cfg}  gap={args.gap_ms}ms")

    turn_wavs: list[Path] = []
    sample_rate = None
    t_total = time.time()
    for i, (speaker, text) in enumerate(turns):
        wav = workdir / f"turn_{i:04d}_{speaker}.wav"
        if wav.exists():
            print(f"  [{i+1}/{len(turns)}] cached")
            sample_rate = sf.info(str(wav)).samplerate
        else:
            t0 = time.time()
            audio, sr = render_turn(model, text, voices_for[speaker], args.max_tokens, args.cfg, args.ddpm)
            sf.write(str(wav), audio, sr)
            sample_rate = sr
            dt = time.time() - t0
            dur = len(audio) / sr
            print(f"  [{i+1}/{len(turns)}] {speaker} ({voices_for[speaker]}) {len(text.split())}w -> {dur:.1f}s ({dt:.1f}s render)")
        turn_wavs.append(wav)

    raw_stitched = out_path.parent / f"{out_path.stem}_raw.wav"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Stitching with {args.gap_ms}ms gaps -> {raw_stitched.name}")
    stitch(turn_wavs, args.gap_ms, sample_rate, out_path)

    print(f"Loudness normalizing -> {out_path.name}")
    raw_stitched_path = out_path.with_name(out_path.stem + "_pre_loudnorm.wav")
    out_path.rename(raw_stitched_path)
    loudnorm(raw_stitched_path, out_path)
    raw_stitched_path.unlink(missing_ok=True)

    if args.mp3:
        mp3_path = out_path.with_suffix(".mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(out_path), "-codec:a", "libmp3lame", "-qscale:a", "2", str(mp3_path)],
            check=True, capture_output=True,
        )
        print(f"  -> {mp3_path}")

    print(f"DONE in {time.time() - t_total:.1f}s  ({out_path})")


if __name__ == "__main__":
    main()
