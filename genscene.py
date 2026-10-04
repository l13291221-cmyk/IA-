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
import os, base64, json
import requests

_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
# modelli immagine, in ordine: il primo che risponde vince (come per il testo)
_MODELS = ["gemini-2.5-flash-image", "gemini-2.5-flash-image-preview",
           "gemini-2.0-flash-preview-image-generation"]


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
                   aspect: str = "9:16", timeout: int = 90) -> str | None:
    """Genera UNA scena col personaggio di riferimento. Ritorna out_path o None.
    Best-effort: ogni errore -> None (chi chiama ripiega sul ritaglio dell'immagine)."""
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
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                if os.path.getsize(out_path) > 2000:
                    return out_path
        except Exception:
            continue
    return None


def generate_object(prompt: str, api_key: str, out_path: str,
                    aspect: str = "9:16", timeout: int = 90) -> str | None:
    """Scena SENZA personaggio (oggetto/luogo: caveau, documenti, grafico...)."""
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
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                if os.path.getsize(out_path) > 2000:
                    return out_path
        except Exception:
            continue
    return None


def diagnose(api_key: str, character_path: str, out_path: str, timeout: int = 90) -> dict:
    """Prova UNA generazione e torna il dettaglio per capire cosa non va.
    {ok, model, status, detail, saved}. Usato dal tasto diagnostico in Admin."""
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
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img))
                return {"ok": True, "status": 200, "detail": "immagine generata", "model": m,
                        "saved": os.path.basename(out_path)}
            return {"ok": False, "status": 200, "detail": "risposta senza immagine (solo testo)", "model": m}
        except Exception as exc:
            last = {"ok": False, "status": -1, "detail": f"{type(exc).__name__}: {exc}"[:200], "model": m}
    return last
