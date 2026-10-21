"""Tabelle comuni a tutte le tecniche, giorno per giorno (giorno = chiusura UTC):
  rank[moneta, giorno]   posizione per volume medio dei 30 giorni fino a quel giorno (999 = non valida)
  btc_reg[D][giorno]     Bitcoin (Bitstamp, dal 2011) chiude sopra la sua EMA di D giorni
  xr[L][moneta, giorno]  posizione per rendimento di L giorni tra le 20 più scambiate (99 = fuori)
  close[moneta, giorno]  chiusura giornaliera (per il conto finale)
"""
import glob
import os
import sys

import numpy as np

import engine as E

D1 = 86400_000
H1 = sys.argv[1] if len(sys.argv) > 1 else "h1"
OLD = "old"
DAY0 = 17348                                   # 2017-07-01
STABLE = {"USDC", "FDUSD", "TUSD", "USDP", "DAI", "BUSD", "PAXG"}


def clean(a):
    a = a[np.argsort(a[:, 0], kind="stable")]
    a = a[np.r_[True, np.diff(a[:, 0]) > 0]]
    ok = (a[:, 2] >= a[:, 3]) & (a[:, 4] > 0) & (a[:, 3] > 0) & np.isfinite(a).all(1)
    return a[ok]


def main():
    coins = sorted(os.path.basename(p)[:-4] for p in glob.glob(f"{H1}/*.npy"))
    coins = [c for c in coins if c not in STABLE]
    now_day = 0
    data = {}
    for c in coins:
        a = clean(np.load(f"{H1}/{c}.npy"))
        if len(a) < 24 * 60:
            continue
        data[c] = a
        now_day = max(now_day, int(a[-1, 0] // D1))
    coins = sorted(data)
    nd = now_day - DAY0 + 1
    vol = np.zeros((len(coins), nd))
    hrs = np.zeros((len(coins), nd))
    close = np.full((len(coins), nd), np.nan)
    for ci, c in enumerate(coins):
        a = data[c]
        d = (a[:, 0] // D1).astype(np.int64) - DAY0
        ok = d >= 0
        np.add.at(vol[ci], d[ok], a[ok, 5])
        np.add.at(hrs[ci], d[ok], 1)
        last = np.r_[d[1:] != d[:-1], True] & ok
        close[ci, d[last]] = a[last, 4]
    # volume medio di 30 giorni: valido solo se la moneta ha almeno 30 giorni e oggi ha ≥ 20 ore
    have = (hrs >= 20).astype(float)
    cs = np.cumsum(np.c_[np.zeros(len(coins)), vol], 1)
    ch = np.cumsum(np.c_[np.zeros(len(coins)), have], 1)
    v30 = np.full(vol.shape, np.nan)
    first = np.argmax(hrs > 0, 1)
    for d in range(29, nd):
        s = (cs[:, d + 1] - cs[:, d - 29]) / 30
        n = ch[:, d + 1] - ch[:, d - 29]
        ok = (n >= 25) & (have[:, d] > 0) & (d - first >= 29)
        v30[ok, d] = s[ok]
    rank = np.full(vol.shape, 999, np.int16)
    for d in range(nd):
        ok = np.flatnonzero(np.isfinite(v30[:, d]))
        if len(ok):
            order = ok[np.argsort(-v30[ok, d])]
            rank[order, d] = np.arange(1, len(order) + 1)
    # Bitcoin: Bitstamp dal 2011 (più lungo), chiusure giornaliere
    bs = clean(np.load(f"{OLD}/BTC_bitstamp.npy"))
    bd = (bs[:, 0] // D1).astype(np.int64)
    last = np.r_[bd[1:] != bd[:-1], True]
    bdays, bclose = bd[last], bs[last, 4]
    btc_reg = {}
    for D in (20, 50, 100, 200):
        e = E.ema(bclose, D)
        reg = (bclose > e) & (np.arange(len(bclose)) >= D)
        full = np.zeros(nd, bool)
        m = (bdays >= DAY0) & (bdays < DAY0 + nd)
        full[bdays[m] - DAY0] = reg[m]
        # giorni mancanti: copia l'ultimo valore noto
        known = np.zeros(nd, bool)
        known[bdays[m] - DAY0] = True
        idx = np.maximum.accumulate(np.where(known, np.arange(nd), 0))
        btc_reg[D] = full[idx]
    # momento trasversale: tra le 20 più scambiate, posizione per rendimento di L giorni
    cf = close.copy()
    for ci in range(len(coins)):                 # riempi i buchi in avanti
        idx = np.maximum.accumulate(np.where(np.isfinite(cf[ci]), np.arange(nd), 0))
        cf[ci] = cf[ci, idx]
    xr = {}
    for L in (7, 14, 30, 60):
        r = np.full(vol.shape, np.nan)
        r[:, L:] = cf[:, L:] / cf[:, :-L] - 1
        out = np.full(vol.shape, 99, np.int16)
        for d in range(L, nd):
            ok = np.flatnonzero((rank[:, d] <= 20) & np.isfinite(r[:, d]) & np.isfinite(close[:, d - L]))
            if len(ok):
                order = ok[np.argsort(-r[ok, d])]
                out[order, d] = np.arange(1, len(order) + 1)
        xr[L] = out
    np.savez_compressed("prep.npz", coins=np.array(coins), rank=rank, close=close, v30=v30,
                        **{f"btc{D}": btc_reg[D] for D in btc_reg}, **{f"xr{L}": xr[L] for L in xr},
                        day0=DAY0, nd=nd)
    print(len(coins), "monete,", nd, "giorni")
    for y in range(2017, 2027):
        d = (np.datetime64(f"{y}-12-31") - np.datetime64("1970-01-01")).astype(int) - DAY0
        d = min(d, nd - 2)
        top = [coins[i] for i in np.argsort(rank[:, d])[:10] if rank[i, d] < 999]
        print(y, "prime 10:", " ".join(top))


def main_old():
    """Storia vecchia: BTC (Bitstamp, dal 2011-09), ETH e LTC (Coinbase, dal 2016). Tutte «prime 3»."""
    os.makedirs("oldset", exist_ok=True)
    src = {"BTC": "old/BTC_bitstamp.npy", "ETH": "old/ETH_coinbase.npy", "LTC": "old/LTC_coinbase.npy"}
    day0 = 15218                                 # 2011-09-01
    data = {c: clean(np.load(f)) for c, f in src.items() if os.path.exists(f)}
    for c, a in data.items():
        np.save(f"oldset/{c}.npy", a)
    coins = sorted(data)
    nd = int(max(a[-1, 0] for a in data.values()) // D1) - day0 + 1
    rank = np.full((len(coins), nd), 999, np.int16)
    close = np.full((len(coins), nd), np.nan)
    for ci, c in enumerate(coins):
        a = data[c]
        d = (a[:, 0] // D1).astype(np.int64) - day0
        last = np.r_[d[1:] != d[:-1], True]
        close[ci, d[last]] = a[last, 4]
        first = d[0]
        rank[ci, first + 30:] = 1
    bclose_d = (data["BTC"][:, 0] // D1).astype(np.int64)
    last = np.r_[bclose_d[1:] != bclose_d[:-1], True]
    bdays, bclose = bclose_d[last], data["BTC"][last, 4]
    out = {}
    for D in (20, 50, 100, 200):
        e = E.ema(bclose, D)
        reg = (bclose > e) & (np.arange(len(bclose)) >= D)
        full = np.zeros(nd, bool)
        known = np.zeros(nd, bool)
        full[bdays - day0] = reg
        known[bdays - day0] = True
        idx = np.maximum.accumulate(np.where(known, np.arange(nd), 0))
        out[f"btc{D}"] = full[idx]
    for L in (7, 14, 30, 60):
        out[f"xr{L}"] = np.full((len(coins), nd), 99, np.int16)
    np.savez_compressed("prep_old.npz", coins=np.array(coins), rank=rank, close=close, day0=day0, nd=nd, **out)
    print("storia vecchia:", {c: (str(np.datetime64(int(a[0, 0]), "ms"))[:10], len(a)) for c, a in data.items()})


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "old":
        main_old()
    else:
        main()
