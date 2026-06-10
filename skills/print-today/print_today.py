#!/usr/bin/env python3
"""Print today's Things items to the default printer.

Skips the Things "Work" project on weekends. Manual trigger only.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile

THINGS_PY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "things", "things.py"
)
WIDTH = 31
INDENT = 4


def load_today():
    result = subprocess.run(
        ["python3", THINGS_PY, "today"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout).get("items", [])


def is_weekend(d):
    return d.weekday() >= 5


def filter_items(items, today):
    if is_weekend(today):
        return [i for i in items if i.get("project") != "Work"]
    return items


def wrap_title(title, indent=INDENT, width=WIDTH):
    available = width - indent
    words = title.split()
    lines = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= available:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def format_sheet(items, today, weekend_skipped):
    date_str = f"{today.strftime('%A, %B')} {today.day} {today.year}"
    out = []
    out.append(f"TODAY  ·  {date_str}")
    out.append("─" * WIDTH)
    out.append("")
    if not items:
        out.append("    (nothing scheduled)")
        out.append("")
    else:
        for item in items:
            title_lines = wrap_title(item["title"])
            out.append(f"☐   {title_lines[0]}")
            for tl in title_lines[1:]:
                out.append(f"    {tl}")
            out.append("")
    out.append("─" * WIDTH)
    footer = f"{len(items)} item{'s' if len(items) != 1 else ''}"
    if weekend_skipped:
        footer += " · Work skipped (weekend)"
    out.append(footer)
    return "\n".join(out)


def print_sheet(text, dry_run=False):
    if dry_run:
        sys.stdout.write(text + "\n")
        return
    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(text + "\n")
        tmp = f.name
    try:
        subprocess.run(["lp", tmp], check=True)
    finally:
        os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the formatted sheet to stdout instead of the printer",
    )
    args = parser.parse_args()

    today = datetime.date.today()
    items = load_today()
    weekend = is_weekend(today)
    filtered = filter_items(items, today)

    sheet = format_sheet(filtered, today, weekend_skipped=weekend)
    print_sheet(sheet, dry_run=args.dry_run)

    if not args.dry_run:
        msg = f"Printed {len(filtered)} item{'s' if len(filtered) != 1 else ''}"
        if weekend:
            msg += " (Work filtered, weekend)"
        msg += " to default printer."
        sys.stdout.write(msg + "\n")


if __name__ == "__main__":
    main()
