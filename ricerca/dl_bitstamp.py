"""Bitcoin da Bitstamp, candele da 1 ora dal 2011 (serve a «Bitcoin sopra la sua media»)."""
import json, sys, time, urllib.request
import numpy as np
OUT = sys.argv[1]

def get(url):
    for a in range(6):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(3 * (a + 1))
    return None

# Bitstamp BTC/USD: 1000 candele a richiesta
rows, start = [], 1314835200   # 1/9/2011
while True:
    d = get(f"https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=3600&limit=1000&start={start}")
    o = ((d or {}).get("data") or {}).get("ohlc") or []
    if not o:
        break
    rows += [[int(x["timestamp"]) * 1000, float(x["open"]), float(x["high"]), float(x["low"]), float(x["close"]),
              float(x["volume"]) * float(x["close"])] for x in o]
    nxt = int(o[-1]["timestamp"]) + 3600
    if nxt <= start or len(o) < 1000:
        break
    start = nxt
    time.sleep(0.3)
np.save(f"{OUT}/BTC_bitstamp.npy", np.array(rows))
print("bitstamp BTC", len(rows), flush=True)
print("fatto", flush=True)
