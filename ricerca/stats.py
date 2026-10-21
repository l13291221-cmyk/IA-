"""Numeri di ogni tecnica per periodo e universo, dai cumuli mensili di run.py.

Periodi (mesi da 2017-08 = 0):
  scoperta    2017-08 → 2021-12   (qui si sceglie)
  conferma    2022-01 → 2023-12   (si guarda solo per le migliori della scoperta)
  esame       2024-01 → oggi      (si guarda UNA volta alla fine, per poche tecniche)
"""
import glob

import numpy as np

UNIV = {3: 1, 5: 2, 10: 3, 20: 4, 40: 5, 999: 6}     # top N → quanti gruppi sommare
PER = {"scoperta": (0, 53), "conferma": (53, 77), "esame": (77, 112)}
YEARS = {y: (max(0, (y - 2017) * 12 - 7), min(112, (y - 2017) * 12 + 5)) for y in range(2017, 2027)}


def load(out):
    parts = sorted(glob.glob(f"{out}/acc_*.npy"))
    return np.concatenate([np.load(p) for p in parts]).astype(np.float64)


def by_universe(A):
    """[S, 6 universi, mesi, statistiche] con i gruppi sommati (prime 3, 5, 10, 20, 40, tutte)."""
    return np.cumsum(A, axis=1)


def metrics(U, a, b):
    """U = [S, universi, mesi, stat]; mesi [a, b). Ritorna dict di array [S, universi]."""
    x = U[:, :, a:b]
    n = x[..., 0].sum(-1)
    s1 = x[..., 1].sum(-1)
    s2 = x[..., 2].sum(-1)
    w = x[..., 3].sum(-1)
    raw = x[..., 4].sum(-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        mean = s1 / n
        sd = np.sqrt(np.maximum(s2 / n - mean ** 2, 1e-12))
        t = mean / sd * np.sqrt(n)
        mon = x[..., 1]                                  # R di ogni mese (0 se nessuna operazione)
        ms = mon.std(-1)
        sharpe = mon.mean(-1) / np.where(ms > 0, ms, np.nan) * np.sqrt(12)
        win = w / n
    months = b - a
    return {"n": n, "mean": mean, "t": t, "sharpe": sharpe, "win": win, "rpm": s1 / months, "raw": raw / n,
            "pos_months": (mon > 0).sum(-1) / np.maximum(1, (x[..., 0] > 0).sum(-1))}


def years(U, years_list):
    """R tagliato per anno: [S, universi, anni]."""
    return np.stack([U[:, :, a:b, 1].sum(-1) for y, (a, b) in YEARS.items() if y in years_list], -1)


K_NAMES = [f"{p}_{m}" for p in ("scoperta", "conferma", "esame") for m in ("n", "s1", "s2", "w", "raw", "sharpe")] + \
    [f"y{y}" for y in range(2017, 2027)]


def summarize(A):
    """Da cumuli mensili [S, 6 gruppi, mesi, stat] a un riassunto compatto [S, 6 universi, 28]:
    per ogni periodo n, somma R, somma R², vinte, R vero, Sharpe mensile; poi R di ogni anno."""
    U = by_universe(A.astype(np.float64))
    out = []
    for p, (a, b) in PER.items():
        x = U[:, :, a:b]
        mon = x[..., 1]
        ms = mon.std(-1)
        with np.errstate(divide="ignore", invalid="ignore"):
            sh = mon.mean(-1) / np.where(ms > 0, ms, np.nan) * np.sqrt(12)
        out += [x[..., 0].sum(-1), x[..., 1].sum(-1), x[..., 2].sum(-1), x[..., 3].sum(-1), x[..., 4].sum(-1), sh]
    for y, (a, b) in YEARS.items():
        out.append(U[:, :, a:b, 1].sum(-1))
    return np.stack(out, -1).astype(np.float32)


def load_summary(out):
    parts = sorted(glob.glob(f"{out}/sum_*.npy"))
    return np.concatenate([np.load(p) for p in parts])
