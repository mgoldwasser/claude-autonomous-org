#!/usr/bin/env python3
"""Daily model-freshness job.

1. Fetch /v1/models (no LLM call) using Claude Code's keychain OAuth token.
2. Compute the latest model per family (fable/opus/sonnet/haiku) by created_at.
3. Write ~/.claude/latest-models.json (consumed by model_proxy.py).
4. Sync pinned IDs in the autonomous-org repo agents + ~/.claude/settings.json;
   on change: bump plugin version, commit, push, update local plugin install.
5. Pin tier aliases and stale IDs in ALL installed plugin agent frontmatter
   (~/.claude/plugins/cache). Replaces the enforcement proxy as default path:
   ANTHROPIC_BASE_URL breaks Remote Control (Claude Code >= 2.1.196 disables
   it for any non-api.anthropic.com base URL), so the proxy is opt-in only.
"""

import glob

import datetime
import json
import os
import re
import subprocess
import sys
import urllib.request

HOME = os.path.expanduser("~")
OUT = os.path.join(HOME, ".claude", "latest-models.json")
ORG_REPO = os.path.join(HOME, "claude-autonomous-org")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")
FAMILIES = ("fable", "opus", "sonnet", "haiku")


def log(msg):
    print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}")


def get_token():
    raw = subprocess.check_output(
        ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
        text=True,
    )
    return json.loads(raw)["claudeAiOauth"]["accessToken"]


def fetch_models(token):
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/models",
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "oauth-2025-04-20",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]


def family_of(model_id):
    parts = model_id.split("-")
    return parts[1] if len(parts) > 1 and parts[0] == "claude" and parts[1] in FAMILIES else None


SDK_FALLBACK_URL = (
    "https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/"
    "main/src/anthropic/types/model_param.py"
)


def latest_from_api():
    """Primary: /v1/models — account-serveable ground truth with created_at."""
    models = fetch_models(get_token())
    latest, stale, by_family = {}, [], {}
    for m in models:
        fam = family_of(m["id"])
        if fam:
            by_family.setdefault(fam, []).append(m)
    for fam, ms in by_family.items():
        ms.sort(key=lambda m: m.get("created_at", ""), reverse=True)
        latest[fam] = ms[0]["id"]
        stale.extend(m["id"] for m in ms[1:])
    return latest, stale, "api"


def latest_from_sdk_repo():
    """Fallback (no auth): parse ordered model literals from the public Python
    SDK source. The list is newest-first, so the first ID seen per family is
    that family's latest. May include models this account cannot serve."""
    with urllib.request.urlopen(SDK_FALLBACK_URL, timeout=30) as r:
        text = r.read().decode()
    ids = re.findall(r'"(claude-[a-z0-9.-]+)"', text)
    latest, stale, seen = {}, [], set()
    for mid in ids:
        if mid in seen:
            continue
        seen.add(mid)
        fam = family_of(mid)
        if not fam:
            continue
        if fam not in latest:
            latest[fam] = mid
        else:
            stale.append(mid)
    return latest, stale, "sdk-repo"


def main():
    try:
        latest, stale, source = latest_from_api()
    except Exception as e:
        log(f"API source failed ({e}); falling back to public SDK repo")
        latest, stale, source = latest_from_sdk_repo()
    log(f"source={source}")

    payload = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "latest": latest,
        "stale": sorted(stale),
    }
    prev = {}
    if os.path.exists(OUT):
        try:
            prev = json.load(open(OUT))
        except Exception:
            pass
    json.dump(payload, open(OUT, "w"), indent=2)
    changed = prev.get("latest") != latest
    log(f"latest={latest} changed={changed}")

    # --- Sync org repo agent pins ---
    repo_changed = False
    agents_dir = os.path.join(ORG_REPO, "agents")
    if os.path.isdir(agents_dir):
        for fname in os.listdir(agents_dir):
            path = os.path.join(agents_dir, fname)
            text = open(path).read()

            def repl(match):
                fam = family_of(match.group(1))
                if fam and fam in latest and match.group(1) != latest[fam]:
                    return f"model: {latest[fam]}"
                return match.group(0)

            new = re.sub(r"^model: (claude-[a-z0-9.-]+)$", repl, text, flags=re.M)
            if new != text:
                open(path, "w").write(new)
                repo_changed = True
                log(f"updated pin in {fname}")

    if repo_changed:
        pj = os.path.join(ORG_REPO, ".claude-plugin", "plugin.json")
        d = json.load(open(pj))
        major, minor, patch = d["version"].split(".")
        d["version"] = f"{major}.{minor}.{int(patch) + 1}"
        json.dump(d, open(pj, "w"), indent=2)
        open(pj, "a").write("\n")
        subprocess.run(
            ["git", "-C", ORG_REPO, "commit", "-aqm",
             f"Auto-bump model pins to latest ({d['version']})\n\nBy model-freshness daily job."],
            check=True,
        )
        subprocess.run(["git", "-C", ORG_REPO, "push", "-q"], check=True)
        subprocess.run(["claude", "plugin", "marketplace", "update", "autonomous-org-marketplace"],
                       capture_output=True)
        subprocess.run(["claude", "plugin", "update", "autonomous-org@autonomous-org-marketplace"],
                       capture_output=True)
        log(f"org plugin bumped to {d['version']} and reinstalled")

    # --- Pin aliases + stale IDs in all installed plugin agents ---
    # Plugin updates overwrite the cache; this re-applies daily.
    pin_re = re.compile(r"^model: (claude-[a-z0-9.-]+|opus|sonnet|fable|haiku)\s*$", re.M)
    for path in glob.glob(os.path.join(HOME, ".claude", "plugins", "cache",
                                       "*", "*", "*", "agents", "*.md")):
        try:
            text = open(path).read()

            def pin(match):
                mid = match.group(1)
                fam = mid if mid in latest else family_of(mid)  # alias or full ID
                if fam in latest and mid != latest[fam]:
                    return f"model: {latest[fam]}"
                return match.group(0)

            new = pin_re.sub(pin, text)
            if new != text:
                open(path, "w").write(new)
                log(f"pinned {os.path.relpath(path, HOME)}")
        except Exception as e:
            log(f"plugin pin skip {path}: {e}")

    # --- Sync settings.json main model ---
    s = json.load(open(SETTINGS))
    cur = s.get("model", "")
    fam = family_of(cur)
    if fam and fam in latest and cur != latest[fam]:
        s["model"] = latest[fam]
        json.dump(s, open(SETTINGS, "w"), indent=2)
        log(f"settings.json model {cur} -> {latest[fam]}")

    log("done")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(1)
