"""
ML for Business - Flask backend (Ollama edition)

Browser -> Flask (/api/analyze) -> Ollama (localhost:11434)

Flask owns the prompts, validates input, rate-limits per IP, caps how many
generations run at once, and streams tokens back so the demo feels live even
on modest hardware. Ollama should only listen on localhost; never expose its
port directly.

Run:   python app.py
Prod:  gunicorn -w 1 --threads 8 -b 127.0.0.1:5000 app:app
       (keep -w 1: rate limits and the concurrency cap live in this process)
"""

import json
import os
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context
from werkzeug.middleware.proxy_fix import ProxyFix

from prompts import PROMPTS

# ─── Config (all overridable with environment variables) ───
BASE_DIR        = Path(__file__).resolve().parent
OLLAMA_URL      = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
MAX_INPUT_CHARS = int(os.environ.get("MAX_INPUT_CHARS", "3000"))
MAX_NEW_TOKENS  = int(os.environ.get("MAX_NEW_TOKENS", "800"))
RATE_LIMIT      = int(os.environ.get("RATE_LIMIT_PER_MIN", "6"))   # requests per IP per minute
MAX_CONCURRENT  = int(os.environ.get("MAX_CONCURRENT", "2"))       # simultaneous generations
READ_TIMEOUT    = int(os.environ.get("READ_TIMEOUT_SECONDS", "120"))
TRUST_PROXY     = os.environ.get("TRUST_PROXY", "0") == "1"        # set to 1 behind Cloudflare Tunnel / nginx

SENTINEL_ERROR = "\x1eERROR:"   # marks an error mid-stream; the browser splits on this

app = Flask(__name__)
if TRUST_PROXY:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

_slots   = threading.BoundedSemaphore(MAX_CONCURRENT)
_hits    = defaultdict(deque)
_hits_lk = threading.Lock()


# ─── Helpers ───
def rate_limited(ip: str) -> bool:
    """True if this IP has used up its requests for the last 60 seconds."""
    now = time.monotonic()
    with _hits_lk:
        q = _hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return True
        q.append(now)
        if len(_hits) > 500:  # keep the dict from growing forever
            for k in [k for k, v in _hits.items() if not v]:
                _hits.pop(k, None)
        return False


def ollama_status():
    """Return (ok, detail). Checks Ollama is reachable and the model is pulled."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        r.raise_for_status()
        names = {m.get("name") for m in r.json().get("models", [])}
    except requests.RequestException:
        return False, "Ollama is not reachable. Start it with: ollama serve"
    want = OLLAMA_MODEL if ":" in OLLAMA_MODEL else f"{OLLAMA_MODEL}:latest"
    if want not in names:
        return False, f"Model not installed. Run: ollama pull {OLLAMA_MODEL}"
    return True, "ready"


def warm_up():
    """Load the model into memory at startup so the first visitor isn't waiting on it."""
    ok, _ = ollama_status()
    if not ok:
        return
    try:
        requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "keep_alive": "30m"},
            timeout=300,
        )
    except requests.RequestException:
        pass


def stream_from_ollama(module: str, user_input: str):
    """Yield text pieces from Ollama. The concurrency slot is released by call_on_close in analyze()."""
    payload = {
        "model": OLLAMA_MODEL,
        "stream": True,
        "keep_alive": "30m",
        "messages": [
            {"role": "system", "content": PROMPTS[module]},
            {"role": "user", "content": user_input},
        ],
        "options": {"temperature": 0.3, "num_predict": MAX_NEW_TOKENS, "num_ctx": 4096},
    }
    try:
        with requests.post(
            f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=(5, READ_TIMEOUT)
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                if "error" in chunk:
                    yield f"{SENTINEL_ERROR} The model returned an error. Try again."
                    return
                piece = chunk.get("message", {}).get("content", "")
                if piece:
                    yield piece
                if chunk.get("done"):
                    return
    except requests.Timeout:
        yield f"{SENTINEL_ERROR} The model took too long to respond. Try a shorter input."
    except (requests.RequestException, ValueError):
        yield f"{SENTINEL_ERROR} Lost connection to the model. Try again in a moment."


# ─── Routes ───
@app.after_request
def secure(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@app.get("/")
def index():
    # Serve only index.html, never the whole project folder (keeps app.py private).
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/health")
def health():
    ok, detail = ollama_status()
    return jsonify({"ok": ok, "model": OLLAMA_MODEL, "detail": detail}), (200 if ok else 503)


@app.post("/api/analyze")
def analyze():
    body = request.get_json(silent=True) or {}
    module = body.get("module")
    user_input = body.get("input")

    if module not in PROMPTS:
        return jsonify({"error": "Unknown module."}), 400
    if not isinstance(user_input, str) or not user_input.strip():
        return jsonify({"error": "Enter some text first."}), 400
    user_input = user_input.strip()
    if len(user_input) > MAX_INPUT_CHARS:
        return jsonify({"error": f"Input is too long. Keep it under {MAX_INPUT_CHARS} characters."}), 400

    if rate_limited(request.remote_addr or "unknown"):
        return jsonify({"error": "Too many requests. Wait a minute and try again."}), 429

    ok, detail = ollama_status()
    if not ok:
        app.logger.warning("Ollama check failed: %s", detail)  # technical detail stays in your console
        return jsonify({"error": "The agent is offline right now. Please try again later."}), 503

    if not _slots.acquire(blocking=False):
        return jsonify({"error": "The agent is busy with other visitors. Try again in a few seconds."}), 503

    resp = Response(
        stream_with_context(stream_from_ollama(module, user_input)),
        mimetype="text/plain",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},  # no-buffering for nginx
    )
    resp.call_on_close(_slots.release)  # runs even if the visitor leaves before streaming starts
    return resp


if __name__ == "__main__":
    threading.Thread(target=warm_up, daemon=True).start()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False, threaded=True)
