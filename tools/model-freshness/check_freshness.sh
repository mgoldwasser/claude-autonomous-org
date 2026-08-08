#!/usr/bin/env bash
# SessionStart hook: if latest-models.json is missing or older than 24h,
# kick off a background refresh. Never blocks session start; always exits 0.
F="$HOME/.claude/latest-models.json"
if [ ! -f "$F" ] || [ -n "$(find "$F" -mmin +1440 2>/dev/null)" ]; then
  nohup /usr/bin/python3 "$HOME/.claude/model-freshness/refresh_models.py" \
    >> "$HOME/.claude/model-freshness/refresh.log" 2>&1 &
fi
exit 0
