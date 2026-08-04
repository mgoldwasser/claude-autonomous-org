# Enforcement Classification

Per spec section 49, every control is classified honestly. Do not represent a
prompt-based control as enforced.

- **DETERMINISTIC** — enforced by code or configuration the model cannot
  override.
- **MODEL-INSTRUCTION** — enforced by system-prompt instructions; models
  follow them reliably but not provably.
- **CONVENTION** — documented practice only.

| Control | Class | Mechanism |
|---|---|---|
| Agent-routing matrix (who may spawn whom) | DETERMINISTIC | `hooks/enforce-agent-routing.py` PreToolUse hook |
| Leaf agents cannot spawn subagents | DETERMINISTIC (×2) | Routing hook + `disallowedTools: [Agent]` in leaf frontmatter |
| Model per role (Fable/Opus/Sonnet) | DETERMINISTIC | `model:` frontmatter per agent |
| Sonnet agents cannot run shell commands | DETERMINISTIC | `tools:` allowlist (Read/Write/Edit/Grep/Glob) |
| Sonnet never user-facing | DETERMINISTIC + MODEL-INSTRUCTION | No Sonnet agent is an entry point; hook blocks escalation paths; Chief of Staff synthesis instruction |
| Chief of Staff as default main-session agent | DETERMINISTIC (once configured) | `"agent": "chief-of-staff"` in settings — user must apply (see README) |
| Auto-memory disabled | DETERMINISTIC (once configured) | `"autoMemoryEnabled": false` in settings — user must apply |
| Intent-brief discipline (no invented requirements) | MODEL-INSTRUCTION | chief-of-staff prompt |
| Strategy Gate (Product waits for strategy) | MODEL-INSTRUCTION | ceo + product-lead prompts |
| Acceptance freeze | MODEL-INSTRUCTION | product-lead prompt + ACCEPTANCE.md artifact |
| Technical Freshness Gate | MODEL-INSTRUCTION | tech-lead + engineer + quality-auditor prompts |
| Blind review (QA unbiased by engineering narrative) | MODEL-INSTRUCTION | ceo + quality-auditor prompts |
| Quality cannot modify implementation | MODEL-INSTRUCTION (partial DETERMINISTIC) | quality-auditor prompt; tester limited to Read/Grep/Glob/Bash |
| Tester does not change production code | MODEL-INSTRUCTION | tester prompt (Bash could technically write; needed to run software) |
| Defect-family expansion | MODEL-INSTRUCTION | quality-auditor + tester prompts |
| Compressed packets across boundaries | MODEL-INSTRUCTION | all manager prompts |
| Two-strike rule for new persistent rules | MODEL-INSTRUCTION | correction-ledger skill (loads only on invocation) |
| Archive-never-delete during audits | MODEL-INSTRUCTION | phase0-audit / org-install skills |
| Fable→Opus fallback (never Sonnet) for user-facing turns | CONVENTION / KNOWN LIMITATION | No per-agent fallback mechanism documented in current Claude Code; `fallbackModel` settings key unverified. Verify against current docs at install time; otherwise rely on manual `/model opus` when Fable is unavailable |
| Subagent spawn-depth limit env var | KNOWN LIMITATION | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` not found in current official docs; depth is bounded structurally by the routing matrix instead (max chain: chief-of-staff → ceo → lead → specialist) |

## Notes

- The routing hook fails open on malformed input and can be disabled with
  `AUTONOMOUS_ORG_ROUTING=off`. This is a deliberate availability trade-off:
  a broken hook must not brick unrelated tool calls. The failure mode is
  "org discipline temporarily reverts to prompts," not "user blocked."
- The hook governs only edges involving the org's 14 agent names. Other
  plugins and user agents are untouched (non-interference).
- Facts verified against code.claude.com docs on 2026-08-04: agent
  frontmatter `model` values; PreToolUse hook firing for subagent calls with
  caller `agent_type`/`agent_id`; `Agent` matcher name (with `Task` legacy
  alias); JSON `permissionDecision` denial format; `agent` and
  `autoMemoryEnabled` settings keys. Re-verify on major Claude Code updates.
