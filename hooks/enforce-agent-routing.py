#!/usr/bin/env python3
"""Deterministic agent-routing enforcement for the autonomous-org plugin.

PreToolUse hook on the Agent tool. Reads the hook JSON from stdin, determines
the calling agent (`agent_type`, absent for the main session) and the requested
`subagent_type`, and allows only the approved organizational edges.

Design rules:
- Only edges involving org agents are governed. If neither the caller nor the
  requested agent belongs to the organization, the hook stays silent so it
  never interferes with other plugins or user agents.
- Org agents may only spawn their approved subordinates. Leaf agents spawn
  nothing.
- The main session (or any non-org caller) may enter the organization only
  through `chief-of-staff` or `ceo`.
- Denials name the manager that owns the requested work.
- Fail-open on malformed input: a broken hook must not brick unrelated tool
  calls. Set AUTONOMOUS_ORG_ROUTING=off to disable enforcement entirely.

No LLM is involved; this is deterministic code by design (spec section 31).
"""

import json
import os
import sys

# Approved edges (spec section 31; chief-of-staff direct routes added by
# user directive 2026-08-27: bounded single-track work may skip the CEO).
ALLOWED_EDGES = {
    "chief-of-staff": {
        "ceo",
        "tech-lead",
        "researcher",
        "engineer",
        "mechanical-analyst",
    },
    "ceo": {"strategy", "product-lead", "tech-lead", "quality-auditor"},
    "strategy": {"researcher"},
    "product-lead": {"ux-designer", "product-innovation"},
    "tech-lead": {
        "researcher",
        "engineer",
        "mechanical-analyst",
        "knowledge-maintainer",
        "bulk-worker",
    },
    "quality-auditor": {"tester", "researcher"},
    # Leaf agents spawn nothing.
    "ux-designer": set(),
    "product-innovation": set(),
    "researcher": set(),
    "engineer": set(),
    "mechanical-analyst": set(),
    "tester": set(),
    "knowledge-maintainer": set(),
    "bulk-worker": set(),
}

ORG_AGENTS = set(ALLOWED_EDGES)

# Entry points a non-org caller (including the main session) may spawn.
ENTRY_POINTS = {"chief-of-staff", "ceo"}

# Which manager owns each org agent, for denial messages.
OWNER = {
    "ceo": "chief-of-staff",
    "strategy": "ceo",
    "product-lead": "ceo",
    "tech-lead": "ceo",
    "quality-auditor": "ceo",
    "researcher": "strategy, tech-lead, or quality-auditor",
    "ux-designer": "product-lead",
    "product-innovation": "product-lead",
    "engineer": "tech-lead",
    "mechanical-analyst": "tech-lead",
    "knowledge-maintainer": "tech-lead",
    "bulk-worker": "tech-lead",
    "tester": "quality-auditor",
}

PLUGIN_PREFIX = "autonomous-org:"


def normalize(name):
    """Strip the plugin namespace so plugin-scoped and bare names match."""
    if not isinstance(name, str):
        return ""
    name = name.strip()
    if name.startswith(PLUGIN_PREFIX):
        name = name[len(PLUGIN_PREFIX):]
    return name


def allow():
    # No output, exit 0: no opinion; normal permission flow continues.
    sys.exit(0)


def deny(reason):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def main():
    if os.environ.get("AUTONOMOUS_ORG_ROUTING", "").lower() in {"off", "0", "false"}:
        allow()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        allow()  # fail-open: never block unrelated calls on malformed input

    if not isinstance(payload, dict):
        allow()

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        allow()

    requested = normalize(tool_input.get("subagent_type"))
    caller = normalize(payload.get("agent_type")) or "main"

    caller_in_org = caller in ORG_AGENTS
    requested_in_org = requested in ORG_AGENTS

    # Not our business: neither side belongs to the organization.
    if not caller_in_org and not requested_in_org:
        allow()

    # Org caller spawning something.
    if caller_in_org:
        allowed = ALLOWED_EDGES[caller]
        if requested in allowed:
            allow()
        if not allowed:
            deny(
                f"Routing denied: '{caller}' is a leaf agent and may not spawn "
                f"subagents. Escalate to your manager instead."
            )
        owner = OWNER.get(requested)
        owned_by = f" That work is owned by '{owner}'." if owner else ""
        deny(
            f"Routing denied: '{caller}' may only spawn "
            f"{sorted(allowed)}.{owned_by}"
        )

    # Non-org caller (main session or another plugin's agent) requesting an
    # org agent: only entry points are allowed.
    if requested in ENTRY_POINTS:
        allow()
    owner = OWNER.get(requested, "ceo")
    deny(
        f"Routing denied: enter the organization through 'chief-of-staff' or "
        f"'ceo'. '{requested}' is owned by '{owner}' and is spawned only "
        f"through the organizational hierarchy."
    )


if __name__ == "__main__":
    main()
