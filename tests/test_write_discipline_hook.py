#!/usr/bin/env python3
"""Tests for hooks/enforce-write-discipline.py.

Run: python3 tests/test_write_discipline_hook.py
"""

import json
import os
import subprocess
import sys
import unittest

HOOK = os.path.join(os.path.dirname(__file__), "..", "hooks", "enforce-write-discipline.py")


def run_hook(caller, command, env_extra=None):
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    if caller is not None:
        payload["agent_type"] = caller
    env = dict(os.environ)
    env.pop("AUTONOMOUS_ORG_ROUTING", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, HOOK], input=json.dumps(payload),
        capture_output=True, text=True, env=env,
    )


class WriteDisciplineTest(unittest.TestCase):
    def assert_allowed(self, caller, command, **kw):
        proc = run_hook(caller, command, **kw)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "", f"expected allow: {proc.stdout}")

    def assert_denied(self, caller, command):
        proc = run_hook(caller, command)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_engineer_denied_push_and_deploy(self):
        for cmd in [
            "git push origin feature",
            "git push -u origin main",
            "cd repo && git push",
            "git merge feature-branch",
            "gh pr merge 42 --squash",
            "npm publish",
            "docker push gcr.io/x/y",
            "gcloud run deploy api --source=.",
            "firebase deploy --only hosting",
            "helm upgrade prod ./chart",
            "kubectl apply -f deploy.yaml",
            "terraform apply -auto-approve",
            "vercel --prod",
        ]:
            with self.subTest(cmd=cmd):
                self.assert_denied("engineer", cmd)

    def test_tester_denied_push(self):
        self.assert_denied("tester", "git push origin test-branch")

    def test_namespaced_caller_denied(self):
        self.assert_denied("autonomous-org:engineer", "git push")

    def test_engineer_allowed_local_git_and_builds(self):
        for cmd in [
            "git status",
            "git commit -m 'feat: parser'",
            "git checkout -b feature/x",
            "git log --oneline",
            "npm test",
            "python3 -m pytest",
            "docker build -t local/test .",
            "terraform plan",
            "kubectl get pods",
            "echo 'pushing boundaries'",  # word 'push' outside command position
        ]:
            with self.subTest(cmd=cmd):
                self.assert_allowed("engineer", cmd)

    def test_managers_and_main_untouched(self):
        self.assert_allowed("tech-lead", "git push origin main")
        self.assert_allowed(None, "git push origin main")
        self.assert_allowed("ceo", "gcloud run deploy x")

    def test_non_org_agents_untouched(self):
        self.assert_allowed("some-other-agent", "git push --force origin main")

    def test_escape_hatch(self):
        self.assert_allowed("engineer", "git push", env_extra={"AUTONOMOUS_ORG_ROUTING": "off"})

    def test_malformed_fails_open(self):
        proc = subprocess.run([sys.executable, HOOK], input="not json",
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
