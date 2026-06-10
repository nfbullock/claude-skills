"""Parse [SPEAKER] scripts into ordered (speaker, text) turns.

Library only — projects supply their own speaker tags, pronunciation tweaks,
and entrypoint. See examples/build_turns.py for a usage template.

Usage:
    from chunker import parse_combined, subsplit_long, apply_pronunciation_tweaks, compile_tweaks

    turns = parse_combined(['scripts/act1.md', 'scripts/act2.md'], speakers=('HOST', 'GUEST'))
    turns = subsplit_long(turns, max_words=200)
    tweaks = compile_tweaks([('API', 'A P I'), ('GCS', 'G C S')])
    turns = [(s, apply_pronunciation_tweaks(t, tweaks)) for s, t in turns]
"""

from __future__ import annotations

import re
from pathlib import Path

HEADER_RE = re.compile(r"^#.*$", re.MULTILINE)
QUOTABLE_RE = re.compile(r"^>\s*quotable:.*$", re.MULTILINE | re.IGNORECASE)
STAGE_DIR_RE = re.compile(r"\[(laughs|pause|chuckles|sigh|beat|silence)\]", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _clean_text(text: str) -> str:
    text = HEADER_RE.sub("", text)
    text = QUOTABLE_RE.sub("", text)
    text = STAGE_DIR_RE.sub("", text)
    return text


def apply_pronunciation_tweaks(text: str, tweaks: list[tuple[re.Pattern, str]]) -> str:
    for pat, repl in tweaks:
        text = pat.sub(repl, text)
    return text


def compile_tweaks(raw: list[tuple[str, str]], word_boundary: bool = True) -> list[tuple[re.Pattern, str]]:
    """Turn (pattern, replacement) string pairs into compiled regexes.

    By default wraps each pattern in word boundaries (\\b...\\b). Set
    word_boundary=False if your patterns are already full regexes.
    """
    out = []
    for pat, repl in raw:
        if word_boundary:
            out.append((re.compile(rf"\b{pat}\b"), repl))
        else:
            out.append((re.compile(pat), repl))
    return out


def parse_script(path: str | Path, speakers: tuple[str, ...]) -> list[tuple[str, str]]:
    """Return ordered list of (speaker, text) turns.

    speakers: tuple of valid speaker tags, e.g. ('HOST', 'GUEST').
    """
    tag_re = re.compile(rf"^\[({'|'.join(speakers)})\]\s*", re.MULTILINE)
    raw = Path(path).read_text()
    raw = _clean_text(raw)

    matches = list(tag_re.finditer(raw))
    if not matches:
        return []

    turns: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        speaker = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        body = raw[start:end].strip()
        body = WHITESPACE_RE.sub(" ", body)
        if body:
            turns.append((speaker, body))
    return turns


def parse_combined(paths: list[str | Path], speakers: tuple[str, ...]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for p in paths:
        out.extend(parse_script(p, speakers))
    return out


def subsplit_long(turns: list[tuple[str, str]], max_words: int = 200) -> list[tuple[str, str]]:
    """Split any turn longer than max_words on sentence boundaries, keeping speaker."""
    out: list[tuple[str, str]] = []
    for speaker, text in turns:
        if len(text.split()) <= max_words:
            out.append((speaker, text))
            continue
        sentences = SENT_SPLIT_RE.split(text)
        chunk: list[str] = []
        chunk_wc = 0
        for s in sentences:
            wc = len(s.split())
            if chunk and chunk_wc + wc > max_words:
                out.append((speaker, " ".join(chunk)))
                chunk = [s]
                chunk_wc = wc
            else:
                chunk.append(s)
                chunk_wc += wc
        if chunk:
            out.append((speaker, " ".join(chunk)))
    return out
