"""Il "cervello che impara": memoria CONDIVISA di cosa fa vincere e cosa fa perdere.

Per ogni operazione CHIUSA, il bot scrive qui il TIPO di mossa (direzione + cripto)
e com'è andata (vinto/perso, quanto in %). Prima di aprire una nuova operazione
ri-legge questa memoria: se quel tipo di mossa in passato ha SISTEMATICAMENTE perso,
la evita (ogni tanto la riprova, così se il mercato cambia se ne accorge).

La memoria è UNA SOLA e CONDIVISA fra tutti i bot, si tramanda ai figli, e viene
salvata su disco/GitHub insieme allo stato: quello che impara in DEMO NON si perde
quando passi ai soldi veri. È, letteralmente, il suo cervello.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List


class Brain:
    def __init__(self, min_samples: int = 8, avoid_winrate: float = 0.35, explore: float = 0.10):
        self.stats: Dict[str, Dict[str, float]] = {}   # "LONG·BTC" -> {w,l,pnl,n}
        self.min_samples = min_samples      # quante prove servono prima di dare un giudizio
        self.avoid_winrate = avoid_winrate  # sotto questo winrate (e in perdita) → evita
        self.explore = explore              # ogni tanto riprova anche i "cattivi" (il mercato cambia)
        self._rng = random.Random()

    @staticmethod
    def key(side: int, asset: str) -> str:
        return f"{'LONG' if side > 0 else 'SHORT'}·{asset}"

    def record(self, side: int, asset: str, win: bool, pnl: float) -> None:
        s = self.stats.setdefault(self.key(side, asset), {"w": 0, "l": 0, "pnl": 0.0, "n": 0})
        s["n"] += 1
        s["pnl"] += float(pnl)
        s["w" if win else "l"] += 1

    def should_take(self, side: int, asset: str) -> bool:
        """True = si può fare. False = tipo di mossa che storicamente perde → salta."""
        s = self.stats.get(self.key(side, asset))
        if not s or s["n"] < self.min_samples:
            return True                                  # pochi dati: deve provare per imparare
        winrate = s["w"] / s["n"]
        avg_pnl = s["pnl"] / s["n"]
        if winrate < self.avoid_winrate and avg_pnl < 0:
            return self._rng.random() < self.explore     # di solito evita, ogni tanto riprova
        return True

    def lessons(self, limit: int = 8) -> List[dict]:
        """Le "lezioni" imparate, per mostrarle sul sito."""
        out = []
        for k, s in self.stats.items():
            if s["n"] < 3:
                continue
            wr = round(100 * s["w"] / s["n"])
            avg = s["pnl"] / s["n"]
            verdict = "buono ✅" if (wr >= 50 and avg > 0) else \
                      ("da evitare ⛔" if (wr < self.avoid_winrate * 100 and avg < 0) else "così così")
            out.append({"setup": k, "n": s["n"], "winrate": wr, "avg_pnl": round(avg, 2), "verdict": verdict})
        out.sort(key=lambda x: (x["winrate"], x["avg_pnl"]), reverse=True)
        return out[:limit]

    def to_state(self) -> Dict[str, Any]:
        return {"stats": self.stats}

    def load_state(self, st: Dict[str, Any]) -> None:
        try:
            self.stats = {k: {"w": int(v["w"]), "l": int(v["l"]), "pnl": float(v["pnl"]), "n": int(v["n"])}
                          for k, v in (st.get("stats") or {}).items()}
        except Exception:
            self.stats = {}
