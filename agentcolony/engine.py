"""Il motore 24/7.

Fa girare due cose in parallelo:

  1. PALESTRA (demo, veloce): lo sciame evolutivo scopre di continuo la strategia
     "campione" — soldi finti, quindi può sbagliare e morire senza danni.

  2. BANCO OPERATIVO (tempo reale): il campione opera su UN conto, con prezzi reali.
     - DEMO  → portafoglio simulato (PaperBroker)
     - LIVE  → ordini veri su Kraken (LiveBroker), SOLO se attivato e con chiavi.

Sicurezza sui soldi veri: limite di capitale, limite per-ordine, stop-perdita
giornaliero automatico e tasto di emergenza. Lo stato è salvato su disco, così un
riavvio riprende da dove era (adatto al 24/7).
"""
from __future__ import annotations

import copy
import datetime as _dt
import json
import os
import threading
import time
from collections import deque
from typing import Any, Dict, Optional

from . import config as cfgmod
from . import strategy
from .broker import PaperBroker, LiveBroker
from .colony import Colony
from .genome import Genome
from .livefeed import LiveFeed

STATE_PATH = os.path.join(cfgmod.DATA_DIR, "state.json")


class Engine:
    def __init__(self) -> None:
        self.cfg = cfgmod.load()
        self.lock = threading.RLock()
        self._stop = False
        self.paused = False

        self.events: deque = deque(maxlen=120)
        self.desk_equity_hist: deque = deque(maxlen=400)

        # feed prezzo reale
        self.feed = LiveFeed(self.cfg["symbol"], poll_seconds=min(15, self.cfg["live_poll_seconds"]))
        self.feed.start()

        # palestra evolutiva (demo)
        self.colony = self._new_colony()

        # campione + banco operativo
        self.champion: Genome = self.colony.best_genome()
        self.desk_series: deque = deque(maxlen=300)
        self.in_position = False
        self.entry_price = 0.0
        self.effective_mode = "demo"
        self.live_error = ""
        self.live_stopped_reason = ""
        self.broker = None
        self.paper_start = float(self.cfg["live_capital_eur"])
        self._paper_restore: Optional[Dict[str, float]] = None

        self.day = _today()
        self.day_start_equity = 0.0

        self._load_state()
        self._ensure_broker(force=True)

        # thread
        threading.Thread(target=self._lab_loop, daemon=True).start()
        threading.Thread(target=self._live_loop, daemon=True).start()
        threading.Thread(target=self._autosave_loop, daemon=True).start()
        self._log("🚀 Motore avviato in modalità " + self.effective_mode.upper())

    # ------------------------------------------------------------------ util
    def _log(self, msg: str) -> None:
        self.events.appendleft({"t": time.strftime("%H:%M:%S"), "msg": msg})

    def _new_colony(self) -> Colony:
        return Colony(
            seed_capital=20.0,
            starting_population=int(self.cfg["lab_population"]),
            market_vol=float(self.cfg["lab_vol"]),
            market_regime=self.cfg["lab_regime"],
            symbol=self.cfg["symbol"],
            use_real=False,   # la palestra è sempre sintetica e veloce
        )

    # --------------------------------------------------------------- broker
    def _can_go_live(self) -> bool:
        return bool(
            self.cfg["mode"] == "live"
            and self.cfg["live_enabled"]
            and self.cfg["acknowledged_risk"]
            and self.cfg["api_key"]
            and self.cfg["api_secret"]
        )

    def _ensure_broker(self, force: bool = False) -> None:
        want_live = self._can_go_live() and not self.live_stopped_reason
        have_live = isinstance(self.broker, LiveBroker)
        if not force and (want_live == have_live) and self.broker is not None:
            return
        if want_live:
            try:
                self.broker = LiveBroker(self.cfg["api_key"], self.cfg["api_secret"], self.cfg["symbol"])
                self.effective_mode = "live"
                self.live_error = ""
                # se sul conto c'è già cripto, la adottiamo come posizione aperta
                b = self.broker.balances()
                if b["COIN"] * self.broker.price() > 1.0:
                    self.in_position = True
                    if not self.entry_price:
                        self.entry_price = self.broker.price()
                self._log("💶 SOLDI VERI attivi su Kraken (" + self.cfg["symbol"] + ")")
            except Exception as e:
                self.broker = PaperBroker(self.feed, self.paper_start, self.cfg["symbol"])
                self.effective_mode = "demo"
                self.live_error = f"chiavi non valide o Kraken irraggiungibile: {str(e)[:160]}"
                self._log("⚠️ Live non attivabile → resto in DEMO. " + self.live_error)
        else:
            pb = PaperBroker(self.feed, self.paper_start, self.cfg["symbol"])
            if self._paper_restore:
                pb.eur = self._paper_restore.get("eur", pb.eur)
                pb.coin = self._paper_restore.get("coin", pb.coin)
                self._paper_restore = None
            self.broker = pb
            self.effective_mode = "demo"

    # ------------------------------------------------------------- persistenza
    def _load_state(self) -> None:
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                st = json.load(f)
        except Exception:
            return
        try:
            if st.get("champion"):
                self.champion = Genome(**st["champion"])
            d = st.get("desk", {})
            self.in_position = bool(d.get("in_position", False))
            self.entry_price = float(d.get("entry_price", 0.0))
            self._paper_restore = {"eur": float(d.get("paper_eur", self.paper_start)),
                                   "coin": float(d.get("paper_coin", 0.0))}
            self.desk_equity_hist = deque(st.get("desk_equity_hist", []), maxlen=400)
            self.day = st.get("day", _today())
            self.day_start_equity = float(st.get("day_start_equity", 0.0))
            self.live_stopped_reason = st.get("live_stopped_reason", "")
            self._log("💾 Stato precedente ripristinato")
        except Exception:
            pass

    def _save_state(self) -> None:
        with self.lock:
            paper_eur = getattr(self.broker, "eur", self.paper_start)
            paper_coin = getattr(self.broker, "coin", 0.0)
            st = {
                "champion": self.champion.to_dict(),
                "desk": {
                    "in_position": self.in_position,
                    "entry_price": self.entry_price,
                    "paper_eur": paper_eur,
                    "paper_coin": paper_coin,
                },
                "desk_equity_hist": list(self.desk_equity_hist),
                "day": self.day,
                "day_start_equity": self.day_start_equity,
                "live_stopped_reason": self.live_stopped_reason,
            }
        try:
            os.makedirs(cfgmod.DATA_DIR, exist_ok=True)
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(st, f, indent=2)
        except Exception:
            pass

    # -------------------------------------------------------------- i 3 loop
    def _lab_loop(self) -> None:
        while not self._stop:
            if not self.paused:
                with self.lock:
                    self.colony.tick()
            time.sleep(1.0 / max(0.5, float(self.cfg["lab_tps"])))

    def _autosave_loop(self) -> None:
        while not self._stop:
            time.sleep(20)
            self._save_state()

    def _live_loop(self) -> None:
        while not self._stop:
            try:
                if not self.paused:
                    self._desk_step()
            except Exception as e:
                self._log("errore banco: " + str(e)[:140])
            time.sleep(max(5, int(self.cfg["live_poll_seconds"])))

    # --------------------------------------------------------- passo del banco
    def _desk_step(self) -> None:
        with self.lock:
            self._ensure_broker()
            if self.broker is None:
                return
            price = self.broker.price()
            if price <= 0:
                return
            self.desk_series.append(round(price, 2))
            equity = self.broker.equity()

            # reset giornaliero dello stop-perdita
            today = _today()
            if today != self.day or self.day_start_equity <= 0:
                self.day = today
                self.day_start_equity = equity

            # STOP-PERDITA GIORNALIERO (solo soldi veri)
            if self.effective_mode == "live":
                loss = self.day_start_equity - equity
                if loss >= float(self.cfg["daily_loss_limit_eur"]) > 0:
                    self._do_kill("stop-perdita giornaliero raggiunto (-€%.2f)" % loss)
                    return

            # aggiorna il campione quando siamo liquidi (fuori posizione)
            if not self.in_position:
                self.champion = self.colony.best_genome()

            champ = copy.copy(self.champion)
            champ.take_profit = float(self.cfg["take_profit"])
            champ.stop_loss = float(self.cfg["stop_loss"])

            series = list(self.desk_series)
            action = strategy.decide(champ, series, price, self.in_position, self.entry_price)

            if action == strategy.BUY and not self.in_position:
                avail = self.broker.balances()["EUR"]
                size = min(float(self.cfg["per_order_eur"]), float(self.cfg["live_capital_eur"]), avail)
                if size > 1.0:
                    res = self.broker.market_buy(size)
                    if res.get("ok"):
                        self.in_position = True
                        self.entry_price = price
                        self._log(f"🟢 COMPRA {self.effective_mode.upper()} €{size:.2f} @ {price:.2f} ({champ.strategy})")
                    else:
                        self._log("compra non riuscita: " + str(res.get("reason", "")))
            elif action == strategy.SELL and self.in_position:
                res = self.broker.market_sell_all()
                if res.get("ok"):
                    pnl = (price - self.entry_price) / self.entry_price * 100 if self.entry_price else 0
                    self.in_position = False
                    self.entry_price = 0.0
                    self._log(f"🔴 VENDI {self.effective_mode.upper()} @ {price:.2f} (P&L {pnl:+.1f}%)")

            self.desk_equity_hist.append(round(self.broker.equity(), 2))

    # ---------------------------------------------------------------- comandi
    def apply_settings(self, update: Dict[str, Any]) -> Dict[str, Any]:
        with self.lock:
            old_symbol = self.cfg["symbol"]
            self.cfg = cfgmod.save(update)
            # riattiva il live se l'utente lo riabilita esplicitamente
            if update.get("live_enabled"):
                self.live_stopped_reason = ""
            self.paper_start = float(self.cfg["live_capital_eur"])
            if self.cfg["symbol"] != old_symbol:
                self.feed.stop()
                self.feed = LiveFeed(self.cfg["symbol"], poll_seconds=min(15, self.cfg["live_poll_seconds"]))
                self.feed.start()
                self.desk_series.clear()
            self._ensure_broker(force=True)
            self._log("⚙️ Impostazioni aggiornate — modalità effettiva: " + self.effective_mode.upper())
        return cfgmod.public_view(self.cfg)

    def _do_kill(self, reason: str) -> None:
        try:
            if self.in_position and self.broker is not None:
                self.broker.market_sell_all()
        except Exception:
            pass
        self.in_position = False
        self.entry_price = 0.0
        self.live_stopped_reason = reason
        self.cfg = cfgmod.save({"live_enabled": False})
        self._ensure_broker(force=True)
        self._log("🛑 EMERGENZA: " + reason + " — trading reale fermato, posizione chiusa.")

    def kill_switch(self) -> None:
        with self.lock:
            self._do_kill("tasto di emergenza premuto")

    def set_pause(self, value: bool) -> None:
        self.paused = value
        self._log("⏸️ In pausa" if value else "▶️ Ripreso")

    def reset_lab(self) -> None:
        with self.lock:
            self.colony = self._new_colony()
            self._log("↻ Palestra riavviata da zero")

    # ----------------------------------------------------------------- stato
    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            price = self.broker.price() if self.broker else self.feed.price
            bal = self.broker.balances() if self.broker else {"EUR": 0, "COIN": 0}
            equity = self.broker.equity() if self.broker else 0.0
            trade_log = getattr(self.broker, "trade_log", [])[-12:][::-1]
            desk = {
                "effective_mode": self.effective_mode,
                "price": round(price, 2),
                "price_is_real": self.feed.is_real,
                "eur": round(bal["EUR"], 2),
                "coin": round(bal["COIN"], 8),
                "coin_value": round(bal["COIN"] * price, 2),
                "equity": round(equity, 2),
                "in_position": self.in_position,
                "entry_price": round(self.entry_price, 2),
                "capital_limit": self.cfg["live_capital_eur"],
                "day_start_equity": round(self.day_start_equity, 2),
                "equity_hist": list(self.desk_equity_hist),
                "trades": trade_log,
                "champion": self.champion.to_dict(),
                "live_error": self.live_error,
                "live_stopped_reason": self.live_stopped_reason,
                "feed_error": self.feed.last_error,
            }
            return {
                "config": cfgmod.public_view(self.cfg),
                "paused": self.paused,
                "desk": desk,
                "lab": self.colony.snapshot(),
                "events": list(self.events)[:20],
            }

    def shutdown(self) -> None:
        self._stop = True
        self._save_state()


def _today() -> str:
    return _dt.date.today().isoformat()
