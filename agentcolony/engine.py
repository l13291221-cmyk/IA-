"""Il motore 24/7.

Fa girare in parallelo:

  1. PALESTRA (demo, veloce): sciame evolutivo che scopre di continuo i genomi
     migliori — soldi finti, quindi impara senza rischi.

  2. SCIAME OPERATIVO (tempo reale): tanti agenti che operano su UN conto nettato,
     si clonano quando raddoppiano e si autoeliminano quando perdono la quota.
     - DEMO  → soldi finti su prezzi reali
     - LIVE  → ordini veri su Kraken (solo se attivato, con chiavi e consenso)
     I nuovi agenti ereditano i geni dei campioni della palestra (intelligenza
     condivisa). Il totale a rischio non supera mai il tetto di capitale scelto.

Sicurezza soldi veri: tetto di capitale, stop-perdita giornaliero automatico,
tasto di emergenza. Lo stato è salvato su disco → adatto al 24/7.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import threading
import time
from collections import deque
from typing import Any, Dict, Optional

from . import config as cfgmod
from . import statestore
from .broker import LiveBroker
from .colony import Colony
from .livefeed import MultiFeed
from .permits import PermitCenter
from .swarm import TradingSwarm

STATE_PATH = os.path.join(cfgmod.DATA_DIR, "state.json")


class Engine:
    def __init__(self) -> None:
        self.cfg = cfgmod.load()
        self.lock = threading.RLock()
        self._stop = False
        self.paused = False

        self.events: deque = deque(maxlen=120)
        self.permits = PermitCenter()   # moduli di guadagno + richieste/permessi
        self.effective_mode = "demo"
        self.live_error = ""
        self.live_stopped_reason = ""

        self.day = _today()
        self.day_start_equity = 0.0

        self._pending_state: Optional[Dict[str, Any]] = None
        self._restored = False
        self._last_remote = 0.0   # ultimo backup su GitHub (se configurato)

        # feed prezzo reale su PIÙ cripto (è il bot a scegliere su quale operare)
        self.feed = MultiFeed(self.cfg["symbol"], poll_seconds=min(20, self.cfg["live_poll_seconds"]))
        self.feed.start()

        # palestra evolutiva (demo, veloce) = fonte dei genomi campione
        self.colony = self._new_colony()

        self._load_state()
        self.swarm: Optional[TradingSwarm] = None
        self._build_swarm()

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
            use_real=False,
        )

    def _can_go_live(self) -> bool:
        return bool(
            self.cfg["mode"] == "live"
            and self.cfg["live_enabled"]
            and self.cfg["acknowledged_risk"]
            and self.cfg["api_key"]
            and self.cfg["api_secret"]
        )

    # --------------------------------------------------------------- sciame
    def _build_swarm(self) -> None:
        want_live = self._can_go_live() and not self.live_stopped_reason
        broker = None
        if want_live:
            try:
                broker = LiveBroker(self.cfg["api_key"], self.cfg["api_secret"], self.cfg["symbol"])
                self.effective_mode = "live"
                self.live_error = ""
                self._log("💶 SOLDI VERI attivi su Kraken (" + self.cfg["symbol"] + ")")
            except Exception as e:
                broker = None
                self.effective_mode = "demo"
                self.live_error = f"chiavi non valide o Kraken irraggiungibile: {str(e)[:150]}"
                self._log("⚠️ Live non attivabile → resto in DEMO. " + self.live_error)
        else:
            self.effective_mode = "demo"

        self.swarm = TradingSwarm(
            feed=self.feed,
            start_capital=float(self.cfg["start_capital_eur"]),
            lab=self.colony,
            broker=broker,
            max_bots=int(self.cfg["max_bots"]),
            min_order_eur=float(self.cfg["min_order_eur"]),
            analysis_days=float(self.cfg["analysis_days"]),
            analysis_start=float(self.cfg.get("analysis_start", 0.0)),
            daily_target=float(self.cfg.get("daily_target_eur", 0.5)),
            day_seconds=max(60.0, float(self.cfg.get("day_minutes", 1440)) * 60.0),
            leverage=float(self.cfg.get("leverage", 1.0)),
            allow_short=bool(self.cfg.get("allow_short", False)),
            max_trade_pct=float(self.cfg.get("max_trade_pct", 25)),
            stop_loss_pct=float(self.cfg.get("stop_loss_pct", 8)),
            take_profit_pct=float(self.cfg.get("take_profit_pct", 16)),
        )
        if not self._restored and self._pending_state:
            self.swarm.load_state(self._pending_state)
            self._restored = True
        # memorizza l'inizio dell'analisi così il conto alla rovescia sopravvive ai riavvii
        if not self.cfg.get("analysis_start"):
            self.cfg = cfgmod.save({"analysis_start": self.swarm.analysis_start})

    def _ensure_swarm(self) -> None:
        want_live = self._can_go_live() and not self.live_stopped_reason
        have_live = bool(self.swarm and self.swarm.live)
        if want_live != have_live:
            self._build_swarm()

    # ------------------------------------------------------------- persistenza
    def _load_state(self) -> None:
        st = None
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                st = json.load(f)
        except Exception:
            st = None
        # se in locale non c'è nulla (es. host riavviato da zero), prova il backup su GitHub
        if not st and statestore.enabled():
            try:
                st = statestore.load()
                if st:
                    self._log("💾 Stato recuperato dal backup su GitHub (il bot si era salvato da solo)")
            except Exception:
                st = None
        if not st:
            return
        self._pending_state = st.get("swarm")
        self.day = st.get("day", _today())
        self.day_start_equity = float(st.get("day_start_equity", 0.0))
        self.live_stopped_reason = st.get("live_stopped_reason", "")
        if st.get("permits"):
            self.permits.load_state(st["permits"])

    def _save_state(self) -> None:
        with self.lock:
            st = {
                "swarm": self.swarm.to_state() if self.swarm else None,
                "day": self.day,
                "day_start_equity": self.day_start_equity,
                "live_stopped_reason": self.live_stopped_reason,
                "permits": self.permits.to_state(),
            }
        try:
            os.makedirs(cfgmod.DATA_DIR, exist_ok=True)
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(st, f, indent=2)
        except Exception:
            pass
        # backup su GitHub (se configurato), a intervalli, così sopravvive ai riavvii dell'host.
        # Salva SOLO lo stato dei bot: nessuna chiave API finisce mai qui.
        if statestore.enabled():
            try:
                every = max(60.0, float(os.environ.get("STATE_BACKUP_SECONDS", "180")))
            except (TypeError, ValueError):
                every = 180.0
            now = time.time()
            if now - self._last_remote >= every:
                self._last_remote = now
                try:
                    statestore.save(st)
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
                    self._swarm_step()
            except Exception as e:
                self._log("errore sciame: " + str(e)[:140])
            time.sleep(max(5, int(self.cfg["live_poll_seconds"])))

    def _swarm_step(self) -> None:
        with self.lock:
            self._ensure_swarm()
            if self.swarm is None:
                return
            equity = self.swarm.total_equity()

            today = _today()
            if today != self.day or self.day_start_equity <= 0:
                self.day = today
                self.day_start_equity = equity

            if self.effective_mode == "live":
                # limite duro = il capitale: se i soldi si esauriscono, ferma tutto.
                # (lo stop-loss tattico lo gestisce l'IA per ogni bot; questo è solo il fondo)
                floor = max(float(self.cfg["min_order_eur"]), self.swarm.start_capital * 0.05)
                if equity <= floor:
                    self._do_kill("capitale esaurito (perdita entro il limite di €%.0f)" % self.swarm.start_capital)
                    return

            self.swarm.step()

    # ---------------------------------------------------------------- comandi
    def apply_settings(self, update: Dict[str, Any]) -> Dict[str, Any]:
        with self.lock:
            old_symbol = self.cfg["symbol"]
            self.cfg = cfgmod.save(update)
            if update.get("live_enabled"):
                self.live_stopped_reason = ""
            if self.cfg["symbol"] != old_symbol:
                self.feed.stop()
                self.feed = MultiFeed(self.cfg["symbol"], poll_seconds=min(20, self.cfg["live_poll_seconds"]))
                self.feed.start()
                self.colony = self._new_colony()
            self._build_swarm()
            self._log("⚙️ Impostazioni aggiornate — modalità: " + self.effective_mode.upper())
        return cfgmod.public_view(self.cfg)

    def _do_kill(self, reason: str) -> None:
        try:
            if self.swarm:
                self.swarm.liquidate()
        except Exception:
            pass
        self.live_stopped_reason = reason
        self.cfg = cfgmod.save({"live_enabled": False})
        self._build_swarm()
        self._log("🛑 EMERGENZA: " + reason + " — trading reale fermato, posizione chiusa.")

    def kill_switch(self) -> None:
        with self.lock:
            self._do_kill("tasto di emergenza premuto")

    def set_pause(self, value: bool) -> None:
        self.paused = value
        self._log("⏸️ In pausa" if value else "▶️ Ripreso")

    def skip_analysis(self) -> None:
        with self.lock:
            if self.swarm:
                self.swarm.skip_analysis()
                self.cfg = cfgmod.save({"analysis_start": self.swarm.analysis_start})

    def reset_lab(self) -> None:
        with self.lock:
            self.colony = self._new_colony()
            self._log("↻ Palestra riavviata da zero")

    # --- moduli di guadagno e permessi ---------------------------------
    def enable_module(self, mid: str) -> Dict[str, Any]:
        with self.lock:
            return self.permits.request_enable(mid)

    def approve_request(self, rid: int) -> Dict[str, Any]:
        with self.lock:
            return self.permits.approve(rid)

    def deny_request(self, rid: int) -> Dict[str, Any]:
        with self.lock:
            return self.permits.deny(rid)

    # ----------------------------------------------------------------- stato
    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            sw = self.swarm.snapshot() if self.swarm else {}
            equity = sw.get("total_equity", 0.0)
            pnl = equity - self.day_start_equity if self.day_start_equity else 0.0
            lab = self.colony.snapshot()
            return {
                "config": cfgmod.public_view(self.cfg),
                "paused": self.paused,
                "effective_mode": self.effective_mode,
                "price": round(self.feed.price(), 2),
                "price_is_real": self.feed.is_real,
                "feed_error": self.feed.last_error,
                "live_error": self.live_error,
                "live_stopped_reason": self.live_stopped_reason,
                "day_start_equity": round(self.day_start_equity, 2),
                "pnl_today": round(pnl, 2),
                "swarm": sw,
                "lab": {
                    "population": lab["population"],
                    "best_generation": lab["best_generation"],
                    "births": lab["births"],
                    "deaths": lab["deaths"],
                    "champion": self.colony.best_genome().to_dict(),
                },
                "permits": self.permits.snapshot(),
                "events": list(self.events)[:16],
            }

    def shutdown(self) -> None:
        self._stop = True
        self._save_state()


def _today() -> str:
    return _dt.date.today().isoformat()
