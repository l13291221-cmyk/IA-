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
import hmac
import json
import os
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _as_int(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0

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
            return hmac.compare_digest(got, TOKEN)

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
            if path == "/api/module/enable":
                return self._json(engine.enable_module(str(self._body().get("id", ""))))
            if path == "/api/permits/approve":
                return self._json(engine.approve_request(_as_int(self._body().get("id"))))
            if path == "/api/permits/deny":
                return self._json(engine.deny_request(_as_int(self._body().get("id"))))
            return self._json({"error": "not found"}, 404)

    return Handler


def _keep_awake_loop() -> None:
    """Tiene il bot ACCESO h24 su un host gratuito (es. Render) che si spegne dopo
    ~15 min di inattività.

    Il bot "si visita" da solo sul suo indirizzo PUBBLICO ogni pochi minuti: quella
    richiesta esce su internet e rientra dalla porta d'ingresso dell'host, quindi conta
    come visita vera e AZZERA il timer di spegnimento. Finché il bot è sveglio continua a
    pingarsi → il timer non arriva mai a 15 min → non si spegne più.

    Si attiva SOLO se c'è un indirizzo pubblico: la variabile SELF_PING_URL, oppure
    RENDER_EXTERNAL_URL che Render fornisce da solo. In locale (nessuna delle due) NON
    fa nulla, quindi la demo sul tuo PC resta identica.
    """
    url = os.environ.get("SELF_PING_URL") or os.environ.get("RENDER_EXTERNAL_URL", "")
    if not url:
        return
    interval = _as_int(os.environ.get("SELF_PING_SECONDS")) or 300   # default 5 min
    interval = max(60, min(interval, 840))   # tra 1 e 14 min (sotto il limite di 15)
    while True:
        time.sleep(interval)
        try:   # apre la home pubblica (non serve token): basta la visita a resettare il timer
            urllib.request.urlopen(url, timeout=20).read(64)
        except Exception:
            pass


def main() -> None:
    global TOKEN
    p = argparse.ArgumentParser(description="AgentColony — sito di gestione + motore 24/7")
    p.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")),
                   help="porta (di default legge la variabile PORT, es. su Render)")
    p.add_argument("--host", default="127.0.0.1", help="127.0.0.1=solo locale (sicuro) · 0.0.0.0=esposto in rete")
    p.add_argument("--token", default="", help="password per proteggere il sito se esposto in rete")
    p.add_argument("--open", action="store_true", help="apre automaticamente il browser all'avvio")
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
    # auto-sveglia: solo se online (indirizzo pubblico presente) → si pinga da solo h24
    if os.environ.get("SELF_PING_URL") or os.environ.get("RENDER_EXTERNAL_URL"):
        threading.Thread(target=_keep_awake_loop, daemon=True).start()
        print("  🔁 Auto-sveglia ATTIVA: il bot si visita da solo per non spegnersi.")
    if args.open:
        # apre il browser da solo poco dopo che il server è pronto (in silenzio se non riesce)
        def _open_browser():
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Timer(1.5, _open_browser).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nChiusura…")
        engine.shutdown()
        httpd.shutdown()


if __name__ == "__main__":
    main()
