"""Monta ogni parte appena tutte le sue immagini sono pronte (gira in parallelo alla generazione).

  python render_when_ready.py A B [FLAG]

Non si blocca su una parte in attesa: monta intanto le altre già pronte. Quando esiste il
file FLAG (generazione finita) monta anche le parti incomplete, usando l'immagine precedente
al posto di quelle mancanti.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import produce as P  # noqa: E402

a, b = int(sys.argv[1]), int(sys.argv[2])
flag = sys.argv[3] if len(sys.argv) > 3 else None


def needed(r, k):
    names = [P.key_img_name(k, i) for i, sc in enumerate(r["scenes"]) if sc.get("p") and not sc.get("img")]
    # anche le immagini riusate da altre parti (potrebbero essere ancora in generazione)
    names += [sc["img"].split(":")[0][:-6] for sc in r["scenes"] if sc.get("img")]
    return names


def done(k):
    n = int(str(k).lstrip("p"))
    alt = f"{n:02d}.mp4"
    return os.path.exists(os.path.join(P.OUT, P.out_name(k))) or (not str(k).startswith("p") and os.path.exists(os.path.join(P.OUT, alt)))


todo = [k for k in P.keys_in(P.plan(), a, b) if not done(k)]
while todo:
    pl = P.plan()
    finished = bool(flag and os.path.exists(flag))
    ready = [k for k in todo if k in pl and all(P.have(x) for x in needed(pl[k], k))]
    pick = ready[0] if ready else (todo[0] if finished else None)
    if pick is None:
        time.sleep(15)
        continue
    t0 = time.time()
    try:
        P.render_key(pl, pick)
        print(f"RENDERED {P.out_name(pick)} in {time.time() - t0:.0f}s", flush=True)
    except Exception as exc:
        print(f"ERROR {pick}: {exc}", flush=True)
    todo.remove(pick)
