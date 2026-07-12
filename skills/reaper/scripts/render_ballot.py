#!/usr/bin/env python3
"""Render a reaper BALLOT (designed, printable HTML -> PDF) from a reaper LEDGER.

Two-layer contract (fable #26): the ledger on disk is exhaustive and never printed;
the ballot is the only paper Nick touches. Hard page budget <= 8 (target 4-6).

Usage:
    render_ballot.py <ledger.md> <out.html> <out.pdf> [--curation curation.json]
                     [--redline redline.md] [--no-pdf]

Without --curation the ballot falls back to ledger-section grouping (one line per
item) — correct but uncurated. With --curation, Claude's editorial layer (big
rocks, project groups, auto-KILL strip, ledger-only set) drives the layout. The
curation file must account for EVERY ledger item exactly once; the script hard-
fails otherwise, which is the coverage guarantee.

Numbering is identical between ledger and ballot (walkthrough-by-number contract).
Stdlib only; PDF via a headless Chromium-family browser found on this machine.
"""

import html
import json
import os
import re
import subprocess
import sys
from datetime import date

CHIP = {
    "ECHO": "E", "ZOMBIE": "Z", "STALE": "S", "VAGUE": "V",
    "WIDOWED": "W", "NESTED": "N", "PRINCIPLE": "P",
}

CHROMIUM_CANDIDATES = [
    os.environ.get("BALLOT_CHROMIUM", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


# ---------------------------------------------------------------- ledger parse

def parse_ledger(path):
    text = open(path, encoding="utf-8").read()
    m = re.search(r"^# Reaper Sweep — (\d{4}-\d{2}-\d{2})", text, re.M)
    ledger_date = date.fromisoformat(m.group(1)) if m else None

    items, section = {}, None
    cur = None
    for line in text.splitlines():
        sec = re.match(r"^## Section \d+ — (\w+)", line)
        if sec:
            section = sec.group(1).upper()
            cur = None
            continue
        start = re.match(r"^#(\d+)\s*$", line)
        if start and section in CHIP:
            n = int(start.group(1))
            cur = {"n": n, "class": section, "title": "", "last_moved": None,
                   "note": ""}
            items[n] = cur
            continue
        if cur is None:
            continue
        t = re.match(r"^\s+Title:\s+(.*)$", line)
        if t and not cur["title"]:
            cur["title"] = t.group(1).strip()
            continue
        lm = re.search(r"Last moved:\s+(\d{4}-\d{2}-\d{2})", line)
        if lm:
            cur["last_moved"] = date.fromisoformat(lm.group(1))
    return ledger_date, items


def age_str(item, ledger_date):
    if item.get("last_moved") and ledger_date:
        return f"{(ledger_date - item['last_moved']).days}d"
    return ""


# ---------------------------------------------------------------- curation

def validate_coverage(items, cur):
    seen = {}

    def take(n, where):
        if n not in items:
            fail(f"curation references #{n}, not in ledger")
        if n in seen:
            fail(f"#{n} appears in both {seen[n]} and {where}")
        seen[n] = where

    for i, rock in enumerate(cur.get("rocks", []), 1):
        if "anchor" in rock:
            take(rock["anchor"], f"rock {i}")
        for n in rock.get("members", []):
            take(n, f"rock {i}")
    for g in cur.get("groups", []):
        for n in g.get("members", []):
            take(n, f"group '{g['name']}'")
    for n in cur.get("strip", {}).get("members", []):
        take(n, "strip")
    for n_str in cur.get("ledger_only", {}):
        take(int(n_str), "ledger_only")

    missing = sorted(set(items) - set(seen))
    if missing:
        fail(f"ledger items not accounted for: {missing}")


def fail(msg):
    sys.exit(f"render_ballot: {msg}")


def fallback_curation(items):
    """No curation file: group by ledger classification, everything printed."""
    groups = []
    for cls in ["ECHO", "ZOMBIE", "STALE", "VAGUE", "WIDOWED", "NESTED",
                "PRINCIPLE"]:
        members = [n for n in sorted(items) if items[n]["class"] == cls]
        if members:
            groups.append({"name": cls.title(), "verdict": "", "members": members,
                           "group_mark": False})
    return {"rocks": [], "groups": groups, "strip": {"members": []},
            "ledger_only": {}, "labels": {}}


# ---------------------------------------------------------------- html

def esc(s):
    return html.escape(str(s), quote=False)


def label_for(n, items, cur):
    lab = cur.get("labels", {}).get(str(n))
    if lab:
        return lab
    title = items[n]["title"]
    return title if len(title) <= 96 else title[:93].rstrip() + "…"


def chip_html(n, items):
    return f'<span class="chip">{CHIP[items[n]["class"]]}</span>'


def markrow(size="lg"):
    words = ["KEEP", "KILL", "RESHAPE", "DEFER"]
    boxes = "".join(f'<span class="mk"><span class="cb"></span>{w}</span>'
                    for w in words)
    return f'<span class="markrow {size}">{boxes}</span>'


def krd():
    return '<span class="krd">K&thinsp;·&thinsp;X&thinsp;·&thinsp;R&thinsp;·&thinsp;D</span>'


def item_line(n, items, cur, ledger_date, note=None):
    ages = cur.get("ages", {})
    # an explicit "" in the curation suppresses a misleading computed age
    age = ages[str(n)] if str(n) in ages else age_str(items[n], ledger_date)
    agehtml = f'<span class="age">{esc(age)}</span>' if age else ""
    notehtml = f' <span class="linenote">{esc(note)}</span>' if note else ""
    return (f'<div class="item"><span class="n">#{n}</span>{chip_html(n, items)}'
            f'<span class="lbl">{esc(label_for(n, items, cur))}{notehtml}</span>'
            f'{agehtml}{krd()}</div>')


def rides_line(nums, items, cur):
    if not nums:
        return ""
    bits = " &nbsp;·&nbsp; ".join(
        f'<span class="riden">#{n}</span> {esc(short(n, items, cur))}'
        for n in nums)
    return (f'<div class="rides"><span class="rideslabel">rides this mark'
            f' (override any by number):</span> {bits}</div>')


def short(n, items, cur):
    lab = cur.get("micro", {}).get(str(n)) or label_for(n, items, cur)
    return lab if len(lab) <= 60 else lab[:57].rstrip() + "…"


def flag_html(flag):
    if not flag:
        return ""
    cls = "flag-red" if flag.get("tone") == "alert" else "flag-gold"
    return f' <span class="{cls}">{esc(flag["text"])}</span>'


def build_html(items, cur, ledger_date, redline_html=""):
    d = cur.get("date") or (ledger_date.isoformat() if ledger_date else "")
    title = cur.get("title", f"Reaper Ballot — {d}")
    subtitle = cur.get("subtitle", "")
    pen_rule = cur.get("pen_rule",
        "One mark per line — or one mark on a group header, which covers every "
        "line under it. A line mark beats its group mark. Blank = undecided. "
        "K keep &nbsp;·&nbsp; X kill &nbsp;·&nbsp; R reshape &nbsp;·&nbsp; D defer.")

    out = [f'<header><h1>{esc(title)}</h1>']
    if subtitle:
        out.append(f'<div class="sub">{esc(subtitle)}</div>')
    out.append(f'<div class="penrule">{pen_rule}</div></header>')

    for r in cur.get("rulings", []):
        opts = "".join(f'<span class="mk"><span class="cb"></span>{esc(o)}</span>'
                       for o in r["options"])
        out.append('<div class="rock ruling">')
        out.append(f'<div class="rockhead"><span class="rockn">{esc(r["id"])}'
                   f'</span><b>{esc(r["label"])}</b></div>')
        out.append(f'<div class="markrow lg ruling-opts">{opts}</div>')
        if r.get("stake"):
            out.append(f'<div class="stake">{esc(r["stake"])}'
                       f'{flag_html(r.get("flag"))}</div>')
        if r.get("detail"):
            out.append(f'<div class="detail">{esc(r["detail"])}</div>')
        if r.get("cascade"):
            casc = " ".join(f"#{n}" for n in r["cascade"])
            out.append(f'<div class="rides"><span class="rideslabel">if adopted, '
                       f'the walkthrough cascades:</span> {casc} (each still '
                       f'marked below — the ruling sets their default)</div>')
        out.append("</div>")

    rocks = cur.get("rocks", [])
    if rocks:
        out.append('<div class="sechead">The big rocks — if you only mark this '
                   'page, the sweep still worked</div>')
    for i, r in enumerate(rocks, 1):
        anchor = r.get("anchor")
        out.append('<div class="rock">')
        nhtml = (f'<span class="n">#{anchor}</span>{chip_html(anchor, items)}'
                 if anchor else "")
        out.append(f'<div class="rockhead"><span class="rockn">{i}</span>{nhtml}'
                   f'<b>{esc(r["label"])}</b>{markrow()}</div>')
        if r.get("stake"):
            out.append(f'<div class="stake">{esc(r["stake"])}'
                       f'{flag_html(r.get("flag"))}</div>')
        out.append(rides_line(r.get("members", []), items, cur))
        out.append("</div>")

    out.append('<div class="pagebreak"></div>')
    out.append('<div class="sechead">By project — a group mark covers the whole '
               'group; any line you mark yourself wins</div>')
    for g in cur.get("groups", []):
        out.append('<div class="group">')
        mark = markrow("sm") if g.get("group_mark", True) else \
            '<span class="nomark">no single fate — mark lines individually</span>'
        verdict = (f'<span class="verdict">{esc(g["verdict"])}</span>'
                   if g.get("verdict") else "")
        out.append(f'<div class="grouphead"><b>{esc(g["name"])}</b>{verdict}'
                   f'{mark}</div>')
        for n in g.get("members", []):
            out.append(item_line(n, items, cur, ledger_date,
                                 note=cur.get("notes", {}).get(str(n))))
        out.append("</div>")

    strip = cur.get("strip", {})
    if strip.get("members"):
        out.append('<div class="group strip">')
        out.append(f'<div class="grouphead"><b class="stripword">Already-'
                   f'recommended KILL</b><span class="verdict">'
                   f'{esc(strip.get("note", "one mark here confirms the whole strip; cross out any line to save it"))}'
                   f'</span><span class="markrow sm"><span class="mk">'
                   f'<span class="cb"></span>CONFIRM ALL</span></span></div>')
        for n in strip["members"]:
            out.append(item_line(n, items, cur, ledger_date,
                                 note=cur.get("notes", {}).get(str(n))))
        out.append("</div>")

    lo = cur.get("ledger_only", {})
    closing = cur.get("closing", {})
    out.append('<div class="closing">')
    if closing.get("counts"):
        out.append(f'<div class="counts">{esc(closing["counts"])}</div>')
    if lo:
        los = " &nbsp;·&nbsp; ".join(
            f'#{n} {esc(why)}' for n, why in sorted(lo.items(), key=lambda kv: int(kv[0])))
        out.append(f'<div class="lo"><b>Ledger-only ({len(lo)} — not decisions, '
                   f'not printed above):</b> {los}</div>')
    if closing.get("question"):
        out.append(f'<div class="question">{esc(closing["question"])}</div>')
        out.append('<div class="qlines"></div>')
    out.append('<div class="walk">When the pen is done: “walk the numbers” with '
               'Claude — kills and Things-side executions run programmatically '
               'on your word. The exhaustive ledger (sources, evidence, dates) '
               'lives at artifacts/reaper/ and answers any “what was #NN again?”'
               '</div>')
    out.append("</div>")

    if redline_html:
        out.append('<div class="pagebreak"></div>')
        out.append(f'<div class="redline">{redline_html}</div>')

    return HTML_SHELL.format(title=esc(title), body="\n".join(out))


HTML_SHELL = """<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
@page {{ size: letter; margin: 0.5in 0.5in 0.55in 0.5in; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --ink: #111; --muted: #555; --faint: #999;
  --accent: #b00020; --gold: #8a6500;
}}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
       Helvetica, Arial, sans-serif; color: var(--ink); font-size: 9.5px;
       line-height: 1.32; background: #fff; }}
header {{ border-bottom: 2px solid var(--ink); padding-bottom: 4px;
          margin-bottom: 7px; }}
h1 {{ font-size: 16px; letter-spacing: 0.4px; }}
.sub {{ color: var(--muted); font-size: 9px; margin-top: 2px; }}
.penrule {{ margin-top: 4px; font-size: 8.5px; color: var(--ink);
            border: 1px solid var(--faint); padding: 3px 6px; }}
.sechead {{ font-size: 8.5px; text-transform: uppercase; letter-spacing: 1.2px;
            color: var(--muted); margin: 8px 0 4px;
            border-bottom: 1px solid var(--faint); padding-bottom: 2px; }}
.rock {{ border: 1px solid var(--ink); padding: 4px 6px 4px; margin-bottom: 5px;
         page-break-inside: avoid; }}
.rock.ruling {{ border-width: 2px; }}
.rockhead {{ display: flex; align-items: baseline; gap: 5px; font-size: 10.5px; }}
.rockn {{ font-weight: 700; font-size: 11px; min-width: 13px; }}
.rockhead b {{ flex: 1; font-weight: 650; }}
.stake {{ font-size: 9px; color: var(--muted); margin: 2px 0 0 18px; }}
.detail {{ font-size: 9px; margin: 2px 0 0 18px; }}
.rides {{ font-size: 8px; color: var(--muted); margin: 3px 0 0 18px;
          line-height: 1.5; }}
.rideslabel {{ text-transform: uppercase; letter-spacing: 0.5px;
               font-size: 7px; color: var(--faint); }}
.riden {{ font-weight: 700; color: var(--ink); }}
.ruling-opts {{ margin: 3px 0 0 18px; }}
.group {{ margin-bottom: 6px; page-break-inside: avoid; }}
.grouphead {{ display: flex; align-items: baseline; gap: 8px;
              border-bottom: 1px solid var(--ink); padding-bottom: 1px;
              margin-bottom: 2px; font-size: 10px; }}
.grouphead b {{ font-weight: 700; }}
.verdict {{ flex: 1; font-size: 8.5px; color: var(--muted); font-style: italic; }}
.nomark {{ font-size: 7.5px; color: var(--faint); text-transform: uppercase;
           letter-spacing: 0.5px; }}
.item {{ display: flex; align-items: baseline; gap: 4px; padding: 1.5px 0;
         border-bottom: 1px dotted #ddd; }}
.item .n {{ font-weight: 700; min-width: 24px; font-variant-numeric: tabular-nums; }}
.chip {{ display: inline-block; border: 1px solid var(--faint); color: var(--muted);
         font-size: 6.5px; font-weight: 700; padding: 0 2.5px; border-radius: 2px;
         line-height: 1.5; }}
.item .lbl {{ flex: 1; }}
.linenote {{ color: var(--muted); font-size: 8.5px; }}
.age {{ color: var(--muted); font-size: 8.5px; min-width: 26px; text-align: right;
        font-variant-numeric: tabular-nums; }}
.krd {{ color: var(--faint); font-size: 8.5px; letter-spacing: 1px;
        min-width: 52px; text-align: right; font-weight: 600; }}
.markrow {{ white-space: nowrap; }}
.markrow .mk {{ margin-left: 9px; font-size: 8.5px; letter-spacing: 0.5px;
                font-weight: 600; }}
.markrow.sm .mk {{ font-size: 7.5px; margin-left: 7px; }}
.cb {{ display: inline-block; width: 10px; height: 10px;
       border: 1.3px solid var(--ink); vertical-align: -1.5px; margin-right: 3px; }}
.markrow.sm .cb {{ width: 8.5px; height: 8.5px; }}
.strip .grouphead {{ border-bottom-color: var(--accent); }}
.stripword {{ color: var(--accent); }}
.flag-red {{ color: var(--accent); font-weight: 700; }}
.flag-gold {{ color: var(--gold); font-weight: 700; }}
.closing {{ margin-top: 9px; border-top: 2px solid var(--ink); padding-top: 5px; }}
.counts {{ font-size: 9px; margin-bottom: 3px; }}
.lo {{ font-size: 8px; color: var(--muted); margin-bottom: 5px; line-height: 1.5; }}
.question {{ font-family: Georgia, serif; font-size: 11.5px; margin: 7px 0 4px;
             font-style: italic; }}
.qlines {{ height: 52px;
  background: repeating-linear-gradient(to bottom, transparent 0, transparent 15px,
              #bbb 15px, #bbb 16px); -webkit-print-color-adjust: exact; }}
.walk {{ font-size: 8px; color: var(--muted); margin-top: 6px; }}
.pagebreak {{ break-after: page; }}
.redline h2 {{ font-size: 12px; margin-bottom: 4px; }}
.redline h3 {{ font-size: 10px; margin: 6px 0 2px; }}
.redline p, .redline li {{ font-size: 9px; line-height: 1.45; margin-bottom: 3px; }}
.redline ul {{ margin-left: 14px; }}
@media print {{ body {{ -webkit-print-color-adjust: exact; }} }}
</style></head><body>
{body}
</body></html>
"""


# ---------------------------------------------------------------- redline md

def md_to_html(md):
    """Tiny markdown subset: ##/### headers, - bullets, paragraphs, **bold**."""
    out, in_ul = [], False
    for line in md.splitlines():
        line = line.rstrip()
        if line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h2>{inline(line[2:])}</h2>")
        elif line:
            out.append(f"<p>{inline(line)}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


# ---------------------------------------------------------------- pdf

def find_chromium():
    for p in CHROMIUM_CANDIDATES:
        if p and os.path.exists(p):
            return p
    fail("no Chromium-family browser found for PDF rendering "
         "(set BALLOT_CHROMIUM=/path/to/binary)")


def html_to_pdf(html_path, pdf_path):
    browser = find_chromium()
    cmd = [browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={os.path.abspath(pdf_path)}",
           "file://" + os.path.abspath(html_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not os.path.exists(pdf_path):
        fail(f"PDF render failed ({browser}):\n{r.stderr[-500:]}")


def pdf_page_count(pdf_path):
    try:
        from pypdf import PdfReader
        return len(PdfReader(pdf_path).pages)
    except ImportError:
        data = open(pdf_path, "rb").read()
        counts = re.findall(rb"/Count\s+(\d+)", data)
        return max(int(c) for c in counts) if counts else None


# ---------------------------------------------------------------- main

def main():
    args = sys.argv[1:]
    if len(args) < 3:
        fail(__doc__.strip().splitlines()[0] + "\n\n" + "usage: see module docstring")
    ledger_path, out_html, out_pdf = args[0], args[1], args[2]
    curation_path = redline_path = None
    no_pdf = "--no-pdf" in args
    if "--curation" in args:
        curation_path = args[args.index("--curation") + 1]
    if "--redline" in args:
        redline_path = args[args.index("--redline") + 1]

    ledger_date, items = parse_ledger(ledger_path)
    if not items:
        fail(f"no items parsed from {ledger_path} — ledger format changed?")

    if curation_path:
        cur = json.load(open(curation_path, encoding="utf-8"))
        validate_coverage(items, cur)
    else:
        cur = fallback_curation(items)

    redline_html = ""
    if redline_path:
        redline_html = md_to_html(open(redline_path, encoding="utf-8").read())

    doc = build_html(items, cur, ledger_date, redline_html)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"ballot html: {out_html}  ({len(items)} ledger items accounted for)")

    if no_pdf:
        return
    html_to_pdf(out_html, out_pdf)
    pages = pdf_page_count(out_pdf)
    print(f"ballot pdf:  {out_pdf}  ({pages} pages)")
    if pages and pages > 8:
        fail(f"page budget blown: {pages} > 8. Tighten the curation "
             "(shorter labels, more strip, more ledger_only).")


if __name__ == "__main__":
    main()
