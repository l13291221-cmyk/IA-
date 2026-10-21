"""Tassi di finanziamento dei perpetui Binance (ogni 8 ore) da data.binance.vision, dal 2019-09.
Salva fund/<MONETA>.npy con colonne [t ms, tasso]."""
import io, os, sys, time, urllib.request, zipfile, csv
import numpy as np
from concurrent.futures import ThreadPoolExecutor
OUT = sys.argv[1]
COINS = sys.argv[2].split(",")

def get(url):
    for a in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (a + 1))
        except Exception:
            time.sleep(2 * (a + 1))
    return None

def one(c):
    path = f"{OUT}/{c}.npy"
    if os.path.exists(path):
        return c, -1
    rows = []
    for y in range(2019, 2027):
        for m in range(1, 13):
            if (y, m) < (2019, 9) or (y, m) > (2026, 9):
                continue
            z = get(f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{c}USDT/{c}USDT-fundingRate-{y}-{m:02d}.zip")
            if not z:
                continue
            with zipfile.ZipFile(io.BytesIO(z)) as zf:
                for name in zf.namelist():
                    for row in csv.reader(io.TextIOWrapper(zf.open(name))):
                        try:
                            rows.append((int(row[0]), float(row[2])))
                        except (ValueError, IndexError):
                            pass
    if rows:
        np.save(path, np.array(sorted(set(rows)), dtype=np.float64))
    return c, len(rows)

with ThreadPoolExecutor(8) as ex:
    for c, n in ex.map(one, COINS):
        print(c, n, flush=True)
print("fatto", flush=True)
