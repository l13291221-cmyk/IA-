"""CATALOGO: famiglie di entrata × filtri × uscite → decine di migliaia di tecniche diverse.

Una tecnica è un dizionario (spec) con:
  tf     timeframe delle candele (1h / 4h / 1d)
  fam,p  famiglia di entrata e i suoi numeri
  trend  filtro di tendenza della moneta (EMA sullo stesso timeframe)
  btc    Bitcoin sopra la sua media di D giorni (chiusura giornaliera)
  vol    volume della candela ≥ m volte la media
  htf    chiusura giornaliera della moneta sopra la sua EMA di D giorni
  stop   stop iniziale (multipli di ATR, minimo recente o percentuale)
  tp     obiettivo in multipli del rischio (0 = nessuno)
  trail  stop che sale (minimo di M candele, chandelier, EMA)
  be     stop a pareggio dopo +be R
  xs     uscita a segnale
  hold   durata massima in candele
Le idee vengono da: canali di Donchian e Turtle, «Catching Crypto Trends» (insieme di Donchian),
Quantpedia (MAX / MIN, stagionalità orarie e di calendario), rottura di volatilità di Larry
Williams, RSI(2) di Connors, Bollinger / Keltner / squeeze, Supertrend, MACD, Ichimoku,
Heikin-Ashi, momentum per serie storica e trasversale (Liu-Tsyvinski-Wu), forza contro Bitcoin,
ritardo delle monete dietro a Bitcoin, picchi di volume, candele enormi, NR7 / inside bar,
compressione e rottura, comprare la discesa in tendenza, giorni della settimana, fine mese.
"""
from __future__ import annotations

import json
import random
import zlib

import numpy as np

import engine as E

D1 = 86400_000
BPD = {"1h": 24, "4h": 6, "1d": 1}
WARM = 210

LB = [5, 10, 20, 30, 50, 100, 200]
HOLD = {"1h": [4, 8, 12, 24, 48, 96, 168, 336],
        "4h": [2, 3, 6, 12, 18, 30, 42, 84, 180],
        "1d": [1, 2, 3, 5, 7, 10, 15, 20, 30, 60, 120]}

# famiglia: (timeframe ammessi, griglia dei parametri, uscita propria a segnale?)
FAM = {
    "donch":     (("1h", "4h", "1d"), [(n,) for n in LB], False),
    "donchi":    (("1h", "4h", "1d"), [(n,) for n in LB], False),
    "closehigh": (("1h", "4h", "1d"), [(n,) for n in LB], False),
    "closelow":  (("1h", "4h", "1d"), [(n,) for n in LB], False),
    "macross":   (("1h", "4h", "1d"), [(5, 20), (9, 21), (10, 30), (12, 26), (20, 50), (20, 100), (50, 200)], True),
    "pxma":      (("1h", "4h", "1d"), [(n,) for n in (10, 20, 50, 100, 200)], True),
    "roc":       (("1h", "4h", "1d"), [(n, k) for n in (1, 3, 6, 12, 24, 48) for k in (1, 1.5, 2, 3)], False),
    "rsitrend":  (("1h", "4h", "1d"), [(n, v) for n in (7, 14, 21) for v in (55, 60, 65, 70, 75)], False),
    "rsirev":    (("1h", "4h", "1d"), [(n, v) for n in (2, 3, 4, 7, 14) for v in (5, 10, 15, 20, 25, 30)], False),
    "bbbreak":   (("1h", "4h", "1d"), [(n, k) for n in (20, 50) for k in (1.5, 2, 2.5, 3)], False),
    "bbrev":     (("1h", "4h", "1d"), [(n, k) for n in (20, 50) for k in (1.5, 2, 2.5, 3)], False),
    "kelt":      (("1h", "4h", "1d"), [(n, k) for n in (20, 50) for k in (1.5, 2, 3)], False),
    "macd":      (("1h", "4h", "1d"), [(f, s, g, z) for f, s, g in ((12, 26, 9), (8, 21, 5), (19, 39, 9), (5, 35, 5))
                                       for z in (0, -1, 1)], True),
    "supert":    (("1h", "4h", "1d"), [(n, m) for n in (7, 10, 14, 20) for m in (2, 3, 4)], True),
    "squeeze":   (("1h", "4h", "1d"), [(k, n) for k in (50, 100, 200) for n in (10, 20, 30)], False),
    "volbo":     (("1h", "4h", "1d"), [(k,) for k in (0.25, 0.5, 0.75, 1.0)], False),
    "pullback":  (("1h", "4h", "1d"), [(s, L) for s in (10, 20, 50) for L in (100, 200)], False),
    "downstreak": (("1h", "4h", "1d"), [(k,) for k in (2, 3, 4, 5, 6)], False),
    "upstreak":  (("1h", "4h", "1d"), [(k,) for k in (2, 3, 4, 5)], False),
    "inside":    (("1h", "4h", "1d"), [(1,)], False),
    "nr":        (("1h", "4h", "1d"), [(n,) for n in (4, 7, 10)], False),
    "zrev":      (("1h", "4h", "1d"), [(n, k) for n in (20, 50, 100) for k in (1.5, 2, 2.5, 3)], False),
    "stochrev":  (("1h", "4h", "1d"), [(n, v) for n in (14, 21) for v in (10, 20)], False),
    "adxdi":     (("1h", "4h", "1d"), [(n, t) for n in (14, 20) for t in (20, 25, 30)], False),
    "hour":      (("1h",), [(h,) for h in range(24)], False),
    "dow":       (("1d",), [(d,) for d in range(7)], False),
    "tom":       (("1d",), [(k,) for k in (1, 2, 3)], False),
    "bigup":     (("1h", "4h", "1d"), [(k,) for k in (1.5, 2, 2.5, 3)], False),
    "bigdown":   (("1h", "4h", "1d"), [(k,) for k in (1.5, 2, 2.5, 3)], False),
    "volup":     (("1h", "4h", "1d"), [(m,) for m in (3, 5, 8)], False),
    "voldown":   (("1h", "4h", "1d"), [(m,) for m in (3, 5, 8)], False),
    "yearhigh":  (("1h", "4h", "1d"), [(d,) for d in (90, 180, 365)], False),
    "tsmom":     (("4h", "1d"), [(d,) for d in (7, 14, 30, 60, 90)], True),
    "ensdon":    (("4h", "1d"), [(t,) for t in (0.3, 0.5, 0.7, 0.9)], True),
    "rsbtc":     (("1h", "4h", "1d"), [(n,) for n in (20, 50, 100, 200)], False),
    "lagcatch":  (("1h", "4h"), [(n, k) for n in (1, 3, 6) for k in (1.5, 2, 3)], False),
    "dipbuy":    (("1h", "4h", "1d"), [(n, x) for n in (20, 50, 100) for x in (0.1, 0.2, 0.3)], False),
    "atrexp":    (("1h", "4h", "1d"), [(k,) for k in (1.5, 2, 2.5)], False),
    "consol":    (("1h", "4h", "1d"), [(n, x) for n in (20, 50) for x in (0.05, 0.1, 0.15, 0.2)], False),
    "ichi":      (("1h", "4h", "1d"), [(9, 26)], True),
    "ha":        (("1h", "4h", "1d"), [(k,) for k in (2, 3, 4)], True),
    "xsmom":     (("1d",), [(L, K, K2) for L in (7, 14, 30, 60) for K in (1, 2, 3, 5) for K2 in (1, 2, 3)], True),
    "rand":      (("1h", "4h", "1d"), [(p,) for p in (0.01, 0.03, 0.1)], False),
    "nearhigh":  (("4h", "1d"), [(d, x) for d in (90, 365) for x in (0.8, 0.9, 0.95)], False),
    "dayrun":    (("1h",), [(k, hmax) for k in (0.3, 0.5, 0.75, 1.0) for hmax in (12, 20)], True),
    "fund":      (("1h", "4h", "1d"), [(thr, n) for thr in (0.0, -0.0001, -0.0003) for n in (1, 3, 9)], False),
    # ---- 3ª ondata: famiglie nuove ----
    "cci":       (("1h", "4h", "1d"), [(n, v, m) for n in (14, 20, 40) for v in (100, 150, 200) for m in (1, -1)], False),
    "aroon":     (("1h", "4h", "1d"), [(n, t) for n in (14, 25, 50) for t in (70, 90)], False),
    "obv":       (("1h", "4h", "1d"), [(n,) for n in (20, 50, 100)], False),
    "mfi":       (("1h", "4h", "1d"), [(n, v) for n in (7, 14) for v in (10, 20, 30, 60, 70, 80)], False),
    "cmf":       (("1h", "4h", "1d"), [(n, t) for n in (20, 50) for t in (0.05, 0.1, 0.2)], False),
    "kama":      (("1h", "4h", "1d"), [(n,) for n in (10, 20, 30)], True),
    "hma":       (("1h", "4h", "1d"), [(n,) for n in (9, 21, 55)], True),
    "trix":      (("1h", "4h", "1d"), [(n,) for n in (9, 15, 30)], True),
    "psar":      (("1h", "4h", "1d"), [(st,) for st in (0.01, 0.02, 0.04)], True),
    "linreg":    (("1h", "4h", "1d"), [(n, k) for n in (20, 50, 100) for k in (0.05, 0.1, 0.2)], False),
    "er":        (("1h", "4h", "1d"), [(n, t) for n in (10, 20, 50) for t in (0.3, 0.5, 0.7)], False),
    "vwap":      (("1h", "4h", "1d"), [(n,) for n in (24, 50, 100, 200)], True),
    "vcp":       (("1h", "4h", "1d"), [(k, n) for k in (0.6, 0.75) for n in (10, 20, 50)], False),
    "rsidiv":    (("1h", "4h", "1d"), [(n,) for n in (20, 50)], False),
    "elder":     (("1h", "4h", "1d"), [(13,)], True),
    "ma3stack":  (("1h", "4h", "1d"), [(5, 20, 50), (10, 30, 100), (20, 50, 200)], True),
}
MR = {"rsidiv", "fund", "closelow", "rsirev", "bbrev", "downstreak", "zrev", "stochrev", "bigdown", "voldown", "dipbuy", "lagcatch"}

TREND = [None, ("ema", 50), ("ema", 100), ("ema", 200), ("stack",), ("adx", 20)]
BTC = [None, 20, 50, 100, 200]
VOL = [None, 1.5, 2, 3]
HTF = [None, 20, 50]
STOP = [("atr", s) for s in (0.5, 1, 1.5, 2, 3, 4, 6)] + [("swing", k) for k in (3, 5, 10, 20)] + \
       [("pct", p) for p in (0.03, 0.08, 0.2)]
TP = [0, 0, 0, 1, 1.5, 2, 3, 5]
TRAIL = [None, None, None] + [("llc", m) for m in (3, 5, 10, 20, 30, 50)] + [("chand", 22, k) for k in (2, 3, 4)] + \
        [("ema", n) for n in (10, 20, 50)]
BE = [0, 0, 1, 2]
XS = [None, None, "fam", "ema20", "ema50", "sma5up", "rsi70", "low10"]


def key(s):
    return json.dumps(s, sort_keys=True, separators=(",", ":"))


def sample(rng, fam=None):
    fam = fam or rng.choice(list(FAM))
    tfs, grid, _own = FAM[fam]
    tf = rng.choice(tfs)
    s = {"tf": tf, "fam": fam, "p": list(rng.choice(grid)),
         "trend": rng.choice(TREND), "btc": rng.choice(BTC), "vol": rng.choice(VOL), "htf": rng.choice(HTF),
         "stop": rng.choice(STOP), "tp": rng.choice(TP), "trail": rng.choice(TRAIL), "be": rng.choice(BE),
         "xs": rng.choice(XS), "hold": rng.choice(HOLD[tf])}
    if tf == "1d":
        s["htf"] = None                               # sarebbe lo stesso filtro di tendenza
    return {k: (list(v) if isinstance(v, tuple) else v) for k, v in s.items()}


NO_CONF = {"donchi", "volbo", "inside", "nr", "rand"}   # entrate dentro la candela o a caso: non come conferma


def add_confluence(rng, s):
    """Aggiunge un secondo segnale (dello stesso timeframe) che deve esserci nelle ultime w candele."""
    pool = [f for f, (tfs, _g, _o) in FAM.items() if s["tf"] in tfs and f != s["fam"] and f not in NO_CONF]
    f2 = rng.choice(pool)
    s = dict(s)
    s["fam2"] = f2
    s["p2"] = list(rng.choice(FAM[f2][1]))
    s["win2"] = rng.choice([1, 3, 6, 12])
    return s


def catalog(n, seed=1):
    rng = random.Random(seed)
    fams = list(FAM)
    out, seen = [], set()
    while len(out) < n:
        s = sample(rng, fams[len(out) % len(fams)])   # famiglie a turno: tutte ben rappresentate
        k = key(s)
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out


def a14():
    """La tecnica che c'è adesso nel bot (rottura 4h di 30 + volume ×2 + EMA200 + BTC>EMA50 giornaliera,
    stop 2 ATR, stop che sale al minimo di 30 candele, 7 giorni)."""
    return {"tf": "4h", "fam": "donch", "p": [30], "trend": ["ema", 200], "btc": 50, "vol": 2, "htf": None,
            "stop": ["atr", 2], "tp": 0, "trail": ["llc", 30], "be": 0, "xs": None, "hold": 42}


# ------------------------------------------------------------------ costruzione dei segnali
def cross_up(a, b):
    pa, pb = E.shift(a), E.shift(b) if isinstance(b, np.ndarray) else b
    return (a > b) & (pa <= pb)


def _ensdon_score(I):
    def f():
        sc = np.zeros(I.n)
        for n in (10, 20, 30, 60, 90, 150, 250):
            up, lo = I.hh(n), I.ll(n)
            sc += _don_state(I.c, up, (up + lo) / 2)
        return sc / 7
    return I.get("ensdon", f)


@E.nb.njit(cache=True)
def _don_state(c, up, mid):
    st = np.zeros(len(c))
    s = 0.0
    for i in range(len(c)):
        if c[i] > up[i]:
            s = 1.0
        elif c[i] < mid[i]:
            s = 0.0
        st[i] = s
    return st


def family(I, ctx, fam, p):
    """(segnale alla chiusura, livello di entrata dentro la candela dopo o None, uscita propria o None)."""
    c, o, h, l, v = I.c, I.o, I.h, I.l, I.v
    tf = I.tf
    bpd = BPD[tf]
    if fam == "donch":
        return c > I.hh(p[0]), None, None
    if fam == "donchi":
        return np.ones(I.n, bool), E.rolling_max(h, p[0]), None
    if fam == "closehigh":
        return c > E.shift(E.rolling_max(c, p[0])), None, None
    if fam == "closelow":
        return c < E.shift(E.rolling_min(c, p[0])), None, None
    if fam == "macross":
        f, s = I.ema(p[0]), I.ema(p[1])
        return cross_up(f, s), None, f < s
    if fam == "pxma":
        m = I.ema(p[0])
        return cross_up(c, m), None, c < m
    if fam == "roc":
        n, k = p
        thr = k * I.atr(14) / c * np.sqrt(n)
        r = I.roc(n)
        return (r > thr) & ~(E.shift(r) > E.shift(thr)), None, None
    if fam == "rsitrend":
        return cross_up(I.rsi(p[0]), float(p[1])), None, None
    if fam == "rsirev":
        return I.rsi(p[0]) < p[1], None, None
    if fam == "bbbreak":
        up, _lo, _w = I.bb(p[0], p[1])
        return cross_up(c, up), None, None
    if fam == "bbrev":
        _up, lo, _w = I.bb(p[0], p[1])
        return c < lo, None, None
    if fam == "kelt":
        n, k = p
        return cross_up(c, I.ema(n) + k * I.atr(n)), None, None
    if fam == "macd":
        f, s, g, z = p
        m, sg = I.macd(f, s, g)
        e = cross_up(m, sg)
        if z < 0:
            e &= m < 0
        elif z > 0:
            e &= m > 0
        return e, None, m < sg
    if fam == "supert":
        d = I.supertrend(p[0], p[1])
        return (d > 0) & (E.shift(d) < 0), None, d < 0
    if fam == "squeeze":
        k, n = p
        _u, _l, w = I.bb(20, 2.0)
        sq = (w <= E.rolling_min(w, k) * 1.05).astype(float)
        recent = E.shift(E.rolling_max(sq, 10)) > 0
        return recent & (c > I.hh(n)), None, None
    if fam == "volbo":
        return np.ones(I.n, bool), c + p[0] * (h - l), None
    if fam == "pullback":
        s, L = p
        es, el = I.ema(s), I.ema(L)
        return (c > el) & (es > el) & (l <= es) & (c > es) & (c > o), None, None
    if fam == "downstreak":
        return I.streak() <= -p[0], None, None
    if fam == "upstreak":
        return I.streak() >= p[0], None, None
    if fam == "inside":
        return (h < E.shift(h)) & (l > E.shift(l)), h, None
    if fam == "nr":
        r = h - l
        return r <= E.rolling_min(r, p[0]), h, None
    if fam == "zrev":
        return I.z(p[0]) < -p[1], None, None
    if fam == "stochrev":
        return cross_up(I.stoch(p[0]), float(p[1])), None, None
    if fam == "adxdi":
        a, pdi, ndi = I.adx(p[0])
        return (a > p[1]) & cross_up(pdi, ndi), None, None
    if fam == "hour":                                # la candela che CHIUDE all'ora p
        return ((I.hour() + 1) % 24) == p[0], None, None
    if fam == "dow":
        return I.dow() == p[0], None, None
    if fam == "tom":                                 # ultimi k giorni del mese
        nxt = (I.t + p[0] * D1).astype("datetime64[ms]").astype("datetime64[M]")
        cur = I.t.astype("datetime64[ms]").astype("datetime64[M]")
        nx1 = (I.t + (p[0] - 1) * D1).astype("datetime64[ms]").astype("datetime64[M]")
        return (nxt != cur) & (nx1 == cur), None, None
    if fam == "bigup":
        return (c - o) > p[0] * E.shift(I.atr(14)), None, None
    if fam == "bigdown":
        return (o - c) > p[0] * E.shift(I.atr(14)), None, None
    if fam == "volup":
        return (v > p[0] * I.vavg(20)) & (c > o), None, None
    if fam == "voldown":
        return (v > p[0] * I.vavg(20)) & (c < o), None, None
    if fam == "yearhigh":
        return c > I.hh(p[0] * bpd), None, None
    if fam == "tsmom":
        r = I.roc(p[0] * bpd)
        return (r > 0) & ~(E.shift(r) > 0), None, r < 0
    if fam == "ensdon":
        sc = _ensdon_score(I)
        return (sc >= p[0]) & (E.shift(sc) < p[0]), None, sc < p[0]
    if fam == "rsbtc":
        bs = ctx.btc_series(tf)
        if bs is None:
            return None
        ratio = c / bs[0]
        return ratio > E.shift(E.rolling_max(ratio, p[0])), None, None
    if fam == "lagcatch":
        bs = ctx.btc_series(tf)
        if bs is None:
            return None
        n, k = p
        b, batr = bs
        br = b / E.shift(b, n) - 1
        thr = k * batr / b * np.sqrt(n)
        cr = I.roc(n)
        return (br > thr) & (cr < 0.5 * br), None, None
    if fam == "dipbuy":
        n, x = p
        return c / I.hcc(n) - 1 < -x, None, None
    if fam == "atrexp":
        return (I.atr(5) > p[0] * I.atr(50)) & (c > o), None, None
    if fam == "consol":
        n, x = p
        hh, ll = I.hh(n), I.ll(n)
        return ((hh - ll) / c < x) & (c > hh), None, None
    if fam == "ichi":
        tk = (E.rolling_max(h, 9) + E.rolling_min(l, 9)) / 2
        kj = (E.rolling_max(h, 26) + E.rolling_min(l, 26)) / 2
        sa = E.shift((tk + kj) / 2, 26)
        sb = E.shift((E.rolling_max(h, 52) + E.rolling_min(l, 52)) / 2, 26)
        top = np.maximum(sa, sb)
        return cross_up(tk, kj) & (c > top), None, c < np.minimum(sa, sb)
    if fam == "ha":
        hc = (o + h + l + c) / 4
        ho = E.ema(np.r_[(o[0] + c[0]) / 2, hc[:-1]], 3)  # apertura HA = (apertura HA + chiusura HA) / 2 di prima
        green = hc > ho
        red = (~green).astype(float)
        prev_red = E.shift(E.rolling_min(red, p[0])) > 0
        return green & prev_red, None, ~green
    if fam == "xsmom":
        L, K, K2 = p
        r = ctx.xrank(tf, L)
        if r is None:
            return None
        return (r <= K) & (E.shift(r) > K), None, r > K * K2
    if fam == "nearhigh":                            # vicinanza al massimo dell'anno (Jia et al.)
        d, x = p
        r = c / E.rolling_max(h, d * bpd)
        return (r > x) & ~(E.shift(r) > x), None, None
    if fam == "dayrun":                              # giornata anomala: si segue la spinta fino a fine giorno
        k, hmax = p
        day = I.t // D1
        first = np.r_[0, np.flatnonzero(day[1:] != day[:-1]) + 1]
        dopen = o[first][np.searchsorted(first, np.arange(I.n), side="right") - 1]
        datr = ctx.daily_atr_prev(tf)
        hr = (I.hour() + 1) % 24
        sig = (c - dopen > k * datr) & (hr <= hmax) & (hr > 0)
        return sig & ~E.shift(sig.astype(float)).astype(bool), None, hr == 0
    if fam == "fund":                                # tasso di finanziamento basso o negativo: troppi al ribasso
        thr, n = p
        f = ctx.funding(tf, n)
        if f is None:
            return None
        return f < thr, None, None
    if fam == "cci":
        n, v, m = p
        x = I.cci(n)
        return (cross_up(x, float(v)) if m > 0 else cross_up(x, -float(v))), None, None
    if fam == "aroon":
        n, t = p
        up, dn = I.aroon(n)
        return cross_up(up, float(t)) & (dn < 30), None, None
    if fam == "obv":
        o_ = I.obv()
        return (o_ > E.shift(E.rolling_max(o_, p[0]))) & (c > o), None, None
    if fam == "mfi":
        n, v = p
        x = I.mfi(n)
        return ((x < v) if v < 50 else cross_up(x, float(v))), None, None
    if fam == "cmf":
        n, t = p
        return cross_up(I.cmf(n), float(t)), None, None
    if fam == "kama":
        k = I.kama(p[0])
        return cross_up(c, k), None, c < k
    if fam == "hma":
        hm = I.hma(p[0])
        rising = hm > E.shift(hm)
        return rising & ~(E.shift(rising.astype(float)) > 0), None, ~rising
    if fam == "trix":
        t = I.trix(p[0])
        return cross_up(t, 0.0), None, t < 0
    if fam == "psar":
        d = I.psar(p[0])
        return (d > 0) & (E.shift(d) < 0), None, d < 0
    if fam == "linreg":
        n, k = p
        return cross_up(I.slope(n), float(k)), None, None
    if fam == "er":
        n, t = p
        return cross_up(I.er(n), float(t)) & (c > E.shift(c, n)), None, None
    if fam == "vwap":
        w = I.vwap(p[0])
        return cross_up(c, w), None, c < w
    if fam == "vcp":
        k, n = p
        tight = (I.atr(5) < k * I.atr(50)).astype(float)
        recent = E.shift(E.rolling_max(tight, 10)) > 0
        return recent & (c > I.hh(n)), None, None
    if fam == "rsidiv":
        n = p[0]
        r = I.rsi(14)
        newlow = c <= E.shift(E.rolling_min(c, n))
        return newlow & (r > E.shift(E.rolling_min(r, n)) + 5), None, None
    if fam == "elder":
        e = I.ema(13)
        m, sg = I.macd(12, 26, 9)
        hist = m - sg
        green = (e > E.shift(e)) & (hist > E.shift(hist))
        return green & ~(E.shift(green.astype(float)) > 0), None, ~green
    if fam == "ma3stack":
        f, m_, s_ = p
        st = (I.ema(f) > I.ema(m_)) & (I.ema(m_) > I.ema(s_))
        return st & ~(E.shift(st.astype(float)) > 0), None, ~st
    if fam == "rand":
        rs = np.random.default_rng(zlib.crc32(f"{ctx.coin}{tf}{p[0]}".encode()))
        return rs.random(I.n) < p[0] / BPD[tf] * 6, None, None
    raise KeyError(fam)


def build(ctx, s):
    """Tutto quello che serve alla simulazione per la tecnica s su questa moneta, o None."""
    tf = s["tf"]
    I = ctx.ind(tf)
    if I is None or I.n < WARM + 10:
        return None
    fk = ("fam", s["fam"], tuple(s["p"]))
    res = I.get(fk, lambda: family(I, ctx, s["fam"], s["p"]))
    if res is None:
        return None
    ent, lvl, own_exit = res
    ent = ent.copy()
    if s.get("fam2"):                                # 4ª ondata: CONFLUENZA di due segnali
        if tf not in FAM[s["fam2"]][0]:
            return None
        res2 = I.get(("fam", s["fam2"], tuple(s["p2"])), lambda: family(I, ctx, s["fam2"], s["p2"]))
        if res2 is None:
            return None
        e2 = np.asarray(res2[0], bool)
        w = int(s.get("win2") or 1)
        if w > 1:                                    # il secondo segnale nelle ultime w candele
            e2 = E.rolling_max(e2.astype(float), w) > 0
        ent &= e2
    c = I.c
    tr = s["trend"]
    if tr:
        if tr[0] == "ema":
            ent &= c > I.ema(tr[1])
        elif tr[0] == "stack":
            ent &= I.ema(50) > I.ema(200)
        elif tr[0] == "adx":
            ent &= I.adx(14)[0] > tr[1]
    if s["btc"]:
        ent &= ctx.btc_ok(tf, s["btc"])
    if s["vol"]:
        ent &= I.v > s["vol"] * I.vavg(30)
    if s["htf"]:
        ent &= ctx.htf_ok(tf, s["htf"])
    ent[:WARM] = False
    ent &= np.isfinite(c)
    st = s["stop"]
    atr = I.atr(14)
    if st[0] == "atr":
        sd = st[1] * atr
    elif st[0] == "swing":
        sd = np.maximum(c - I.llc(st[1]) + 0.1 * atr, 0.5 * atr)
    else:
        sd = st[1] * c
    sd = np.where(np.isfinite(sd), sd, 0.0)
    trail = s["trail"]
    if trail is None:
        tarr, ut = c, False
    elif trail[0] == "llc":
        tarr, ut = I.llc(trail[1]), True
    elif trail[0] == "chand":
        tarr, ut = I.hcc(trail[1]) - trail[2] * atr, True
    else:
        tarr, ut = I.ema(trail[1]), True
    tarr = np.where(np.isfinite(tarr), tarr, -1.0)
    xs = s["xs"]
    if xs is None:
        xa, ux = None, False
    elif xs == "fam":
        xa, ux = own_exit, own_exit is not None
    elif xs == "ema20":
        xa, ux = c < I.ema(20), True
    elif xs == "ema50":
        xa, ux = c < I.ema(50), True
    elif xs == "sma5up":
        xa, ux = c > I.sma(5), True
    elif xs == "rsi70":
        xa, ux = I.rsi(14) > 70, True
    else:
        xa, ux = c < I.ll(10), True
    if xa is None:
        xa = np.zeros(I.n, bool)
    lv = np.zeros(I.n) if lvl is None else np.where(np.isfinite(lvl), lvl, 0.0)
    return (I, ent, lv, sd, float(s["tp"]), tarr, ut, np.asarray(xa, bool), ux, int(s["hold"]), float(s["be"]))
