"""Broker: lo strato che esegue davvero gli ordini.

- PaperBroker  → DEMO: portafoglio simulato (soldi finti) su prezzi reali/live.
- LiveBroker   → SOLDI VERI: ordini reali su Kraken tramite ccxt e le tue chiavi.

Entrambi espongono la stessa interfaccia, così il motore non sa (e non gli
importa) se sta rischiando soldi finti o veri.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

FEE = 0.0026  # commissione taker Kraken (0,26%)


class PaperBroker:
    """DEMO — nessun soldo reale. Simula EUR + coin usando il prezzo del feed."""

    mode = "demo"

    def __init__(self, feed, start_eur: float = 20.0, symbol: str = "BTC/EUR"):
        self.feed = feed
        self.symbol = symbol
        self.eur = start_eur
        self.coin = 0.0
        self.start_eur = start_eur
        self.trade_log = []

    def price(self) -> float:
        return self.feed.price

    def balances(self) -> Dict[str, float]:
        return {"EUR": self.eur, "COIN": self.coin}

    def equity(self) -> float:
        return self.eur + self.coin * self.price()

    def market_buy(self, eur_amount: float) -> Dict[str, Any]:
        p = self.price()
        eur_amount = min(eur_amount, self.eur)
        if eur_amount <= 0 or p <= 0:
            return {"ok": False, "reason": "fondi insufficienti"}
        units = (eur_amount * (1 - FEE)) / p
        self.eur -= eur_amount
        self.coin += units
        rec = {"t": time.time(), "side": "BUY", "price": p, "eur": eur_amount, "units": units}
        self.trade_log.append(rec)
        return {"ok": True, **rec}

    def market_sell(self, units: float) -> Dict[str, Any]:
        p = self.price()
        units = min(units, self.coin)
        if units <= 0 or p <= 0:
            return {"ok": False, "reason": "niente da vendere"}
        eur = units * p * (1 - FEE)
        self.coin -= units
        self.eur += eur
        rec = {"t": time.time(), "side": "SELL", "price": p, "eur": eur, "units": units}
        self.trade_log.append(rec)
        return {"ok": True, **rec}

    def market_sell_all(self) -> Dict[str, Any]:
        return self.market_sell(self.coin)


class LiveBroker:
    """SOLDI VERI — ordini reali su Kraken. Richiede chiavi API valide.

    Sicurezza: usa chiavi SENZA permesso di prelievo. Questo broker non chiama
    mai funzioni di prelievo; può solo comprare/vendere sul mercato spot.
    """

    mode = "live"

    def __init__(self, api_key: str, api_secret: str, symbol: str = "BTC/EUR"):
        import ccxt  # type: ignore

        self.symbol = symbol
        self.base = symbol.split("/")[0]   # es. BTC
        self.quote = symbol.split("/")[1]  # es. EUR
        self.ex = ccxt.kraken({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
        })
        self.trade_log = []
        # verifica subito che le chiavi funzionino (solo lettura del saldo)
        self.ex.fetch_balance()

    def price(self) -> float:
        return float(self.ex.fetch_ticker(self.symbol)["last"])

    def balances(self) -> Dict[str, float]:
        bal = self.ex.fetch_balance()
        free = bal.get("free", {})
        return {"EUR": float(free.get(self.quote, 0.0)), "COIN": float(free.get(self.base, 0.0))}

    def equity(self) -> float:
        b = self.balances()
        return b["EUR"] + b["COIN"] * self.price()

    def market_buy(self, eur_amount: float) -> Dict[str, Any]:
        p = self.price()
        if eur_amount <= 0 or p <= 0:
            return {"ok": False, "reason": "importo non valido"}
        units = round((eur_amount / p) * (1 - FEE), 8)
        try:
            order = self.ex.create_order(self.symbol, "market", "buy", units)
            rec = {"t": time.time(), "side": "BUY", "price": p, "eur": eur_amount,
                   "units": units, "id": order.get("id")}
            self.trade_log.append(rec)
            return {"ok": True, **rec}
        except Exception as e:
            return {"ok": False, "reason": str(e)[:200]}

    def market_sell(self, units: float) -> Dict[str, Any]:
        b = self.balances()
        units = round(min(units, b["COIN"]), 8)
        if units <= 0:
            return {"ok": False, "reason": "niente da vendere"}
        try:
            p = self.price()
            order = self.ex.create_order(self.symbol, "market", "sell", units)
            rec = {"t": time.time(), "side": "SELL", "price": p, "eur": units * p,
                   "units": units, "id": order.get("id")}
            self.trade_log.append(rec)
            return {"ok": True, **rec}
        except Exception as e:
            return {"ok": False, "reason": str(e)[:200]}

    def market_sell_all(self) -> Dict[str, Any]:
        return self.market_sell(self.balances()["COIN"])
