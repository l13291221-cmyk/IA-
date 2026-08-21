"""Mercato paper: prova a caricare dati reali da Kraken (ccxt, solo lettura,
nessuna chiave), altrimenti genera una serie sintetica. Avanza una candela per
step() e non finisce mai (quando i dati reali si esauriscono continua sintetico).
"""
from __future__ import annotations

import random
from collections import deque
from typing import Deque, List, Optional


class Market:
    def __init__(
        self,
        symbol: str = "BTC/EUR",
        history: int = 500,
        seed: Optional[int] = None,
        use_real: bool = True,
        drift: float = 0.0,
        vol: float = 0.022,
        regime: str = "meanrev",   # "meanrev" (oscillante) o "gbm" (random walk realistico)
        theta: float = 0.06,       # forza di ritorno alla media (solo meanrev)
    ):
        self.symbol = symbol
        self.rng = random.Random(seed)
        self.drift = drift
        self.vol = vol
        self.regime = regime
        self.theta = theta
        self.closes: Deque[float] = deque(maxlen=history)
        self.real_queue: List[float] = []
        self.source = f"sintetico ({regime})"
        self._price = 30000.0 if "BTC" in symbol.upper() else 100.0
        self._anchor = self._price

        if use_real:
            self._try_load_real(symbol)

        if self.real_queue:
            self._price = self.real_queue[0]
            self._anchor = self._price
            warm = min(80, len(self.real_queue))
            for _ in range(warm):
                self.closes.append(self.real_queue.pop(0))
            self._price = self.closes[-1]
        else:
            # riscaldamento sintetico
            for _ in range(80):
                self._synthetic_step()

    def _try_load_real(self, symbol: str) -> None:
        try:
            import ccxt  # type: ignore

            ex = ccxt.kraken({"enableRateLimit": True})
            ohlcv = ex.fetch_ohlcv(symbol, timeframe="1m", limit=720)
            self.real_queue = [c[4] for c in ohlcv if c and c[4]]
            if self.real_queue:
                self.source = f"kraken:{symbol}"
        except Exception:
            # nessuna rete / ccxt non installato / simbolo assente → sintetico
            self.real_queue = []

    def _synthetic_step(self) -> None:
        if self.regime == "gbm":
            # random walk: realistico e difficile da battere sistematicamente
            shock = self.rng.gauss(self.drift, self.vol)
            self._price = max(0.01, self._price * (1.0 + shock))
        else:
            # mean-reverting: prezzo che oscilla attorno a un'ancora lenta
            # (crea opportunità "compra basso / vendi alto" da sfruttare)
            self._anchor = max(0.01, self._anchor * (1.0 + self.rng.gauss(self.drift, self.vol * 0.25)))
            pull = self.theta * (self._anchor - self._price) / self._price
            shock = self.rng.gauss(0.0, self.vol)
            self._price = max(0.01, self._price * (1.0 + pull + shock))
        self.closes.append(self._price)

    def step(self) -> float:
        if self.real_queue:
            self._price = self.real_queue.pop(0)
            self.closes.append(self._price)
            if not self.real_queue:
                self.source += " +sintetico"
        else:
            self._synthetic_step()
        return self._price

    @property
    def price(self) -> float:
        return self._price

    def series(self) -> List[float]:
        return list(self.closes)

    def summary(self) -> str:
        s = self.series()
        if len(s) < 5:
            return f"{self.symbol}: dati insufficienti"
        first, last = s[0], s[-1]
        change = (last - first) / first * 100 if first else 0
        hi, lo = max(s), min(s)
        return (
            f"{self.symbol} | prezzo {last:.2f} | variazione finestra {change:+.1f}% | "
            f"max {hi:.2f} min {lo:.2f} | {len(s)} candele"
        )
