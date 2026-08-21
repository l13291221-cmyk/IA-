"""Configurazione e gestione SICURA delle chiavi API.

- Tutto viene salvato in `data/config.json`, che è nel .gitignore → non finisce
  mai su GitHub.
- Le chiavi possono anche arrivare da variabili d'ambiente (consigliato su un
  server/VPS): KRAKEN_API_KEY, KRAKEN_API_SECRET. Se presenti, hanno priorità.
- Il file viene salvato con permessi 600 (solo il tuo utente può leggerlo).
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict

_LOCK = threading.Lock()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

DEFAULTS: Dict[str, Any] = {
    "mode": "demo",                 # "demo" (soldi finti) | "live" (soldi veri)
    "symbol": "BTC/EUR",
    "exchange": "kraken",
    # chiavi API (soldi veri) — meglio usare le variabili d'ambiente
    "api_key": "",
    "api_secret": "",
    # limiti di rischio (soldi veri)
    "live_capital_eur": 20.0,       # capitale massimo che il bot può impiegare
    "per_order_eur": 10.0,          # importo massimo per singolo ordine
    "daily_loss_limit_eur": 5.0,    # se perde più di così in un giorno → STOP automatico
    "take_profit": 0.06,            # obiettivo di uscita del campione (+6%)
    "stop_loss": 0.04,              # stop di protezione (-4%)
    # palestra evolutiva (demo)
    "lab_population": 12,
    "lab_tps": 6.0,                 # velocità di evoluzione (tick/sec)
    "lab_vol": 0.022,
    "lab_regime": "meanrev",
    # motore live
    "live_poll_seconds": 30,        # ogni quanto controlla il prezzo reale
    "live_enabled": False,          # interruttore generale del trading reale
    "acknowledged_risk": False,     # l'utente ha accettato i rischi
}


def _ensure_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load() -> Dict[str, Any]:
    with _LOCK:
        cfg = dict(DEFAULTS)
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except FileNotFoundError:
            pass
        except Exception:
            pass
        # le variabili d'ambiente hanno la priorità sulle chiavi salvate
        cfg["api_key"] = os.environ.get("KRAKEN_API_KEY", cfg.get("api_key", ""))
        cfg["api_secret"] = os.environ.get("KRAKEN_API_SECRET", cfg.get("api_secret", ""))
        return cfg


def save(update: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiorna e salva solo i campi noti. Non salva le chiavi se arrivano da env."""
    with _LOCK:
        _ensure_dir()
        cfg = dict(DEFAULTS)
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except FileNotFoundError:
            pass
        except Exception:
            pass
        for k, v in update.items():
            if k in DEFAULTS:
                cfg[k] = v
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        try:
            os.chmod(CONFIG_PATH, 0o600)  # solo il proprietario può leggere
        except Exception:
            pass
        # rispecchia le env anche nel valore ritornato
        cfg["api_key"] = os.environ.get("KRAKEN_API_KEY", cfg.get("api_key", ""))
        cfg["api_secret"] = os.environ.get("KRAKEN_API_SECRET", cfg.get("api_secret", ""))
        return cfg


def public_view(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Versione della config sicura da mandare al browser: nasconde le chiavi."""
    safe = dict(cfg)
    key = cfg.get("api_key", "")
    secret = cfg.get("api_secret", "")
    safe["api_key"] = (key[:4] + "…" + key[-4:]) if len(key) > 10 else ("impostata" if key else "")
    safe["api_secret"] = "impostato" if secret else ""
    safe["has_keys"] = bool(key and secret)
    safe["keys_from_env"] = bool(os.environ.get("KRAKEN_API_KEY"))
    return safe
