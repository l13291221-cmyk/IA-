"""
MOTORE VIDEO di VcriptoV — micro-servizio che crea SOLO i reel (video).

Perché esiste: su Render free tier (512MB) montare un video con ffmpeg SUL sito
principale fa sforare la memoria (email "exceeded its memory limit" + riavvii).
Questo servizio gira su un'istanza DEDICATA: tutti i 512MB liberi per il video, e
il sito principale non tocca mai ffmpeg. Il sito principale gli chiede il reel via
HTTP, riceve un URL pubblico e lo pubblica su Instagram.

In più tiene sveglia VcriptoV (auto-ping reciproco), come faceva il vecchio bot
che stava qui: così i segnali del sito principale non si fermano mai.

AVVIO su Render:
  • Start command:   gunicorn worker_app:app --timeout 150 --bind 0.0.0.0:$PORT
  • Env (opzionale): REEL_WORKER_SECRET = password (la stessa su VcriptoV)
  • Env (ping):      MUTUAL_PING_URLS   = https://vcriptov.onrender.com

Endpoint:
  GET  /              → ok (health)
  GET  /health        → stato del motore
  POST /render-reel   → { kind, ... } ⇒ { url, caption }   (header X-Worker-Secret)
  GET  /reels/<file>  → serve il video creato (Instagram lo scarica da qui)
"""
import os
import threading
import time

from flask import Flask, request, jsonify, send_from_directory

import content
# QUI il video è ACCESO: è lo scopo unico di questa istanza (sul sito principale
# resta spento per non sforare la memoria).
content.VIDEO_ENABLED = True

app = Flask(__name__)
SECRET = os.environ.get("REEL_WORKER_SECRET", "")


def _authorized(req) -> bool:
    """Se è impostato un segreto, la richiesta deve portarlo (così solo il TUO
    sito principale può usare il motore, non estranei)."""
    return (not SECRET) or (req.headers.get("X-Worker-Secret") == SECRET)


@app.get("/")
def home():
    return "VcriptoV — motore video attivo. 🎬", 200


@app.get("/health")
def health():
    return jsonify({"ok": True, "video": content.video_available()})


@app.post("/render-reel")
def render_reel():
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    spec = request.get_json(force=True, silent=True) or {}
    kind = spec.get("kind")
    try:
        content.cleanup_old()   # non far crescere il disco all'infinito
    except Exception:
        pass
    try:
        if kind == "signal":
            path, caption = content.make_signal_reel(
                spec.get("coin", ""), bool(spec.get("is_buy", True)),
                float(spec.get("price", 0) or 0),
                float(spec.get("sl", 8) or 8),
                float(spec.get("tp", 15) or 15),
                spec.get("risk", "medio"),
                gain_pct=spec.get("gain_pct"),
            )
        else:  # "educational": scheda-pattern dalla libreria (nessuna AI/DB qui)
            path, caption = content.make_educational_reel(int(spec.get("index", 0) or 0))
    except Exception as exc:
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500
    if not path:
        return jsonify({"error": "video non generato (encoder non disponibile?)"}), 500
    fname = os.path.basename(path)
    base = (os.environ.get("RENDER_EXTERNAL_URL") or request.host_url).rstrip("/")
    return jsonify({"url": f"{base}/reels/{fname}", "caption": caption or ""})


@app.get("/reels/<path:name>")
def serve_reel(name):
    # Instagram scarica il video da questo URL pubblico.
    return send_from_directory(content.OUT_DIR, name, mimetype="video/mp4")


# ── Auto-ping: tiene sveglia VcriptoV (e se stesso) sul free tier ──────────────
def _keepalive_loop():
    """Ogni ~10 min fa un ping agli indirizzi in MUTUAL_PING_URLS (VcriptoV) e a
    se stesso, così nessuno dei due si addormenta. È la stessa rete di sicurezza
    che c'era prima su questo servizio."""
    try:
        import requests as _rq
    except Exception:
        return
    urls = [u.strip() for u in os.environ.get("MUTUAL_PING_URLS", "").split(",") if u.strip()]
    self_url = (os.environ.get("RENDER_EXTERNAL_URL") or "").strip()
    if self_url:
        urls.append(self_url.rstrip("/") + "/health")
    if not urls:
        return
    while True:
        time.sleep(600)
        for u in urls:
            try:
                _rq.get(u, timeout=15)
            except Exception:
                pass


threading.Thread(target=_keepalive_loop, name="keepalive", daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
