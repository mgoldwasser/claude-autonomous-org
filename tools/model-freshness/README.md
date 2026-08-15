# Model freshness toolkit (optional)

Keeps every Claude call on the newest model per family, automatically.
Companion tooling to the org's pinned model IDs — the pins guarantee
determinism; this keeps the pins (and everything else) current.

> **⚠️ Remote Control:** Claude Code >= 2.1.196 disables Remote Control
> (`/remote-control`, claude.ai/code, mobile app) whenever
> `ANTHROPIC_BASE_URL` points anywhere other than `api.anthropic.com` —
> including the enforcement proxy below. **Default install is therefore
> pin-sync only (no proxy in settings).** Use the proxy opt-in, per
> invocation, for headless/automation sessions that never need Remote
> Control.

## Components

| File | Role |
|---|---|
| `refresh_models.py` | Daily job: fetch latest model list, write `~/.claude/latest-models.json`, auto-update this plugin's agent pins (commit + push + reinstall), pin tier aliases + stale IDs in **all** installed plugins' agent frontmatter (`~/.claude/plugins/cache`), and sync `settings.json` |
| `model_proxy.py` | **Opt-in.** Local `ANTHROPIC_BASE_URL` proxy (port 8399): rewrites tier aliases and stale model IDs in every outgoing request to the current latest — stale models become uncallable. Disables Remote Control for any session routed through it |
| `check_freshness.sh` | Claude Code hook: background-refresh if the list is >24h old. Register on **both** `SessionStart` and `UserPromptSubmit` — the latter keeps week-long sessions fresh (it fires per message; ~5ms no-op when the list is current) |
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
cp com.goldy.model-refresh.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.goldy.model-refresh.plist
python3 ~/.claude/model-freshness/refresh_models.py   # first run
```

Then add to `~/.claude/settings.json` (hooks only — **no** `ANTHROPIC_BASE_URL`):

```json
{
  "hooks": {
    "SessionStart": [{ "hooks": [{ "type": "command",
      "command": "~/.claude/model-freshness/check_freshness.sh" }] }],
    "UserPromptSubmit": [{ "hooks": [{ "type": "command",
      "command": "~/.claude/model-freshness/check_freshness.sh" }] }]
  }
}
```

## Optional: enforcement proxy (kills Remote Control for routed sessions)

Pin-sync covers every agent whose model is declared in frontmatter or
settings. The proxy additionally hard-blocks stale IDs chosen at runtime
(e.g. a prompt or tool call naming an old model). If you want that and can
live without Remote Control in those sessions:

```bash
cp com.goldy.model-proxy.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.goldy.model-proxy.plist
# per-invocation, e.g. cron/CI/headless:
ANTHROPIC_BASE_URL=http://127.0.0.1:8399 claude -p "..."
```

Setting `ANTHROPIC_BASE_URL` globally in settings.json works too, but turns
Remote Control off machine-wide — the `/remote-control` command disappears
from every session.

## Long-running sessions

The proxy re-reads `latest-models.json` per request (mtime check), so sessions
spanning days pick up refreshed rules without restarting. The
`UserPromptSubmit` hook guarantees the list itself refreshes even when no new
session starts for a week. One consequence to know: if a new model ships
mid-session, the proxy starts rewriting that session's subsequent requests to
it — a mid-conversation model upgrade. That costs one cold prompt-cache
rebuild and can shift behavior mid-task. If you want a session to finish on
the model it started with, add the outgoing model to `allow.json` for the
duration.

## Caveats

- Plugin updates overwrite cached agent frontmatter; the daily job re-pins
  within 24h (or on next session start via the hook). Freshly updated plugins
  can briefly run tier aliases.
- Proxy mode: single point of failure for all routed Claude traffic — launchd
  KeepAlive restarts it in seconds, and removing `ANTHROPIC_BASE_URL` bypasses
  it instantly.
- Deliberate old-model use (e.g. fast mode on a previous Opus): add the ID to
  `~/.claude/model-freshness/allow.json` (`{"allow": ["claude-opus-4-8"]}`).
- Server-side substitution (capacity fallback) happens after the request
  leaves and cannot be controlled client-side.
- `refresh_models.py` paths assume this repo at `~/claude-autonomous-org`;
  edit `ORG_REPO` if yours lives elsewhere.
