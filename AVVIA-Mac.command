#!/bin/bash
# AgentColony - doppio click per avviare (macOS / Linux)
cd "$(dirname "$0")"
echo "============================================================"
echo "   AgentColony - avvio in corso..."
echo "   Lascia questa finestra APERTA mentre lo usi."
echo "   Il browser si aprira' da solo tra pochi secondi."
echo "============================================================"
echo

# --- trova Python 3 ---
PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "[X] Python 3 non trovato."
  echo "    Installalo da https://python.org e riprova."
  echo
  read -n1 -r -p "Premi un tasto per uscire..."
  exit 1
fi

# --- installa ccxt per i prezzi reali (se manca); la demo funziona comunque ---
"$PY" -m pip install --quiet ccxt >/dev/null 2>&1

# --- avvia il sito e apre il browser da solo ---
"$PY" server.py --open

echo
read -n1 -r -p "Il programma si e' chiuso. Premi un tasto per uscire..."
