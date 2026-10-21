"""MOTORE DELLA RICERCA DI MASSA: decine di migliaia di tecniche (solo acquisti) su tutte le
monete con storia, candele da 1h / 4h / 1g.

Regole uguali per tutte le tecniche:
  • si decide alla CHIUSURA della candela e si entra all'APERTURA della successiva (la
    rottura di volatilità entra al suo livello dentro la candela, se toccato);
  • stop / obiettivo controllati candela per candela; se nella stessa candela si toccano
    entrambi conta lo STOP; uno stop che sale usa solo candele già chiuse;
  • una operazione per volta per moneta; costi per lato (commissione + scivolamento);
  • universo: solo le N monete più scambiate in quel momento (volume medio dei 30 giorni prima).
Risultati in R (guadagno diviso il rischio iniziale), aggregati per mese e per periodo.
"""
from __future__ import annotations

import numpy as np
import numba as nb

TF_MS = {"1h": 3600_000, "4h": 4 * 3600_000, "1d": 86400_000}


# ------------------------------------------------------------------ candele
def resample(a, tf):
    """a = [t, o, h, l, c, qv] da 1h → timeframe tf (allineato a UTC)."""
    if tf == "1h":
        return a
    step = TF_MS[tf]
    b = (a[:, 0] // step).astype(np.int64)
    idx = np.flatnonzero(np.r_[True, b[1:] != b[:-1]])
    t = b[idx] * step
    o = a[idx, 1]
    h = np.maximum.reduceat(a[:, 2], idx)
    l = np.minimum.reduceat(a[:, 3], idx)
    c = a[np.r_[idx[1:] - 1, len(a) - 1], 4]
    v = np.add.reduceat(a[:, 5], idx)
    return np.column_stack([t, o, h, l, c, v])


# ------------------------------------------------------------------ indicatori (numba)
@nb.njit(cache=True)
def ema(x, n):
    out = np.empty_like(x)
    k = 2.0 / (n + 1)
    e = x[0]
    for i in range(len(x)):
        e = x[i] * k + e * (1 - k) if i else x[0]
        out[i] = e
    return out


@nb.njit(cache=True)
def rma(x, n):
    out = np.empty_like(x)
    a = x[0]
    for i in range(len(x)):
        a = x[i] if i == 0 else a + (x[i] - a) / n
        out[i] = a
    return out


@nb.njit(cache=True)
def _roll_ext(x, n, sign):
    """massimo (sign=1) o minimo (sign=-1) delle ultime n compresa questa, O(n) con coda monotona;
    NaN finché non ci sono n valori."""
    m = len(x)
    out = np.full(m, np.nan)
    q = np.empty(m, np.int64)
    head = 0
    tail = 0
    for i in range(m):
        v = x[i] * sign
        while tail > head and x[q[tail - 1]] * sign <= v:
            tail -= 1
        q[tail] = i
        tail += 1
        if q[head] <= i - n:
            head += 1
        if i >= n - 1:
            out[i] = x[q[head]]
    return out


def rolling_max(x, n):
    return _roll_ext(np.ascontiguousarray(x, dtype=np.float64), int(n), 1.0)


def rolling_min(x, n):
    return _roll_ext(np.ascontiguousarray(x, dtype=np.float64), int(n), -1.0)


def sma(x, n):
    c = np.cumsum(np.r_[0.0, x])
    out = np.full(len(x), np.nan)
    out[n - 1:] = (c[n:] - c[:-n]) / n
    return out


def rstd(x, n):
    m = sma(x, n)
    m2 = sma(x * x, n)
    return np.sqrt(np.maximum(m2 - m * m, 0))


def shift(x, k=1):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


class Ind:
    """Indicatori di una moneta su un timeframe, calcolati una volta e tenuti in memoria."""

    def __init__(self, a, tf):
        self.tf = tf
        self.t = a[:, 0].astype(np.int64)
        self.o, self.h, self.l, self.c, self.v = (np.ascontiguousarray(a[:, k]) for k in range(1, 6))
        self.n = len(a)
        self._m = {}

    def get(self, key, fn):
        if key not in self._m:
            self._m[key] = fn()
        return self._m[key]

    def ema(self, n):
        return self.get(("ema", n), lambda: ema(self.c, n))

    def sma(self, n):
        return self.get(("sma", n), lambda: sma(self.c, n))

    def tr(self):
        def f():
            pc = shift(self.c)
            pc[0] = self.c[0]
            return np.maximum(self.h - self.l, np.maximum(np.abs(self.h - pc), np.abs(self.l - pc)))
        return self.get("tr", f)

    def atr(self, n=14):
        return self.get(("atr", n), lambda: rma(self.tr(), n))

    def hh(self, n):                        # massimo delle n candele PRIMA
        return self.get(("hh", n), lambda: shift(rolling_max(self.h, n)))

    def ll(self, n):                        # minimo delle n candele PRIMA
        return self.get(("ll", n), lambda: shift(rolling_min(self.l, n)))

    def llc(self, n):                       # minimo delle ultime n compresa questa (stop che sale)
        return self.get(("llc", n), lambda: rolling_min(self.l, n))

    def hcc(self, n):                       # massima chiusura delle ultime n (chandelier)
        return self.get(("hcc", n), lambda: rolling_max(self.c, n))

    def roc(self, n):
        return self.get(("roc", n), lambda: self.c / shift(self.c, n) - 1)

    def rsi(self, n):
        def f():
            d = np.diff(self.c, prepend=self.c[0])
            up = rma(np.clip(d, 0, None), n)
            dn = rma(np.clip(-d, 0, None), n)
            with np.errstate(divide="ignore", invalid="ignore"):
                r = 100 - 100 / (1 + up / dn)
            return np.where(dn == 0, 100.0, r)
        return self.get(("rsi", n), f)

    def bb(self, n, k):
        def f():
            m, s = self.sma(n), rstd(self.c, n)
            return m + k * s, m - k * s, (2 * k * s) / m
        return self.get(("bb", n, k), f)

    def z(self, n):
        return self.get(("z", n), lambda: (self.c - self.sma(n)) / rstd(self.c, n))

    def vavg(self, n):
        return self.get(("vavg", n), lambda: shift(sma(self.v, n)))

    def adx(self, n=14):
        def f():
            up = np.r_[0, np.diff(self.h)]
            dn = np.r_[0, -np.diff(self.l)]
            pdm = np.where((up > dn) & (up > 0), up, 0.0)
            ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
            a = rma(self.tr(), n)
            with np.errstate(divide="ignore", invalid="ignore"):
                pdi = 100 * rma(pdm, n) / a
                ndi = 100 * rma(ndm, n) / a
                dx = 100 * np.abs(pdi - ndi) / (pdi + ndi)
            return rma(np.nan_to_num(dx), n), pdi, ndi
        return self.get(("adx", n), f)

    def macd(self, f_, s_, sig):
        def f():
            m = ema(self.c, f_) - ema(self.c, s_)
            return m, ema(m, sig)
        return self.get(("macd", f_, s_, sig), f)

    def stoch(self, n):
        def f():
            hi, lo = rolling_max(self.h, n), rolling_min(self.l, n)
            with np.errstate(divide="ignore", invalid="ignore"):
                return 100 * (self.c - lo) / (hi - lo)
        return self.get(("stoch", n), f)

    def supertrend(self, n, m):
        return self.get(("st", n, m), lambda: _supertrend(self.h, self.l, self.c, self.atr(n), m))

    def hour(self):
        return self.get("hour", lambda: (self.t // 3600_000) % 24)

    def dow(self):                          # 0 = lunedì
        return self.get("dow", lambda: ((self.t // 86400_000) + 3) % 7)

    def ibs(self):
        def f():
            with np.errstate(divide="ignore", invalid="ignore"):
                return (self.c - self.l) / (self.h - self.l)
        return self.get("ibs", f)

    def streak(self):
        return self.get("streak", lambda: _streak(self.c))

    # ---- indicatori aggiunti per la 3ª ondata ----
    def tp(self):
        return self.get("tp", lambda: (self.h + self.l + self.c) / 3)

    def cci(self, n):
        def f():
            tp = self.tp()
            m = sma(tp, n)
            md = _roll_mad(tp, m, n)
            with np.errstate(divide="ignore", invalid="ignore"):
                return (tp - m) / (0.015 * md)
        return self.get(("cci", n), f)

    def aroon(self, n):
        return self.get(("aroon", n), lambda: _aroon(self.h, self.l, n))

    def obv(self):
        return self.get("obv", lambda: np.cumsum(np.sign(np.diff(self.c, prepend=self.c[0])) * self.v))

    def mfi(self, n):
        def f():
            tp = self.tp()
            raw = tp * self.v
            d = np.diff(tp, prepend=tp[0])
            pos = sma(np.where(d > 0, raw, 0.0), n)
            neg = sma(np.where(d < 0, raw, 0.0), n)
            with np.errstate(divide="ignore", invalid="ignore"):
                return np.where(neg == 0, 100.0, 100 - 100 / (1 + pos / neg))
        return self.get(("mfi", n), f)

    def cmf(self, n):
        def f():
            rng = self.h - self.l
            with np.errstate(divide="ignore", invalid="ignore"):
                mfm = np.where(rng > 0, ((self.c - self.l) - (self.h - self.c)) / rng, 0.0)
                return sma(mfm * self.v, n) / sma(self.v, n)
        return self.get(("cmf", n), f)

    def kama(self, n):
        return self.get(("kama", n), lambda: _kama(self.c, n, 2, 30))

    def hma(self, n):
        def f():
            h = max(2, n // 2)
            raw = 2 * _wma(self.c, h) - _wma(self.c, n)
            return _wma(np.nan_to_num(raw, nan=self.c[0]), max(2, int(round(n ** 0.5))))
        return self.get(("hma", n), f)

    def trix(self, n):
        def f():
            t = ema(ema(ema(self.c, n), n), n)
            return (t / shift(t) - 1) * 100
        return self.get(("trix", n), f)

    def psar(self, step):
        return self.get(("psar", step), lambda: _psar(self.h, self.l, step, 0.2))

    def slope(self, n):
        def f():
            x = np.arange(n, dtype=float)
            xm = x.mean()
            w = (x - xm) / ((x - xm) ** 2).sum()          # pendenza dei minimi quadrati sulle n ultime
            out = np.full(self.n, np.nan)
            if self.n >= n:
                out[n - 1:] = np.convolve(self.c, w[::-1], mode="valid")
            return out / self.atr(14)
        return self.get(("slope", n), f)

    def er(self, n):
        def f():
            ch = np.abs(self.c - shift(self.c, n))
            vol = sma(np.abs(np.diff(self.c, prepend=self.c[0])), n) * n
            with np.errstate(divide="ignore", invalid="ignore"):
                return ch / vol
        return self.get(("er", n), f)

    def vwap(self, n):
        def f():
            with np.errstate(divide="ignore", invalid="ignore"):
                return sma(self.c * self.v, n) / sma(self.v, n)
        return self.get(("vwap", n), f)


@nb.njit(cache=True)
def _supertrend(h, l, c, a, m):
    n = len(c)
    d = np.ones(n)
    fu = np.empty(n)
    fl = np.empty(n)
    for i in range(n):
        mid = (h[i] + l[i]) / 2
        ub, lb = mid + m * a[i], mid - m * a[i]
        if i == 0:
            fu[i], fl[i] = ub, lb
            continue
        fu[i] = ub if (ub < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
        fl[i] = lb if (lb > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
        d[i] = 1.0 if c[i] > fu[i - 1] else (-1.0 if c[i] < fl[i - 1] else d[i - 1])
    return d


@nb.njit(cache=True)
def _streak(c):
    out = np.zeros(len(c))
    for i in range(1, len(c)):
        if c[i] > c[i - 1]:
            out[i] = out[i - 1] + 1 if out[i - 1] > 0 else 1
        elif c[i] < c[i - 1]:
            out[i] = out[i - 1] - 1 if out[i - 1] < 0 else -1
    return out


# ------------------------------------------------------------------ simulazione (numba)
@nb.njit(cache=True)
def simulate(o, h, l, c, ent, entry_lvl, stop_dist, tp_mult, trail, use_trail, exit_sig, use_exit, hold, fee, be):
    """ent[i]: segnale alla chiusura di i (o dentro la candela i+1 se entry_lvl[i] > 0).
    stop_dist[i]: distanza dello stop iniziale in prezzo. tp_mult: obiettivo in multipli dello
    stop (<= 0 = nessuno). trail[k]: livello dello stop che sale noto alla chiusura di k.
    exit_sig[k]: uscita all'apertura dopo k. be > 0: lo stop va all'entrata quando una candela
    chiusa ha toccato +be R. Ritorna (indice entrata, indice uscita, R, resa)."""
    n = len(c)
    out_i = np.empty(n, np.int64)
    out_k = np.empty(n, np.int64)
    out_r = np.empty(n)
    out_ret = np.empty(n)
    m = 0
    i = 0
    while i < n - 1:
        if not ent[i] or not (stop_dist[i] > 0):
            i += 1
            continue
        j = i + 1
        if entry_lvl[i] > 0:                       # entra quando il prezzo tocca il livello
            if h[j] < entry_lvl[i]:
                i += 1
                continue
            e = max(entry_lvl[i], o[j])
        else:
            e = o[j]
        stop = e - stop_dist[i]
        if stop <= 0:
            i += 1
            continue
        risk = e - stop
        tgt = e + tp_mult * risk if tp_mult > 0 else 1e300
        px = -1.0
        k = j
        last = min(j + hold, n) - 1
        while True:
            if k > j and use_trail and trail[k - 1] > stop:
                stop = trail[k - 1]
            if k > j and be > 0 and stop < e and h[k - 1] >= e + be * risk:
                stop = e
            lo = l[k]
            if k == j and entry_lvl[i] > 0:
                lo = min(l[k], e)                   # dopo l'entrata dentro la candela: stop prudente
            if lo <= stop:
                px = min(stop, o[k]) if k > j else stop
                break
            if h[k] >= tgt:
                px = max(tgt, o[k]) if k > j else tgt
                break
            if use_exit and exit_sig[k] and k + 1 < n:
                k += 1
                px = o[k]
                break
            if k >= last:
                px = c[k]
                break
            k += 1
        net = px * (1 - fee) - e * (1 + fee)
        out_i[m] = j
        out_k[m] = k
        out_r[m] = net / risk
        out_ret[m] = net / e
        m += 1
        i = k                                       # il prossimo segnale può nascere alla chiusura dell'uscita
    return out_i[:m], out_k[:m], out_r[:m], out_ret[:m]


@nb.njit(cache=True)
def accumulate(acc, b, m, r, ret, rlo, rhi):
    """acc[bucket, mese, statistica] += operazioni: n, R tagliato, R tagliato², vinte, R vero, resa."""
    for q in range(len(r)):
        if b[q] < 0 or m[q] < 0 or m[q] >= acc.shape[1]:
            continue
        rc = min(max(r[q], rlo), rhi)
        a = acc[b[q], m[q]]
        a[0] += 1
        a[1] += rc
        a[2] += rc * rc
        a[3] += 1.0 if r[q] > 0 else 0.0
        a[4] += r[q]
        a[5] += ret[q]


@nb.njit(cache=True)
def _roll_mad(x, m, n):
    out = np.full(len(x), np.nan)
    for i in range(n - 1, len(x)):
        s = 0.0
        for j in range(i - n + 1, i + 1):
            s += abs(x[j] - m[i])
        out[i] = s / n
    return out


@nb.njit(cache=True)
def _aroon(h, l, n):
    """Aroon su (alto, basso): 100 × (n − candele dal massimo/minimo delle ultime n+1) / n."""
    up = np.full(len(h), np.nan)
    dn = np.full(len(h), np.nan)
    for i in range(n, len(h)):
        bh = i
        bl = i
        for j in range(i - n, i + 1):
            if h[j] >= h[bh]:
                bh = j
            if l[j] <= l[bl]:
                bl = j
        up[i] = 100.0 * (n - (i - bh)) / n
        dn[i] = 100.0 * (n - (i - bl)) / n
    return up, dn


@nb.njit(cache=True)
def _kama(c, n, fast, slow):
    out = np.copy(c)
    fs = 2.0 / (fast + 1)
    ss = 2.0 / (slow + 1)
    for i in range(1, len(c)):
        if i < n:
            out[i] = c[i]
            continue
        ch = abs(c[i] - c[i - n])
        vol = 0.0
        for j in range(i - n + 1, i + 1):
            vol += abs(c[j] - c[j - 1])
        er = ch / vol if vol > 0 else 0.0
        sc = (er * (fs - ss) + ss) ** 2
        out[i] = out[i - 1] + sc * (c[i] - out[i - 1])
    return out


@nb.njit(cache=True)
def _wma(x, n):
    out = np.full(len(x), np.nan)
    den = n * (n + 1) / 2.0
    for i in range(n - 1, len(x)):
        s = 0.0
        for k in range(n):
            s += x[i - n + 1 + k] * (k + 1)
        out[i] = s / den
    return out


@nb.njit(cache=True)
def _psar(h, l, step, mx):
    """Parabolic SAR: direzione +1 (sotto il prezzo, rialzo) / −1."""
    n = len(h)
    d = np.ones(n)
    if n < 3:
        return d
    up = True
    sar = l[0]
    ep = h[0]
    af = step
    for i in range(1, n):
        sar = sar + af * (ep - sar)
        if up:
            sar = min(sar, l[i - 1], l[i - 2] if i > 1 else l[i - 1])
            if l[i] < sar:
                up = False
                sar = ep
                ep = l[i]
                af = step
            elif h[i] > ep:
                ep = h[i]
                af = min(af + step, mx)
        else:
            sar = max(sar, h[i - 1], h[i - 2] if i > 1 else h[i - 1])
            if h[i] > sar:
                up = True
                sar = ep
                ep = h[i]
                af = step
            elif l[i] < ep:
                ep = l[i]
                af = min(af + step, mx)
        d[i] = 1.0 if up else -1.0
    return d
