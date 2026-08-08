# Model freshness toolkit (optional)

Keeps every Claude call on the newest model per family, automatically.
Companion tooling to the org's pinned model IDs — the pins guarantee
determinism; this keeps the pins (and everything else) current.

## Components

| File | Role |
|---|---|
| `refresh_models.py` | Daily job: fetch latest model list, write `~/.claude/latest-models.json`, auto-update this plugin's agent pins (commit + push + reinstall) and `settings.json` |
| `model_proxy.py` | Local `ANTHROPIC_BASE_URL` proxy (port 8399): rewrites tier aliases and stale model IDs in every outgoing request to the current latest — stale models become uncallable |
| `check_freshness.sh` | Claude Code `SessionStart` hook: background-refresh if the list is >24h old |
| `com.goldy.model-*.plist` | macOS launchd units (daily refresh + keep-alive proxy) — rename/adjust paths for your user |

## Model-list sources (in order)

1. `/v1/models` API — ground truth for *your account* (uses Claude Code's
   keychain OAuth token on macOS; set `ANTHROPIC_API_KEY` elsewhere)
2. Fallback, no auth: the public `anthropic-sdk-python` repo's ordered model
   literals on raw.githubusercontent.com

## Install (macOS)

```bash
mkdir -p ~/.claude/model-freshness
cp refresh_models.py model_proxy.py check_freshness.sh ~/.claude/model-freshness/
# edit the two plists: replace /Users/goldy with your home; then:
cp com.goldy.model-*.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.goldy.model-proxy.plist
launchctl load ~/Library/LaunchAgents/com.goldy.model-refresh.plist
python3 ~/.claude/model-freshness/refresh_models.py   # first run
```

Then add to `~/.claude/settings.json`:

```json
{
  "env": { "ANTHROPIC_BASE_URL": "http://127.0.0.1:8399" },
  "hooks": { "SessionStart": [{ "hooks": [{ "type": "command",
    "command": "~/.claude/model-freshness/check_freshness.sh" }] }] }
}
```

## Caveats

- The proxy is a single point of failure for all Claude traffic — launchd
  KeepAlive restarts it in seconds, and removing `ANTHROPIC_BASE_URL` from
  settings bypasses it instantly.
- Deliberate old-model use (e.g. fast mode on a previous Opus): add the ID to
  `~/.claude/model-freshness/allow.json` (`{"allow": ["claude-opus-4-8"]}`).
- Server-side substitution (capacity fallback) happens after the request
  leaves and cannot be controlled client-side.
- `refresh_models.py` paths assume this repo at `~/claude-autonomous-org`;
  edit `ORG_REPO` if yours lives elsewhere.
