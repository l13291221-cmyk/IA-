"""Cervello LLM OPZIONALE (Claude). Disattivato di default.

Se imposti ANTHROPIC_API_KEY e installi il pacchetto `anthropic`, la colonia può
chiedere a Claude di proporre i parametri di strategia del fondatore (la tua
"analisi iniziale del mercato"). Non viene chiamato a ogni tick: sarebbe costoso
e inutile. Serve solo a dare un punto di partenza "ragionato" invece che casuale.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


def llm_available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401

        return True
    except Exception:
        return False


def propose_genome(market_summary: str, model: str = "claude-opus-5") -> Optional[Dict[str, Any]]:
    """Chiede a Claude parametri di strategia prudenti. Ritorna un dict o None."""
    if not llm_available():
        return None
    try:
        import anthropic

        client = anthropic.Anthropic()
        schema = (
            'Rispondi SOLO con un oggetto JSON con questi campi: '
            '{"strategy":"trend"|"meanrev","fast_ma":int(3-15),"slow_ma":int(10-60),'
            '"rsi_period":int(6-24),"rsi_buy":float(15-45),"rsi_sell":float(55-85),'
            '"risk_fraction":float(0.2-1.0),"take_profit":float(0.02-0.15),'
            '"stop_loss":float(0.015-0.1),"thesis":"breve frase"}'
        )
        msg = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Sei uno stratega di trading quantitativo prudente. In base a questo "
                        "riassunto di mercato, proponi i parametri di partenza per un piccolo "
                        "bot di PAPER trading (soldi finti).\n\n"
                        f"Mercato: {market_summary}\n\n{schema}"
                    ),
                }
            ],
        )
        text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
    except Exception:
        return None
    return None
