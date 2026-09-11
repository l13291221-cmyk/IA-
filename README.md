# Motore VIDEO di VcriptoV 🎬

Micro-servizio che crea **solo i reel (video)** per VcriptoV.

Esiste perché su Render free tier (512MB) montare un video con ffmpeg SUL sito
principale fa sforare la memoria. Qui gira su un'istanza dedicata: tutti i 512MB
liberi per il video, e il sito principale non tocca mai ffmpeg.

## Avvio su Render
- **Start command:** `gunicorn worker_app:app --timeout 150` (già nel `Procfile`)
- **Environment (opzionale ma consigliato):** `REEL_WORKER_SECRET` = una password
  (la stessa va incollata su VcriptoV). Se non la metti, il servizio funziona
  comunque ma senza protezione.

## Endpoint
- `GET /health` — stato del motore
- `POST /render-reel` — `{kind, ...}` ⇒ `{url, caption}` (header `X-Worker-Secret`)
- `GET /reels/<file>` — serve il video (Instagram lo scarica da qui)

## Come si collega
Su VcriptoV → Area creatore → 🎨 Contenuti automatici → incolla l'indirizzo di
questo servizio e la stessa password nei campi "🎬 Motore VIDEO".
