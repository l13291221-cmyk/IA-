"""Scelta delle immagini riusate con la REGOLA DEI 30 REEL.

Un'immagine (anche specchiata) non può comparire in un reel se è già stata usata in uno
dei 30 reel precedenti, né due volte nello stesso reel. Quando la scelta preferita non è
libera, si prende l'immagine della libreria più simile (per descrizione) tra quelle libere.

  python selector.py PLAN.json [LIBRARY_EXTRA.json]   -> riscrive le scelte "img" nel piano
"""
import json
import math
import re
import sys
from collections import Counter

WINDOW = 30

STOP = set("""a an the and or of to in on at by for with from into onto over under above below his her
its their him he she it they them is are be been being was were has have had this that these those
there here as like while than then very big huge giant small tiny little one two three four five
same style vertical no text letters words wolf the image reference cap set per cartoon bold clean outlines flat
vibrant colors face looking looks look standing stands holding holds behind front next background
""".split())


SYN = {
    "exchange": "exchange building trading app", "exchanges": "exchange building trading app",
    "decentralized": "machines automatic portal", "fee": "toll gremlins receipt", "fees": "toll gremlins receipt",
    "patience": "waiting hourglass bench calm", "patient": "waiting hourglass calm", "crash": "red falling chart",
    "crashed": "red falling chart", "drop": "red falling chart", "profit": "coins gold", "profits": "coins gold",
    "stock": "stock exchange shares company", "stocks": "stock exchange shares company", "shares": "stock certificate company",
    "company": "headquarters company building", "companies": "headquarters company building",
    "scam": "scam detective suspicious", "scams": "scam detective suspicious", "hack": "hacker", "hacked": "hacker",
    "fear": "scared fear worried", "greed": "greed coins", "bond": "certificate bank interest", "bonds": "certificate bank interest",
    "inflation": "prices rising shrinking banknote", "rates": "interest dial bank", "dividend": "envelope coins dividend",
    "dividends": "envelope coins dividend", "gold": "gold bars", "silver": "silver bars", "oil": "oil barrels refinery",
    "wallet": "wallet phone hardware", "keys": "keys padlock", "chart": "chart screen", "trend": "staircase chart",
    "learn": "books teacher", "plan": "plan notebook map", "risk": "tightrope danger", "loss": "red falling worried",
}


def tokens(text, expand=False):
    words = [w for w in re.findall(r"[a-z]+", (text or "").lower()) if w not in STOP and len(w) > 2]
    if expand:
        words += [x for w in words for x in SYN.get(w, "").split()]
    return words


def is_pointing(desc):
    d = (desc or "").lower()
    return "points at the viewer" in d or "pointing at the viewer" in d or "pointing directly at the viewer" in d


class Library:
    def __init__(self):
        self.desc = {}      # id -> descrizione
        self.born = {}      # id -> parte in cui l'immagine nasce (riusabile solo dopo)

    def add(self, img_id, desc, part):
        if img_id not in self.desc:
            self.desc[img_id] = desc
            self.born[img_id] = part

    def build_index(self):
        df = Counter()
        self.tok = {}
        for k, d in self.desc.items():
            t = Counter(tokens(d))
            self.tok[k] = t
            df.update(t.keys())
        n = max(1, len(self.desc))
        self.idf = {w: math.log((n + 1) / (c + 0.5)) for w, c in df.items()}
        self.vec = {k: self._vec(t) for k, t in self.tok.items()}

    def _vec(self, counts):
        v = {w: c * self.idf.get(w, 1.0) for w, c in counts.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / norm for w, x in v.items()}

    def similar(self, query, allowed, bonus=None):
        q = self._vec(Counter(tokens(query, expand=True)))
        best, score = None, -1.0
        for k in allowed:
            v = self.vec.get(k, {})
            s = sum(q.get(w, 0) * x for w, x in v.items()) + (bonus(k) if bonus else 0)
            if s > score:
                best, score = k, s
        return best, score


def base_id(img):
    return img.split(":")[0].rsplit("_", 1)[0]          # "08_s4_1.jpg:flip" -> "08_s4"


def img_name(part, i):
    return f"{part:02d}_s{i}"


def order_key(k):
    """'45' -> 45 ; 'p050' (video VcriptoV dopo la parte 50) -> 50.5"""
    k = str(k)
    return float(k[1:]) + 0.5 if k.startswith("p") else float(k)


def key_img_name(k, i):
    k = str(k)
    return f"{k}_s{i}" if k.startswith("p") else img_name(int(k), i)


def ordered(plan):
    return sorted(plan, key=order_key)


def library_from_plan(plan, extra=None):
    lib = Library()
    for k, d in (extra or {}).items():
        lib.add(k, d, -1 if (k.startswith("00") or k.startswith("L")) else 0)
    for pos, k in enumerate(ordered(plan), start=1):
        for i, sc in enumerate(plan[k]["scenes"]):
            if sc.get("p"):
                lib.add(key_img_name(k, i), sc["p"], pos)
    lib.build_index()
    return lib


def apply_rule(plan, lib, history=None):
    """history: immagini del reel 001 (fatto fuori dal piano), posizione 0.
    La regola vale sulla POSIZIONE di pubblicazione: i 30 video precedenti, promo comprese."""
    used = {0: set((history or {}).get(1, []))}
    changed = 0
    for pos, k in enumerate(ordered(plan), start=1):
        window = set()
        for m in range(pos - WINDOW, pos):
            window |= used.get(m, set())
        this = {key_img_name(k, i) for i, sc in enumerate(plan[k]["scenes"]) if sc.get("p")}
        for i, sc in enumerate(plan[k]["scenes"]):
            if not sc.get("img") or sc["img"] == "intro":
                continue
            pref = sc.get("img_pref") or sc["img"]
            sc["img_pref"] = pref
            if pref == "auto":
                pref = "auto_1.jpg"
            b = base_id(pref)
            if b in lib.desc and b not in window and b not in this and lib.born.get(b, 0) < pos:
                choice = b
            else:
                allowed = [x for x in lib.desc if x not in window and x not in this and lib.born.get(x, 0) < pos]
                if sc["say"].startswith(("Follow for part", "Thanks for following", "Start free")):
                    allowed = [x for x in allowed if is_pointing(lib.desc[x])] or allowed
                hint = sc.get("hint", "")
                if hint:          # le parole chiave scritte apposta contano più del testo parlato
                    query = sc["say"] + (" " + hint) * 5
                else:
                    query = sc["say"] + " " + lib.desc.get(b, "") + " " + lib.desc.get(b, "")
                promo = str(k).startswith("p")
                choice, _ = lib.similar(query, allowed, (lambda x: 0.12 if x.startswith("p") else 0) if promo else None)
                changed += 1
            flip = pref.endswith(":flip") if choice == b else (pos + i) % 2 == 1
            sc["img"] = f"{choice}_1.jpg" + (":flip" if flip else "")
            this.add(choice)
        used[pos] = this
    return changed, used


def check(plan, history=None):
    used = {0: set((history or {}).get(1, []))}
    bad = []
    for pos, k in enumerate(ordered(plan), start=1):
        ids = [key_img_name(k, i) if sc.get("p") else base_id(sc["img"])
               for i, sc in enumerate(plan[k]["scenes"]) if sc.get("p") or (sc.get("img") and sc["img"] != "intro")]
        if len(ids) != len(set(ids)):
            bad.append((k, "doppia nello stesso reel"))
        for m in range(pos - WINDOW, pos):
            clash = set(ids) & used.get(m, set())
            if clash:
                bad.append((k, f"usata anche {pos - m} video prima: {sorted(clash)}"))
        used[pos] = set(ids)
    return bad


if __name__ == "__main__":
    path = sys.argv[1]
    plan = json.load(open(path))
    extra = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
    if len(sys.argv) > 3:      # libreria generica: {"L001": {"theme":..., "p":...}}
        extra.update({k: v["p"] for k, v in json.load(open(sys.argv[3])).items()})
    lib = library_from_plan(plan, extra)
    history = {1: [k for k in extra if k.startswith("01_")]}
    changed, _ = apply_rule(plan, lib, history)
    json.dump(plan, open(path, "w"), indent=1, ensure_ascii=False)
    problems = check(plan, history)
    print(f"libreria: {len(lib.desc)} immagini | scelte cambiate per la regola dei {WINDOW} reel: {changed} | problemi: {len(problems)}")
    for p in problems[:10]:
        print("  ", p)
