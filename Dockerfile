# MOTORE VIDEO di VcriptoV — immagine per Render (se il servizio usa Docker).
FROM python:3.11-slim

WORKDIR /app

# Font belli per le schede (Liberation) — così i reel non usano il font di ripiego.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
# Avvia il motore video (crea i reel + tiene sveglia VcriptoV).
CMD gunicorn worker_app:app --timeout 150 --workers 1 --threads 2 --bind 0.0.0.0:$PORT
