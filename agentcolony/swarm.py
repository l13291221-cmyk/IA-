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
import random
import time
from collections import deque
from typing import Any, Callable, Dict, List, Optional

from .agent import FEE
from .brain import Brain
from .genome import Genome, crossover, mutate
from . import strategy
from . import signals

_bot_id = itertools.count(1)
_MIN_HOLD = 5   # cicli minimi prima di poter uscire per "trend girato" (evita i round-trip lampo)


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
        self.day_start_equity = seed   # saldo a inizio giornata (per la quota giornaliera)
        # leva / short (usati in DEMO; il reale resta spot long)
        self.leverage = 1.0
        self.allow_short = False
        self.max_trade_pct = 25.0   # % del saldo per operazione (lo decidi tu dal sito)
        self.side = 0          # 0 = flat, +1 = long, -1 = short
        self.margin = 0.0      # capitale bloccato come margine
        self.units = 0.0       # unità nozionali (margine × leva / prezzo)
        self.symbol: Optional[str] = None   # cripto attualmente operata (multi-asset, demo)
        self._pos_val = 0.0    # valore posizione in EUR (aggiornato a ogni ciclo)
        self.cooldown = 0      # cicli di pausa dopo una chiusura (meno operazioni = meno commissioni)
        self.hold = 0          # cicli da quando è aperta la posizione (per non chiuderla troppo presto)
        self.brain: Optional[Brain] = None   # cervello condiviso (cosa fa vincere/perdere)
        self.entry_side = 0    # direzione con cui è stata aperta (per aggiornare il cervello alla chiusura)
        self.entry_asset = ""  # cripto con cui è stata aperta
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

    def _pos_value(self, price: float) -> float:
        # valore corrente della posizione con leva/short; a 0 = liquidazione (margine perso)
        return max(0.0, self.margin + self.side * self.units * (price - self.entry_price))

    def _mark(self, feed) -> None:
        # aggiorna il valore in EUR della posizione al prezzo attuale della sua cripto
        if self.symbol and self.side != 0:
            self._pos_val = self._pos_value(feed.price(self.symbol))
        elif self.symbol and self.coin > 0:
            self._pos_val = self.coin * feed.price(self.symbol)
        else:
            self._pos_val = 0.0

    def equity(self) -> float:
        return self.cash + self._pos_val

    def in_position(self) -> bool:
        return self.coin > 0 or self.side != 0

    def _buy(self, price: float) -> None:
        # quanto investire lo DECIDE IL BOT (il suo "istinto di rischio" che evolve),
        # fino al tetto massimo che hai scelto (default 100% = può puntare anche tutto).
        bal = self.cash
        frac = min(max(0.05, self.genome.risk_fraction), self.max_trade_pct / 100.0)
        eur = bal * frac
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
        self.entry_side = 1
        self.entry_asset = (self.symbol.split("/")[0] if self.symbol else "?")
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
        if self.brain:   # anche il reale nutre il cervello condiviso
            self.brain.record(self.entry_side, self.entry_asset, win, pnl)
        self.cash += eur
        self.coin = 0.0
        self.entry_price = 0.0
        self.n_trades += 1
        # aggiorna la riga di apertura o aggiungine una di chiusura
        self.trades.appendleft({"t": time.time(), "side": "VENDI", "price": round(price, 2),
                                "eur": round(eur, 2), "result": "vinto" if win else "perso",
                                "pnl": round(pnl, 1)})

    # --- posizioni con leva / short (solo DEMO) ---
    def _open_demo(self, side: int, price: float, reason: str = "") -> None:
        # quanto puntare lo decide il BOT (istinto di rischio evolutivo), entro il tetto scelto
        bal = self.cash
        frac = min(max(0.05, self.genome.risk_fraction), self.max_trade_pct / 100.0)
        margin = bal * frac
        if margin < 0.5 or price <= 0:
            return
        self.cash -= margin
        self.side = side
        self.margin = margin
        self.entry_price = price
        self.units = (margin * self.leverage) / price
        self.hold = 0
        self.entry_side = side
        self.entry_asset = (self.symbol.split("/")[0] if self.symbol else "?")
        self.n_trades += 1
        row = {"t": time.time(), "side": "LONG" if side > 0 else "SHORT",
               "price": round(price, 2), "eur": round(margin, 2), "result": "aperto"}
        if reason:
            row["reason"] = reason
        self.trades.appendleft(row)

    def _close_demo(self, price: float, liquidated: bool = False) -> None:
        if self.side == 0:
            return
        val = self._pos_value(price)
        fee = self.units * (price + self.entry_price) * FEE   # commissioni ~ andata+ritorno
        cash_back = max(0.0, val - fee)
        win = cash_back > self.margin
        self.wins += 1 if win else 0
        self.closed += 1
        pnl = (self.side * (price - self.entry_price) / self.entry_price * 100 * self.leverage) if self.entry_price else 0.0
        if self.brain:   # aggiorna il cervello condiviso: cosa mi ha fatto vincere/perdere
            self.brain.record(self.entry_side, self.entry_asset, win, pnl)
        self.cash += cash_back
        self.n_trades += 1
        res = "liquidato" if liquidated else ("vinto" if win else "perso")
        self.trades.appendleft({"t": time.time(), "side": "CHIUDI", "price": round(price, 2),
                                "eur": round(cash_back, 2), "result": res, "pnl": round(pnl, 1)})
        self.side = 0
        self.margin = 0.0
        self.units = 0.0
        self.entry_price = 0.0
        self.symbol = None
        self.cooldown = 6    # pausa dopo una chiusura (profilo attivo: riparte prima a cercare)

    def step(self, feed) -> None:
        if self.live:
            # SOLDI VERI: opera solo sulla coppia impostata (spot long, invariato/testato)
            price = feed.price(self.symbol)
            series = feed.series(self.symbol)
            if price > 0:
                action = strategy.decide(self.genome, series, price, self.in_position(), self.entry_price)
                if action == strategy.BUY and not self.in_position():
                    self._buy(price)
                elif action == strategy.SELL and self.in_position():
                    self._sell(price)
            self._mark(feed)
            return
        # DEMO multi-cripto: se in posizione la gestisce, se liquido SCEGLIE dove operare
        if self.side != 0:
            price = feed.price(self.symbol)
            if price > 0:
                self.hold += 1
                # variazione DIREZIONALE dall'ingresso (+ = a favore, − = contro)
                change = self.side * (price - self.entry_price) / self.entry_price if self.entry_price else 0.0
                if self._pos_value(price) <= 0:
                    self._close_demo(price, liquidated=True)          # liquidazione
                elif change <= -self.genome.stop_loss:
                    self._close_demo(price)                            # STOP-LOSS: taglia la perdita
                elif change >= self.genome.take_profit:
                    self._close_demo(price)                            # TAKE-PROFIT: incassa il guadagno
                elif self.hold >= _MIN_HOLD and getattr(feed, "ta_ready", False) \
                        and signals.trend_flipped(feed, self.symbol, self.side):
                    self._close_demo(price)                            # il trend 4H si è girato contro
        elif self.cooldown > 0:
            self.cooldown -= 1   # in pausa: niente nuove operazioni per qualche ciclo
        else:
            # scansiona TUTTE le cripto e sceglie dove c'è un'opportunità
            use_ta = getattr(feed, "ta_ready", False)   # tecnica multi-timeframe solo su dati reali
            candidates = []
            for s in feed.symbols:
                pr = feed.price(s)
                if pr <= 0:
                    continue
                asset = s.split("/")[0]
                if use_ta:
                    # TECNICA: Trend(4H) + Ritracciamento(1H) + Conferma(15M) + Volume
                    res = signals.evaluate(feed, s)
                    if res and (res["side"] == "long" or (res["side"] == "short" and self.allow_short)):
                        sd = 1 if res["side"] == "long" else -1
                        if self.brain is None or self.brain.should_take(sd, asset):   # il cervello sconsiglia i tipi che perdono
                            candidates.append((s, res["side"], pr, res.get("reason", "")))
                else:
                    # offline / senza dati reali: strategia semplice, così la demo non resta ferma
                    sig = strategy.signal(self.genome, feed.series(s), pr)
                    if sig == "long" or (sig == "short" and self.allow_short):
                        sd = 1 if sig == "long" else -1
                        if self.brain is None or self.brain.should_take(sd, asset):
                            candidates.append((s, sig, pr, ""))
            if candidates:
                s, sig, pr, reason = random.choice(candidates)   # bot diversi scelgono cripto diverse
                self.symbol = s
                self._open_demo(1 if sig == "long" else -1, pr, reason)
        self._mark(feed)

    def flatten(self, feed) -> None:
        if self.live and self.coin > 0:
            self._sell(feed.price(self.symbol))
        elif self.side != 0:
            self._close_demo(feed.price(self.symbol))
        self._mark(feed)

    def winrate(self) -> float:
        return round(100 * self.wins / self.closed, 1) if self.closed else 0.0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gen": self.generation,
            "parent": self.parent_id,
            "status": "vivo",
            "equity": round(self.equity(), 2),
            "cash": round(self.cash, 2),
            "coin_value": round(self._pos_val, 2),
            "in_position": self.in_position(),
            "side": ("long" if self.side > 0 else ("short" if self.side < 0 else "flat")),
            "leverage": round(self.leverage, 1),
            "asset": (self.symbol.split("/")[0] if self.symbol else "—"),
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
        feed,                     # MultiFeed: tiene d'occhio più cripto insieme
        start_capital: float,
        lab,                      # Colony: memoria/cervello condiviso
        broker=None,              # None = demo · LiveBroker = soldi veri
        max_bots: int = 8,
        min_order_eur: float = 5.0,
        reproduce_multiple: float = 2.0,
        ruin_fraction: float = 0.2,
        analysis_days: float = 30.0,
        analysis_start: float = 0.0,
        daily_target: float = 0.5,
        day_seconds: float = 86400.0,
        leverage: float = 1.0,
        allow_short: bool = False,
        max_trade_pct: float = 25.0,
        stop_loss_pct: float = 8.0,
        take_profit_pct: float = 16.0,
    ):
        self.feed = feed
        self.primary = feed.primary
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
        self.daily_target = float(daily_target)   # € che ogni bot deve GUADAGNARE al giorno
        self.day_seconds = float(day_seconds)     # durata di una "giornata"
        self.day_start_time = time.time()
        self.day_number = 1
        self.game_overs = 0
        self.leverage = max(1.0, float(leverage))
        self.allow_short = bool(allow_short)
        self.max_trade_pct = float(max_trade_pct)
        self.stop_loss_pct = max(1.0, float(stop_loss_pct))
        self.take_profit_pct = max(1.0, float(take_profit_pct))
        self.brain = Brain()   # cervello CONDIVISO: impara cosa fa vincere/perdere, si tramanda e si salva

        self.bots: List[Bot] = []
        self.graveyard: deque = deque(maxlen=30)
        self.births = 0
        self.deaths = 0
        self.series: deque = deque(maxlen=400)
        self.equity_hist: deque = deque(maxlen=400)
        self.events: deque = deque(maxlen=60)
        self._bot_counter = itertools.count(1)  # numera i bot da 1 in questo sciame

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
        b.id = next(self._bot_counter)   # numerazione da 1 per questo sciame (Bot 1, 2, 3…)
        b.genome.stop_loss = self.stop_loss_pct / 100.0      # respiro prima di tagliare (lo decidi tu dal sito)
        b.genome.take_profit = self.take_profit_pct / 100.0  # obiettivo di guadagno per trade
        b.leverage = self.leverage       # leva (demo)
        b.allow_short = self.allow_short # consenti operazioni al ribasso (demo)
        b.max_trade_pct = self.max_trade_pct  # % del saldo per operazione
        b.brain = self.brain                  # tutti i bot condividono lo STESSO cervello
        b.symbol = self.primary if b.live else None   # live: coppia fissa · demo: sceglie lui
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

    def total_equity(self) -> float:
        return sum(b.equity() for b in self.bots)

    # ------------------------------------------------------------------- ciclo
    def step(self) -> None:
        price = self.feed.price(self.primary)
        if price <= 0:
            return
        self.series.append(round(price, 2))

        if self.in_analysis():
            self.equity_hist.append(round(self.total_equity(), 2))
            return

        # 1) ogni bot decide e opera da solo (in DEMO sceglie LUI la cripto su cui operare)
        for b in self.bots:
            b.step(self.feed)

        # 2) riproduzione: chi raddoppia si clona e dà METÀ al figlio
        for b in list(self.bots):
            if b.equity() >= self.reproduce_threshold and len(self.bots) < self.max_bots:
                b.flatten(self.feed)                   # incassa la posizione
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
            if b.equity() <= self.ruin_threshold:
                b.flatten(self.feed)
                self.bots.remove(b)
                self.deaths += 1
                self.graveyard.appendleft({
                    "id": b.id, "gen": b.generation, "parent": b.parent_id,
                    "final": round(b.equity(), 2), "children": b.children,
                    "n_trades": b.n_trades, "winrate": b.winrate(),
                    "died": time.strftime("%d/%m %H:%M"),
                })
                self._log(f"💀 Bot #{b.id} ha perso la sua quota → morto (autoeliminato)")

        # 3b) FINE GIORNATA: chi non ha GUADAGNATO almeno la quota del giorno → GAME OVER
        if self.day_seconds > 0 and (time.time() - self.day_start_time) >= self.day_seconds:
            for b in list(self.bots):
                gain = b.equity() - b.day_start_equity
                if self.daily_target > 0 and gain < self.daily_target:
                    b.flatten(self.feed)
                    if b in self.bots:
                        self.bots.remove(b)
                    self.deaths += 1
                    self.game_overs += 1
                    self.graveyard.appendleft({
                        "id": b.id, "gen": b.generation, "parent": b.parent_id,
                        "final": round(b.equity(), 2), "children": b.children,
                        "n_trades": b.n_trades, "winrate": b.winrate(),
                        "died": time.strftime("%d/%m %H:%M"),
                    })
                    self._log(
                        f"🔴 GAME OVER Bot #{b.id}: giorno {self.day_number} chiuso senza la quota "
                        f"(+€{gain:.2f} < €{self.daily_target:.2f})"
                    )
            # inizia una nuova giornata per i sopravvissuti
            self.day_number += 1
            self.day_start_time = time.time()
            for b in self.bots:
                b.day_start_equity = b.equity()

        # 4) se muoiono tutti, riparte un nuovo Bot 1 dal miglior genoma imparato
        if not self.bots:
            self._spawn(self._fresh_genome(), 1, None, self.start_capital)
            self._log("🔁 Tutti morti → riparte Bot 1 dal miglior genoma imparato")

        self.equity_hist.append(round(self.total_equity(), 2))

    def liquidate(self) -> None:
        for b in self.bots:
            b.flatten(self.feed)

    # ------------------------------------------------------------------ stato
    def snapshot(self) -> Dict[str, Any]:
        bots = sorted(self.bots, key=lambda b: b.equity(), reverse=True)
        rem = self.analysis_remaining()
        return {
            "mode": "live" if self.live else "demo",
            "start_capital": round(self.start_capital, 2),
            "total_equity": round(self.total_equity(), 2),
            "bots_alive": len(self.bots),
            "births": self.births,
            "deaths": self.deaths,
            "max_bots": self.max_bots,
            "reproduce_threshold": round(self.reproduce_threshold, 2),
            "ruin_threshold": round(self.ruin_threshold, 2),
            "daily_target": round(self.daily_target, 2),
            "day_number": self.day_number,
            "seconds_to_close": max(0, round(self.day_seconds - (time.time() - self.day_start_time))),
            "game_overs": self.game_overs,
            "best_generation": max((b.generation for b in self.bots), default=1),
            "bots_total": len(self.bots),
            "analysis": {
                "active": self.in_analysis(),
                "days": self.analysis_days,
                "remaining_days": round(rem / 86400, 2),
                "progress_pct": round(100 * (1 - rem / max(self.analysis_days * 86400, 1)), 1),
            },
            "bots": [b.snapshot() for b in bots[:60]],   # mostra i primi 60 (per tenere leggera la UI)
            "graveyard": list(self.graveyard)[:10],
            "events": list(self.events)[:12],
            "equity_hist": list(self.equity_hist),
            "brain_lessons": self.brain.lessons(),   # cosa ha imparato (setup buoni/da evitare)
        }

    # ----------------------------------------------------------- persistenza
    def to_state(self) -> Dict[str, Any]:
        return {
            "start_capital": self.start_capital,
            "analysis_start": self.analysis_start,
            "births": self.births,
            "deaths": self.deaths,
            "day_number": self.day_number,
            "graveyard": list(self.graveyard),
            "equity_hist": list(self.equity_hist),
            "brain": self.brain.to_state(),
            "bots": [
                {"genome": b.genome.to_dict(), "gen": b.generation, "parent": b.parent_id,
                 "cash": b.cash, "coin": b.coin, "entry": b.entry_price, "seed": b.seed,
                 "children": b.children, "n_trades": b.n_trades, "wins": b.wins,
                 "closed": b.closed, "trades": list(b.trades),
                 # posizione demo con leva/short (così l'equity resta continua dopo un riavvio)
                 "symbol": b.symbol, "side": b.side, "margin": b.margin, "units": b.units,
                 "day_start_equity": b.day_start_equity}
                for b in self.bots
            ],
        }

    def load_state(self, st: Dict[str, Any]) -> None:
        try:
            self.start_capital = float(st.get("start_capital", self.start_capital))
            self.analysis_start = float(st.get("analysis_start", self.analysis_start))
            self.births = int(st.get("births", 0))
            self.deaths = int(st.get("deaths", 0))
            self.day_number = int(st.get("day_number", 1))
            self.day_start_time = time.time()
            self.graveyard = deque(st.get("graveyard", []), maxlen=30)
            self.equity_hist = deque(st.get("equity_hist", []), maxlen=400)
            self.brain.load_state(st.get("brain") or {})   # recupera ciò che ha imparato
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
                # posizione demo con leva/short (se presente nello stato salvato)
                if not b.live:
                    b.symbol = a.get("symbol")
                    b.side = int(a.get("side", 0))
                    b.margin = float(a.get("margin", 0.0))
                    b.units = float(a.get("units", 0.0))
                b.day_start_equity = float(a.get("day_start_equity", b.cash))
                b._mark(self.feed)   # ricalcola il valore della posizione al prezzo attuale
            if not self.bots:
                self._spawn(self._fresh_genome(), 1, None, self.start_capital)
            self._log("💾 Sciame ripristinato dallo stato salvato")
        except Exception:
            pass
