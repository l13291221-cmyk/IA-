"""Sciame di bot INDIPENDENTI (demo o soldi veri).

Come richiesto:
- Prima c'è una fase di ANALISI del mercato (default 30 giorni): i bot osservano e
  la palestra impara, ma non si opera.
- Poi parte UN SOLO bot col capitale impostato (es. 20€).
- Ogni bot decide DA SOLO (investimenti diversi) e tiene la SUA tabella di operazioni
  (ogni segnale vinto/perso).
- Quando un bot RADDOPPIA (arriva a 40) si CLONA e dà METÀ al figlio (20/20); poi si
  ripete. Se perde troppo si AUTOELIMINA (finisce nel "cimitero", segnato morto).
- Ciò che i bot imparano viene CONDIVISO: i genomi vincenti finiscono nella memoria
  comune della palestra, da cui i nuovi bot ereditano.

Soldi veri: ogni bot piazza i PROPRI ordini reali su Kraken (≥ ordine minimo). Il
massimo che puoi perdere è il capitale iniziale (spot, nessuna leva); più stop-perdita
giornaliero e tasto di emergenza gestiti dal motore.
"""
from __future__ import annotations

import copy
import itertools
import time
from collections import deque
from typing import Any, Callable, Dict, List, Optional

from .agent import FEE
from .genome import Genome, crossover, mutate
from . import strategy

_bot_id = itertools.count(1)


class Bot:
    """Un singolo bot: portafoglio proprio, decisioni proprie, ordini propri."""

    def __init__(self, genome: Genome, seed: float, generation: int, parent_id: Optional[int],
                 broker=None, min_order_eur: float = 5.0):
        self.id = next(_bot_id)
        self.genome = genome
        self.generation = generation
        self.parent_id = parent_id
        self.seed = seed
        self.cash = seed
        self.coin = 0.0
        self.entry_price = 0.0
        self.broker = broker           # None = demo · LiveBroker = soldi veri
        self.min_order = min_order_eur
        self.alive = True
        self.children = 0
        self.n_trades = 0
        self.wins = 0
        self.closed = 0          # posizioni chiuse (per il winrate)
        self.trades: deque = deque(maxlen=40)
        self.born = time.time()

    @property
    def live(self) -> bool:
        return self.broker is not None

    def equity(self, price: float) -> float:
        return self.cash + self.coin * price

    def in_position(self) -> bool:
        return self.coin > 0

    def _buy(self, price: float) -> None:
        eur = self.cash * self.genome.risk_fraction
        if self.live:
            eur = max(eur, self.min_order)      # rispetta il minimo di Kraken
        eur = min(eur, self.cash)
        if eur <= 0 or (self.live and eur < self.min_order):
            return
        if self.live:
            r = self.broker.market_buy(eur)
            if not r.get("ok"):
                return
            units = float(r["units"])
        else:
            units = (eur * (1 - FEE)) / price
        self.cash -= eur
        self.coin += units
        self.entry_price = price
        self.n_trades += 1
        self.trades.appendleft({"t": time.time(), "side": "COMPRA", "price": round(price, 2),
                                "eur": round(eur, 2), "result": "aperto"})

    def _sell(self, price: float) -> None:
        units = self.coin
        if units <= 0:
            return
        cost = units * self.entry_price
        if self.live:
            if units * price < self.min_order:
                # troppo piccolo per Kraken: prova comunque, altrimenti resta
                pass
            r = self.broker.market_sell(units)
            if not r.get("ok"):
                return
            units = float(r["units"])
            eur = float(r["eur"]) * (1 - FEE)
        else:
            eur = units * price * (1 - FEE)
        win = eur >= cost
        self.wins += 1 if win else 0
        self.closed += 1
        pnl = (price - self.entry_price) / self.entry_price * 100 if self.entry_price else 0.0
        self.cash += eur
        self.coin = 0.0
        self.entry_price = 0.0
        self.n_trades += 1
        # aggiorna la riga di apertura o aggiungine una di chiusura
        self.trades.appendleft({"t": time.time(), "side": "VENDI", "price": round(price, 2),
                                "eur": round(eur, 2), "result": "vinto" if win else "perso",
                                "pnl": round(pnl, 1)})

    def step(self, series: List[float], price: float) -> None:
        action = strategy.decide(self.genome, series, price, self.in_position(), self.entry_price)
        if action == strategy.BUY and not self.in_position():
            self._buy(price)
        elif action == strategy.SELL and self.in_position():
            self._sell(price)

    def flatten(self, price: float) -> None:
        if self.in_position():
            self._sell(price)

    def winrate(self) -> float:
        return round(100 * self.wins / self.closed, 1) if self.closed else 0.0

    def snapshot(self, price: float) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gen": self.generation,
            "parent": self.parent_id,
            "status": "vivo",
            "equity": round(self.equity(price), 2),
            "cash": round(self.cash, 2),
            "coin_value": round(self.coin * price, 2),
            "in_position": self.in_position(),
            "children": self.children,
            "n_trades": self.n_trades,
            "wins": self.wins,
            "winrate": self.winrate(),
            "strategy": self.genome.strategy,
            "trades": list(self.trades),
        }


class TradingSwarm:
    def __init__(
        self,
        price_fn: Callable[[], float],
        start_capital: float,
        lab,                      # Colony: memoria/cervello condiviso
        broker=None,              # None = demo · LiveBroker = soldi veri
        max_bots: int = 8,
        min_order_eur: float = 5.0,
        reproduce_multiple: float = 2.0,
        ruin_fraction: float = 0.2,
        analysis_days: float = 30.0,
        analysis_start: float = 0.0,
    ):
        self.price_fn = price_fn
        self.start_capital = float(start_capital)
        self.lab = lab
        self.broker = broker
        self.live = broker is not None
        self.max_bots = max_bots
        self.min_order = min_order_eur
        self.reproduce_threshold = self.start_capital * reproduce_multiple
        self.ruin_threshold = self.start_capital * ruin_fraction
        self.analysis_days = float(analysis_days)
        self.analysis_start = float(analysis_start) or time.time()

        self.bots: List[Bot] = []
        self.graveyard: deque = deque(maxlen=30)
        self.births = 0
        self.deaths = 0
        self.series: deque = deque(maxlen=400)
        self.equity_hist: deque = deque(maxlen=400)
        self.events: deque = deque(maxlen=60)

        # UN SOLO bot all'avvio (come richiesto)
        self._spawn(self._fresh_genome(), generation=1, parent=None, seed=self.start_capital)
        self._log(f"👶 Bot 1 creato con €{self.start_capital:.0f}")

    # ------------------------------------------------------------------ util
    def _log(self, msg: str) -> None:
        self.events.appendleft(msg)

    def _fresh_genome(self) -> Genome:
        g = mutate(self.lab.best_genome(), self.lab.rng)
        return g

    def _spawn(self, genome: Genome, generation: int, parent, seed: float) -> Bot:
        b = Bot(copy.copy(genome), seed, generation, parent, broker=self.broker, min_order_eur=self.min_order)
        self.bots.append(b)
        return b

    # ------------------------------------------------------------- analisi
    def analysis_remaining(self) -> float:
        elapsed = time.time() - self.analysis_start
        return max(0.0, self.analysis_days * 86400 - elapsed)

    def in_analysis(self) -> bool:
        return self.analysis_remaining() > 0

    def skip_analysis(self) -> None:
        self.analysis_start = time.time() - self.analysis_days * 86400 - 1
        self._log("⏩ Analisi saltata: i bot iniziano a operare")

    def total_equity(self, price: Optional[float] = None) -> float:
        p = price if price is not None else self.price_fn()
        return sum(b.equity(p) for b in self.bots)

    # ------------------------------------------------------------------- ciclo
    def step(self) -> None:
        price = self.price_fn()
        if price <= 0:
            return
        self.series.append(round(price, 2))
        series = list(self.series)

        if self.in_analysis():
            self.equity_hist.append(round(self.total_equity(price), 2))
            return

        # 1) ogni bot decide e opera da solo
        for b in self.bots:
            b.step(series, price)

        # 2) riproduzione: chi raddoppia si clona e dà METÀ al figlio
        for b in list(self.bots):
            if b.equity(price) >= self.reproduce_threshold and len(self.bots) < self.max_bots:
                b.flatten(price)                       # incassa la posizione
                total = b.cash
                half = total / 2.0
                b.cash = half                          # il genitore tiene metà
                # il figlio eredita geni del genitore + un campione della palestra, con mutazione
                child_genome = mutate(crossover(b.genome, self.lab.best_genome(), self.lab.rng), self.lab.rng)
                child = self._spawn(child_genome, b.generation + 1, b.id, half)
                b.children += 1
                self.births += 1
                self.lab._remember(b.genome)           # CONDIVIDE ciò che ha funzionato
                self._log(f"🐣 Bot #{b.id} ha raddoppiato → crea Bot #{child.id} e gli dà €{half:.2f}")

        # 3) autoeliminazione: chi perde troppo muore (impara: il suo genoma non si propaga)
        for b in list(self.bots):
            if b.equity(price) <= self.ruin_threshold:
                b.flatten(price)
                self.bots.remove(b)
                self.deaths += 1
                self.graveyard.appendleft({
                    "id": b.id, "gen": b.generation, "parent": b.parent_id,
                    "final": round(b.equity(price), 2), "children": b.children,
                    "n_trades": b.n_trades, "winrate": b.winrate(),
                    "died": time.strftime("%d/%m %H:%M"),
                })
                self._log(f"💀 Bot #{b.id} ha perso la sua quota → morto (autoeliminato)")

        # 4) se muoiono tutti, riparte un nuovo Bot 1 dal miglior genoma imparato
        if not self.bots:
            self._spawn(self._fresh_genome(), 1, None, self.start_capital)
            self._log("🔁 Tutti morti → riparte Bot 1 dal miglior genoma imparato")

        self.equity_hist.append(round(self.total_equity(price), 2))

    def liquidate(self) -> None:
        price = self.price_fn()
        for b in self.bots:
            b.flatten(price)

    # ------------------------------------------------------------------ stato
    def snapshot(self) -> Dict[str, Any]:
        price = self.price_fn()
        bots = sorted(self.bots, key=lambda b: b.equity(price), reverse=True)
        rem = self.analysis_remaining()
        return {
            "mode": "live" if self.live else "demo",
            "start_capital": round(self.start_capital, 2),
            "total_equity": round(self.total_equity(price), 2),
            "bots_alive": len(self.bots),
            "births": self.births,
            "deaths": self.deaths,
            "max_bots": self.max_bots,
            "reproduce_threshold": round(self.reproduce_threshold, 2),
            "ruin_threshold": round(self.ruin_threshold, 2),
            "best_generation": max((b.generation for b in self.bots), default=1),
            "bots_total": len(self.bots),
            "analysis": {
                "active": self.in_analysis(),
                "days": self.analysis_days,
                "remaining_days": round(rem / 86400, 2),
                "progress_pct": round(100 * (1 - rem / max(self.analysis_days * 86400, 1)), 1),
            },
            "bots": [b.snapshot(price) for b in bots[:60]],   # mostra i primi 60 (per tenere leggera la UI)
            "graveyard": list(self.graveyard)[:10],
            "events": list(self.events)[:12],
            "equity_hist": list(self.equity_hist),
        }

    # ----------------------------------------------------------- persistenza
    def to_state(self) -> Dict[str, Any]:
        return {
            "start_capital": self.start_capital,
            "analysis_start": self.analysis_start,
            "births": self.births,
            "deaths": self.deaths,
            "graveyard": list(self.graveyard),
            "equity_hist": list(self.equity_hist),
            "bots": [
                {"genome": b.genome.to_dict(), "gen": b.generation, "parent": b.parent_id,
                 "cash": b.cash, "coin": b.coin, "entry": b.entry_price, "seed": b.seed,
                 "children": b.children, "n_trades": b.n_trades, "wins": b.wins,
                 "closed": b.closed, "trades": list(b.trades)}
                for b in self.bots
            ],
        }

    def load_state(self, st: Dict[str, Any]) -> None:
        try:
            self.start_capital = float(st.get("start_capital", self.start_capital))
            self.analysis_start = float(st.get("analysis_start", self.analysis_start))
            self.births = int(st.get("births", 0))
            self.deaths = int(st.get("deaths", 0))
            self.graveyard = deque(st.get("graveyard", []), maxlen=30)
            self.equity_hist = deque(st.get("equity_hist", []), maxlen=400)
            self.bots = []
            for a in st.get("bots", []):
                b = self._spawn(Genome(**a["genome"]), a.get("gen", 1), a.get("parent"), a.get("seed", self.start_capital))
                b.cash = float(a.get("cash", self.start_capital))
                b.coin = float(a.get("coin", 0.0))
                b.entry_price = float(a.get("entry", 0.0))
                b.children = int(a.get("children", 0))
                b.n_trades = int(a.get("n_trades", 0))
                b.wins = int(a.get("wins", 0))
                b.closed = int(a.get("closed", 0))
                b.trades = deque(a.get("trades", []), maxlen=40)
            if not self.bots:
                self._spawn(self._fresh_genome(), 1, None, self.start_capital)
            self._log("💾 Sciame ripristinato dallo stato salvato")
        except Exception:
            pass
