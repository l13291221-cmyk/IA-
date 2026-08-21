"""La colonia: gestisce lo sciame di agenti, la riproduzione, la morte e la
"conoscenza condivisa" (hall of fame dei genomi migliori).

Ciclo di vita di un agente (esattamente come immaginato):
  1. Parte con `seed_capital` (es. 20€ finti).
  2. Fa trading autonomo cercando di arrivare a `reproduce_threshold` (es. 40€).
  3. Quando ci arriva: REGALA un seed a un FIGLIO (una sua copia mutata, che
     eredita anche i geni dei migliori della colonia) e tiene il resto.
  4. Se scende sotto `ruin_threshold` (es. 7€): si AUTOELIMINA.
  5. I geni dei sopravvissuti si diffondono → la colonia "diventa più brava"
     per selezione naturale, non per magia.
"""
from __future__ import annotations

import random
from collections import deque
from typing import Any, Dict, List, Optional

from .agent import Agent
from .genome import Genome, crossover, mutate, random_genome
from .market import Market


class Colony:
    def __init__(
        self,
        seed_capital: float = 20.0,
        reproduce_multiple: float = 2.0,
        ruin_fraction: float = 0.35,
        max_population: int = 30,
        starting_population: int = 10,
        symbol: str = "BTC/EUR",
        use_real: bool = True,
        market_vol: float = 0.022,
        market_drift: float = 0.0,
        market_regime: str = "meanrev",
        rng_seed: Optional[int] = None,
        use_llm: bool = False,
    ):
        self.rng = random.Random(rng_seed)
        self.seed_capital = seed_capital
        self.reproduce_threshold = seed_capital * reproduce_multiple
        self.ruin_threshold = seed_capital * ruin_fraction
        self.max_population = max_population
        self.market = Market(
            symbol=symbol, use_real=use_real, seed=rng_seed,
            drift=market_drift, vol=market_vol, regime=market_regime,
        )

        self.agents: List[Agent] = []
        self.hall_of_fame: List[Genome] = []   # conoscenza condivisa
        self.tick_count = 0
        self.births = 0
        self.deaths = 0
        self.peak_equity = seed_capital * starting_population
        self.events: deque = deque(maxlen=80)
        self.equity_history: deque = deque(maxlen=240)
        self.price_history: deque = deque(maxlen=240)

        # sciame di fondatori diversi: il primo può usare Claude, gli altri sono casuali
        founder_genome = self._founder_genome(use_llm)
        self.agents.append(Agent(founder_genome, seed_capital, generation=0))
        for _ in range(max(0, starting_population - 1)):
            g = random_genome(self.rng)
            g.thesis = "fondatore casuale"
            self.agents.append(Agent(g, seed_capital, generation=0))
        self._log(
            f"👑 {len(self.agents)} fondatori nati con €{seed_capital:.0f} ciascuno "
            f"(capitale iniziale simulato €{seed_capital * len(self.agents):.0f})"
        )

    # --- avvio -----------------------------------------------------------
    def _founder_genome(self, use_llm: bool) -> Genome:
        base = random_genome(self.rng)
        base.thesis = "fondatore: strategia iniziale"
        if use_llm:
            try:
                from .llm import propose_genome

                proposed = propose_genome(self.market.summary())
                if proposed:
                    for k, v in proposed.items():
                        if hasattr(base, k) and v is not None:
                            setattr(base, k, v)
                    base.slow_ma = max(int(base.slow_ma), int(base.fast_ma) + 3)
                    self._log("🧠 Genoma del fondatore proposto da Claude (LLM)")
            except Exception:
                pass
        return base

    # --- utilità ---------------------------------------------------------
    def _log(self, msg: str) -> None:
        self.events.appendleft({"t": self.tick_count, "msg": msg})

    def total_equity(self) -> float:
        p = self.market.price
        return sum(a.equity(p) for a in self.agents)

    def _remember(self, genome: Genome) -> None:
        self.hall_of_fame.append(genome)
        if len(self.hall_of_fame) > 12:
            self.hall_of_fame.pop(0)

    def _child_genome(self, parent: Agent) -> Genome:
        # eredita dal genitore + (a volte) incrocia con un campione della colonia
        base = parent.genome
        if self.hall_of_fame and self.rng.random() < 0.6:
            mate = self.rng.choice(self.hall_of_fame)
            base = crossover(parent.genome, mate, self.rng)
        child = mutate(base, self.rng)
        child.thesis = f"erede di #{parent.id} (gen {parent.generation + 1})"
        return child

    # --- ciclo principale -----------------------------------------------
    def tick(self) -> None:
        price = self.market.step()
        series = self.market.series()
        self.tick_count += 1

        for a in list(self.agents):
            a.step(series, price)

        # riproduzione (chi raggiunge la soglia regala un seed a un figlio)
        for a in list(self.agents):
            if a.equity(price) >= self.reproduce_threshold:
                # liquida in cash per uno split pulito (paper)
                a.cash = a.cash + a.coin * price
                a.coin = 0.0
                a.entry_price = 0.0
                total = a.cash
                child_seed = self.seed_capital
                a.cash = total - child_seed  # il genitore tiene il resto
                child = Agent(
                    self._child_genome(a),
                    child_seed,
                    generation=a.generation + 1,
                    parent_id=a.id,
                )
                child.born_tick = self.tick_count
                a.children += 1
                self._remember(a.genome)
                self.agents.append(child)
                self.births += 1
                self._log(
                    f"🐣 #{a.id} ha raggiunto €{total:.0f} → nasce il figlio "
                    f"#{child.id} (gen {child.generation}) con €{child_seed:.0f}"
                )

        # morte per rovina (autoeliminazione)
        for a in list(self.agents):
            if a.equity(price) <= self.ruin_threshold:
                self.agents.remove(a)
                self.deaths += 1
                self._log(f"💀 #{a.id} fallito (€{a.equity(price):.1f}) — si autoelimina")

        # tetto di popolazione → selezione naturale (elimina il più debole)
        while len(self.agents) > self.max_population:
            weakest = min(self.agents, key=lambda x: x.equity(price))
            self.agents.remove(weakest)
            self.deaths += 1
            self._log(f"⚖️ popolazione piena: eliminato il più debole #{weakest.id}")

        # estinzione totale → rinascita dal miglior genoma ricordato
        if not self.agents:
            g = self.rng.choice(self.hall_of_fame) if self.hall_of_fame else random_genome(self.rng)
            founder = Agent(mutate(g, self.rng), self.seed_capital, generation=0)
            founder.genome.thesis = "rinato dal miglior genoma ricordato"
            self.agents.append(founder)
            self._log(f"🔥 Colonia estinta → rinascita #{founder.id} dalla memoria collettiva")

        eq = self.total_equity()
        self.peak_equity = max(self.peak_equity, eq)
        self.equity_history.append(round(eq, 2))
        self.price_history.append(round(price, 2))

    def best_genome(self) -> Genome:
        """Il 'campione' attuale: il genoma dell'agente vivo più ricco."""
        if self.agents:
            best = max(self.agents, key=lambda a: a.equity(self.market.price))
            return best.genome
        if self.hall_of_fame:
            return self.hall_of_fame[-1]
        return random_genome(self.rng)

    # --- stato per la dashboard -----------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        price = self.market.price
        agents = sorted(self.agents, key=lambda a: a.equity(price), reverse=True)
        return {
            "tick": self.tick_count,
            "price": round(price, 2),
            "symbol": self.market.symbol,
            "source": self.market.source,
            "population": len(self.agents),
            "births": self.births,
            "deaths": self.deaths,
            "total_equity": round(self.total_equity(), 2),
            "peak_equity": round(self.peak_equity, 2),
            "seed_capital": self.seed_capital,
            "reproduce_threshold": self.reproduce_threshold,
            "ruin_threshold": round(self.ruin_threshold, 2),
            "max_population": self.max_population,
            "best_generation": max((a.generation for a in self.agents), default=0),
            "hall_of_fame": len(self.hall_of_fame),
            "agents": [a.snapshot(price) for a in agents],
            "events": list(self.events)[:24],
            "equity_history": list(self.equity_history),
            "price_history": list(self.price_history),
        }
