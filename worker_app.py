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
  • Env (ping):      MUTUAL_PING_URLS   = https://vcriptov.onrender.com  (ping ogni 5 min)

Endpoint:
  GET  /              → ok (health)
  GET  /health        → stato del motore
  POST /render-reel   → { kind, ... } ⇒ { url, caption }   (header X-Worker-Secret)
                        kind "cartoon" ⇒ 202 { pending, job } — poi GET /job/<job>
  GET  /reels/<file>  → serve il video creato (Instagram lo scarica da qui)
"""
import os
import subprocess
import sys


def _ensure_deps():
    """A PROVA DI TUTTO: se le librerie del motore mancano (Render a volte NON
    esegue il build e non installa nulla → 'No module named flask'), le installo
    io stesso PRIMA di importarle, nello STESSO Python che sta girando. Così il
    motore parte comunque, qualunque cosa faccia Render."""
    try:
        import flask  # noqa: F401
        import PIL  # noqa: F401
        import numpy  # noqa: F401
        import imageio  # noqa: F401
        import edge_tts  # noqa: F401
        return  # già tutto presente
    except Exception:
        pass
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    for cmd in (
        [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", req],
        [sys.executable, "-m", "pip", "install", "--no-cache-dir",
         "Flask", "gunicorn", "Pillow", "numpy", "imageio", "imageio-ffmpeg", "requests", "edge-tts"],
    ):
        try:
            print("Installo le librerie del motore video…", flush=True)
            subprocess.check_call(cmd)
            return
        except Exception as exc:
            print(f"Tentativo di installazione fallito: {exc}", flush=True)


_ensure_deps()

import threading  # noqa: E402
import time  # noqa: E402

from flask import Flask, request, jsonify, send_from_directory  # noqa: E402

import content  # noqa: E402
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
    return jsonify({"ok": True, "video": content.video_available(),
                    "keepalive_every": KEEPALIVE_EVERY, "keepalive": _KEEPALIVE["targets"],
                    "keepalive_urls": _KEEPALIVE["urls"],
                    "keepalive_alive": bool(_KEEPALIVE["thread"] and _KEEPALIVE["thread"].is_alive())})


# ── Reel CARTOON (omino che parla): li creo in BACKGROUND, uno alla volta ─────
# Con la CPU minima di Render un video può superare il timeout di una richiesta:
# il sito riceve subito un "job" e ripassa dopo qualche minuto a prendere il video.
_JOBS = {}
_JOBS_LOCK = threading.Lock()


def _public_base():
    return (os.environ.get("RENDER_EXTERNAL_URL") or request.host_url).rstrip("/")


def _run_cartoon(job_id, script, base):
    try:
        import cartoon
        path = cartoon.make_cartoon_reel(script)
        _JOBS[job_id].update(status="done", url=f"{base}/reels/{os.path.basename(path)}")
    except Exception as exc:
        _JOBS[job_id].update(status="error", error=f"{type(exc).__name__}: {exc}"[:300])


def _start_cartoon(spec):
    try:
        content.cleanup_old()
    except Exception:
        pass
    with _JOBS_LOCK:
        now = time.time()
        for k in [k for k, j in _JOBS.items() if now - j["ts"] > 6 * 3600]:
            _JOBS.pop(k, None)
        running = [k for k, j in _JOBS.items() if j["status"] == "running"]
        if running:   # uno alla volta (memoria)
            if _JOBS[running[0]].get("key") == (spec.get("key") or ""):
                return running[0]          # è lo stesso video richiesto di nuovo
            return None                    # un ALTRO video è in corso: riprova dopo
        job_id = f"{int(now * 1000)}"
        _JOBS[job_id] = {"status": "running", "ts": now, "caption": spec.get("caption") or "",
                         "key": spec.get("key") or ""}
    threading.Thread(target=_run_cartoon, args=(job_id, spec.get("data") or {}, _public_base()),
                     daemon=True).start()
    return job_id


def _run_ai(job_id, script, key, base):
    try:
        import reel_ai
        path = reel_ai.make_ai_reel(script, content.OUT_DIR, key)
        _JOBS[job_id].update(status="done", url=f"{base}/reels/{os.path.basename(path)}")
    except Exception as exc:
        _JOBS[job_id].update(status="error", error=f"{type(exc).__name__}: {exc}"[:300])


def _start_ai(spec):
    try:
        content.cleanup_old()
    except Exception:
        pass
    with _JOBS_LOCK:
        now = time.time()
        for k in [k for k, j in _JOBS.items() if now - j["ts"] > 6 * 3600]:
            _JOBS.pop(k, None)
        running = [k for k, j in _JOBS.items() if j["status"] == "running"]
        if running:
            if _JOBS[running[0]].get("key") == (spec.get("key") or ""):
                return running[0]
            return None
        job_id = f"{int(now * 1000)}"
        _JOBS[job_id] = {"status": "running", "ts": now, "caption": spec.get("caption") or "",
                         "key": spec.get("key") or ""}
    threading.Thread(target=_run_ai, args=(job_id, spec.get("data") or {},
                     spec.get("gemini_key") or "", _public_base()), daemon=True).start()
    return job_id


@app.get("/job/<job_id>")
def job_status(job_id):
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    j = _JOBS.get(job_id)
    if not j:
        return jsonify({"error": "job sconosciuto (motore riavviato?)"}), 404
    return jsonify({k: v for k, v in j.items() if k != "ts"})


@app.post("/render-reel")
def render_reel():
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    spec = request.get_json(force=True, silent=True) or {}
    kind = spec.get("kind")
    if kind == "cartoon":
        job_id = _start_cartoon(spec)
        if not job_id:
            return jsonify({"busy": True, "error": "il motore sta già creando un altro video"}), 409
        return jsonify({"pending": True, "job": job_id, "caption": spec.get("caption") or ""}), 202
    if kind == "ai":
        # reel stile "MaialeDiWallStreet": scene generate dall'IA (Gemini) + voce.
        # spec["data"] = copione (title/scenes), spec["gemini_key"] = chiave immagini.
        job_id = _start_ai(spec)
        if not job_id:
            return jsonify({"busy": True, "error": "il motore sta già creando un altro video"}), 409
        return jsonify({"pending": True, "job": job_id, "caption": spec.get("caption") or ""}), 202
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
        elif kind in ("market", "quiz", "myth", "top5", "fng", "candles", "chat"):
            # formati diversi: testi e dati li decide il sito (spec["data"])
            import reels2
            path = reels2.render(kind, spec.get("data") or {})
            caption = spec.get("caption") or ""
        elif kind == "promo":
            # Reel ANIMATO in stile pubblicità (titolo enorme, spunte, grafico al neon, invito).
            import promo_reel
            data = spec.get("data") or {}
            path, caption = promo_reel.render(int(spec.get("index", data.get("index", 0)) or 0), hook=data.get("hook"))
            caption = spec.get("caption") or caption
        elif kind == "custom":
            # Testo GIÀ scritto dal sito (AI lì): reel "sempre diverso" senza AI qui.
            path, _cap = content.make_custom_reel(
                spec.get("title", ""), spec.get("sub", ""), spec.get("expl", ""))
            caption = spec.get("caption") or _cap or ""
        else:  # "educational": scheda-pattern dalla libreria (nessuna AI/DB qui)
            path, caption = content.make_educational_reel(int(spec.get("index", 0) or 0))
    except Exception as exc:
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500
    if not path:
        return jsonify({"error": "video non generato (encoder non disponibile?)"}), 500
    fname = os.path.basename(path)
    base = (os.environ.get("RENDER_EXTERNAL_URL") or request.host_url).rstrip("/")
    return jsonify({"url": f"{base}/reels/{fname}", "caption": caption or ""})


@app.post("/render-post")
def render_post():
    """Immagine da POST (4:5) negli stessi formati dei reel: {kind, data, caption}."""
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    spec = request.get_json(force=True, silent=True) or {}
    kind = spec.get("kind")
    try:
        content.cleanup_old()
    except Exception:
        pass
    try:
        import reels2
        if kind not in reels2.RENDERERS and kind != "promo":
            return jsonify({"error": f"formato sconosciuto: {kind}"}), 400
        path = reels2.render(kind, spec.get("data") or {}, still=True)
    except Exception as exc:
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500
    base = (os.environ.get("RENDER_EXTERNAL_URL") or request.host_url).rstrip("/")
    return jsonify({"url": f"{base}/posts/{os.path.basename(path)}", "caption": spec.get("caption") or ""})


@app.post("/gen-test")
def gen_test():
    """Diagnostica: prova a generare UNA immagine col personaggio e torna l'esito
    (ok + url, oppure l'errore esatto di Gemini). Serve a capire se la chiave fa
    davvero immagini. spec = { gemini_key }."""
    if not _authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    spec = request.get_json(force=True, silent=True) or {}
    try:
        import genscene
        out = os.path.join(content.OUT_DIR, f"gentest_{int(time.time())}.png")
        ch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reel3d_assets", "character.jpg")
        res = genscene.diagnose(spec.get("gemini_key") or "", ch, out)
        if res.get("ok"):
            res["url"] = f"{_public_base()}/posts/{os.path.basename(out)}"
        return jsonify(res)
    except Exception as exc:
        return jsonify({"ok": False, "detail": f"{type(exc).__name__}: {exc}"[:300]}), 500


@app.get("/posts/<path:name>")
def serve_post(name):
    return send_from_directory(content.OUT_DIR, name, mimetype="image/png")


@app.get("/reels/<path:name>")
def serve_reel(name):
    # Instagram scarica il video da questo URL pubblico.
    return send_from_directory(content.OUT_DIR, name, mimetype="video/mp4")


# ── Auto-ping: tiene sveglia VcriptoV (e se stesso) sul free tier ──────────────
# `requests` importato QUI, nel thread principale: importarlo dentro il thread del
# ping poteva bloccarlo per sempre dopo il fork di gunicorn (lucchetto d'import
# rimasto chiuso nel processo copiato) → il ping non partiva mai.
try:
    import requests as _rq
except Exception:  # pragma: no cover
    _rq = None
KEEPALIVE_EVERY = int(os.environ.get("KEEPALIVE_EVERY", "300"))   # 5 minuti
_KEEPALIVE = {"targets": {}, "thread": None, "urls": [], "pid": None}
_KEEPALIVE_LOCK = threading.Lock()


def _ping_url(u: str) -> str:
    """Un indirizzo "nudo" (https://vcriptov.onrender.com) diventa la sua pagina
    LEGGERA /ping: prima si caricava la home intera di VcriptoV ogni volta."""
    u = u.strip().rstrip("/")
    return u + "/ping" if u.count("/") <= 2 else u


def _keepalive_loop():
    """Ogni 5 minuti fa un ping agli indirizzi in MUTUAL_PING_URLS (VcriptoV) e a
    se stesso, così nessuno dei due si addormenta (Render free dorme dopo 15 min).
    VcriptoV fa lo stesso verso questo servizio: ping reciproco."""
    if _rq is None:
        return
    # `or`: una variabile impostata ma VUOTA su Render non deve spegnere il ping
    urls = [_ping_url(u) for u in (os.environ.get("MUTUAL_PING_URLS")
                                   or "https://vcriptov.onrender.com").split(",") if u.strip()]
    self_url = (os.environ.get("RENDER_EXTERNAL_URL") or "").strip()
    if self_url:
        urls.append(self_url.rstrip("/") + "/health")
    _KEEPALIVE["urls"] = urls
    time.sleep(20)          # lascia finire l'avvio, poi SUBITO il primo giro
    while True:
        for u in urls:
            try:
                r = _rq.get(u, timeout=20)
                _KEEPALIVE["targets"][u] = {"ok": r.status_code < 500, "code": r.status_code, "at": time.time()}
            except Exception as exc:
                _KEEPALIVE["targets"][u] = {"ok": False, "error": type(exc).__name__, "at": time.time()}
        time.sleep(KEEPALIVE_EVERY)


def _ensure_keepalive():
    """Avvia il thread del ping in QUESTO processo se non gira. Chiamato all'avvio
    E a ogni richiesta: se gunicorn carica l'app in un processo e poi la "copia"
    nei worker (fork), il thread partito all'import non esiste nel worker."""
    t = _KEEPALIVE["thread"]
    if t is not None and t.is_alive() and _KEEPALIVE["pid"] == os.getpid():
        return
    with _KEEPALIVE_LOCK:
        t = _KEEPALIVE["thread"]
        if t is not None and t.is_alive() and _KEEPALIVE["pid"] == os.getpid():
            return
        _KEEPALIVE["pid"] = os.getpid()
        _KEEPALIVE["thread"] = threading.Thread(target=_keepalive_loop, name="keepalive", daemon=True)
        _KEEPALIVE["thread"].start()


_ensure_keepalive()


@app.before_request
def _keepalive_guard():
    _ensure_keepalive()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
