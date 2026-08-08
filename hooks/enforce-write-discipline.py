#!/usr/bin/env python3
"""Deterministic push/deploy discipline for the autonomous-org plugin.

PreToolUse hook on the Bash tool. Leaf agents (engineer, tester, and other
org leaves) may build, test, and commit in their isolated worktrees, but may
not push to shared branches, publish, or deploy — integration is the Tech
Lead's sequential responsibility. This prevents parallel engineers from
clobbering each other's work.

Scope rules mirror enforce-agent-routing.py:
- Only org leaf agents are governed; the main session, org managers, and
  non-org agents pass through untouched.
- Fail-open on malformed input; AUTONOMOUS_ORG_ROUTING=off disables.
"""

import json
import os
import re
import sys

# Org leaf agents that must not push/publish/deploy.
RESTRICTED_AGENTS = {
    "engineer",
    "tester",
    "ux-designer",
    "product-innovation",
    "researcher",
    "mechanical-analyst",
    "knowledge-maintainer",
    "bulk-worker",
}

PLUGIN_PREFIX = "autonomous-org:"

# Patterns for commands that publish work beyond the agent's own worktree.
FORBIDDEN = [
    (r"\bgit\b[^|;&]*\bpush\b", "git push"),
    (r"\bgit\b[^|;&]*\bmerge\b", "git merge"),
    (r"\bgh\s+pr\s+merge\b", "gh pr merge"),
    (r"\bnpm\s+publish\b", "npm publish"),
    (r"\byarn\s+publish\b", "yarn publish"),
    (r"\bpnpm\s+publish\b", "pnpm publish"),
    (r"\btwine\s+upload\b", "twine upload"),
    (r"\bcargo\s+publish\b", "cargo publish"),
    (r"\bdocker\b[^|;&]*\bpush\b", "docker push"),
    (r"\bgcloud\b[^|;&]*\bdeploy\b", "gcloud deploy"),
    (r"\bgcloud\s+app\s+deploy\b", "gcloud app deploy"),
    (r"\bfirebase\s+deploy\b", "firebase deploy"),
    (r"\bfly(ctl)?\s+deploy\b", "fly deploy"),
    (r"\bvercel\b(\s+deploy\b|.*--prod\b)", "vercel deploy"),
    (r"\bnetlify\s+deploy\b", "netlify deploy"),
    (r"\bhelm\s+(install|upgrade|uninstall)\b", "helm release"),
    (r"\bkubectl\s+(apply|delete|patch|scale|rollout)\b", "kubectl mutation"),
    (r"\bterraform\s+(apply|destroy)\b", "terraform apply/destroy"),
    (r"\bserverless\s+deploy\b|\bsls\s+deploy\b", "serverless deploy"),
]


def normalize(name):
    if not isinstance(name, str):
        return ""
    name = name.strip()
    if name.startswith(PLUGIN_PREFIX):
        name = name[len(PLUGIN_PREFIX):]
    return name


def allow():
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
        allow()

    if not isinstance(payload, dict):
        allow()

    caller = normalize(payload.get("agent_type"))
    if caller not in RESTRICTED_AGENTS:
        allow()  # main session, org managers, non-org agents: not our business

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        allow()

    command = tool_input.get("command")
    if not isinstance(command, str):
        allow()

    for pattern, label in FORBIDDEN:
        if re.search(pattern, command):
            deny(
                f"Write discipline: '{caller}' may not run {label}. Leaf agents "
                f"commit in their own worktree only; the tech-lead integrates "
                f"and deploys sequentially. Report your branch and commits in "
                f"ARTIFACTS instead."
            )

    allow()


if __name__ == "__main__":
    main()
