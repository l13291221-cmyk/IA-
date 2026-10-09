"""Monta un gruppo di reel della serie su GitHub Actions (tanti computer in parallelo).

  KEYS="65,66,p070,71" python studio/batch_render.py      → studio/work/out/065.mp4, …
  REEL_LANG=it KEYS=... python studio/batch_render.py      → la COPIA IN ITALIANO (solo anteprima,
                                                             mai pubblicata), testi da series/plan_it.json

Stessi copioni (series/plan.json), stessa voce e stesso montaggio dei video fatti a mano;
le immagini sono quelle della libreria (library/<nome>.jpg).
"""
import json
import os
import sys
import time

STUDIO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, STUDIO)
import render_reel  # noqa: E402

LIB = os.path.join(STUDIO, "library")
REEL_LANG = os.environ.get("REEL_LANG", "en")
IT_SERIES = {"HOW TO INVEST IN CRYPTO": "COME INVESTIRE IN CRYPTO", "HOW TO INVEST": "COME INVESTIRE",
             "YOUR CRYPTO ASSISTANT": "IL TUO ASSISTENTE CRYPTO"}
IT_VOICE = os.environ.get("VOICE") or "it-IT-DiegoNeural"     # la voce italiana più naturale fra quelle gratis
IT_RATE = os.environ.get("RATE") or "+5%"
HOOK = os.environ.get("HOOK", "1") == "1"         # inizio col "gancio" (ora per tutti): il lupo dice subito la prima frase
MAXSEC = float(os.environ.get("MAXSEC") or 0)     # durata massima (es. 35 s): voce un po' più veloce se serve
OUT = os.path.join(STUDIO, "work", "out")
INTRO = os.path.join(STUDIO, "intro.mp4")


def key_img_name(k, i):
    return f"{k}_s{i}" if k.startswith("p") else f"{int(k):02d}_s{i}"


def out_name(k):
    return f"{int(k[1:]):03d}a.mp4" if k.startswith("p") else f"{int(k):03d}.mp4"


def lib_img(name_1jpg):
    """"17_s2_1.jpg:flip" → "17_s2.jpg:flip" se esiste nella libreria, se no None."""
    base, _, flip = name_1jpg.partition(":")
    stem = base[:-6] if base.endswith("_1.jpg") else base.rsplit(".", 1)[0]
    if os.path.exists(os.path.join(LIB, stem + ".jpg")):
        return stem + ".jpg" + (":" + flip if flip else "")
    return None


def spec_for(pl, k, it=None):
    """Spec del video `k`. Con `it` (traduzioni di plan_it.json) la copia in italiano:
    stesse immagini, testi e voce italiani."""
    r = pl[k]
    n = int(k.lstrip("p"))
    scenes = [{"say": r["intro_say"], "img": "intro"}]
    last = None
    for i, sc in enumerate(r["scenes"]):
        img = lib_img(sc["img"]) if sc.get("img") else lib_img(key_img_name(k, i) + "_1.jpg")
        img = img or last
        if img is None:
            raise RuntimeError(f"manca la prima immagine di {k}")
        last = img
        d = {"say": sc["say"], "img": img}
        if sc.get("show"):
            d["show"] = sc["show"]
        scenes.append(d)
    spec = {"part": n, "badge": r.get("badge"), "series": r.get("series", "HOW TO INVEST IN CRYPTO"),
            "voice": "en-US-AndrewNeural", "rate": "+6%", "intro": INTRO, "img_dir": LIB, "scenes": scenes}
    if it is not None:
        tr = it[k]
        if len(tr["scenes"]) != len(r["scenes"]):
            raise RuntimeError(f"traduzione di {k}: scene diverse dall'inglese")
        scenes[0]["say"] = tr["intro_say"]
        for d, t in zip(scenes[1:], tr["scenes"]):
            d["say"] = t["say"]
            d.pop("show", None)
            if t.get("show"):
                d["show"] = t["show"]
        spec.update(series=IT_SERIES.get(spec["series"], spec["series"]), part_label="PARTE",
                    voice=IT_VOICE, rate=IT_RATE)
    if HOOK:
        # NUOVO INIZIO: niente "How to invest in crypto. Part N." detto a voce (il titolo resta
        # scritto in alto): il lupo dice subito la prima frase, con i sottotitoli. Se la frase dura
        # più dell'intro, dopo si vede la sua immagine.
        first = scenes[1]
        hook = {"say": first["say"], "img": "intro", "caption": True, "after": first["img"]}
        if first.get("show"):
            hook["show"] = first["show"]
        spec["scenes"] = [hook] + scenes[2:]
    if MAXSEC:
        spec["max_seconds"] = MAXSEC
    return spec


def main():
    pl = json.load(open(os.path.join(STUDIO, "series", "plan.json")))
    it = json.load(open(os.path.join(STUDIO, "series", "plan_it.json"))) if REEL_LANG == "it" else None
    keys = [k.strip() for k in os.environ.get("KEYS", "").split(",") if k.strip()]
    os.makedirs(OUT, exist_ok=True)
    bad = []
    for k in keys:
        out = os.path.join(OUT, out_name(k))
        for attempt in range(3):                      # la voce (Edge) ogni tanto non risponde
            try:
                t0 = time.time()
                sp = os.path.join(OUT, f"spec_{k}.json")
                json.dump(spec_for(pl, k, it), open(sp, "w"), indent=1, ensure_ascii=False)
                render_reel.build(sp, out)
                print(f"RENDERED {out_name(k)} in {time.time() - t0:.0f}s", flush=True)
                break
            except Exception as exc:
                print(f"ERRORE {k} (tentativo {attempt + 1}): {exc}", flush=True)
                time.sleep(10)
        else:
            bad.append(k)
    for f in os.listdir(OUT):
        if not f.endswith(".mp4"):
            p = os.path.join(OUT, f)
            if os.path.isfile(p):
                os.remove(p)
    print("NON RIUSCITI:", ",".join(bad) if bad else "nessuno")


if __name__ == "__main__":
    main()
