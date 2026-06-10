---
name: print-today
description: Print today's Things 3 items to the default network printer. Skips the Things "Work" project on weekends (Sat/Sun). Manual trigger only — Nick runs /print-today when he wants the sheet.
status: active
---

# /print-today

Pulls today's Things 3 items, formats as a minimal printable sheet, sends to the system default printer. On weekends, items in the Things "Work" project are filtered out.

## How to invoke

When Nick types `/print-today`:

```bash
~/venv/default/bin/python /Users/dad/Documents/sandbox/projects/claude_skills/print-today/print_today.py
```

Add `--dry-run` to preview the formatted sheet in the terminal without sending to the printer.

After printing, report a one-line confirmation: item count and (if weekend) whether Work was filtered.

## What it prints

Single page, plain text, monospace. Title + date header, checkboxes for each item, item titles only (no tags, projects, notes, deadlines — that's by design, leaves room to mark up with pen). Footer with item count and weekend-skip note when applicable.

## Implementation notes

- Reads via `claude_skills/things/things.py today` (sqlite, read-only — won't lag in-app edits by more than a few seconds).
- Weekend detection: Python `datetime.date.today().weekday() >= 5`.
- Print mechanism: `lp` (CUPS). Uses system default printer (Brother_HL_L6200DW_series at time of build, but the skill doesn't hardcode it).
- Long titles wrap to a 31-char column; subsequent lines indented under the title.
- Python stdlib only — no external dependencies.

## What this skill does NOT do

- No deadlines, tags, projects, or notes on the printout — that's by design.
- No automation. Manual trigger only. If Nick wants a daily cron, that's a follow-up.
- No "print to PDF" or alternate-printer support. One printer, one format. Add later if needed.
- Doesn't mark items as printed in Things — the printout is a snapshot, not a mutation.

## Files

- `print_today.py` — the script.
- `SKILL.md` — this file.
