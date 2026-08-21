"""Feed del prezzo reale in tempo reale.

Prova a leggere il prezzo vero da Kraken (ccxt, pubblico, senza chiavi). Se ccxt
non c'è o non c'è rete, genera un prezzo "finto ma realistico" così la DEMO
funziona comunque offline. In modalità soldi veri il prezzo DEVE essere reale:
`is_real` dice se il prezzo corrente è autentico.
"""
from __future__ import annotations

import random
import threading
import time
from collections import deque
from typing import Deque, List, Optional


class LiveFeed:
    def __init__(self, symbol: str = "BTC/EUR", poll_seconds: float = 15.0, history: int = 300):
        self.symbol = symbol
        self.poll_seconds = poll_seconds
        self.prices: Deque[float] = deque(maxlen=history)
        self.times: Deque[float] = deque(maxlen=history)
        self._price = 0.0
        self.is_real = False
        self.last_error = ""
        self._rng = random.Random()
        self._lock = threading.Lock()
        self._stop = False
        self._ex = None
        self._init_exchange()
        self._prefetch_history()
        self._poll_once(initial=True)

    def _init_exchange(self) -> None:
        try:
            import ccxt  # type: ignore

            self._ex = ccxt.kraken({"enableRateLimit": True})
        except Exception as e:
            self._ex = None
            self.last_error = f"ccxt non disponibile: {e}"

    def _prefetch_history(self) -> None:
        """Riempi la serie con lo storico, così gli indicatori partono subito."""
        if self._ex is not None:
            try:
                ohlcv = self._ex.fetch_ohlcv(self.symbol, timeframe="1m", limit=self.prices.maxlen)
                for c in ohlcv:
                    if c and c[4]:
                        self.prices.append(round(float(c[4]), 2))
                        self.times.append(c[0] / 1000.0)
                if self.prices:
                    self._price = self.prices[-1]
                    self.is_real = True
                    return
            except Exception:
                pass
        # fallback: storia sintetica (solo DEMO / offline) così gli indicatori partono subito
        base = 30000.0 if "BTC" in self.symbol.upper() else 100.0
        p = base
        anchor = base
        now = time.time()
        n = 150
        for i in range(n):
            anchor *= (1.0 + self._rng.gauss(0.0, 0.004))
            p = max(0.01, p * (1.0 + 0.06 * (anchor - p) / p + self._rng.gauss(0.0, 0.015)))
            self.prices.append(round(p, 2))
            self.times.append(now - (n - i) * 60)
        self._price = p

    def _poll_once(self, initial: bool = False) -> None:
        price = None
        if self._ex is not None:
            try:
                t = self._ex.fetch_ticker(self.symbol)
                price = float(t["last"])
                self.is_real = True
                self.last_error = ""
            except Exception as e:
                self.is_real = False
                self.last_error = f"lettura prezzo fallita: {str(e)[:120]}"
        if price is None:
            # fallback sintetico (solo per DEMO / offline)
            base = self._price or (30000.0 if "BTC" in self.symbol.upper() else 100.0)
            price = max(0.01, base * (1.0 + self._rng.gauss(0.0, 0.004)))
            self.is_real = False
        with self._lock:
            self._price = price
            self.prices.append(round(price, 2))
            self.times.append(time.time())

    def run(self) -> None:
        while not self._stop:
            self._poll_once()
            time.sleep(max(2.0, self.poll_seconds))

    def start(self) -> None:
        threading.Thread(target=self.run, daemon=True).start()

    def stop(self) -> None:
        self._stop = True

    @property
    def price(self) -> float:
        with self._lock:
            return self._price

    def series(self) -> List[float]:
        with self._lock:
            return list(self.prices)
