"""Genoma di una strategia: i "geni" che un agente trasmette ai figli.

L'evoluzione avviene per mutazione + crossover; la selezione la fa il mercato
(chi raddoppia si riproduce, chi va in rovina muore).
"""
from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any, Dict

STRATEGIES = ("trend", "meanrev")


@dataclass
class Genome:
    strategy: str = "trend"      # "trend" (segui il trend) o "meanrev" (ritorno alla media)
    fast_ma: int = 5             # media mobile veloce
    slow_ma: int = 20            # media mobile lenta
    rsi_period: int = 14
    rsi_buy: float = 35.0        # compra sotto questo RSI (meanrev)
    rsi_sell: float = 65.0       # vendi sopra questo RSI
    risk_fraction: float = 0.5   # quota di liquidità impiegata per ogni acquisto
    take_profit: float = 0.06    # esci a +6%
    stop_loss: float = 0.04      # esci a -4%
    thesis: str = "strategia di base"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def random_genome(rng: random.Random) -> Genome:
    fast = rng.randint(3, 12)
    slow = fast + rng.randint(8, 40)
    return Genome(
        strategy=rng.choice(STRATEGIES),
        fast_ma=fast,
        slow_ma=slow,
        rsi_period=rng.randint(8, 20),
        rsi_buy=rng.uniform(20, 40),
        rsi_sell=rng.uniform(60, 80),
        risk_fraction=rng.uniform(0.25, 0.9),
        take_profit=rng.uniform(0.03, 0.12),
        stop_loss=rng.uniform(0.02, 0.08),
        thesis="strategia casuale iniziale",
    )


def mutate(g: Genome, rng: random.Random, rate: float = 0.3) -> Genome:
    def jint(v: int, lo: int, hi: int, span: int) -> int:
        if rng.random() < rate:
            v = v + rng.randint(-span, span)
        return max(lo, min(hi, v))

    def jflt(v: float, lo: float, hi: float, span: float) -> float:
        if rng.random() < rate:
            v = v + rng.uniform(-span, span)
        return max(lo, min(hi, v))

    strategy = g.strategy
    if rng.random() < rate * 0.4:
        strategy = rng.choice(STRATEGIES)

    fast = jint(g.fast_ma, 3, 15, 2)
    slow = jint(g.slow_ma, fast + 3, 60, 4)
    return Genome(
        strategy=strategy,
        fast_ma=fast,
        slow_ma=max(slow, fast + 3),
        rsi_period=jint(g.rsi_period, 6, 24, 2),
        rsi_buy=jflt(g.rsi_buy, 15, 45, 4),
        rsi_sell=jflt(g.rsi_sell, 55, 85, 4),
        risk_fraction=jflt(g.risk_fraction, 0.2, 1.0, 0.1),
        take_profit=jflt(g.take_profit, 0.02, 0.15, 0.02),
        stop_loss=jflt(g.stop_loss, 0.015, 0.1, 0.015),
        thesis=g.thesis,
    )


def crossover(a: Genome, b: Genome, rng: random.Random) -> Genome:
    def pick(x, y):
        return x if rng.random() < 0.5 else y

    fast = pick(a.fast_ma, b.fast_ma)
    slow = pick(a.slow_ma, b.slow_ma)
    return Genome(
        strategy=pick(a.strategy, b.strategy),
        fast_ma=fast,
        slow_ma=max(slow, fast + 3),
        rsi_period=pick(a.rsi_period, b.rsi_period),
        rsi_buy=pick(a.rsi_buy, b.rsi_buy),
        rsi_sell=pick(a.rsi_sell, b.rsi_sell),
        risk_fraction=pick(a.risk_fraction, b.risk_fraction),
        take_profit=pick(a.take_profit, b.take_profit),
        stop_loss=pick(a.stop_loss, b.stop_loss),
        thesis="incrocio di due strategie",
    )
