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

# Siti "amici" da tenere svegli A VICENDA (ping reciproco): oltre a pingare sé
# stesso, il bot pinga anche questi indirizzi ogni pochi minuti. Così, se l'altro
# sito non riesce ad auto-pingarsi, ci pensa questo (rete di sicurezza reciproca).
# Modificabile con la variabile d'ambiente MUTUAL_PING_URLS (uno o più indirizzi
# separati da virgola). Per SPEGNERLO: imposta MUTUAL_PING_URLS a vuoto.
_DEFAULT_MUTUAL_PING = "https://vcriptov.onrender.com"

# stato "resta acceso": per mostrare sul sito il timer di spegnimento di Render e
# l'auto-ping. `last_visit` viene azzerato da una visita VERA (apertura pagina) o dal
# ping automatico; NON dai controlli di stato in background, così il timer si vede scorrere.
_STATS_LOCK = threading.Lock()
_STATS = {"last_visit": time.time(), "ping_count": 0, "ping_last": 0.0,
          "ping_interval": 0, "online": False,
          # ping reciproco verso l'ALTRO sito (per tenerlo sveglio a vicenda)
          "mping_count": 0, "mping_last": 0.0, "mping_interval": 0,
          "mping_urls": 0, "mping_ok": 0}


def _touch_visit() -> None:
    with _STATS_LOCK:
        _STATS["last_visit"] = time.time()


def _render_stats() -> dict:
    with _STATS_LOCK:
        now = time.time()
        return {
            "online": _STATS["online"],
            "spindown_total": 900,   # Render gratis: ~15 min senza visite → si spegne
            "idle_seconds": max(0, round(now - _STATS["last_visit"])),
            "ping_count": _STATS["ping_count"],
            "ping_interval": _STATS["ping_interval"],
            "ping_last_ago": (round(now - _STATS["ping_last"]) if _STATS["ping_last"] else None),
            # ping reciproco verso l'altro sito (rete di sicurezza a vicenda)
            "mutual": {
                "urls": _STATS["mping_urls"],
                "interval": _STATS["mping_interval"],
                "count": _STATS["mping_count"],
                "ok": _STATS["mping_ok"],
                "last_ago": (round(now - _STATS["mping_last"]) if _STATS["mping_last"] else None),
            },
        }


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
                    snap = engine.snapshot()
                    snap["render"] = _render_stats()   # timer spegnimento + auto-ping
                    return self._json(snap)
                return self._json({"error": "not found"}, 404)
            try:
                if path in ("/", "/index.html", "/app.html"):
                    _touch_visit()   # una visita VERA azzera il timer di spegnimento
                    return self._send(200, "text/html; charset=utf-8", _page("app.html"))
                return self._send(404, "text/plain; charset=utf-8", b"404")
            except FileNotFoundError:
                return self._send(404, "text/plain; charset=utf-8", b"pagina non trovata")

        def do_POST(self):
            path = self.path.split("?")[0]
            if not self._authed():
                return self._json({"error": "token"}, 401)
            _touch_visit()   # un'azione VERA (click) azzera il timer di spegnimento
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
            if path == "/api/reset-swarm":
                engine.reset_swarm()
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
    with _STATS_LOCK:
        _STATS["online"] = True
        _STATS["ping_interval"] = interval
    while True:
        time.sleep(interval)
        try:   # apre la home pubblica (non serve token): basta la visita a resettare il timer
            urllib.request.urlopen(url, timeout=20).read(64)
        except Exception:
            pass
        with _STATS_LOCK:
            _STATS["ping_count"] += 1
            _STATS["ping_last"] = time.time()


def _mutual_ping_targets() -> list:
    """Gli indirizzi degli altri siti da tenere svegli (ping reciproco).

    Di default pinga `_DEFAULT_MUTUAL_PING`. Con la variabile MUTUAL_PING_URLS
    puoi metterne uno o più (separati da virgola o spazio), oppure lasciarla
    VUOTA per spegnere del tutto il ping reciproco.
    """
    raw = os.environ.get("MUTUAL_PING_URLS")
    if raw is None:                       # variabile non impostata → uso il default
        raw = _DEFAULT_MUTUAL_PING
    return [u.strip() for u in raw.replace(",", " ").split() if u.strip().startswith("http")]


def _mutual_ping_loop() -> None:
    """Pinga l'ALTRO sito (o più siti) ogni pochi minuti per tenerlo sveglio.

    È il "gemello" dell'auto-ping: se l'altro sito non riuscisse a tenersi sveglio
    da solo, ci pensa questo. Si attiva SOLO online (quando c'è un indirizzo
    pubblico) e SOLO se ci sono indirizzi da pingare. Intervallo: MUTUAL_PING_SECONDS
    (default 5 min), tra 1 e 14 min.
    """
    urls = _mutual_ping_targets()
    if not urls:
        return
    interval = _as_int(os.environ.get("MUTUAL_PING_SECONDS")) or 300   # default 5 min
    interval = max(60, min(interval, 840))
    with _STATS_LOCK:
        _STATS["mping_urls"] = len(urls)
        _STATS["mping_interval"] = interval
    while True:
        time.sleep(interval)
        ok = 0
        for u in urls:
            try:   # basta una visita all'altro sito per azzerare il SUO timer di spegnimento
                urllib.request.urlopen(u, timeout=20).read(64)
                ok += 1
            except Exception:
                pass
        with _STATS_LOCK:
            _STATS["mping_count"] += 1
            _STATS["mping_last"] = time.time()
            _STATS["mping_ok"] = ok


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
        # ping reciproco: tiene sveglio ANCHE l'altro sito (rete di sicurezza a vicenda)
        targets = _mutual_ping_targets()
        if targets:
            threading.Thread(target=_mutual_ping_loop, daemon=True).start()
            print("  🤝 Ping reciproco ATTIVO verso: " + ", ".join(targets))
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
