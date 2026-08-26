"""Logica di decisione pura, condivisa da tutti.

Usata sia dagli agenti della palestra (demo) sia dal campione che opera sui soldi
veri: un'unica fonte di verità, così demo e reale si comportano identici.
"""
from __future__ import annotations

from typing import List

from . import indicators as ind
from .genome import Genome

BUY, SELL, HOLD = "COMPRA", "VENDI", "ATTENDI"


def decide(genome: Genome, series: List[float], price: float,
           in_position: bool, entry_price: float) -> str:
    fast = ind.sma(series, genome.fast_ma)
    slow = ind.sma(series, genome.slow_ma)
    r = ind.rsi(series, genome.rsi_period)
    if fast is None or slow is None or r is None:
        return HOLD

    if in_position:
        change = (price - entry_price) / entry_price if entry_price else 0.0
        if change >= genome.take_profit or change <= -genome.stop_loss:
            return SELL
        if genome.strategy == "trend" and fast < slow:
            return SELL
        if genome.strategy == "meanrev" and r >= genome.rsi_sell:
            return SELL
        return HOLD

    if genome.strategy == "trend":
        if fast > slow and r < genome.rsi_sell:
            return BUY
    else:  # meanrev
        if r < genome.rsi_buy:
            return BUY
    return HOLD


def signal(genome: Genome, series: List[float], price: float):
    """Che posizione APRIRE se siamo liquidi: 'long', 'short' o None.

    Regole per NON operare a vanvera (le commissioni mangiano i conti piccoli):
    - se il mercato è troppo PIATTO non si entra (non vale la commissione);
    - si chiede una CONFERMA di slancio, così non si "prende il coltello che cade"
      (ipervenduto ma ancora in caduta) né si insegue un rialzo già esaurito.
    (Usata in demo per supportare anche le operazioni al ribasso / con leva.)"""
    fast = ind.sma(series, genome.fast_ma)
    slow = ind.sma(series, genome.slow_ma)
    r = ind.rsi(series, genome.rsi_period)
    if fast is None or slow is None or r is None:
        return None
    vol = ind.volatility(series, 20) or 0.0
    if vol < 0.0012:            # mercato quasi fermo: meglio stare fuori (le fee lo dissanguano)
        return None
    mom = ind.momentum(series, 3) or 0.0   # micro-slancio delle ultime barre (conferma)
    if genome.strategy == "trend":
        if fast > slow and r < genome.rsi_sell and mom > 0:
            return "long"
        if fast < slow and r > genome.rsi_buy and mom < 0:
            return "short"
    else:  # meanrev: entra sull'eccesso SOLO quando ha iniziato a rientrare
        if r < genome.rsi_buy and mom > 0:
            return "long"
        if r > genome.rsi_sell and mom < 0:
            return "short"
    return None


def should_exit(genome: Genome, series: List[float], price: float, side: int, entry: float) -> bool:
    """True se chiudere la posizione (take-profit/stop-loss direzionale o segnale opposto)."""
    fast = ind.sma(series, genome.fast_ma)
    slow = ind.sma(series, genome.slow_ma)
    r = ind.rsi(series, genome.rsi_period)
    if fast is None or slow is None or r is None or not entry:
        return False
    change = (price - entry) / entry if side > 0 else (entry - price) / entry
    if change >= genome.take_profit or change <= -genome.stop_loss:
        return True
    if side > 0:  # long
        if genome.strategy == "trend" and fast < slow:
            return True
        if genome.strategy == "meanrev" and r >= genome.rsi_sell:
            return True
    else:  # short
        if genome.strategy == "trend" and fast > slow:
            return True
        if genome.strategy == "meanrev" and r <= genome.rsi_buy:
            return True
    return False
