"""model-check engine — has open-weights SOTA leapt past what Nick has on disk?

Two modes:
  * AUTONOMOUS (launchd, weekly): `python model_watcher.py [--domain X]`
      For each domain, shells out to `claude -p` to do LIVE research (web +
      Hugging Face + Reddit — never training data), compares to on-disk
      inventory and the last-known frontier, and stays SILENT unless something
      actually leapt. On a leap it prints and pushes a phone notification.
  * INTERACTIVE (the /model-check skill): the human-in-the-loop Claude calls
      `--print-context` to get hardware + inventory + last state as JSON, does
      the research itself, then pipes a verdict back via `--save`.

Hardware is DETECTED at runtime (system_profiler), never hardcoded — so the
profile can't rot when Nick changes machines or RAM.

State: ~/.model_watcher/state.json  (per-domain frontier + last_run date)
"""
import argparse
import json
import pathlib
import subprocess
import sys
from datetime import date

MODELS_DIR = pathlib.Path("/Volumes/NewSamsung/models/standalone")
STATE_DIR = pathlib.Path.home() / ".model_watcher"
STATE_FILE = STATE_DIR / "state.json"

PUSH_SEND = pathlib.Path(
    "/Users/dad/Documents/sandbox/projects/claude_skills/push-notify/scripts/send.py"
)
PUSH_PYTHON = pathlib.Path.home() / "venv/default/bin/python"

# Each domain names WHERE to look so the research is grounded in live community
# signal, not the model's memory. Order: leaderboard -> HF trending -> Reddit.
DOMAINS = {
    "llm": {
        "label": "general local LLM (reasoning / coding / writing)",
        "sources": (
            "the LMArena and Open LLM leaderboards; Hugging Face trending "
            "text-generation models (huggingface.co/models?pipeline_tag="
            "text-generation&sort=trending); and reddit r/LocalLLaMA sorted by "
            "top of the past month"
        ),
        "leap_examples": (
            "Llama 3 -> 3.1, Qwen2.5 -> Qwen3, a new MoE that beats the user's "
            "size class, a reasoning model that newly fits in the envelope"
        ),
    },
    "stt": {
        "label": "speech-to-text / ASR",
        "sources": (
            "the Hugging Face Open ASR Leaderboard (hf.co/spaces/hf-audio/"
            "open_asr_leaderboard); HF trending automatic-speech-recognition "
            "models; and reddit r/LocalLLaMA and r/MachineLearning"
        ),
        "leap_examples": (
            "a new model that takes #1 on Open ASR by a clear WER margin, or a "
            "much smaller model matching the current best"
        ),
    },
    "tts": {
        "label": "text-to-speech / voice cloning",
        "sources": (
            "the TTS Arena leaderboard (hf.co/spaces/TTS-AGI/TTS-Arena-V2); HF "
            "trending text-to-speech models; and reddit r/LocalLLaMA"
        ),
        "leap_examples": (
            "a new open TTS that clearly beats the current naturalness/cloning "
            "leader, or adds a capability (streaming, languages) the user lacks"
        ),
    },
    "image": {
        "label": "text-to-image generation",
        "sources": (
            "image-arena rankings (artificialanalysis.ai/text-to-image and "
            "imgsys.org); HF trending text-to-image models; and reddit "
            "r/StableDiffusion sorted by top of the past month"
        ),
        "leap_examples": (
            "a new open base model that outclasses the user's on photorealism / "
            "prompt-adherence / speed within the VRAM envelope"
        ),
    },
}


# ---------------------------------------------------------------- hardware ---
def detect_hardware() -> dict:
    """Pull the real machine profile so the prompt never relies on a hardcode."""
    def sp(datatype: str) -> str:
        try:
            return subprocess.run(
                ["system_profiler", datatype], capture_output=True,
                text=True, timeout=30, check=True,
            ).stdout
        except Exception:
            return ""

    hw, disp = sp("SPHardwareDataType"), sp("SPDisplaysDataType")

    def grab(text: str, key: str) -> str:
        for line in text.splitlines():
            if key in line and ":" in line:
                return line.split(":", 1)[1].strip()
        return ""

    # GPU core count lives in the Displays block, under the chipset stanza.
    gpu_cores = ""
    in_apple = False
    for line in disp.splitlines():
        if "Chipset Model:" in line:
            in_apple = "Apple" in line
        if in_apple and "Total Number of Cores:" in line:
            gpu_cores = line.split(":", 1)[1].strip()
            break

    return {
        "model": grab(hw, "Model Name") or "Mac",
        "model_id": grab(hw, "Model Identifier"),
        "chip": grab(hw, "Chip") or "Apple Silicon",
        "cpu_cores": grab(hw, "Total Number of Cores"),
        "gpu_cores": gpu_cores,
        "memory": grab(hw, "Memory") or "unknown",
    }


def memory_gb(hw: dict) -> int:
    try:
        return int(hw["memory"].split()[0])
    except Exception:
        return 0


def envelope(hw: dict) -> str:
    """Rough usable-model guidance for unified-memory Apple Silicon."""
    gb = memory_gb(hw)
    if not gb:
        return "(unknown memory — judge conservatively)"
    # leave headroom for OS + KV cache; ~0.55B params per GB at 4-bit
    q4 = int(gb * 0.55)
    q8 = int(gb * 0.30)
    return (
        f"~{gb} GB unified memory. Comfortable ceiling roughly ~{q4}B params at "
        f"4-bit or ~{q8}B at 8-bit. Prefer MLX builds; GGUF via llama.cpp/Ollama "
        f"also fine. Mention quant + runtime when recommending."
    )


# --------------------------------------------------------------- inventory ---
def inventory(domain: str) -> str:
    d = MODELS_DIR / domain
    if not MODELS_DIR.exists():
        return "(models drive not mounted)"
    if not d.exists():
        return "(none on disk)"
    items = sorted(
        p.name for p in d.iterdir()
        if not p.name.startswith(".") and not p.name.startswith("._")
    )
    return ", ".join(items) or "(none on disk)"


# ------------------------------------------------------------------- state ---
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"frontier": {}, "last_run": {}}


def save_state(domain: str, frontier: str) -> None:
    state = load_state()
    state.setdefault("frontier", {})[domain] = frontier
    state.setdefault("last_run", {})[domain] = date.today().isoformat()
    STATE_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ----------------------------------------------------------------- prompt ----
def build_prompt(domain: str, hw: dict, inv: str, last: str) -> str:
    cfg = DOMAINS[domain]
    return f"""\
You are a research assistant checking whether open-weights {cfg['label']} SOTA
has DRASTICALLY moved. Be terse. Be stingy about declaring a leap.

CRITICAL: do NOT answer from memory. Use web search and fetch to read CURRENT
sources as of {date.today().isoformat()}. Specifically consult: {cfg['sources']}.
If you cannot actually load fresh pages, set "leap": false and say so.

HARDWARE: {hw['model']} — {hw['chip']}, {hw['cpu_cores']} CPU cores,
{hw['gpu_cores']} GPU cores. {envelope(hw)}

ON DISK NOW (this domain): {inv}

LAST KNOWN FRONTIER (previous run, may be stale): {last}

TASK:
1. From the live sources above, determine the current best open-weights option(s)
   for this hardware and domain.
2. Compare against BOTH the on-disk inventory and the last known frontier.
3. A DRASTIC leap = a newly-released model that a daily user would clearly notice
   outclasses what they have — not a minor finetune, not a 1-2 point benchmark
   bump, not a same-family size variant. Examples: {cfg['leap_examples']}.

Return ONLY valid JSON, no prose, no code fences:
{{
  "leap": true | false,
  "frontier": "<one-line summary of current best-for-this-hardware>",
  "headline": "<one line, only if leap=true, else empty>",
  "details": "<2-4 sentences: what changed + exactly what to download, only if leap>",
  "sources": ["<url actually read>", "<url>"]
}}"""


def extract_json(text: str) -> dict:
    """Pull the first balanced JSON object out of `text`.

    `claude -p` sometimes wraps the JSON in prose ("Here's the result: {...}.
    Let me know...") or trails extra lines, which broke a bare json.loads (the
    stt/tts failures on the first live run). Scan to the first '{' and let the
    decoder consume exactly one value, ignoring whatever surrounds it.
    """
    start = text.find("{")
    if start == -1:
        raise ValueError(f"no JSON object in model reply: {text[:200]!r}")
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


def ask_claude(prompt: str) -> dict:
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--allowed-tools", "WebSearch", "WebFetch",
         "--output-format", "json"],
        capture_output=True, text=True, timeout=900, check=True,
    )
    envelope_json = json.loads(result.stdout)
    body = envelope_json.get("result", result.stdout)
    return extract_json(body)


# ------------------------------------------------------------------ notify ---
def push(title: str, message: str) -> None:
    if not PUSH_SEND.exists() or not PUSH_PYTHON.exists():
        return
    try:
        subprocess.run(
            [str(PUSH_PYTHON), str(PUSH_SEND),
             "--title", title, "--message", message,
             "--tags", "rocket", "--priority", "high"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        pass


# -------------------------------------------------------------------- main ---
def run(domains: list[str]) -> int:
    hw = detect_hardware()
    leaps = []
    for domain in domains:
        try:
            verdict = ask_claude(
                build_prompt(domain, hw, inventory(domain),
                             load_state().get("frontier", {}).get(domain, "(none)"))
            )
        except Exception as e:
            print(f"[{domain}] check failed: {e}", file=sys.stderr)
            continue
        save_state(domain, verdict.get("frontier", "(unknown)"))
        if verdict.get("leap"):
            leaps.append((domain, verdict))

    if not leaps:
        return 0  # silent — nothing leapt

    lines = []
    for domain, v in leaps:
        print(f"\n\U0001f680 [{domain}] {v['headline']}\n")
        print(v["details"])
        if v.get("sources"):
            print("\nSources:")
            for s in v["sources"]:
                print(f"  {s}")
        lines.append(f"{domain}: {v['headline']}")
    push("Local model leap", " | ".join(lines))
    print()
    return 0


def print_context() -> int:
    hw = detect_hardware()
    state = load_state()
    print(json.dumps({
        "hardware": hw,
        "envelope": envelope(hw),
        "inventory": {d: inventory(d) for d in DOMAINS},
        "domains": {d: DOMAINS[d] for d in DOMAINS},
        "state": state,
    }, indent=2))
    return 0


def save_from_stdin() -> int:
    payload = json.loads(sys.stdin.read())
    save_state(payload["domain"], payload["frontier"])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", choices=list(DOMAINS), help="check one domain only")
    ap.add_argument("--print-context", action="store_true",
                    help="dump hardware + inventory + state as JSON (for the skill)")
    ap.add_argument("--save", action="store_true",
                    help="read {domain, frontier} JSON from stdin and persist")
    args = ap.parse_args()

    if args.print_context:
        sys.exit(print_context())
    if args.save:
        sys.exit(save_from_stdin())
    sys.exit(run([args.domain] if args.domain else list(DOMAINS)))
