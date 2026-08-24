"""Moduli di guadagno + casella Richieste & Permessi (l'IA chiede, tu decidi).

Onestà prima di tutto:
- L'unico modulo che guadagna DAVVERO è il trading cripto (lo sciame di bot).
- Gli altri moduli sono PREDISPOSTI ma non generano guadagni finti: richiedono una
  tua approvazione e un'integrazione reale (e legale).
- Nessuna azione che tocchi account/soldi/credenziali parte senza il tuo OK: quando
  serve un accesso, l'IA lo CHIEDE qui e tu Approvi o Rifiuti.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

# Elenco dei moduli. "stato": attivo | proposto | bloccato | approvato
DEFAULT_MODULES: List[Dict[str, Any]] = [
    {
        "id": "crypto", "nome": "Trading di criptovalute", "stato": "attivo", "access": False,
        "desc": "L'unico modulo che opera davvero: lo sciame di bot su Kraken (demo o soldi veri).",
    },
    {
        "id": "contenuti", "nome": "Contenuti da pubblicare", "stato": "proposto", "access": True,
        "desc": "L'IA PREPARA testi/idee; li pubblichi TU dopo averli letti. Non pubblica al posto tuo.",
        "access_desc": "accesso per pubblicare le bozze sui tuoi profili",
    },
    {
        "id": "affiliazioni", "nome": "Affiliazioni / referral", "stato": "proposto", "access": True,
        "desc": "L'IA propone contenuti coi tuoi link di affiliazione; li approvi e pubblichi tu.",
        "access_desc": "i tuoi link di affiliazione",
    },
    {
        "id": "lavoretti", "nome": "Lavoretti online (freelance / microtask)", "stato": "bloccato", "access": True,
        "desc": ("Non disponibile: far operare in automatico account freelance o di sondaggi viola le "
                 "loro regole (rischio ban) e attira truffe. Servirebbe un'integrazione legale, la tua "
                 "approvazione e la tua supervisione."),
    },
]


class PermitCenter:
    def __init__(self) -> None:
        self.modules: List[Dict[str, Any]] = [dict(m) for m in DEFAULT_MODULES]
        self.requests: List[Dict[str, Any]] = []
        self._next_id = 1
        self.events: List[str] = []

    # --- moduli ----------------------------------------------------------
    def _module(self, mid: str) -> Optional[Dict[str, Any]]:
        return next((m for m in self.modules if m["id"] == mid), None)

    def request_enable(self, mid: str) -> Dict[str, Any]:
        """L'utente chiede di attivare un modulo → l'IA apre una richiesta di permesso."""
        m = self._module(mid)
        if not m:
            return {"ok": False, "reason": "modulo sconosciuto"}
        if m["stato"] == "attivo":
            return {"ok": False, "reason": "già attivo"}
        if m["stato"] == "bloccato":
            return {"ok": False, "reason": "modulo non disponibile per motivi di sicurezza"}
        # evita doppioni
        if any(r["modulo"] == mid and r["stato"] == "in_attesa" for r in self.requests):
            return {"ok": False, "reason": "richiesta già in attesa"}
        if m.get("access"):
            titolo = f"Il modulo «{m['nome']}» chiede un accesso"
            dettaglio = f"Per funzionare vorrebbe: {m.get('access_desc', 'un accesso')}. Approvi?"
        else:
            titolo = f"Attivare il modulo «{m['nome']}»?"
            dettaglio = "Il modulo verrà segnato come approvato (serve poi un'integrazione reale)."
        req = {
            "id": self._next_id, "tipo": "accesso" if m.get("access") else "modulo",
            "modulo": mid, "titolo": titolo, "dettaglio": dettaglio,
            "stato": "in_attesa", "t": time.strftime("%d/%m %H:%M"),
        }
        self._next_id += 1
        self.requests.insert(0, req)
        self.events.insert(0, f"🙋 L'IA ha chiesto il permesso: {titolo}")
        return {"ok": True, "request": req}

    # --- richieste -------------------------------------------------------
    def _request(self, rid: int) -> Optional[Dict[str, Any]]:
        return next((r for r in self.requests if r["id"] == rid), None)

    def approve(self, rid: int) -> Dict[str, Any]:
        r = self._request(rid)
        if not r or r["stato"] != "in_attesa":
            return {"ok": False}
        r["stato"] = "approvato"
        m = self._module(r["modulo"])
        if m:
            m["stato"] = "approvato"
            m["nota"] = "approvato dall'utente — in attesa di integrazione reale (nessun guadagno finto)"
        self.events.insert(0, f"✅ Hai APPROVATO: {r['titolo']}")
        return {"ok": True}

    def deny(self, rid: int) -> Dict[str, Any]:
        r = self._request(rid)
        if not r or r["stato"] != "in_attesa":
            return {"ok": False}
        r["stato"] = "rifiutato"
        self.events.insert(0, f"⛔ Hai RIFIUTATO: {r['titolo']}")
        return {"ok": True}

    # --- stato / persistenza --------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        return {
            "modules": self.modules,
            "requests": self.requests[:20],
            "pending": sum(1 for r in self.requests if r["stato"] == "in_attesa"),
            "events": self.events[:10],
        }

    def to_state(self) -> Dict[str, Any]:
        return {"modules": self.modules, "requests": self.requests, "next_id": self._next_id, "events": self.events[:20]}

    def load_state(self, st: Dict[str, Any]) -> None:
        try:
            if st.get("modules"):
                self.modules = st["modules"]
            self.requests = st.get("requests", [])
            self._next_id = int(st.get("next_id", 1))
            self.events = st.get("events", [])
        except Exception:
            pass
