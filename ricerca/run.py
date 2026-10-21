"""Prova di massa: ogni tecnica del catalogo su ogni moneta, risultati per mese e per gruppo di
classifica (la moneta era tra le prime 3 / 5 / 10 / 20 / 40 più scambiate quando è nato il segnale).

uso: python run.py SPECS.json OUT_DIR [costo per lato]
In OUT_DIR: acc_<pezzo>.npy  forma [tecniche, 6 gruppi, mesi, 6 statistiche]
            statistiche: operazioni, R tagliato [-3, 10], R tagliato², vinte, R vero, resa %
"""
from __future__ import annotations

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

import catalog as C
import engine as E

D1 = 86400_000
OLD_ERA = os.environ.get("ERA") == "old"     # storia vecchia: BTC Bitstamp dal 2011, ETH/LTC Coinbase dal 2016
NB, NS = 6, 6                               # gruppi di classifica, statistiche
NM = 184 if OLD_ERA else 112                # mesi da 2011-09 oppure da 2017-08
EDGES = np.array([3, 5, 10, 20, 40, 998])
M0 = (2011 - 1970) * 12 + 8 if OLD_ERA else (2017 - 1970) * 12 + 7
FEE = 0.0015
H1 = "oldset" if OLD_ERA else "h1"
PREP = "prep_old.npz" if OLD_ERA else "prep.npz"
SUMMARY = os.environ.get("SUMMARY") == "1"      # salva solo il riassunto (per centinaia di migliaia di tecniche)
P = None
BTC = None
FUND = {}


def month_of(t):
    return t.astype("datetime64[ms]").astype("datetime64[M]").astype(np.int64) - M0


class Ctx:
    def __init__(self, coin, ci, a):
        self.coin, self.ci, self.a = coin, ci, a
        self._I, self._x = {}, {}

    def ind(self, tf):
        if tf not in self._I:
            arr = E.resample(self.a, tf)
            self._I[tf] = E.Ind(arr, tf) if len(arr) > C.WARM + 10 else None
        return self._I[tf]

    def drop(self, tf):
        self._I.pop(tf, None)
        for k in [k for k in self._x if k[0] == tf]:
            del self._x[k]

    def mem(self, k, fn):
        if k not in self._x:
            self._x[k] = fn()
        return self._x[k]

    def day(self, tf):                       # ultimo giorno completo alla chiusura di ogni candela
        return self.mem((tf, "day"), lambda: (self.ind(tf).t + E.TF_MS[tf]) // D1 - 1 - P["day0"])

    def _per_day(self, tf, tab, fill):
        d = self.day(tf)
        out = np.full(len(d), fill, dtype=tab.dtype)
        ok = (d >= 0) & (d < len(tab))
        out[ok] = tab[d[ok]]
        return out

    def btc_ok(self, tf, D):
        return self.mem((tf, "btc", D), lambda: self._per_day(tf, P[f"btc{D}"], False))

    def rank(self, tf):
        return self.mem((tf, "rank"), lambda: self._per_day(tf, P["rank"][self.ci], np.int16(999)))

    def xrank(self, tf, L):
        if tf != "1d":
            return None
        return self.mem((tf, "xr", L), lambda: self._per_day(tf, P[f"xr{L}"][self.ci], np.int16(99)).astype(float))

    def htf_ok(self, tf, D):
        def f():
            Id = self.ind("1d")
            if Id is None:
                return np.zeros(self.ind(tf).n, bool)
            reg = (Id.c > Id.ema(D)) & (np.arange(Id.n) >= D)
            dd = (Id.t // D1).astype(np.int64)
            want = self.day(tf) + P["day0"]
            pos = np.searchsorted(dd, want)
            ok = (pos < len(dd)) & (dd[np.minimum(pos, len(dd) - 1)] == want)
            out = np.zeros(len(want), bool)
            out[ok] = reg[pos[ok]]
            return out
        return self.mem((tf, "htf", D), f)

    def btc_series(self, tf):
        def f():
            bI = BTC.get(tf)
            I = self.ind(tf)
            pos = np.searchsorted(bI.t, I.t)
            ok = (pos < bI.n) & (bI.t[np.minimum(pos, bI.n - 1)] == I.t)
            c = np.full(I.n, np.nan)
            a = np.full(I.n, np.nan)
            c[ok] = bI.c[pos[ok]]
            a[ok] = bI.atr(14)[pos[ok]]
            return c, a
        return self.mem((tf, "btcs"), f)

    def daily_atr_prev(self, tf):
        def f():
            Id = self.ind("1d")
            out = np.full(self.ind(tf).n, np.nan)
            if Id is None:
                return out
            dd = (Id.t // D1).astype(np.int64)
            want = (self.ind(tf).t // D1).astype(np.int64) - 1
            pos = np.searchsorted(dd, want)
            ok = (pos < len(dd)) & (dd[np.minimum(pos, len(dd) - 1)] == want)
            out[ok] = Id.atr(14)[pos[ok]]
            return out
        return self.mem((tf, "datr"), f)

    def funding(self, tf, n):
        if self.coin not in FUND:
            return None
        def f():
            fr = FUND[self.coin]
            m = E.sma(fr[:, 1], n) if n > 1 else fr[:, 1]
            tclose = self.ind(tf).t + E.TF_MS[tf]
            pos = np.searchsorted(fr[:, 0], tclose, side="right") - 1   # ultimo tasso già pagato
            out = np.full(len(tclose), np.nan)
            ok = (pos >= 0) & (tclose - fr[np.maximum(pos, 0), 0] < 3 * 8 * 3600_000)
            out[ok] = m[pos[ok]]
            return out
        return self.mem((tf, "fund", n), f)

    def month(self, tf):
        return self.mem((tf, "month"), lambda: month_of(self.ind(tf).t))


class _BtcInd(dict):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def get(self, tf):
        if tf not in self:
            self[tf] = E.Ind(E.resample(self.a, tf), tf)
        return self[tf]


def init():
    global P, BTC
    import glob
    for p in ([] if OLD_ERA else glob.glob("fund/*.npy")):
        name = os.path.basename(p)[:-4]
        name = name[4:] if name.startswith("1000") else name
        a = np.load(p)
        if len(a) > 30:
            FUND[name] = a[np.argsort(a[:, 0])]
    z = np.load(PREP)
    P = {k: z[k] for k in z.files}
    P["day0"] = int(P["day0"])
    BTC = _BtcInd(np.load(f"{H1}/BTC.npy"))


def run_coins(args):
    specs, coins, fee = args
    acc = np.zeros((len(specs), NB, NM, NS))
    names = list(P["coins"])
    order = sorted(range(len(specs)), key=lambda i: ("1h", "4h", "1d").index(specs[i]["tf"]))
    for coin in coins:
        a = np.load(f"{H1}/{coin}.npy")
        import prep
        a = prep.clean(a)
        ctx = Ctx(coin, names.index(coin), a)
        last_tf = None
        for si in order:
            s = specs[si]
            if s["tf"] != last_tf:
                if last_tf:
                    ctx.drop(last_tf)
                last_tf = s["tf"]
            b = C.build(ctx, s)
            if b is None:
                continue
            I, ent, lv, sd, tp, tarr, ut, xa, ux, hold, be = b
            ei, ek, r, ret = E.simulate(I.o, I.h, I.l, I.c, ent, lv, sd, tp, tarr, ut, xa, ux, hold, fee, be)
            if len(r) == 0:
                continue
            rk = ctx.rank(s["tf"])[ei - 1]
            bk = np.searchsorted(EDGES, rk).astype(np.int64)
            bk[rk >= 999] = -1
            E.accumulate(acc[si], bk, ctx.month(s["tf"])[ei], r, ret, -3.0, 10.0)
        del ctx
    return acc


def groups(n):
    """Monete divise in n gruppi di peso simile (numero di candele)."""
    names = list(P["coins"])
    sizes = [(os.path.getsize(f"{H1}/{c}.npy"), c) for c in names]
    sizes.sort(reverse=True)
    g = [[] for _ in range(n)]
    w = [0] * n
    for sz, c in sizes:
        k = int(np.argmin(w))
        g[k].append(c)
        w[k] += sz
    return g


def main():
    specs = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    fee = float(sys.argv[3]) if len(sys.argv) > 3 else FEE
    chunk = int(os.environ.get("CHUNK", "2500"))
    os.makedirs(out, exist_ok=True)
    init()
    gs = groups(8)
    with Pool(4, initializer=init) as pool:
        for c0 in range(0, len(specs), chunk):
            path = f"{out}/{'sum' if SUMMARY else 'acc'}_{c0 // chunk:04d}.npy"
            if os.path.exists(path):
                continue
            t0 = time.time()
            part = specs[c0:c0 + chunk]
            tot = None
            for acc in pool.imap_unordered(run_coins, [(part, g, fee) for g in gs]):
                tot = acc if tot is None else tot + acc
            if SUMMARY:
                import stats
                np.save(path, stats.summarize(tot))
            else:
                np.save(path, tot.astype(np.float32))
            print(f"pezzo {c0 // chunk}: {len(part)} tecniche in {time.time() - t0:.0f}s", flush=True)
    print("fatto", flush=True)


if __name__ == "__main__":
    main()
