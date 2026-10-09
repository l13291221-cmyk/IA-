"""Costruttore dei copioni (parti 38+): scrive in plan.json.

Ogni scena è (testo detto, immagine[, sostituzioni sottotitoli]):
  immagine = "prompt della scena nuova"   -> generata su Vadoo (2 crediti)
           = "@NN_sK"  /  "@NN_sK!"       -> riuso dalla libreria (! = specchiata)
La scena finale "Follow for part N: ..." viene aggiunta in automatico.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = {}
for _l in open(os.path.join(HERE, "topics_all.txt")):
    _n, _c, _t = _l.rstrip("\n").split("|", 2)
    TOP[int(_n)] = (_c, _t)
TOP[37] = ("C", "free crypto airdrops, real or scam")
# la 391 è il primo argomento del bot automatico (continua la serie da solo)
_bl = [l.strip().split("|", 1) for l in open(os.path.join(HERE, "bot_backlog.txt")) if "|" in l]
if _bl:
    TOP[391] = (_bl[0][0], _bl[0][1])

# Immagini generiche del lupo che indica lo spettatore (per il finale), a rotazione.
CTA_POOL = ["01_s8", "04_s6", "38_s6", "39_s5", "40_s5", "41_s5", "42_s5", "43_s6", "44_s5", "45_s6"]

PLAN = {}


def to_img(ref):
    flip = ref.endswith("!")
    return f"{ref.strip('@!')}_1.jpg" + (":flip" if flip else "")


def reel(n, scenes, cta=None, last_say=None):
    cat, _topic = TOP[n]
    crypto = cat == "C"
    out = []
    for sc in scenes:
        say, img = sc[0], sc[1]
        d = {"say": say}
        if img.startswith("@auto"):
            d["img"] = "auto"                      # scelta automatica (regola dei 30 reel)
            d["hint"] = img[6:].strip()            # "@auto:oro lingotti" -> parole chiave
        elif img.startswith("@"):
            d["img"] = to_img(img)
        else:
            d["p"] = img
        if len(sc) > 2 and sc[2]:
            d["show"] = sc[2]
        out.append(d)
    nxt = TOP.get(n + 1)
    say = last_say or (f"Follow for part {n + 1}: {nxt[1]}. Not financial advice." if nxt
                       else "Thanks for following the whole series. Not financial advice.")
    if cta is None:
        k = n % len(CTA_POOL)
        flip = (n // len(CTA_POOL)) % 2 == 1
        cta = "@" + CTA_POOL[k] + ("!" if flip else "")
    d = {"say": say}
    if cta.startswith("@"):
        d["img"] = to_img(cta)
    else:
        d["p"] = cta
    out.append(d)
    PLAN[str(n)] = {"part": n,
                    "series": "HOW TO INVEST IN CRYPTO" if crypto else "HOW TO INVEST",
                    "intro_say": f"How to invest in crypto. Part {n}." if crypto else f"How to invest. Part {n}.",
                    "scenes": out}


def save():
    path = os.path.join(HERE, "plan.json")
    plan = json.load(open(path)) if os.path.exists(path) else {}
    plan.update(PLAN)
    json.dump(plan, open(path, "w"), indent=1, ensure_ascii=False)
    new = sum(1 for r in PLAN.values() for s in r["scenes"] if s.get("p"))
    ks = sorted(PLAN, key=lambda k: float(k[1:]) + 0.5 if k.startswith("p") else float(k))
    print(f"{ks[0]}-{ks[-1]}: {len(PLAN)} video, {new} immagini nuove")


def promo(n, scenes):
    """Video su VcriptoV, pubblicato subito dopo la parte n (file NNNa.mp4)."""
    out = []
    for sc in scenes:
        say, img = sc[0], sc[1]
        d = {"say": say}
        if img.startswith("@auto"):
            d["img"], d["hint"] = "auto", img[6:].strip()
        elif img.startswith("@"):
            d["img"] = to_img(img)
        else:
            d["p"] = img
        if len(sc) > 2 and sc[2]:
            d["show"] = sc[2]
        out.append(d)
    out.append({"say": "Start free at VcriptoV dot com. Link in bio. Not financial advice.", "img": "auto",
                "hint": "points at the viewer", "show": {"VcriptoV dot com": "VCRIPTOV.COM"}})
    PLAN[f"p{n:03d}"] = {"part": n, "promo": True, "badge": "VCRIPTOV", "series": "YOUR CRYPTO ASSISTANT",
                         "intro_say": "Meet VcriptoV.", "scenes": out}
