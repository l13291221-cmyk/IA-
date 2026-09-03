"""Feed dei prezzi reali in tempo reale — su PIÙ cripto insieme, da PIÙ FONTI.

È il BOT a scegliere su quale cripto operare, quindi qui teniamo d'occhio un
paniere di monete contemporaneamente. Per non ritrovarsi MAI su prezzi finti
quando basterebbe cambiare fornitore, i prezzi veri vengono cercati a CASCATA su
più fonti pubbliche (senza chiavi):

    1. Kraken     (via ccxt, se installato)
    2. Coinbase   (API pubblica)
    3. Binance    (endpoint dati pubblico)
    4. CoinGecko  (solo prezzo spot, ultima spiaggia)

Si usa la PRIMA fonte che risponde. Se una fonte è irraggiungibile (es. bloccata
dall'host), viene messa in "pausa" per un minuto e si prova la successiva, finché
non si trovano dati VERI. Solo se NESSUNA fonte risponde si passa a prezzi
"finti ma realistici", così la DEMO funziona comunque offline.

`is_real` dice se i prezzi sono veri; `source` dice DA DOVE arrivano.
In modalità soldi veri i prezzi DEVONO essere reali.
"""
from __future__ import annotations

import json as _json
import random
import threading
import time
import urllib.error as _urlerr
import urllib.request as _urlreq
from collections import deque
from typing import Dict, List, Optional, Tuple

# prezzi di partenza per il mercato sintetico (demo/offline)
_BASE_PRICES = {"BTC": 60000, "ETH": 3000, "SOL": 150, "XRP": 0.6, "ADA": 0.5,
                "DOGE": 0.15, "LTC": 80, "LINK": 15, "DOT": 6, "AVAX": 30}
_DEFAULT_BASES = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "LTC", "LINK"]

# nomi delle monete su CoinGecko (per l'ultima fonte, solo prezzo spot)
_CG_IDS = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple",
           "ADA": "cardano", "DOGE": "dogecoin", "LTC": "litecoin", "LINK": "chainlink",
           "DOT": "polkadot", "AVAX": "avalanche-2"}

_HTTP_TIMEOUT = 12.0
_UA = "AgentColony/1.0 (+price-feed)"
_TF_SECONDS = {"4h": 14400, "1h": 3600, "15m": 900}


def _http_json(url: str):
    req = _urlreq.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
    with _urlreq.urlopen(req, timeout=_HTTP_TIMEOUT) as r:
        return _json.loads(r.read().decode("utf-8", "replace"))


# ─────────────────────────── FONTI DEI PREZZI ───────────────────────────
# Ogni fonte espone:
#   ticker(base, quote) -> float | None          (prezzo attuale)
#   ohlcv(base, quote, tf, limit) -> list         (candele [ts,o,h,l,c,v], crescente)
# In caso di problemi sollevano un'eccezione (gestita da chi chiama).

class _KrakenCCXT:
    name = "kraken"

    def __init__(self, ex):
        self._ex = ex

    def ticker(self, base: str, quote: str) -> Optional[float]:
        t = self._ex.fetch_ticker(f"{base}/{quote}")
        last = t.get("last") if isinstance(t, dict) else None
        return float(last) if last else None

    def ohlcv(self, base: str, quote: str, tf: str, limit: int) -> list:
        rows = self._ex.fetch_ohlcv(f"{base}/{quote}", timeframe=tf, limit=limit)
        return [[float(x) for x in r] for r in rows] if rows else []


class _Coinbase:
    name = "coinbase"
    # Coinbase non ha il 4h: per il timeframe alto uso il 6h (21600s), va bene lo stesso
    # per il filtro di trend (EMA50/EMA200 su timeframe alto).
    _GRAN = {"15m": 900, "1h": 3600, "4h": 21600}

    def ticker(self, base: str, quote: str) -> Optional[float]:
        j = _http_json(f"https://api.coinbase.com/v2/prices/{base}-{quote}/spot")
        amt = (((j or {}).get("data") or {}).get("amount"))
        return float(amt) if amt else None

    def ohlcv(self, base: str, quote: str, tf: str, limit: int) -> list:
        g = self._GRAN.get(tf)
        if not g:
            return []
        url = f"https://api.exchange.coinbase.com/products/{base}-{quote}/candles?granularity={g}"
        rows = _http_json(url)   # [[time, low, high, open, close, volume], ...] (dal più recente)
        if not isinstance(rows, list):
            return []
        out = []
        for r in rows[:limit]:
            try:  # da [t,low,high,open,close,vol] a [ts_ms,open,high,low,close,vol]
                out.append([float(r[0]) * 1000.0, float(r[3]), float(r[2]),
                            float(r[1]), float(r[4]), float(r[5])])
            except (TypeError, ValueError, IndexError):
                continue
        out.reverse()   # in ordine cronologico crescente
        return out


class _Binance:
    name = "binance"
    # endpoint DATI pubblico (niente conto/trading) → di solito raggiungibile ovunque
    _HOST = "https://data-api.binance.vision"
    _INT = {"15m": "15m", "1h": "1h", "4h": "4h"}

    def _sym(self, base: str, quote: str) -> str:
        return f"{base}{quote}".upper()

    def ticker(self, base: str, quote: str) -> Optional[float]:
        j = _http_json(f"{self._HOST}/api/v3/ticker/price?symbol={self._sym(base, quote)}")
        p = (j or {}).get("price")
        return float(p) if p else None

    def ohlcv(self, base: str, quote: str, tf: str, limit: int) -> list:
        i = self._INT.get(tf)
        if not i:
            return []
        url = f"{self._HOST}/api/v3/klines?symbol={self._sym(base, quote)}&interval={i}&limit={limit}"
        rows = _http_json(url)   # [[openTime,o,h,l,c,v,...], ...] crescente
        if not isinstance(rows, list):
            return []
        out = []
        for r in rows:
            try:
                out.append([float(r[0]), float(r[1]), float(r[2]),
                            float(r[3]), float(r[4]), float(r[5])])
            except (TypeError, ValueError, IndexError):
                continue
        return out


class _CoinGecko:
    name = "coingecko"
    # Ultima spiaggia: SOLO prezzo spot (le sue candele non hanno il volume, che serve
    # alla tecnica). Almeno il prezzo è VERO → niente "simulato". Una chiamata sola per
    # tutte le monete, con cache di 15s per non superare i limiti gratuiti.

    def __init__(self):
        self._cache: Dict[str, Tuple[float, Dict[str, float]]] = {}

    def _all(self, quote: str) -> Dict[str, float]:
        q = quote.lower()
        ts, data = self._cache.get(q, (0.0, {}))
        if data and (time.time() - ts) < 15.0:
            return data
        ids = ",".join(sorted(set(_CG_IDS.values())))
        j = _http_json(f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={q}")
        data = {}
        if isinstance(j, dict):
            for cid, v in j.items():
                if isinstance(v, dict) and q in v:
                    try:
                        data[cid] = float(v[q])
                    except (TypeError, ValueError):
                        pass
        if data:
            self._cache[q] = (time.time(), data)
        return data

    def ticker(self, base: str, quote: str) -> Optional[float]:
        cid = _CG_IDS.get(base.upper())
        if not cid:
            return None
        return self._all(quote).get(cid)

    def ohlcv(self, base: str, quote: str, tf: str, limit: int) -> list:
        return []


class MultiFeed:
    """Tiene d'occhio PIÙ cripto insieme, con prezzi VERI cercati a cascata su più
    fonti pubbliche. Sintetico solo se nessuna fonte risponde (demo/offline).
    """

    def __init__(self, primary: str = "BTC/EUR", poll_seconds: float = 20.0, history: int = 300):
        base0 = primary.split("/")[0] if "/" in primary else "BTC"
        quote = primary.split("/")[1] if "/" in primary else "EUR"
        bases = [base0] + [b for b in _DEFAULT_BASES if b != base0]
        self.primary = f"{base0}/{quote}"
        self.symbols: List[str] = [f"{b}/{quote}" for b in bases]
        self.poll_seconds = poll_seconds
        self.is_real = False
        self.source = ""          # da quale fonte arrivano i prezzi ora ("" = sintetico)
        self.last_error = ""
        self._rng = random.Random()
        self._lock = threading.Lock()
        self._stop = False
        self._d: Dict[str, dict] = {s: {"price": 0.0, "series": deque(maxlen=history), "anchor": 0.0}
                                    for s in self.symbols}
        # candele multi-timeframe (per la tecnica Trend+Ritracciamento+Conferma). Solo dati reali.
        self._tf: Dict[str, Dict[str, list]] = {s: {"4h": [], "1h": [], "15m": []} for s in self.symbols}
        self._tf_lock = threading.Lock()
        self.ta_ready = False
        self._cooldown: Dict[str, float] = {}   # fonte -> istante fino al quale saltarla

        # costruisci l'elenco delle FONTI, in ordine di preferenza
        self._providers: list = []
        try:
            import ccxt  # type: ignore
            ex = ccxt.kraken({"enableRateLimit": True})
            try:
                ex.timeout = 8000   # non restare appeso se Kraken non risponde
            except Exception:
                pass
            self._providers.append(_KrakenCCXT(ex))
        except Exception as e:
            self.last_error = f"ccxt non disponibile: {e}"
        self._providers += [_Coinbase(), _Binance(), _CoinGecko()]

        self._prefetch(history)

    # --------------------------------------------------- util fonti (cascata)
    @staticmethod
    def _split(sym: str) -> Tuple[str, str]:
        if "/" in sym:
            a, b = sym.split("/", 1)
            return a, b
        return sym, "EUR"

    def _usable(self, p) -> bool:
        return time.time() >= self._cooldown.get(p.name, 0.0)

    def _penalize(self, p) -> None:
        self._cooldown[p.name] = time.time() + 60.0   # in pausa 1 min, poi si riprova

    def _ticker_any(self, base: str, quote: str) -> Tuple[Optional[float], str]:
        """Prezzo attuale dalla PRIMA fonte che risponde. (prezzo, nome_fonte) o (None, '')."""
        for p in self._providers:
            if not self._usable(p):
                continue
            try:
                v = p.ticker(base, quote)
                if v and v > 0:
                    return float(v), p.name
            except (_urlerr.URLError, _urlerr.HTTPError, TimeoutError, OSError, ValueError) as e:
                self.last_error = f"{p.name}: {str(e)[:80]}"
                self._penalize(p)
            except Exception as e:
                self.last_error = f"{p.name}: {str(e)[:80]}"
                self._penalize(p)
        return None, ""

    def _ohlcv_any(self, base: str, quote: str, tf: str, limit: int) -> Tuple[list, str]:
        """Candele dalla prima fonte che le fornisce. (candele, nome_fonte) o ([], '')."""
        for p in self._providers:
            if not self._usable(p):
                continue
            try:
                rows = p.ohlcv(base, quote, tf, limit)
                if rows:
                    return rows, p.name
            except (_urlerr.URLError, _urlerr.HTTPError, TimeoutError, OSError, ValueError) as e:
                self.last_error = f"{p.name} candele: {str(e)[:80]}"
                self._penalize(p)
            except Exception as e:
                self.last_error = f"{p.name} candele: {str(e)[:80]}"
                self._penalize(p)
        return [], ""

    # --- candele multi-timeframe (4H/1H/15M) per la tecnica di trading ---
    def _refresh_tf_once(self) -> None:
        limits = {"4h": 260, "1h": 120, "15m": 60}   # abbastanza per EMA200 su 4H, EMA20 su 1H, ecc.
        got_any = False
        for s in self.symbols:
            base, quote = self._split(s)
            for tf, lim in limits.items():
                rows, _name = self._ohlcv_any(base, quote, tf, lim)
                if rows:
                    with self._tf_lock:
                        self._tf[s][tf] = rows
                    got_any = True
        if got_any:
            self.ta_ready = True

    def _tf_loop(self) -> None:
        while not self._stop:
            self._refresh_tf_once()
            time.sleep(180.0)   # i timeframe alti cambiano lentamente: basta ogni 3 min

    def ohlcv(self, sym: str, tf: str) -> list:
        with self._tf_lock:
            return list(self._tf.get(sym, {}).get(tf, []))

    def _synth_base(self, sym: str) -> float:
        return float(_BASE_PRICES.get(sym.split("/")[0], 100.0))

    def _synth_tick(self, sym: str) -> float:
        d = self._d[sym]
        base = d["price"] or self._synth_base(sym)
        d["anchor"] = max(1e-9, (d["anchor"] or base) * (1 + self._rng.gauss(0.0, 0.004)))
        return max(1e-9, base * (1 + 0.06 * (d["anchor"] - base) / base + self._rng.gauss(0.0, 0.02)))

    def _set_price(self, sym: str, price: float) -> None:
        d = self._d[sym]
        with self._lock:
            d["price"] = price
            d["series"].append(round(price, 6))

    def _prefetch(self, history: int) -> None:
        real_any = False
        src = ""
        for s in self.symbols:
            d = self._d[s]
            base, quote = self._split(s)
            closes: List[float] = []
            rows, name = self._ohlcv_any(base, quote, "15m", min(history, 200))
            if rows:
                closes = [r[4] for r in rows if r[4]]
                src = src or name
            if not closes:   # niente candele da questa fonte: almeno il prezzo spot
                px, name = self._ticker_any(base, quote)
                if px:
                    closes = [px]
                    src = src or name
            if closes:
                for c in closes[-history:]:
                    d["series"].append(round(float(c), 6))
                d["price"] = d["series"][-1]
                d["anchor"] = d["price"]
                real_any = True
            else:            # offline totale: mercato sintetico
                p = anchor = self._synth_base(s)
                for _ in range(150):
                    anchor = max(1e-9, anchor * (1 + self._rng.gauss(0.0, 0.004)))
                    p = max(1e-9, p * (1 + 0.06 * (anchor - p) / p + self._rng.gauss(0.0, 0.02)))
                    d["series"].append(round(p, 6))
                d["price"] = p
                d["anchor"] = anchor
        self.is_real = real_any
        self.source = src if real_any else ""

    def _poll_once(self) -> None:
        real = 0
        src = ""
        for s in self.symbols:
            base, quote = self._split(s)
            px, name = self._ticker_any(base, quote)
            if px is None:
                px = self._synth_tick(s)   # questa moneta ora non ha fonti → sintetico per un giro
            else:
                real += 1
                if s == self.primary:
                    src = name
                elif not src:
                    src = name
            self._set_price(s, px)
        self.is_real = real > 0
        self.source = src if real > 0 else ""

    def run(self) -> None:
        while not self._stop:
            self._poll_once()
            time.sleep(max(3.0, self.poll_seconds))

    def start(self) -> None:
        threading.Thread(target=self.run, daemon=True).start()
        threading.Thread(target=self._tf_loop, daemon=True).start()   # candele 4H/1H/15M

    def stop(self) -> None:
        self._stop = True

    def price(self, sym: Optional[str] = None) -> float:
        with self._lock:
            return self._d.get(sym or self.primary, {}).get("price", 0.0)

    def series(self, sym: Optional[str] = None) -> List[float]:
        with self._lock:
            return list(self._d.get(sym or self.primary, {}).get("series", []))
