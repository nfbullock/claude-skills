# sources/

Out-of-band inputs the reaper should read in addition to the live sources (vault, Claude history, Things 3, memory). Anything that can't be discovered by walking standard directories goes here.

## claude_ai_exports/

Drop manual claude.ai conversation exports here as `.zip` files. The reaper reads the **freshest zip by mtime** on each run. Old exports stay around for audit, but only the latest one is scanned.

To produce a new export: claude.ai → Settings → Privacy → Export data. Wait for the email, download the zip, drop it here. No renaming required.

Keep this directory under git unless an export contains something you don't want in history; in that case, gitignore the zip and re-export with the offending conversation deleted first.
