"""Sciame operativo con soldi VERI (o demo), su un unico conto nettato.

Idea: tanti agenti, ognuno con la sua quota di capitale, che decidono in autonomia.
Quando un agente raddoppia la sua quota → si CLONA (il figlio eredita i geni +
quelli dei campioni della palestra). Quando perde quasi tutta la quota → si
AUTOELIMINA. Esattamente come richiesto.

Sicurezza per i soldi veri:
- il totale impiegato non supera MAI `capital` (il tetto che decidi tu);
- gli ordini reali vengono ACCORPATI (netting) in un solo ordine per ciclo, così
  non si mandano micro-ordini sotto il minimo di Kraken;
- il conto reale detiene solo la posizione netta dello sciame; il resto del tuo
  saldo Kraken non viene toccato.

Il "libro" dei singoli agenti è un'attribuzione: la loro somma è ancorata a ogni
ciclo al valore reale della quota dello sciame (`cash + coin*prezzo`).
"""
from __future__ import annotations

import copy
import itertools
from collections import deque
from typing import Any, Callable, Dict, List, Optional

from .agent import FEE, Agent
from .genome import crossover, mutate

_book_id = itertools.count(1)


class TradingSwarm:
    def __init__(
        self,
        price_fn: Callable[[], float],
        capital: float,
        lab,                      # Colony: fonte dei genomi campione (intelligenza condivisa)
        broker=None,              # None = demo (finto) · LiveBroker = soldi veri
        desired_seed: float = 20.0,
        reproduce_multiple: float = 2.0,
        ruin_fraction: float = 0.15,
        max_agents: int = 12,
        min_order_eur: float = 5.0,
    ):
        self.price_fn = price_fn
        self.capital = float(capital)
        self.lab = lab
        self.broker = broker
        self.live = broker is not None
        self.max_agents = max_agents
        self.min_order_eur = min_order_eur

        n = max(1, min(max_agents, round(self.capital / max(1.0, desired_seed))))
        self.seed = self.capital / n
        self.reproduce_threshold = self.seed * reproduce_multiple
        self.ruin_threshold = self.seed * ruin_fraction

        # libro reale della quota dello sciame
        self.cash = self.capital
        self.coin = 0.0

        self.agents: List[Agent] = []
        for _ in range(n):
            self._spawn(self.lab.best_genome(), generation=0, parent=None, seed=self.seed)

        self.births = 0
        self.deaths = 0
        self.series: deque = deque(maxlen=300)
        self.equity_hist: deque = deque(maxlen=400)
        self.orders: deque = deque(maxlen=20)
        self.events: deque = deque(maxlen=60)
        self.last_error = ""
        self._log(f"👑 Sciame avviato: {n} agenti · quota €{self.seed:.2f} · tetto €{self.capital:.0f}")

    # ------------------------------------------------------------------ util
    def _log(self, msg: str) -> None:
        self.events.appendleft(msg)

    def _spawn(self, genome, generation: int, parent, seed: float) -> Agent:
        a = Agent(copy.copy(genome), seed, generation=generation, parent_id=parent)
        a.id = next(_book_id)
        self.agents.append(a)
        return a

    def equity(self, price: Optional[float] = None) -> float:
        p = price if price is not None else self.price_fn()
        return self.cash + self.coin * p

    # --------------------------------------------------------------- esecuzione
    def _execute_buy(self, eur: float, price: float) -> None:
        # non superare mai il tetto di capitale né la liquidità
        room = self.capital - self.coin * price
        eur = min(eur, room, self.cash)
        if eur < (self.min_order_eur if self.live else 0.01):
            return
        if self.live and self.broker is not None:
            r = self.broker.market_buy(eur)
            if not r.get("ok"):
                self.last_error = str(r.get("reason", ""))[:160]
                return
            units = float(r["units"])
        else:
            units = (eur * (1 - FEE)) / price
        self.cash -= eur
        self.coin += units
        self.orders.appendleft({"side": "BUY", "price": round(price, 2), "eur": round(eur, 2)})

    def _execute_sell(self, units: float, price: float, force: bool = False) -> None:
        units = min(units, self.coin)
        eur_val = units * price
        if units <= 0:
            return
        if not force and self.live and eur_val < self.min_order_eur:
            return
        if self.live and self.broker is not None:
            r = self.broker.market_sell(units)
            if not r.get("ok"):
                self.last_error = str(r.get("reason", ""))[:160]
                return
            units = float(r["units"])
            eur = float(r["eur"]) * (1 - FEE)
        else:
            eur = units * price * (1 - FEE)
        self.cash += eur
        self.coin -= units
        self.orders.appendleft({"side": "SELL", "price": round(price, 2), "eur": round(eur, 2)})

    # ------------------------------------------------------------------- ciclo
    def step(self) -> None:
        price = self.price_fn()
        if price <= 0:
            return
        self.series.append(round(price, 2))
        series = list(self.series)

        # 1) ogni agente decide e opera sul PROPRIO libro (virtuale)
        for a in self.agents:
            a.step(series, price)

        # 2) ancora la somma dei libri al valore reale della quota
        real_eq = self.equity(price)
        virt_eq = sum(a.equity(price) for a in self.agents)
        if virt_eq > 1e-9:
            scale = real_eq / virt_eq
            for a in self.agents:
                a.cash *= scale
                a.coin *= scale

        # 3) quanto "vuole" essere investito lo sciame, in aggregato
        invested = sum(a.coin * price for a in self.agents)
        frac = invested / real_eq if real_eq > 1e-9 else 0.0
        frac = max(0.0, min(1.0, frac))
        deployable = min(self.capital, real_eq)
        target_coin_value = deployable * frac
        target_coin = target_coin_value / price
        delta_units = target_coin - self.coin
        delta_eur = delta_units * price

        # 4) UN solo ordine netto per portare la posizione reale al target
        if delta_eur > 0:
            self._execute_buy(delta_eur, price)
        elif delta_units < 0:
            self._execute_sell(-delta_units, price, force=(target_coin_value < 1e-6))

        # 5) riproduzione (chi raddoppia la quota si clona)
        for a in list(self.agents):
            if a.equity(price) >= self.reproduce_threshold and len(self.agents) < self.max_agents:
                total = a.cash + a.coin * price
                a.cash = self.seed
                a.coin = 0.0
                a.entry_price = 0.0
                surplus = max(self.seed, total - self.seed)
                base = a.genome
                champ = self.lab.best_genome()
                child_genome = mutate(crossover(a.genome, champ, self.lab.rng), self.lab.rng)
                child_genome.thesis = f"erede di #{a.id}"
                child = self._spawn(child_genome, a.generation + 1, a.id, surplus)
                a.children += 1
                self.births += 1
                self._log(f"🐣 #{a.id} ha raddoppiato → figlio #{child.id} (gen {child.generation})")

        # 6) autoeliminazione (chi perde quasi tutta la quota muore)
        for a in list(self.agents):
            if a.equity(price) <= self.ruin_threshold and len(self.agents) > 1:
                self.agents.remove(a)
                self.deaths += 1
                self._log(f"💀 #{a.id} ha perso la sua quota → si autoelimina")

        # 7) tetto agenti → elimina il più debole
        while len(self.agents) > self.max_agents:
            weak = min(self.agents, key=lambda x: x.equity(price))
            self.agents.remove(weak)
            self.deaths += 1

        # 8) estinzione → riparte dal miglior genoma della palestra
        if not self.agents:
            self._spawn(self.lab.best_genome(), 0, None, min(self.capital, self.equity(price)))
            self._log("🔥 Sciame estinto → riparte dal miglior genoma della palestra")

        self.equity_hist.append(round(self.equity(price), 2))

    # ------------------------------------------------------------------ stato
    def snapshot(self) -> Dict[str, Any]:
        price = self.price_fn()
        agents = sorted(self.agents, key=lambda a: a.equity(price), reverse=True)
        return {
            "mode": "live" if self.live else "demo",
            "capital": round(self.capital, 2),
            "equity": round(self.equity(price), 2),
            "cash": round(self.cash, 2),
            "coin": round(self.coin, 8),
            "coin_value": round(self.coin * price, 2),
            "invested_pct": round(100 * self.coin * price / max(self.equity(price), 1e-9), 1),
            "population": len(self.agents),
            "births": self.births,
            "deaths": self.deaths,
            "best_generation": max((a.generation for a in self.agents), default=0),
            "reproduce_threshold": round(self.reproduce_threshold, 2),
            "ruin_threshold": round(self.ruin_threshold, 2),
            "agents": [a.snapshot(price) for a in agents],
            "orders": list(self.orders)[:10],
            "events": list(self.events)[:12],
            "equity_hist": list(self.equity_hist),
            "last_error": self.last_error,
        }

    def liquidate(self) -> None:
        """Vende tutta la posizione reale (per il tasto di emergenza)."""
        self._execute_sell(self.coin, self.price_fn(), force=True)

    # ----------------------------------------------------------- persistenza
    def to_state(self) -> Dict[str, Any]:
        return {
            "capital": self.capital,
            "seed": self.seed,
            "cash": self.cash,
            "coin": self.coin,
            "births": self.births,
            "deaths": self.deaths,
            "agents": [
                {"genome": a.genome.to_dict(), "gen": a.generation, "parent": a.parent_id,
                 "cash": a.cash, "coin": a.coin, "entry": a.entry_price, "seed": a.seed}
                for a in self.agents
            ],
            "equity_hist": list(self.equity_hist),
        }

    def load_state(self, st: Dict[str, Any]) -> None:
        from .genome import Genome
        try:
            self.cash = float(st["cash"])
            self.coin = float(st["coin"])
            self.births = int(st.get("births", 0))
            self.deaths = int(st.get("deaths", 0))
            self.equity_hist = deque(st.get("equity_hist", []), maxlen=400)
            self.agents = []
            for a in st.get("agents", []):
                ag = self._spawn(Genome(**a["genome"]), a.get("gen", 0), a.get("parent"), a.get("seed", self.seed))
                ag.cash = float(a.get("cash", self.seed))
                ag.coin = float(a.get("coin", 0.0))
                ag.entry_price = float(a.get("entry", 0.0))
            if not self.agents:
                self._spawn(self.lab.best_genome(), 0, None, self.seed)
            self._log("💾 Sciame ripristinato dallo stato salvato")
        except Exception:
            pass
