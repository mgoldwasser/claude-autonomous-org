# autonomous-org

Run Claude Code as a small autonomous organization instead of one monolithic
coding agent.

A Claude Code **plugin**: 14 role agents, a deterministic agent-routing hook,
and guided install/audit/validation skills. You talk to a Fable-powered Chief
of Staff; it delegates through a CEO to Strategy, Product, Tech, and an
independent Quality function; Opus specialists do the work; Sonnet serves as
an internal bulk/documentation service that never reaches you directly.

```
USER → Chief of Staff (Fable) → CEO (Fable)
        ├─ Strategy (Fable) ──── Researcher (Opus)
        ├─ Product Lead (Opus) ─ UX / Innovation (Opus)
        ├─ Tech Lead (Opus) ──── Researcher / Engineer / Analyst (Opus), Docs / Bulk (Sonnet)
        └─ Quality (Fable) ───── Tester / Researcher (Opus)
```

## What you get

- **Intent interpretation** — dictated, typo-filled requests are cleaned into
  intent briefs without inventing requirements.
- **Independent quality** — implementation never certifies itself. Quality
  reviews blind against frozen acceptance criteria, expands each valid defect
  into its failure family, and returns PASS / PASS WITH KNOWN LIMITATIONS /
  FAIL.
- **Deterministic org boundaries** — a PreToolUse hook (plain Python, no LLM)
  allows only approved manager→subordinate edges. Engineers can't spawn their
  own reviewers; Sonnet workers can't escalate; leaves can't spawn at all.
- **Freshness discipline** — implementation may not rely on unverified
  mutable technical facts (versions, APIs, schemas); Research verifies
  against current official sources.
- **Instruction hygiene** — a Phase 0 audit archives accumulated prompt debt
  (never deletes), and a two-strike rule keeps new persistent rules rare.

## Install

From GitHub (replace `OWNER` with the repo owner):

```
/plugin marketplace add OWNER/claude-autonomous-org
/plugin install autonomous-org
```

From a local clone:

```bash
claude plugin marketplace add /path/to/claude-autonomous-org
claude plugin install autonomous-org@autonomous-org-marketplace
```

### Try it before making it your default

Installing the plugin changes nothing about your normal sessions — it only
makes the agents, hook, and skills available. The routing hook governs only
this plugin's 14 agent names; your other agents, skills, and plugins pass
through untouched.

To use the organization on demand without touching settings:

```bash
claude --agent chief-of-staff        # one session run by the org
```

or spawn `chief-of-staff` from any session via the Agent tool. Run
`/org-validate` while trying it. Adopt it as your default (step below) only
once you're satisfied — and consider `--scope project` installation if you
want the org in one repo only.

### Make it the default (optional)

Inside Claude Code, run the guided onboarding:

```
/org-install
```

It scans your existing agents, skills, hooks, CLAUDE.md stack, and settings
for anything that would fight the organization (duplicate agent names,
competing orchestration hooks, contradictory workflow rules), proposes a
per-item resolution, and **only acts with your explicit consent** — replaced
items are archived with a manifest and checksums, never deleted.

Finally apply the settings it proposes (merged, not overwritten):

```json
{
  "model": "fable",
  "agent": "chief-of-staff",
  "autoMemoryEnabled": false
}
```

Restart Claude Code. You should now be talking to the Chief of Staff.

## Skills

| Skill | Purpose |
|---|---|
| `/org-install` | Guided onboarding: conflict scan → consented archive → settings → validation |
| `/phase0-audit` | Full instruction/memory audit: atomize every rule, archive prompt debt, rebuild minimal stack, reversible before/after report |
| `/correction-ledger` | Two-strike rule: log corrections in `.claude/state/corrections.jsonl`; persistent rules only after the same mistake twice, at the narrowest scope |
| `/org-validate` | Behavioral validation runbook (tests A–J: intent, strategy gate, freshness, adversarial QA, disputes, context isolation, Sonnet boundary, two-strike, routing, audit integrity) |

## How work flows

Small fix: Chief of Staff → CEO → Tech Lead → Engineer → proportional
verification. Full product request: parallel Strategy/Product/Tech discovery →
Strategic Product Brief → frozen `ACCEPTANCE.md` → architecture → freshness
verification → bounded implementation → blind Quality review + adversarial
testing → repair loop until evidence supports release → synthesis back to you.

The org scales itself to the task — no ceremony agents. Details:
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Enforcement honesty

Not every rule can be enforced in code. [docs/ENFORCEMENT.md](docs/ENFORCEMENT.md)
classifies every control as DETERMINISTIC, MODEL-INSTRUCTION, or CONVENTION —
including what the routing hook does and doesn't guarantee.

Test the deterministic core:

```
python3 tests/test_routing_hook.py
```

## Known limitations

- **Fable→Opus fallback**: current Claude Code documents no per-agent
  fallback model. If Fable is unavailable, switch with `/model opus`; the org
  never routes user-facing turns to Sonnet regardless.
- **Spawn depth**: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` is not in current
  official docs; depth is instead bounded structurally by the routing matrix
  (longest chain: chief-of-staff → ceo → lead → specialist).
- The routing hook fails open on malformed input and can be disabled with
  `AUTONOMOUS_ORG_ROUTING=off` (availability over lockout — see
  ENFORCEMENT.md).
- Behavioral guarantees (blind review, acceptance freeze, packet compression)
  are prompt-enforced; run `/org-validate` to check them on your install.
- Fable access requires a plan/API tier that includes Fable models. Without
  it, set the Fable roles' `model:` to `opus` in `agents/*.md`.

## Repo layout

```
.claude-plugin/   plugin.json, marketplace.json
agents/           14 role agents (frontmatter: name, description, model, tools)
hooks/            hooks.json + enforce-agent-routing.py (PreToolUse, deterministic)
skills/           org-install, phase0-audit, correction-ledger, org-validate
tests/            routing-hook test suite (stdlib unittest)
docs/             ARCHITECTURE.md, ENFORCEMENT.md
```

## License

MIT
