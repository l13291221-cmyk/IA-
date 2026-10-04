"""
Generazione SCENE con l'IA (Gemini "nano banana" = gemini-2.5-flash-image).

Dato il personaggio di riferimento (reel3d_assets/character.jpg) + un prompt di
scena, Gemini genera l'immagine della scena mantenendo lo STESSO personaggio
(es. "il lupo in un caveau pieno d'oro"). E' il meccanismo dietro i video tipo
MaialeDiWallStreet: stesso personaggio, tante scene diverse generate dall'IA.

La chiave e' quella che il creatore ha gia' (podcast/Gemini), passata come
`api_key`. DORMIENTE senza chiave.

NB: la coerenza del personaggio e' buona ma non perfetta, specie con un
personaggio fotorealistico. Uno stile piu' "cartoon" resta piu' coerente.
"""
import os, base64, json, urllib.parse, time
import requests

_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
# modelli immagine, in ordine: il primo che risponde vince (come per il testo)
_MODELS = ["gemini-2.5-flash-image", "gemini-2.5-flash-image-preview",
           "gemini-2.0-flash-preview-image-generation"]

# ---- POLLINATIONS: generatore immagini GRATIS e senza chiave (FLUX) ----
# Non blocca il personaggio da una foto (e' testo->immagine), ma con una
# descrizione fissa del lupo + lo STESSO seme teniamo il personaggio coerente
# tra le scene. Illimitato e gratis: la scelta di default.
_POLLI = "https://image.pollinations.ai/prompt/"
# STILE FISSO: cartone 2D (come "MaialeDiWallStreet") applicato a TUTTE le immagini
# (personaggio E scene-oggetto) cosi' il reel e' coerente dall'inizio alla fine.
STYLE = ("2D cartoon illustration, bold thick black outlines, flat vibrant colors, "
         "cel-shaded comic caricature style, clean vector look, mascot style")
WOLF_DESC = ("a cartoon anthropomorphic grey wolf mascot with a confident smug face, "
             "wearing an elegant black suit with tie, big gold chain necklaces and a gold "
             "watch, the same recognizable character every time")
WOLF_SEED = 777   # seme fisso per la coerenza del personaggio tra le scene (Pollinations)


# ---- MISTRAL: generazione immagini via Agents API (FLUX 1.1 Pro) ----
_MISTRAL_AGENTS = {}   # cache: chiave -> agent_id (non ricreo l'agente ogni volta)


def _mistral_agent(key, timeout):
    if _MISTRAL_AGENTS.get(key):
        return _MISTRAL_AGENTS[key]
    try:
        r = requests.post("https://api.mistral.ai/v1/agents",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json={"model": "mistral-medium-2505", "name": "VcriptoV images",
                                "instructions": "Always use the image generation tool to create the requested image.",
                                "tools": [{"type": "image_generation"}]}, timeout=timeout)
        if r.status_code == 200:
            aid = r.json().get("id")
            if aid:
                _MISTRAL_AGENTS[key] = aid
                return aid
        return None
    except Exception:
        return None


def _find_file_id(obj):
    if isinstance(obj, dict):
        for k in ("file_id", "fileId"):
            if obj.get(k):
                return obj[k]
        for v in obj.values():
            f = _find_file_id(v)
            if f:
                return f
    elif isinstance(obj, list):
        for v in obj:
            f = _find_file_id(v)
            if f:
                return f
    return None


def _mistral_image(prompt, key, out_path, timeout=150, retry429=True):
    """Ritorna (out_path, None) o (None, errore).
    retry429: se True (reel in background) aspetta e riprova sul limite 429;
    se False (diagnostico sincrono) UN colpo solo, cosi' non va in timeout."""
    key = (key or "").strip()
    if not key:
        return None, "nessuna chiave Mistral"
    aid = _mistral_agent(key, timeout)
    if not aid:
        return None, "creazione agente Mistral fallita (chiave?)"
    try:
        # Il limite immagini di Mistral (429) e' quasi sempre per-minuto: nel reel
        # (background) aspetto e riprovo; nel diagnostico no (resteresti appeso).
        waits = (0, 20, 30, 45, 60) if retry429 else (0,)
        r = None
        for wait in waits:
            if wait:
                time.sleep(wait)
            r = requests.post("https://api.mistral.ai/v1/conversations",
                              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                              json={"agent_id": aid, "inputs": prompt}, timeout=timeout)
            if r.status_code != 429:
                break   # 200 o errore vero: esco; 429: aspetto e riprovo
        if r.status_code == 429:
            return None, "Mistral: limite immagini raggiunto (429). Aspetta qualche minuto e riprova."
        if r.status_code != 200:
            return None, f"http {r.status_code}: {r.text[:200]}"
        fid = _find_file_id(r.json())
        if not fid:
            return None, "risposta senza immagine"
        rf = requests.get(f"https://api.mistral.ai/v1/files/{fid}/content",
                          headers={"Authorization": f"Bearer {key}"}, timeout=timeout)
        if rf.status_code == 200 and rf.content and len(rf.content) > 2000:
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(rf.content)
            return out_path, None
        return None, f"download immagine http {rf.status_code}"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"[:150]


def _pollinations(prompt: str, out_path: str, seed: int = WOLF_SEED,
                  w: int = 720, h: int = 1280, timeout: int = 120) -> str | None:
    try:
        u = _POLLI + urllib.parse.quote(prompt[:900], safe="")
        r = requests.get(u, params={"width": w, "height": h, "nologo": "true",
                                    "model": "flux", "seed": int(seed)}, timeout=timeout)
        ct = r.headers.get("content-type", "")
        if r.status_code == 200 and r.content and len(r.content) > 2000 and ct.startswith("image"):
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(r.content)
            return out_path
    except Exception:
        return None
    return None


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _extract_image(data: dict):
    """Trova la prima immagine (base64) nelle parti della risposta Gemini."""
    for cand in (data.get("candidates") or []):
        for part in ((cand.get("content") or {}).get("parts") or []):
            inl = part.get("inline_data") or part.get("inlineData")
            if inl and inl.get("data"):
                return inl["data"]
    return None


def generate_scene(prompt: str, character_path: str, api_key: str, out_path: str,
                   aspect: str = "9:16", timeout: int = 150,
                   provider: str = "mistral", seed: int = WOLF_SEED) -> str | None:
    """Genera UNA scena COL personaggio. Ritorna out_path o None.
    provider: 'mistral' (FLUX, genera il lupo dalla descrizione), 'pollinations'
    (gratis, testo->immagine) o 'gemini' (coerenza da foto, serve fatturazione)."""
    if provider == "mistral":
        full = f"{WOLF_DESC}. {prompt}. {STYLE}. vertical 9:16, no text, no watermark."
        out, _err = _mistral_image(full, api_key, out_path, timeout=timeout)
        return out
    if provider == "pollinations":
        full = f"{WOLF_DESC}. {prompt}. {STYLE}. vertical, no text"
        return _pollinations(full, out_path, seed=seed, timeout=timeout)
    key = (api_key or "").strip()
    if not key or not os.path.exists(character_path):
        return None
    full = (f"Keep EXACTLY the same character from the reference image (same wolf, "
            f"same black suit, white shirt, gold Bitcoin chain, same face and colors). "
            f"{prompt}. Cinematic dramatic lighting, highly detailed, vertical 9:16 format.")
    body = {
        "contents": [{"parts": [
            {"text": full},
            {"inline_data": {"mime_type": "image/jpeg", "data": _b64(character_path)}},
        ]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                             "imageConfig": {"aspectRatio": aspect}},
    }
    for m in _MODELS:
        try:
            r = requests.post(f"{_URL}{m}:generateContent", params={"key": key},
                              json=body, timeout=timeout)
            if r.status_code == 400:
                # alcune versioni non accettano imageConfig: riprovo senza
                b2 = json.loads(json.dumps(body)); b2["generationConfig"].pop("imageConfig", None)
                r = requests.post(f"{_URL}{m}:generateContent", params={"key": key},
                                  json=b2, timeout=timeout)
            if r.status_code == 404:
                continue
            if r.status_code != 200:
                continue
            img_b64 = _extract_image(r.json())
            if img_b64:
                os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                if os.path.getsize(out_path) > 2000:
                    return out_path
        except Exception:
            continue
    return None


def generate_object(prompt: str, api_key: str, out_path: str,
                    aspect: str = "9:16", timeout: int = 150,
                    provider: str = "mistral", seed: int = 0) -> str | None:
    """Scena SENZA personaggio (oggetto/luogo: caveau, documenti, grafico...)."""
    if provider == "mistral":
        out, _err = _mistral_image(f"{prompt}. {STYLE}. vertical 9:16, no text, no watermark",
                                   api_key, out_path, timeout=timeout)
        return out
    if provider == "pollinations":
        full = f"{prompt}. {STYLE}. vertical, no text"
        return _pollinations(full, out_path, seed=(seed or 101), timeout=timeout)
    key = (api_key or "").strip()
    if not key:
        return None
    full = f"{prompt}. Cinematic dramatic lighting, highly detailed, vertical 9:16 format, no text."
    body = {"contents": [{"parts": [{"text": full}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                                 "imageConfig": {"aspectRatio": aspect}}}
    for m in _MODELS:
        try:
            r = requests.post(f"{_URL}{m}:generateContent", params={"key": key},
                              json=body, timeout=timeout)
            if r.status_code == 400:
                b2 = json.loads(json.dumps(body)); b2["generationConfig"].pop("imageConfig", None)
                r = requests.post(f"{_URL}{m}:generateContent", params={"key": key}, json=b2, timeout=timeout)
            if r.status_code == 404:
                continue
            if r.status_code != 200:
                continue
            img_b64 = _extract_image(r.json())
            if img_b64:
                os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                if os.path.getsize(out_path) > 2000:
                    return out_path
        except Exception:
            continue
    return None


def diagnose(api_key: str, character_path: str, out_path: str, timeout: int = 150,
             provider: str = "mistral") -> dict:
    """Prova UNA generazione e torna il dettaglio per capire cosa non va.
    {ok, model, status, detail, saved}. Usato dal tasto diagnostico in Admin."""
    if provider == "mistral":
        full = f"{WOLF_DESC}. counting a thick stack of cash in his hands, city skyline behind. {STYLE}. vertical 9:16, no text."
        got, err = _mistral_image(full, api_key, out_path, timeout=min(timeout, 90), retry429=False)
        if got:
            return {"ok": True, "status": 200, "detail": "immagine generata (Mistral/FLUX)",
                    "model": "mistral/flux", "saved": os.path.basename(out_path)}
        return {"ok": False, "status": -1, "detail": err or "Mistral non ha generato", "model": "mistral/flux"}
    if provider == "pollinations":
        full = f"{WOLF_DESC}. standing in a modern trading office with green charts. cinematic, comic illustration, vertical"
        got = _pollinations(full, out_path, seed=WOLF_SEED, timeout=timeout)
        if got:
            return {"ok": True, "status": 200, "detail": "immagine generata (Pollinations, gratis)",
                    "model": "pollinations/flux", "saved": os.path.basename(out_path)}
        return {"ok": False, "status": -1, "detail": "Pollinations non raggiungibile dal motore",
                "model": "pollinations/flux"}
    key = (api_key or "").strip()
    if not key:
        return {"ok": False, "status": 0, "detail": "nessuna chiave Gemini configurata", "model": None}
    have_char = bool(character_path and os.path.exists(character_path))
    parts = [{"text": "A fierce wolf in a black suit with a gold Bitcoin chain, standing in a bank "
                      "vault full of gold, cinematic, vertical 9:16."}]
    if have_char:
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": _b64(character_path)}})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                                 "imageConfig": {"aspectRatio": "9:16"}}}
    last = {"ok": False, "status": 0, "detail": "nessun modello ha risposto", "model": None}
    for m in _MODELS:
        try:
            r = requests.post(f"{_URL}{m}:generateContent", params={"key": key}, json=body, timeout=timeout)
            if r.status_code == 400:
                b2 = json.loads(json.dumps(body)); b2["generationConfig"].pop("imageConfig", None)
                r = requests.post(f"{_URL}{m}:generateContent", params={"key": key}, json=b2, timeout=timeout)
            if r.status_code == 404:
                last = {"ok": False, "status": 404, "detail": f"modello {m} non trovato", "model": m}
                continue
            if r.status_code != 200:
                return {"ok": False, "status": r.status_code, "detail": r.text[:300], "model": m}
            img = _extract_image(r.json())
            if img:
                os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img))
                return {"ok": True, "status": 200, "detail": "immagine generata", "model": m,
                        "saved": os.path.basename(out_path)}
            return {"ok": False, "status": 200, "detail": "risposta senza immagine (solo testo)", "model": m}
        except Exception as exc:
            last = {"ok": False, "status": -1, "detail": f"{type(exc).__name__}: {exc}"[:200], "model": m}
    return last
