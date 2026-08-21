"""Un agente = un bot che fa paper trading con un proprio genoma e un portafoglio
simulato (cash + coin). Decide COMPRA/VENDI/ATTENDI in base al genoma.
"""
from __future__ import annotations

import itertools
from typing import Any, Dict, List, Optional

from . import indicators as ind
from .genome import Genome

FEE = 0.0026  # commissione taker Kraken, applicata a ogni lato (simulata)

_id_counter = itertools.count(1)


class Agent:
    def __init__(
        self,
        genome: Genome,
        seed_capital: float,
        generation: int = 0,
        parent_id: Optional[int] = None,
    ):
        self.id = next(_id_counter)
        self.genome = genome
        self.generation = generation
        self.parent_id = parent_id
        self.seed = seed_capital
        self.cash = seed_capital
        self.coin = 0.0
        self.entry_price = 0.0
        self.alive = True
        self.trades = 0
        self.wins = 0
        self.children = 0
        self.born_tick = 0
        self.last_action = "ATTENDI"

    # --- portafoglio -----------------------------------------------------
    def equity(self, price: float) -> float:
        return self.cash + self.coin * price

    def in_position(self) -> bool:
        return self.coin > 0

    def _buy(self, price: float) -> None:
        spend = self.cash * self.genome.risk_fraction
        if spend < 1e-9 or self.cash <= 0:
            return
        units = (spend * (1 - FEE)) / price
        self.cash -= spend
        self.coin += units
        self.entry_price = price
        self.trades += 1
        self.last_action = "COMPRA"

    def _sell(self, price: float) -> None:
        if self.coin <= 0:
            return
        proceeds = self.coin * price * (1 - FEE)
        cost = self.coin * self.entry_price
        if proceeds > cost:
            self.wins += 1
        self.cash += proceeds
        self.coin = 0.0
        self.entry_price = 0.0
        self.trades += 1
        self.last_action = "VENDI"

    # --- decisione -------------------------------------------------------
    def decide(self, series: List[float], price: float) -> str:
        from . import strategy
        return strategy.decide(self.genome, series, price, self.in_position(), self.entry_price)

    def step(self, series: List[float], price: float) -> None:
        if not self.alive:
            return
        action = self.decide(series, price)
        if action == "COMPRA":
            self._buy(price)
        elif action == "VENDI":
            self._sell(price)
        else:
            self.last_action = "ATTENDI"

    def snapshot(self, price: float) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gen": self.generation,
            "parent": self.parent_id,
            "equity": round(self.equity(price), 2),
            "cash": round(self.cash, 2),
            "coin_value": round(self.coin * price, 2),
            "seed": round(self.seed, 2),
            "trades": self.trades,
            "wins": self.wins,
            "winrate": round(100 * self.wins / self.trades, 1) if self.trades else 0.0,
            "children": self.children,
            "strategy": self.genome.strategy,
            "last": self.last_action,
            "thesis": self.genome.thesis,
        }
