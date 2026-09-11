"""Avvio del MOTORE VIDEO compatibile col vecchio comando `python3 server.py`.

Render, sul servizio esistente, potrebbe ancora usare lo start command vecchio
(`python3 server.py --host 0.0.0.0`). Questo file fa partire lo STESSO motore
video (worker_app), così funziona sia col comando vecchio sia con quello nuovo
(gunicorn worker_app:app). Traffico bassissimo (pochi reel al giorno), quindi il
server integrato di Flask basta e avanza.
"""
import argparse
import os

from worker_app import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, threaded=True)
