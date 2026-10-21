"""Candele da 1 ora di Binance dalla quotazione (anche monete tolte dopo), in formato compatto .npy:
colonne t(ms), o, h, l, c, quote volume."""
import json, os, sys, time, urllib.request
import numpy as np
from concurrent.futures import ThreadPoolExecutor
OUT = sys.argv[1]
COINS = """TRUMP PNUT NEIRO BOME PEOPLE TURBO NOT ACT VIRTUAL PENGU MOVE USUAL BERA KAITO IP LAYER S OM VEN NPXS HNT JASMY CFX AR GMT MASK LUNC MEME W ETHFI AEVO PENDLE RAY BNX ALPACA COTI CHR CTSI KNC BAND NKN SXP WIN DENT STORM TFUEL MTL OGN XVS FIS LINA REEF""".split()
START = 1500000000000
STEP = 3600_000

def get(url):
    for a in range(5):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 400:
                return None
            time.sleep(2 * (a + 1))
        except Exception:
            time.sleep(2 * (a + 1))
    return None

def one(c):
    path = f"{OUT}/{c}.npy"
    if os.path.exists(path):
        return c, -1
    rows, t = [], START
    while True:
        d = get(f"https://data-api.binance.vision/api/v3/klines?symbol={c}USDT&interval=1h&limit=1000&startTime={t}")
        if not d:
            break
        rows += [[x[0], float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[7])] for x in d]
        t = d[-1][0] + STEP
        if len(d) < 1000:
            break
    if rows:
        np.save(path, np.array(rows, dtype=np.float64))
    return c, len(rows)

with ThreadPoolExecutor(6) as ex:
    for c, n in ex.map(one, COINS):
        print(c, n, flush=True)
print("fatto", flush=True)
