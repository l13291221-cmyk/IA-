# IA- — Magazzino reel VcriptoV

Questo repository è il **magazzino dei video** per VcriptoV.

Il vecchio motore video (generazione reel con l'IA) è stato rimosso: i reel ora
si creano fuori (es. con Vadoo) e si **caricano qui**. Il bot di VcriptoV li
pubblica a goccia su Instagram, YouTube e TikTok (uno per ogni slot).

## Come usarlo

1. Carica i video (.mp4) nella cartella **`reels/`**
   (es. `reels/001.mp4`, `reels/002.mp4`, … — vengono pubblicati in ordine di nome, sempre con 3 cifre).
2. Nell'Area creatore di VcriptoV → **Magazzino reel**:
   - Repository: `l13291221-cmyk/IA-`
   - Cartella: `reels`
3. Il repository deve restare **pubblico** (così Instagram può scaricare i video).

## Cosa c'è dentro

- `reels/` — 428 video pronti: la serie *How to invest* (001–390) + 38 video su VcriptoV (`010a`, `020a`, …).
- **Release** `bot-reels-1`, `bot-reels-2`, … — i video creati **ogni giorno** dal bot (dal 391 in poi).
  Stanno nelle Release perché non contano nello spazio del repository.
- `studio/` — come sono fatti i video e il bot automatico (istruzioni in `studio/README.md`).

> Il servizio Render del vecchio motore non serve più e può essere spento.
