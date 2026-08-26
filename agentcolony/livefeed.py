"""Feed dei prezzi reali in tempo reale — su PIÙ cripto insieme.

È il BOT a scegliere su quale cripto operare, quindi qui teniamo d'occhio un
paniere di monete contemporaneamente. Prova a leggere i prezzi veri da Kraken
(ccxt, pubblico, senza chiavi). Se ccxt non c'è o manca la rete, genera prezzi
"finti ma realistici" così la DEMO funziona comunque offline. In modalità soldi
veri i prezzi DEVONO essere reali: `is_real` dice se lo sono.
"""
from __future__ import annotations

import random
import threading
import time
from collections import deque
from typing import Dict, List, Optional

# prezzi di partenza per il mercato sintetico (demo/offline)
_BASE_PRICES = {"BTC": 60000, "ETH": 3000, "SOL": 150, "XRP": 0.6, "ADA": 0.5,
                "DOGE": 0.15, "LTC": 80, "LINK": 15, "DOT": 6, "AVAX": 30}
_DEFAULT_BASES = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "LTC", "LINK"]


class MultiFeed:
    """Tiene d'occhio PIÙ cripto insieme: è il bot a scegliere su quale operare.
    Prezzi reali da Kraken (ccxt pubblico, senza chiavi) o sintetici in demo/offline.
    """

    def __init__(self, primary: str = "BTC/EUR", poll_seconds: float = 20.0, history: int = 300):
        base0 = primary.split("/")[0] if "/" in primary else "BTC"
        quote = primary.split("/")[1] if "/" in primary else "EUR"
        bases = [base0] + [b for b in _DEFAULT_BASES if b != base0]
        self.primary = f"{base0}/{quote}"
        self.symbols: List[str] = [f"{b}/{quote}" for b in bases]
        self.poll_seconds = poll_seconds
        self.is_real = False
        self.last_error = ""
        self._rng = random.Random()
        self._lock = threading.Lock()
        self._stop = False
        self._d: Dict[str, dict] = {s: {"price": 0.0, "series": deque(maxlen=history), "anchor": 0.0}
                                    for s in self.symbols}
        self._ex = None
        try:
            import ccxt  # type: ignore
            self._ex = ccxt.kraken({"enableRateLimit": True})
        except Exception as e:
            self.last_error = f"ccxt non disponibile: {e}"
        self._prefetch(history)

    def _synth_base(self, sym: str) -> float:
        return float(_BASE_PRICES.get(sym.split("/")[0], 100.0))

    def _prefetch(self, history: int) -> None:
        real_any = False
        for s in self.symbols:
            d = self._d[s]
            got = False
            if self._ex is not None:
                try:
                    for c in self._ex.fetch_ohlcv(s, timeframe="1m", limit=history):
                        if c and c[4]:
                            d["series"].append(round(float(c[4]), 6))
                    if d["series"]:
                        d["price"] = d["series"][-1]; d["anchor"] = d["price"]; got = True; real_any = True
                except Exception as e:
                    self.last_error = str(e)[:120]
            if not got:
                p = anchor = self._synth_base(s)
                for _ in range(150):
                    anchor = max(1e-9, anchor * (1 + self._rng.gauss(0.0, 0.004)))
                    p = max(1e-9, p * (1 + 0.06 * (anchor - p) / p + self._rng.gauss(0.0, 0.02)))
                    d["series"].append(round(p, 6))
                d["price"] = p; d["anchor"] = anchor
        self.is_real = real_any

    def _poll_once(self) -> None:
        real = 0
        for s in self.symbols:
            d = self._d[s]
            price = None
            if self._ex is not None:
                try:
                    price = float(self._ex.fetch_ticker(s)["last"]); real += 1
                except Exception as e:
                    self.last_error = str(e)[:120]
            if price is None:
                base = d["price"] or self._synth_base(s)
                d["anchor"] = max(1e-9, (d["anchor"] or base) * (1 + self._rng.gauss(0.0, 0.004)))
                price = max(1e-9, base * (1 + 0.06 * (d["anchor"] - base) / base + self._rng.gauss(0.0, 0.02)))
            with self._lock:
                d["price"] = price
                d["series"].append(round(price, 6))
        self.is_real = real > 0

    def run(self) -> None:
        while not self._stop:
            self._poll_once()
            time.sleep(max(3.0, self.poll_seconds))

    def start(self) -> None:
        threading.Thread(target=self.run, daemon=True).start()

    def stop(self) -> None:
        self._stop = True

    def price(self, sym: Optional[str] = None) -> float:
        with self._lock:
            return self._d.get(sym or self.primary, {}).get("price", 0.0)

    def series(self, sym: Optional[str] = None) -> List[float]:
        with self._lock:
            return list(self._d.get(sym or self.primary, {}).get("series", []))
