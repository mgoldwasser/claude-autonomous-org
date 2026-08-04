---
name: org-install
description: Guided onboarding after installing the autonomous-org plugin. Scans existing agents, skills, hooks, CLAUDE.md, and settings for conflicts; archives only with explicit consent. Use for install, setup, or when the org fights other plugins.
disable-model-invocation: false
---

# Install the Autonomous Organization

Run this AFTER the plugin is installed. It makes the org coexist cleanly with
the user's existing setup. Nothing is modified without explicit consent, and
nothing is ever permanently deleted — only archived.

## Step 1 — Conflict scan (read-only)

Enumerate what exists and what actually loads:

- `~/.claude/settings.json`, `~/.claude/settings.local.json`, project
  `.claude/settings.json` / `.claude/settings.local.json` — note `model`,
  `agent`, `autoMemoryEnabled`, `hooks`, `permissions`.
- `~/.claude/agents/*.md` and project `.claude/agents/*.md`.
- `~/.claude/skills/`, project `.claude/skills/`, and skills from other
  installed plugins (`claude plugin list`).
- Hooks from settings and from other plugins' `hooks/hooks.json`.
- The CLAUDE.md stack: managed policy, `~/.claude/CLAUDE.md`, project
  `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/**/*.md`, imports.
- Auto-memory: `MEMORY.md` and topic files.

Classify each item against the org:

| Conflict class | Examples | Default proposal |
|---|---|---|
| Name collision | existing agent named `ceo`, `engineer`, etc. | archive or rename (user picks) |
| Competing control | another default `agent` setting; another PreToolUse hook matching `Agent`/`Task`; another orchestration plugin | archive/disable one (user picks which) |
| Competing workflow instruction | CLAUDE.md rules or skills mandating a different review/delegation flow | archive or scope down |
| Behavioral memory | auto-memory entries that inject standing behavior | fold into explicit rules or archive; disable auto-memory |
| Harmless coexistence | domain skills (document editing, data viz), read-only tools, unrelated agents | keep |

Managed organization policy: audit and report, never modify.

## Step 2 — Consent

Present the findings as a table (item, class, proposed action, reason). Then
use AskUserQuestion to get explicit approval per group. Do not proceed on
silence. Offer: approve all proposals / pick per item / keep everything and
install alongside.

## Step 3 — Consented archive

For approved items, follow spec section 4.6:

1. Create `~/.claude/archive/instruction-audit/<UTC timestamp>/` (and the
   project-scope equivalent for project files — keep scopes separate).
2. Write `manifest.json`: original path, archive path, sha256 checksum,
   reason, timestamp.
3. Move (or copy, if the file must remain partially active) preserving
   relative paths.
4. Never permanently delete anything.

## Step 4 — Settings

Propose this merge into the appropriate settings scope (show the diff, apply
only with consent — do not overwrite unrelated keys or managed policy):

```json
{
  "model": "fable",
  "agent": "chief-of-staff",
  "autoMemoryEnabled": false
}
```

Notes:
- If the plugin's agents are only available namespaced, use
  `"agent": "autonomous-org:chief-of-staff"` — verify which form resolves by
  running `claude agents` or checking `/agents`.
- Fable→Opus fallback: verify whether the installed Claude Code version
  documents a `fallbackModel` (or equivalent) setting before claiming it; if
  unsupported, record it as a known limitation instead.

## Step 5 — Deeper cleanup and validation

- Offer the full `phase0-audit` skill for the complete instruction-debt audit
  (atomization, baseline/obsolescence/conflict tests, before/after report).
- Run `python3 <plugin>/tests/test_routing_hook.py` to confirm deterministic
  routing.
- Offer the `org-validate` skill for behavioral tests A–J.
- Restart Claude Code so settings and agents load, then confirm the
  chief-of-staff is the active main-session agent.
