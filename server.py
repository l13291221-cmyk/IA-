"""Avvio del MOTORE VIDEO — si auto-installa le librerie se mancano.

Render, su questo servizio, lancia `python3 server.py` ma a volte NON esegue il
build (`pip install`), quindi le librerie (Flask, ecc.) mancano → errore
"No module named 'flask'". Per essere a prova di tutto, qui prima di partire
CONTROLLO che le librerie ci siano e, se mancano, le installo io stesso. Così il
motore parte comunque, qualunque cosa faccia (o non faccia) il build di Render.
"""
import os
import subprocess
import sys


def _ensure_deps():
    """Se mancano le librerie del motore, le installo da requirements.txt nello
    STESSO Python che sta girando (così sono subito importabili)."""
    try:
        import flask  # noqa: F401
        import PIL  # noqa: F401
        import numpy  # noqa: F401
        import imageio  # noqa: F401
        return  # tutto già presente
    except Exception:
        pass
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    try:
        print("Installo le librerie del motore video…", flush=True)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir",
                               "-r", req])
        print("Librerie installate.", flush=True)
    except Exception as exc:
        print(f"Installazione librerie fallita: {exc}", flush=True)


_ensure_deps()

# NB: import DOPO l'installazione, così le librerie appena messe vengono trovate.
import argparse  # noqa: E402

from worker_app import app  # noqa: E402


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    args, _unknown = parser.parse_known_args()
    app.run(host=args.host, port=args.port, threaded=True)
