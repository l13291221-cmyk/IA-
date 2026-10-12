"""TESTI DEI SOCIAL per ogni video, dal suo copione (inglese e italiano).

Scrive series/social.json: per ogni video ("001", "010a", "391", "v001"…)
  argomento (il titolo breve della puntata), frase d'apertura, 2-3 punti chiave e la
  prossima puntata. Il sito ci costruisce descrizione Instagram, titolo e descrizione
  YouTube, testo TikTok e la scritta della copertina: ogni video ha i SUOI testi (prima
  erano 8 frasi uguali a rotazione per tutti, e YouTube vedeva centinaia di titoli identici).

L'argomento della puntata N è quello annunciato alla fine della N-1 ("Follow for part 52:
index funds and Warren Buffett's famous bet").

Uso: python studio/social_meta.py   (rigenera tutto, veloce, nessuna rete)"""
import json
import os
import re

STUDIO = os.path.dirname(os.path.abspath(__file__))
SERIES = os.path.join(STUDIO, "series")
BOT_SCRIPTS = os.path.join(STUDIO, "bot", "scripts")
OUT = os.path.join(SERIES, "social.json")

EN_NUM = ("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
          "sixteen seventeen eighteen nineteen twenty").split()
IT_NUM = ("uno due tre quattro cinque sei sette otto nove dieci undici dodici tredici quattordici quindici "
          "sedici diciassette diciotto diciannove venti").split()
TENS = {"en": {"twenty": 20, "thirty": 30, "forty": 40}, "it": {"venti": 20, "trenta": 30, "quaranta": 40}}
FIRST = {"en": "3 simple rules to stop losing money in crypto",
         "it": "3 regole semplici per non perdere soldi in crypto"}
NEXT_RE = {"en": re.compile(r"[Pp]art ([\w-]+)\s*[:,—-]\s*(.+)"),
           "it": re.compile(r"[Pp]arte ([\w-]+)\s*[:,—-]\s*(.+)")}
STOP_RE = {"en": re.compile(r"\.\s*Not financial advice", re.I),
           "it": re.compile(r"\.\s*Non (?:è|e') (?:un )?consiglio", re.I)}
CTA_RE = re.compile(r"^(Follow for part|Segui per la parte|Start free|Inizia gratis)", re.I)


def _num(word, lang):
    w = word.lower().strip("-")
    if w.isdigit():
        return int(w)
    words = EN_NUM if lang == "en" else IT_NUM
    if w in words:
        return words.index(w) + 1
    for t, v in TENS[lang].items():
        if w.startswith(t):
            rest = w[len(t):].strip("-")
            if not rest:
                return v
            for i, x in enumerate(words[:9]):
                if rest in (x, x[1:]):
                    return v + i + 1
    return None


def _next(last, lang):
    """(numero, argomento) annunciati alla fine di una puntata, o (None, None)."""
    m = NEXT_RE[lang].search(last or "")
    if not m:
        return None, None
    n = _num(m.group(1), lang)
    t = STOP_RE[lang].split(m.group(2))[0].strip().rstrip(".").strip()
    return n, (t or None)


def _show(text, show):
    for k, v in (show or {}).items():
        text = text.replace(k, v)
    return text


def _clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def _sentence_case(t):
    return t[:1].upper() + t[1:] if t else t


def _points(lines):
    """2-3 punti chiave: le frasi centrali, le più brevi e chiare."""
    mid = [x for x in lines[1:] if not CTA_RE.match(x)]
    pick = [x for x in mid if len(x) <= 120][:3] or mid[:2]
    return pick


def _entry(name, part, promo, en_lines, it_lines):
    return {"part": part, "promo": promo,
            "hook_en": en_lines[0] if en_lines else "", "hook_it": it_lines[0] if it_lines else "",
            "points_en": _points(en_lines), "points_it": _points(it_lines) if it_lines else []}


def build():
    plan = json.load(open(os.path.join(SERIES, "plan.json")))
    plan_it = json.load(open(os.path.join(SERIES, "plan_it.json")))
    out, lasts = {}, {"en": {}, "it": {}}
    # serie e promo scritte a mano (plan.json)
    for k, r in plan.items():
        promo = not k.isdigit()
        n = int(k.lstrip("p"))
        name = f"{n:03d}a" if promo else f"{n:03d}"
        en = [_clean(_show(sc["say"], sc.get("show"))) for sc in r["scenes"]]
        it = [_clean(_show(sc["say"], sc.get("show"))) for sc in (plan_it.get(k) or {}).get("scenes", [])]
        out[name] = _entry(name, n, promo, en, it)
        if not promo:
            lasts["en"][n], lasts["it"][n] = en[-1] if en else "", it[-1] if it else ""
    # video fatti dal bot del magazzino (391, 392… e v001, v002…)
    if os.path.isdir(BOT_SCRIPTS):
        for f in sorted(os.listdir(BOT_SCRIPTS)):
            if not f.endswith(".json"):
                continue
            key = f[:-5]
            d = json.load(open(os.path.join(BOT_SCRIPTS, f)))
            en = [_clean(_show(sc["say"], sc.get("show"))) for sc in d.get("en") or []]
            it = [_clean(x if isinstance(x, str) else x.get("say", "")) for x in d.get("it") or []]
            promo = key.startswith("v")
            n = int(key.lstrip("v")) if key.lstrip("v").isdigit() else 0
            name = key if promo else f"{n:03d}"
            out[name] = _entry(name, n, promo, en, it)
            if not promo:
                lasts["en"][n], lasts["it"][n] = en[-1] if en else "", it[-1] if it else ""
    # argomento della puntata N = annunciato alla fine della N-1; prossima = annunciata alla fine della N
    for lang in ("en", "it"):
        topic = {}
        for n, last in lasts[lang].items():
            m, t = _next(last, lang)
            if m and t:
                topic[m] = t
        for name, e in out.items():
            if e["promo"]:
                # promo: la prima frase dell'apertura ("Where does your money go when you use VcriptoV?")
                m = re.match(r"(.+?[.?!])(\s|$)", e[f"hook_{lang}"])
                e[f"topic_{lang}"] = (m.group(1) if m and len(m.group(1)) >= 20 else e[f"hook_{lang}"]).rstrip(".")
                e[f"next_{lang}"] = None
                continue
            n = e["part"]
            e[f"topic_{lang}"] = _sentence_case(topic.get(n) or (FIRST[lang] if n == 1 else e[f"hook_{lang}"]))
            _m, nxt = _next(lasts[lang].get(n), lang)
            e[f"next_{lang}"] = nxt
    return dict(sorted(out.items()))


def main():
    data = build()
    old = open(OUT).read() if os.path.exists(OUT) else ""
    new = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    if new != old:
        open(OUT, "w").write(new)
    print(f"social.json: {len(data)} video{' (aggiornato)' if new != old else ' (invariato)'}")


if __name__ == "__main__":
    main()
