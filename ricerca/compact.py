"""Riassunto PICCOLO dei risultati di un pezzo (100.000 tecniche), da rimandare indietro.
  table [S, 4 universi (prime 3/5/10/20), 6]  n, R medio, Sharpe di scoperta e conferma (float16)
  py    [S, 4]                                anni positivi 2018-2021 (int8)
  idx   [K, 2]   (tecnica, universo) che passano un filtro largo
  rows  [K, 28]  tutti i numeri di quelle (anche l'esame, che si guarda solo alla fine)
uso: python compact.py OUT_DIR PEZZO"""
import sys

import numpy as np

import stats as St

K = {k: i for i, k in enumerate(St.K_NAMES)}
X = St.load_summary(sys.argv[1]).astype(np.float64)[:, :4]
part = sys.argv[2]


def per(p):
    n = X[..., K[f"{p}_n"]]
    with np.errstate(divide="ignore", invalid="ignore"):
        mean = np.where(n > 0, X[..., K[f"{p}_s1"]] / np.maximum(n, 1), np.nan)
    return n, mean, X[..., K[f"{p}_sharpe"]]


nD, mD, sD = per("scoperta")
nV, mV, sV = per("conferma")
py = (X[..., [K[f"y{y}"] for y in (2018, 2019, 2020, 2021)]] > 0).sum(-1).astype(np.int8)
table = np.stack([nD, mD, sD, nV, mV, sV], -1).astype(np.float16)
loose = (nD >= 100) & (nV >= 40) & (sD >= 0.8) & (sV >= 0.8) & (mD >= 0.1) & (mV >= 0.1) & (py >= 3)
idx = np.argwhere(loose)
rows = X[idx[:, 0], idx[:, 1]].astype(np.float32)
np.savez_compressed(f"res_{part}.npz", table=table, py=py, idx=idx.astype(np.int32), rows=rows)
print(f"pezzo {part}: {len(X)} tecniche, {len(idx)} combinazioni nel filtro largo")
