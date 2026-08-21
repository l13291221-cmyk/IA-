"""Indicatori tecnici in puro Python (nessuna dipendenza)."""
from __future__ import annotations

from typing import Optional, Sequence


def sma(values: Sequence[float], n: int) -> Optional[float]:
    """Media mobile semplice sugli ultimi n valori."""
    if n <= 0 or len(values) < n:
        return None
    return sum(values[-n:]) / n


def rsi(values: Sequence[float], n: int = 14) -> Optional[float]:
    """Relative Strength Index (0-100) sugli ultimi n periodi."""
    if len(values) < n + 1:
        return None
    window = values[-(n + 1):]
    gains = 0.0
    losses = 0.0
    for i in range(1, len(window)):
        change = window[i] - window[i - 1]
        if change >= 0:
            gains += change
        else:
            losses -= change
    avg_gain = gains / n
    avg_loss = losses / n
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def momentum(values: Sequence[float], n: int) -> Optional[float]:
    """Variazione percentuale rispetto a n periodi fa."""
    if len(values) < n + 1:
        return None
    past = values[-(n + 1)]
    if past == 0:
        return None
    return (values[-1] - past) / past


def volatility(values: Sequence[float], n: int) -> Optional[float]:
    """Deviazione standard dei rendimenti sugli ultimi n periodi."""
    if len(values) < n + 1:
        return None
    window = values[-(n + 1):]
    rets = []
    for i in range(1, len(window)):
        if window[i - 1] != 0:
            rets.append((window[i] - window[i - 1]) / window[i - 1])
    if not rets:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / len(rets)
    return var ** 0.5
