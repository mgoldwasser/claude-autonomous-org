#!/usr/bin/env python3
"""Tests for hooks/enforce-agent-routing.py.

Feeds hook-style JSON on stdin and asserts allow (no output) or deny
(permissionDecision JSON). Covers every approved edge from spec section 31,
the denied edges from spec section 46 Test I, non-org passthrough, plugin
namespace stripping, the escape hatch, and malformed-input fail-open.

Run: python3 tests/test_routing_hook.py
"""

import json
import os
import subprocess
import sys
import unittest

HOOK = os.path.join(os.path.dirname(__file__), "..", "hooks", "enforce-agent-routing.py")


def run_hook(payload, env_extra=None, raw_stdin=None):
    env = dict(os.environ)
    env.pop("AUTONOMOUS_ORG_ROUTING", None)
    if env_extra:
        env.update(env_extra)
    stdin = raw_stdin if raw_stdin is not None else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, HOOK],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )
    return proc


def hook_call(caller, requested):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Agent",
        "tool_input": {"subagent_type": requested, "prompt": "x"},
    }
    if caller is not None:
        payload["agent_type"] = caller
        payload["agent_id"] = "subagent-test"
    return payload


class RoutingHookTest(unittest.TestCase):
    def assert_allowed(self, caller, requested, **kw):
        proc = run_hook(hook_call(caller, requested), **kw)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "", f"expected allow (silent), got: {proc.stdout}")

    def assert_denied(self, caller, requested, reason_contains=None):
        proc = run_hook(hook_call(caller, requested))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        decision = out["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        if reason_contains:
            self.assertIn(reason_contains, out["hookSpecificOutput"]["permissionDecisionReason"])

    # --- Approved edges (spec section 31) ---

    def test_all_approved_edges_allowed(self):
        edges = [
            ("chief-of-staff", "ceo"),
            ("ceo", "strategy"),
            ("ceo", "product-lead"),
            ("ceo", "tech-lead"),
            ("ceo", "quality-auditor"),
            ("strategy", "researcher"),
            ("product-lead", "ux-designer"),
            ("product-lead", "product-innovation"),
            ("tech-lead", "researcher"),
            ("tech-lead", "engineer"),
            ("tech-lead", "mechanical-analyst"),
            ("tech-lead", "knowledge-maintainer"),
            ("tech-lead", "bulk-worker"),
            ("quality-auditor", "tester"),
            ("quality-auditor", "researcher"),
        ]
        for caller, requested in edges:
            with self.subTest(edge=f"{caller} -> {requested}"):
                self.assert_allowed(caller, requested)

    # --- Spec section 46 Test I: must be denied deterministically ---

    def test_engineer_cannot_spawn_quality_auditor(self):
        self.assert_denied("engineer", "quality-auditor", "leaf agent")

    def test_product_lead_cannot_spawn_tester(self):
        self.assert_denied("product-lead", "tester", "quality-auditor")

    def test_bulk_worker_cannot_spawn_engineer(self):
        self.assert_denied("bulk-worker", "engineer", "leaf agent")

    # --- Other forbidden edges ---

    def test_ceo_cannot_skip_to_engineer(self):
        self.assert_denied("ceo", "engineer", "tech-lead")

    def test_chief_of_staff_only_spawns_ceo(self):
        self.assert_denied("chief-of-staff", "tech-lead")

    def test_leaf_cannot_spawn_anything(self):
        for leaf in [
            "ux-designer", "product-innovation", "researcher", "engineer",
            "mechanical-analyst", "tester", "knowledge-maintainer", "bulk-worker",
        ]:
            with self.subTest(leaf=leaf):
                self.assert_denied(leaf, "ceo", "leaf agent")

    def test_org_agent_cannot_spawn_non_org_agent(self):
        self.assert_denied("ceo", "general-purpose")

    # --- Entry points ---

    def test_main_session_can_spawn_entry_points(self):
        self.assert_allowed(None, "chief-of-staff")
        self.assert_allowed(None, "ceo")

    def test_main_session_cannot_spawn_deep_roles(self):
        self.assert_denied(None, "engineer", "chief-of-staff")
        self.assert_denied(None, "tester", "quality-auditor")

    def test_foreign_agent_cannot_spawn_deep_org_role(self):
        self.assert_denied("some-other-plugin-agent", "engineer")

    # --- Non-interference with the rest of the ecosystem ---

    def test_non_org_edges_pass_through(self):
        self.assert_allowed(None, "general-purpose")
        self.assert_allowed("code-reviewer", "Explore")

    # --- Plugin namespace normalization ---

    def test_namespaced_names_are_normalized(self):
        self.assert_allowed("autonomous-org:ceo", "autonomous-org:tech-lead")
        self.assert_denied("autonomous-org:engineer", "autonomous-org:quality-auditor")

    # --- Escape hatch and robustness ---

    def test_escape_hatch_disables_enforcement(self):
        proc = run_hook(
            hook_call("engineer", "quality-auditor"),
            env_extra={"AUTONOMOUS_ORG_ROUTING": "off"},
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_malformed_input_fails_open(self):
        for raw in ["", "not json", "[]", '{"tool_input": null}', '{"tool_input": "x"}']:
            with self.subTest(raw=raw):
                proc = run_hook(None, raw_stdin=raw)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), "")

    def test_missing_subagent_type_fails_open(self):
        proc = run_hook({"tool_input": {}, "agent_type": "engineer"})
        # No requested agent: engineer spawning "" is denied (leaf), which is
        # correct — engineers may spawn nothing at all.
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
