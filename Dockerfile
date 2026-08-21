# AgentColony — immagine per farlo girare 24/7 (es. su un VPS)
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir ccxt anthropic

COPY . .

# I dati (config, chiavi, stato) vivono in un volume, NON nell'immagine
VOLUME ["/app/data"]
EXPOSE 8000

# Proteggi con un token se esposto in rete:  -e AGENTCOLONY_TOKEN=...
# Chiavi Kraken via env (consigliato):        -e KRAKEN_API_KEY=... -e KRAKEN_API_SECRET=...
CMD ["python3", "server.py", "--host", "0.0.0.0", "--port", "8000"]
