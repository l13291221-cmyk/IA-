"""Produzione in serie dei reel: immagini da Vadoo + montaggio.

  python produce.py images 2 13     # genera (solo) le immagini mancanti delle parti 2..13
  python produce.py render 2 13     # monta i video delle parti 2..13 (out/NN.mp4)
"""
import json
import os
import subprocess
import sys

STUDIO = os.path.dirname(os.path.abspath(__file__))
SERIES = os.path.join(STUDIO, "series")          # copioni (plan.json) e libreria
IMG = os.path.join(STUDIO, "work", "img")        # immagini scaricate da Vadoo (non versionate)
OUT = os.path.join(STUDIO, "work", "out")        # video finiti (poi copiati in ../reels/)
PY = sys.executable
TOOLS = STUDIO
REF = "https://d3adwkbyhxyrtq.cloudfront.net/aivideo/images/1034059/737876313748/wolf_ref.png"
INTRO = os.path.join(STUDIO, "intro.mp4")
PRE = ("The same grey wolf character from the reference image (grey fur, black suit, white shirt, red tie, "
       "thick gold chain with a gold Bitcoin pendant, gold watch), same cartoon style with bold clean black "
       "outlines and flat vibrant colors. ")
SUF = " Vertical 9:16. No text, no letters, no words."


def plan():
    return json.load(open(os.path.join(SERIES, "plan.json")))


def img_name(part, i):
    return f"{part:02d}_s{i}"


def order_key(k):
    k = str(k)
    return float(k[1:]) + 0.5 if k.startswith("p") else float(k)


def key_img_name(k, i):
    k = str(k)
    return f"{k}_s{i}" if k.startswith("p") else img_name(int(k), i)


def keys_in(pl, a, b):
    return sorted([k for k in pl if a <= order_key(k) < b + 1], key=order_key)


def out_name(k):
    k = str(k)
    return f"{int(k[1:]):03d}a.mp4" if k.startswith("p") else f"{int(k):03d}.mp4"


def have(name):
    p = os.path.join(IMG, name + "_1.jpg")
    return os.path.exists(p) and os.path.getsize(p) > 20000


def images(a, b):
    os.makedirs(IMG, exist_ok=True)
    pl = plan()
    for attempt in range(3):
        jobs = []
        for k in keys_in(pl, a, b):
            r = pl[k]
            for i, sc in enumerate(r["scenes"]):
                name = key_img_name(k, i)
                if sc.get("p") and not sc.get("img") and not have(name):
                    jobs.append({"name": name, "model": "grok_imagine", "num": 1, "images": [REF],
                                 "prompt": PRE + sc["p"] + SUF})
        if not jobs:
            print("tutte le immagini ci sono", flush=True)
            return
        print(f"giro {attempt + 1}: {len(jobs)} immagini da generare", flush=True)
        jf = os.path.join(SERIES, f"jobs_{a}_{b}.json")
        json.dump(jobs, open(jf, "w"), indent=1)
        subprocess.run([PY, "-I", os.path.join(TOOLS, "vadoo_web.py"), "gen", jf, IMG], check=False)


def render(a, b):
    os.makedirs(OUT, exist_ok=True)
    pl = plan()
    for k in keys_in(pl, a, b):
        render_key(pl, k)


def render_key(pl, k):
    if True:
        r = pl[k]
        n = int(str(k).lstrip("p"))
        out = os.path.join(OUT, out_name(k))
        if os.path.exists(out):
            print("già fatto", out)
            return
        scenes = [{"say": r["intro_say"], "img": "intro"}]
        last = None
        for i, sc in enumerate(r["scenes"]):
            name = key_img_name(k, i)
            if sc.get("img"):                       # immagine riusata dalla libreria
                base = sc["img"].split(":")[0]
                img = sc["img"] if os.path.exists(os.path.join(IMG, base)) else last
            else:
                img = name + "_1.jpg" if have(name) else last
            if img is None:
                raise RuntimeError(f"manca la prima immagine della parte {n}")
            last = img
            d = {"say": sc["say"], "img": img}
            if sc.get("show"):
                d["show"] = sc["show"]
            scenes.append(d)
        spec = {"part": n, "badge": r.get("badge"), "series": r.get("series", "HOW TO INVEST IN CRYPTO"), "voice": "en-US-AndrewNeural", "rate": "+6%",
                "intro": INTRO, "img_dir": IMG, "scenes": scenes}
        sp = os.path.join(SERIES, "spec_" + out_name(k).replace(".mp4", ".json"))
        json.dump(spec, open(sp, "w"), indent=1, ensure_ascii=False)
        subprocess.run([PY, "-I", os.path.join(TOOLS, "render_reel.py"), sp, out], check=True)


if __name__ == "__main__" and sys.argv[1] in ("images", "render"):
    cmd, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    {"images": images, "render": render}[cmd](a, b)


def images_library():
    """Genera le immagini della libreria generica (series/library_prompts.json)."""
    lib = json.load(open(os.path.join(SERIES, "library_prompts.json")))
    for attempt in range(3):
        jobs = [{"name": k, "model": "grok_imagine", "num": 1, "images": [REF], "prompt": PRE + v["p"] + SUF}
                for k, v in lib.items() if not have(k)]
        if not jobs:
            print("libreria completa", flush=True)
            return
        print(f"libreria giro {attempt + 1}: {len(jobs)} immagini", flush=True)
        jf = os.path.join(SERIES, "jobs_library.json")
        json.dump(jobs, open(jf, "w"), indent=1)
        subprocess.run([PY, "-I", os.path.join(TOOLS, "vadoo_web.py"), "gen", jf, IMG], check=False)


if __name__ == "__main__" and sys.argv[1] == "library":
    images_library()
