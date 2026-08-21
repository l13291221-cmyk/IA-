#!/usr/bin/env python3
"""Sito di gestione + motore 24/7 (solo libreria standard di Python).

    python3 server.py                 # apri http://localhost:8000
    python3 server.py --host 0.0.0.0 --token MIA_PAROLA   # esposto in rete, protetto

Pagine:
  • Panoramica     → come sta andando (equity, posizione, operazioni, eventi)
  • Soldi veri     → interruttore DEMO/LIVE, limiti di rischio, tasto di emergenza
  • Impostazioni   → chiavi API, simbolo, parametri della palestra

Per sicurezza il server ascolta di default solo su localhost (127.0.0.1). Se lo
esponi in rete con --host 0.0.0.0, usa SEMPRE --token per proteggerlo.
"""
from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agentcolony.engine import Engine

HTML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard")
TOKEN = ""


def _page(name: str) -> bytes:
    with open(os.path.join(HTML_DIR, name), "rb") as f:
        return f.read()


def make_handler(engine: Engine):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code: int, ctype: str, body: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200) -> None:
            self._send(code, "application/json", json.dumps(obj).encode())

        def _authed(self) -> bool:
            if not TOKEN:
                return True
            got = self.headers.get("X-Token", "")
            if not got:
                q = self.path.split("?", 1)
                if len(q) == 2:
                    for kv in q[1].split("&"):
                        if kv.startswith("token="):
                            got = kv[6:]
            return got == TOKEN

        def _body(self):
            n = int(self.headers.get("Content-Length", 0) or 0)
            if n <= 0:
                return {}
            try:
                return json.loads(self.rfile.read(n).decode() or "{}")
            except Exception:
                return {}

        def do_GET(self):
            path = self.path.split("?")[0]
            if path.startswith("/api/"):
                if not self._authed():
                    return self._json({"error": "token"}, 401)
                if path == "/api/state":
                    return self._json(engine.snapshot())
                return self._json({"error": "not found"}, 404)
            try:
                if path in ("/", "/index.html", "/app.html"):
                    return self._send(200, "text/html; charset=utf-8", _page("app.html"))
                return self._send(404, "text/plain; charset=utf-8", b"404")
            except FileNotFoundError:
                return self._send(404, "text/plain; charset=utf-8", b"pagina non trovata")

        def do_POST(self):
            path = self.path.split("?")[0]
            if not self._authed():
                return self._json({"error": "token"}, 401)
            if path == "/api/settings":
                return self._json({"ok": True, "config": engine.apply_settings(self._body())})
            if path == "/api/pause":
                engine.set_pause(not engine.paused)
                return self._json({"ok": True, "paused": engine.paused})
            if path == "/api/kill":
                engine.kill_switch()
                return self._json({"ok": True})
            if path == "/api/reset-lab":
                engine.reset_lab()
                return self._json({"ok": True})
            if path == "/api/skip-analysis":
                engine.skip_analysis()
                return self._json({"ok": True})
            return self._json({"error": "not found"}, 404)

    return Handler


def main() -> None:
    global TOKEN
    p = argparse.ArgumentParser(description="AgentColony — sito di gestione + motore 24/7")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--host", default="127.0.0.1", help="127.0.0.1=solo locale (sicuro) · 0.0.0.0=esposto in rete")
    p.add_argument("--token", default="", help="password per proteggere il sito se esposto in rete")
    args = p.parse_args()
    TOKEN = args.token or os.environ.get("AGENTCOLONY_TOKEN", "")

    engine = Engine()
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(engine))
    print("=" * 68)
    print("  AgentColony — sito di gestione + motore 24/7")
    print("=" * 68)
    print(f"  Apri: http://localhost:{args.port}")
    if args.host == "0.0.0.0" and not TOKEN:
        print("  ⚠️  ATTENZIONE: esposto in rete SENZA token! Usa --token per proteggerlo.")
    print("  Modalità di default: DEMO (soldi finti). Ctrl+C per fermare.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nChiusura…")
        engine.shutdown()
        httpd.shutdown()


if __name__ == "__main__":
    main()
