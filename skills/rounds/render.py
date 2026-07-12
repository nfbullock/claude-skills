#!/usr/bin/env python3
"""Render the rounds — Fred's duplex 2-pager — from the markdown he writes.

Same contract as reaper/scripts/render_ballot.py: designed printable HTML ->
PDF via a headless Chromium-family browser, stdlib only, zero provenance
clutter on paper, and a HARD page budget — 2 pages = 1 duplex sheet. The
script fails loudly if the render blows the budget; tighten the prose, don't
loosen the law.

Markdown subset Fred writes (see SKILL.md for the section contract):
    # Title                     -> masthead (one per document)
    > subtitle line             -> small line under the masthead
    ## Section                  -> section head
    ### Card title              -> a re-entry card (bordered block; runs to
                                   the next ###, ##, or page break)
    - bullet                    -> list item
    1. numbered                 -> claim (serif, numbered — the push-against list)
    ---                         -> page break (exactly one: page 1 / page 2)
    **bold**  *em*  `code`      -> inline

Usage:
    render.py <rounds.md> <out.html> <out.pdf> [--no-pdf] [--print]

--print uploads the PDF to shim-api /print (duplex enforced server-side;
passed anyway). Thin stdlib client, same pattern as money/pipeline/shim.py.
"""

import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

PAGE_BUDGET = 2

CHROMIUM_CANDIDATES = [
    os.environ.get("ROUNDS_CHROMIUM", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

SHIM_ENV = os.path.expanduser("~/src/shim-api/studio-api/.env")


def fail(msg):
    sys.exit(f"render_rounds: {msg}")


# ---------------------------------------------------------------- markdown ---

def esc(s):
    return html.escape(str(s), quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def md_to_html(md):
    out = []
    in_card = in_ul = in_ol = False
    pagebreaks = 0

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def close_card():
        nonlocal in_card
        close_lists()
        if in_card:
            out.append("</div>")
            in_card = False

    for raw in md.splitlines():
        line = raw.rstrip()
        if re.fullmatch(r"-{3,}", line):
            close_card()
            out.append('<div class="pagebreak"></div>')
            pagebreaks += 1
            continue
        if line.startswith("# ") and not line.startswith("## "):
            close_card()
            out.append(f'<header><h1>{inline(line[2:])}</h1></header>')
            continue
        if line.startswith("> "):
            close_card()
            out.append(f'<div class="sub">{inline(line[2:])}</div>')
            continue
        if line.startswith("## "):
            close_card()
            out.append(f'<div class="sechead">{inline(line[3:])}</div>')
            continue
        if line.startswith("### "):
            close_card()
            out.append(f'<div class="card"><div class="cardhead">'
                       f'{inline(line[4:])}</div>')
            in_card = True
            continue
        if line.startswith("- "):
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue
        m = re.match(r"^\d+\.\s+(.*)$", line)
        if m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append('<ol class="claims">')
                in_ol = True
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue
        if not line:
            close_lists()
            continue
        close_lists()
        out.append(f"<p>{inline(line)}</p>")
    close_card()
    if pagebreaks != 1:
        fail(f"the rounds is a duplex 2-pager: expected exactly one --- page "
             f"break, found {pagebreaks}")
    return "\n".join(out)


HTML_SHELL = """<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
@page {{ size: letter; margin: 0.5in 0.5in 0.55in 0.5in; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{ --ink: #111; --muted: #555; --faint: #999; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
       Helvetica, Arial, sans-serif; color: var(--ink); font-size: 10px;
       line-height: 1.38; background: #fff; }}
header {{ border-bottom: 2px solid var(--ink); padding-bottom: 4px;
          margin-bottom: 4px; }}
h1 {{ font-size: 16px; letter-spacing: 0.4px; }}
.sub {{ color: var(--muted); font-size: 9px; margin: 2px 0 7px; }}
.sechead {{ font-size: 8.5px; text-transform: uppercase; letter-spacing: 1.2px;
            color: var(--muted); margin: 9px 0 4px;
            border-bottom: 1px solid var(--faint); padding-bottom: 2px; }}
p {{ margin: 0 0 4px; }}
ul {{ margin: 0 0 4px 14px; }}
li {{ margin-bottom: 1.5px; }}
.card {{ border: 1px solid var(--ink); padding: 4px 6px; margin: 0 0 5px;
         page-break-inside: avoid; }}
.cardhead {{ font-weight: 700; font-size: 10.5px; margin-bottom: 2px; }}
.card p {{ margin-bottom: 2px; }}
.card ul {{ margin-bottom: 2px; }}
ol.claims {{ margin: 2px 0 5px 20px; }}
ol.claims li {{ font-family: Georgia, serif; font-size: 10.5px;
                line-height: 1.45; margin-bottom: 5px; }}
code {{ font-family: ui-monospace, Menlo, monospace; font-size: 9px; }}
em {{ color: var(--muted); }}
.pagebreak {{ break-after: page; }}
@media print {{ body {{ -webkit-print-color-adjust: exact; }} }}
</style></head><body>
{body}
</body></html>
"""


def build_html(md_text):
    body = md_to_html(md_text)
    m = re.search(r"<h1>(.*?)</h1>", body)
    title = re.sub(r"<.*?>", "", m.group(1)) if m else "The rounds"
    return HTML_SHELL.format(title=esc(title), body=body)


# --------------------------------------------------------------------- pdf ---

def find_chromium():
    for p in CHROMIUM_CANDIDATES:
        if p and os.path.exists(p):
            return p
    fail("no Chromium-family browser found for PDF rendering "
         "(set ROUNDS_CHROMIUM=/path/to/binary)")


def html_to_pdf(html_path, pdf_path):
    browser = find_chromium()
    cmd = [browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={os.path.abspath(pdf_path)}",
           "file://" + os.path.abspath(html_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not os.path.exists(pdf_path):
        fail(f"PDF render failed ({browser}):\n{r.stderr[-500:]}")


def pdf_page_count(pdf_path):
    data = open(pdf_path, "rb").read()
    counts = re.findall(rb"/Count\s+(\d+)", data)
    return max(int(c) for c in counts) if counts else None


# -------------------------------------------------- shim-api thin client -----
# Same pattern as money/pipeline/shim.py: stdlib only, bearer from env or the
# shim's own .env, multipart hand-rolled. Duplex is enforced server-side; we
# pass it anyway.

def _env(key, default=None):
    if key in os.environ:
        return os.environ[key]
    if os.path.exists(SHIM_ENV):
        with open(SHIM_ENV) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    return default


def _base():
    if "SHIM_BASE_URL" in os.environ:
        return os.environ["SHIM_BASE_URL"]
    host = _env("API_HOST", "127.0.0.1")
    if host in ("0.0.0.0", ""):
        host = "127.0.0.1"
    return f"http://{host}:{_env('API_PORT', '8484')}"


def print_pdf(pdf_path, double_sided=True):
    with open(pdf_path, "rb") as f:
        pdf = f.read()
    if not pdf.startswith(b"%PDF-"):
        fail(f"{pdf_path} is not a PDF")
    boundary = "----rounds" + uuid.uuid4().hex
    fname = os.path.basename(pdf_path)
    body = b"".join([
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"double_sided\"\r\n\r\n"
        f"{'true' if double_sided else 'false'}\r\n".encode(),
        (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
         f"filename=\"{fname}\"\r\nContent-Type: application/pdf\r\n\r\n").encode(),
        pdf,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    token = _env("API_AUTH_TOKEN")
    if token and token != "change-me-to-something-random":
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(_base() + "/print", data=body,
                                 method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            raw = r.read()
            return json.loads(raw) if raw else {"status": r.status}
    except urllib.error.HTTPError as e:
        fail(f"shim-api POST /print -> {e.code}: "
             f"{e.read().decode(errors='replace')[:300]}")
    except urllib.error.URLError as e:
        fail(f"shim-api unreachable at {_base()} ({e.reason}). "
             f"Is the studio-api service running? (curl {_base()}/health)")


# -------------------------------------------------------------------- main ---

def main():
    args = sys.argv[1:]
    if len(args) < 3:
        fail("usage: render.py <rounds.md> <out.html> <out.pdf> "
             "[--no-pdf] [--print]")
    md_path, out_html, out_pdf = args[0], args[1], args[2]
    no_pdf = "--no-pdf" in args
    do_print = "--print" in args
    if no_pdf and do_print:
        fail("--print needs the PDF; drop --no-pdf")

    md_text = open(md_path, encoding="utf-8").read()
    doc = build_html(md_text)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"rounds html: {out_html}")

    if no_pdf:
        return
    html_to_pdf(out_html, out_pdf)
    pages = pdf_page_count(out_pdf)
    print(f"rounds pdf:  {out_pdf}  ({pages} pages)")
    if pages and pages > PAGE_BUDGET:
        fail(f"page budget blown: {pages} > {PAGE_BUDGET}. The rounds is one "
             "duplex sheet — cut prose, don't loosen the law.")

    if do_print:
        resp = print_pdf(out_pdf, double_sided=True)
        print(f"sent to shim-api /print (duplex): {resp}")
        stamp = time.strftime("%Y-%m-%d %H:%M")
        print(f"printed {stamp}")


if __name__ == "__main__":
    main()
