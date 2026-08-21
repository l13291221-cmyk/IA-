#!/usr/bin/env python3
"""Esecuzione da terminale (nessuna dipendenza, nessun browser).

Esempi:
    python3 run_sim.py                 # dati reali se possibile, altrimenti sintetico
    python3 run_sim.py --no-real       # mercato sintetico, offline
    python3 run_sim.py --ticks 5000 --delay 0
"""
from __future__ import annotations

import argparse
import time

from agentcolony.colony import Colony


def main() -> None:
    p = argparse.ArgumentParser(description="AgentColony — sciame evolutivo di trading (PAPER, soldi finti)")
    p.add_argument("--ticks", type=int, default=3000, help="numero di candele da simulare")
    p.add_argument("--seed-capital", type=float, default=20.0, help="capitale iniziale di ogni agente (finto)")
    p.add_argument("--population", type=int, default=10, help="numero di fondatori iniziali")
    p.add_argument("--vol", type=float, default=0.022, help="volatilità del mercato sintetico (0.01=calmo, 0.03=mosso)")
    p.add_argument("--regime", choices=["meanrev", "gbm"], default="meanrev",
                   help="meanrev=oscillante (demo vivace) · gbm=random walk realistico")
    p.add_argument("--symbol", default="BTC/EUR")
    p.add_argument("--no-real", action="store_true", help="usa mercato sintetico (offline)")
    p.add_argument("--llm", action="store_true", help="usa Claude per il genoma del fondatore (richiede ANTHROPIC_API_KEY)")
    p.add_argument("--delay", type=float, default=0.01, help="pausa tra i tick in secondi")
    p.add_argument("--rng", type=int, default=None, help="seed casuale per riproducibilità")
    args = p.parse_args()

    col = Colony(
        seed_capital=args.seed_capital,
        starting_population=args.population,
        market_vol=args.vol,
        market_regime=args.regime,
        symbol=args.symbol,
        use_real=not args.no_real,
        rng_seed=args.rng,
        use_llm=args.llm,
    )

    print("=" * 70)
    print("  AgentColony — SIMULAZIONE (soldi finti). NON è un consiglio finanziario.")
    print("=" * 70)
    print(f"Mercato        : {col.market.source}")
    print(f"Seed per agente: €{args.seed_capital:.0f}")
    print(f"Si riproduce a : €{col.reproduce_threshold:.0f}   |   Fallisce sotto: €{col.ruin_threshold:.1f}")
    print("-" * 70)

    try:
        for i in range(args.ticks):
            col.tick()
            if i % 25 == 0:
                s = col.snapshot()
                print(
                    f"t={s['tick']:5d} | {s['symbol']} €{s['price']:>10.2f} | "
                    f"pop={s['population']:2d} | nascite={s['births']:3d} morti={s['deaths']:3d} | "
                    f"gen_max={s['best_generation']:2d} | capitale=€{s['total_equity']:>8.2f}"
                )
            if args.delay:
                time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\n(interrotto)")

    s = col.snapshot()
    print("-" * 70)
    print("RISULTATO SIMULATO")
    print(f"  Tick totali     : {s['tick']}")
    print(f"  Popolazione viva: {s['population']}")
    print(f"  Nascite / morti : {s['births']} / {s['deaths']}")
    print(f"  Generazione max : {s['best_generation']}")
    print(f"  Capitale finale : €{s['total_equity']:.2f}  (picco €{s['peak_equity']:.2f})")
    print("  Ricorda: è simulazione. Un buon risultato qui NON garantisce nulla sul mercato reale.")


if __name__ == "__main__":
    main()
