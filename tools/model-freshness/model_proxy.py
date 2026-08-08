#!/usr/bin/env python3
"""Model-freshness enforcement proxy.

Listens on 127.0.0.1:8399. Point ANTHROPIC_BASE_URL here. Forwards everything
to api.anthropic.com, but rewrites the `model` field of JSON request bodies:

  - tier aliases (opus, sonnet, fable, haiku) -> latest full ID per family
  - stale full IDs (per ~/.claude/latest-models.json) -> latest ID for family

Exceptions: IDs listed in ~/.claude/model-freshness/allow.json pass through
(e.g. deliberate fast-mode 4.8 use). All rewrite logic fails open — any error
forwards the original request untouched. Streaming (SSE) passes through.

Rewrites are logged to ~/.claude/model-freshness/proxy.log.
"""

import http.client
import http.server
import json
import os
import ssl
import threading
import time

UPSTREAM = "api.anthropic.com"
PORT = 8399
BASE = os.path.dirname(os.path.abspath(__file__))
LATEST_PATH = os.path.join(os.path.expanduser("~"), ".claude", "latest-models.json")
ALLOW_PATH = os.path.join(BASE, "allow.json")
LOG_PATH = os.path.join(BASE, "proxy.log")

_lock = threading.Lock()
_cache = {"mtime": 0, "latest": {}, "stale": set(), "allow": set()}

HOP_HEADERS = {"connection", "keep-alive", "transfer-encoding", "host",
               "content-length", "te", "upgrade", "proxy-connection"}


def _load_rules():
    with _lock:
        try:
            mtime = os.path.getmtime(LATEST_PATH)
            if mtime != _cache["mtime"]:
                d = json.load(open(LATEST_PATH))
                _cache["latest"] = d.get("latest", {})
                _cache["stale"] = set(d.get("stale", []))
                _cache["mtime"] = mtime
                try:
                    _cache["allow"] = set(json.load(open(ALLOW_PATH)).get("allow", []))
                except Exception:
                    _cache["allow"] = set()
        except Exception:
            pass
        return dict(_cache["latest"]), set(_cache["stale"]), set(_cache["allow"])


def _family(model_id):
    parts = model_id.split("-")
    if parts[0] == "claude" and len(parts) > 1:
        return parts[1]
    return model_id  # bare alias like "opus"


def rewrite_model(model):
    """Return (new_model, reason) or (model, None)."""
    latest, stale, allow = _load_rules()
    if not latest or model in allow:
        return model, None
    if model in latest:  # bare alias: "opus", "sonnet", ...
        return latest[model], f"alias {model}"
    if model in stale:
        fam = _family(model)
        if fam in latest:
            return latest[fam], f"stale {model}"
    return model, None


def plog(msg):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


class Proxy(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _forward(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""

        # Rewrite model field (fail-open on any error)
        if body and self.command == "POST":
            try:
                d = json.loads(body)
                if isinstance(d, dict) and isinstance(d.get("model"), str):
                    new, reason = rewrite_model(d["model"])
                    if reason:
                        plog(f"{self.path}: {reason} -> {new}")
                        d["model"] = new
                        body = json.dumps(d).encode()
            except Exception as e:
                plog(f"rewrite error (passing through): {e}")

        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in HOP_HEADERS}
        headers["Host"] = UPSTREAM

        try:
            conn = http.client.HTTPSConnection(UPSTREAM, context=ssl.create_default_context(), timeout=900)
            conn.request(self.command, self.path, body=body or None, headers=headers)
            resp = conn.getresponse()
        except Exception as e:
            plog(f"upstream error: {e}")
            self.send_error(502, "upstream unreachable")
            return

        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() not in HOP_HEADERS:
                self.send_header(k, v)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        try:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
        except Exception as e:
            plog(f"stream error: {e}")
        finally:
            conn.close()

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _forward

    def log_message(self, *args):
        pass  # quiet; rewrites are logged explicitly


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Proxy)
    plog(f"proxy listening on 127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
