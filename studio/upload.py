"""Carica nel magazzino (IA-/reels) i video finiti, IN ORDINE e SENZA BUCHI.

Il bot del sito pubblica il primo video non ancora pubblicato in ordine di nome: se mancasse
un video intermedio, ne pubblicherebbe uno successivo. Quindi carico solo la sequenza continua
(001, 002, ..., 010, 010a, 011, ...) fino al primo video non ancora pronto.
"""
import json
import os
import shutil
import subprocess
import sys
import time

STUDIO = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STUDIO, "work", "out")
REPO = os.path.dirname(STUDIO)
REELS = os.path.join(REPO, "reels")
sys.path.insert(0, STUDIO)
import produce as P  # noqa: E402


def finished(k):
    name = P.out_name(k)
    for cand in (name, f"{int(str(k).lstrip('p')):02d}.mp4" if not str(k).startswith("p") else name):
        f = os.path.join(OUT, cand)
        if os.path.exists(f) and os.path.getsize(f) > 100000:
            return f
    return None


def main(limit=60):
    pl = P.plan()
    keys = sorted(pl, key=P.order_key)
    added = []
    for k in keys:
        dst = os.path.join(REELS, P.out_name(k))
        if os.path.exists(dst):
            continue
        src = finished(k)
        if not src:
            print("mi fermo prima di", P.out_name(k), "(non ancora pronto)")
            break
        shutil.copy(src, dst)
        added.append(P.out_name(k))
        if len(added) >= limit:
            break
    if not added:
        print("niente di nuovo")
        return
    subprocess.run(["git", "-C", REPO, "add"] + [os.path.join("reels", a) for a in added], check=True)
    msg = (f"Reel {added[0][:-4]}-{added[-1][:-4]} ({len(added)} video)\n\n"
           "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
           "Claude-Session: https://claude.ai/code/session_01Aj2u4BUEdW7mRXgWBwGYgu")
    subprocess.run(["git", "-C", REPO, "commit", "-q", "-m", msg], check=True)
    for i in range(4):
        if subprocess.run(["timeout", "900", "git", "-C", REPO, "push", "-q", "origin", "main"]).returncode == 0:
            break
        time.sleep(2 ** (i + 1))
    print("caricati:", " ".join(a[:-4] for a in added))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
