"""Motore di segnali: tecnica "TREND + RITRACCIAMENTO + CONFERMA".

Decide SOLO se entrare LONG o SHORT ORA, su dati REALI multi-timeframe.
Regola d'oro: se manca anche un solo step → NESSUN SEGNALE (non si entra).

STEP 1 — TREND (4H):   EMA50 vs EMA200
STEP 2 — RITRACCIAMENTO (1H): il prezzo è tornato vicino alla EMA20 (non insegue chi pompa)
STEP 3 — CONFERMA (15M):      engulfing OPPURE RSI che esce da <30 (long) / >70 (short)
STEP 4 — VOLUME (15M):        volume della candela di conferma > 130% della media a 20

Le candele sono liste OHLCV: [timestamp, open, high, low, close, volume].
"""
from __future__ import annotations

from typing import List, Optional

from . import indicators as ind

# profilo "più attivo" (DEMO, per imparare più in fretta): filtri più larghi = più
# operazioni. NON cambia quanto punta, solo QUANTO SPESSO entra. Valori più stretti
# (0.015 / 1.30) = meno operazioni ma più selettive.
_PULLBACK_BAND = 0.035   # "vicino" alla EMA20 1H = entro ±3.5% (più largo = entra più spesso)
_VOL_MULT = 1.05         # volume di conferma richiesto: > 105% della media a 20 (meno restrittivo)
_RSI_LOW, _RSI_HIGH = 30.0, 70.0


def _closes(candles: List[list]) -> List[float]:
    return [c[4] for c in candles]


def _engulfing(closed: List[list], side: str) -> bool:
    """Engulfing sulle ultime due candele CHIUSE (o=open, c=close)."""
    if len(closed) < 2:
        return False
    po, pc = closed[-2][1], closed[-2][4]
    o, c = closed[-1][1], closed[-1][4]
    if side == "long":   # rialzista: rossa poi verde che "ingloba" il corpo
        return c > o and pc < po and c >= po and o <= pc
    else:                # ribassista
        return c < o and pc > po and c <= po and o >= pc


def _rsi_exit(closed: List[list], side: str) -> bool:
    """RSI 15M che ESCE dalla zona estrema (da <30 in su per long, da >70 in giù per short)."""
    closes = _closes(closed)
    if len(closes) < 16:
        return False
    r_now = ind.rsi(closes, 14)
    r_prev = ind.rsi(closes[:-1], 14)
    if r_now is None or r_prev is None:
        return False
    if side == "long":
        return r_prev < _RSI_LOW <= r_now
    else:
        return r_prev > _RSI_HIGH >= r_now


def trend_flipped(feed, symbol: str, side: int) -> bool:
    """True se il trend di fondo (4H, EMA50 vs EMA200) si è girato CONTRO la posizione.
    Serve per uscire quando l'onda che avevi preso è finita, non a ogni sussulto."""
    try:
        c4 = feed.ohlcv(symbol, "4h")
    except Exception:
        return False
    if not c4:
        return False
    closes4 = _closes(c4)
    e50 = ind.ema(closes4, 50)
    e200 = ind.ema(closes4, 200)
    if e50 is None or e200 is None:
        return False
    return (e50 < e200) if side > 0 else (e50 > e200)


def evaluate(feed, symbol: str) -> Optional[dict]:
    """Ritorna {"side","price","reason"} se TUTTI gli step passano, altrimenti None."""
    try:
        c4 = feed.ohlcv(symbol, "4h")
        c1 = feed.ohlcv(symbol, "1h")
        c15 = feed.ohlcv(symbol, "15m")
    except Exception:
        return None
    if not c4 or not c1 or not c15:
        return None

    # STEP 1 — TREND su 4H
    closes4 = _closes(c4)
    e50 = ind.ema(closes4, 50)
    e200 = ind.ema(closes4, 200)
    if e50 is None or e200 is None:
        return None
    if e50 > e200:
        trend = "long"
    elif e50 < e200:
        trend = "short"
    else:
        return None

    # STEP 2 — RITRACCIAMENTO su 1H (prezzo rientrato vicino alla EMA20)
    closes1 = _closes(c1)
    e20 = ind.ema(closes1, 20)
    if e20 is None or e20 <= 0:
        return None
    price = closes1[-1]
    if abs(price - e20) / e20 > _PULLBACK_BAND:
        return None   # troppo lontano dalla media: sta pompando, non inseguire

    # STEP 3 — CONFERMA su 15M (usa le candele CHIUSE, non quella in formazione)
    closed = c15[:-1] if len(c15) >= 2 else c15
    if len(closed) < 21:
        return None
    if not (_engulfing(closed, trend) or _rsi_exit(closed, trend)):
        return None

    # STEP 4 — FILTRO VOLUME (15M): candela di conferma > 130% della media a 20
    vols = [c[5] for c in closed]
    avg20 = sum(vols[-21:-1]) / 20.0 if len(vols) >= 21 else 0.0
    if avg20 <= 0 or vols[-1] < _VOL_MULT * avg20:
        return None

    price_now = closed[-1][4]
    verso = "EMA50>EMA200" if trend == "long" else "EMA50<EMA200"
    reason = (f"trend {trend.upper()} 4H ({verso}) · ritracciamento su EMA20 1H · "
              f"conferma 15M · volume {vols[-1] / avg20 * 100:.0f}% della media")
    return {"side": trend, "price": price_now, "reason": reason}
