---
name: correction-ledger
description: Two-strike rule for persistent rules. Use when processing a user correction: log it in the correction ledger; create a persistent rule only after the same underlying mistake is corrected twice.
---

# Correction Ledger — Two-Strike Rule

After Phase 0, persistent behavioral rules should be difficult to create. One
mistake does not justify a standing rule; the same mistake twice does.

## When a user correction arrives

1. Read `.claude/state/corrections.jsonl` (project scope) or
   `~/.claude/state/corrections.jsonl` (user scope). Create the file if
   missing. NEVER load this ledger into normal context — read it only now,
   while processing a correction.
2. Identify the underlying failure mode, not the surface form. Assign or
   match a `failure_key` (e.g. `project-package-manager-pnpm`). Two instances
   may differ in wording but must represent the same failure mode; a
   different package-manager issue is NOT automatically the same correction.
3. Append or update the record:

```json
{
  "failure_key": "project-package-manager-pnpm",
  "scope": "project",
  "count": 1,
  "examples": ["Don't use npm here; this repo uses pnpm."],
  "first_seen": "2026-08-04T00:00:00Z",
  "last_seen": "2026-08-04T00:00:00Z"
}
```

(One JSON object per line; update `count`, `examples`, `last_seen` on match.)

## At count 1

Apply the correction to the current work. Do NOT create a persistent rule.

## At count 2

1. Formulate the minimum viable persistent rule — fewest words preserving
   meaning.
2. Choose the narrowest correct scope:
   - `~/.claude/CLAUDE.md` — only genuinely universal user preferences;
   - `<project>/CLAUDE.md` — project-wide rules;
   - `.claude/rules/` — only rules for particular files/directories;
   - a skill — when the correction implies a procedure, not a standing rule.
3. Write the rule in exactly one location — never duplicate across locations.
4. Record in the ledger which rule was created (`"rule_created": "<path>: <text>"`).

## Hygiene

If a ledger entry's rule later proves obsolete, archive the rule per the
`phase0-audit` procedure rather than deleting it silently.
