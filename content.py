"""
Generatore di CONTENUTI social per VcriptoV (immagini pronte da pubblicare).

Il bot crea da solo delle immagini in stile VcriptoV — schede DIDATTICHE (pattern
di candele, concetti di trading: contenuti "sempreverdi" che fanno crescere il
profilo) e schede SEGNALE — così non devi disegnare/montare niente.

Usa solo Pillow (già installato). Nessun testo copiato da altri: i disegni sono
generati qui. Le immagini sono verticali 1080x1350 (formato Instagram/feed).

Tutto robusto: se un font manca o qualcosa va storto, ritorna None senza crash.
"""

import os
import time

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # Pillow assente: il modulo resta dormiente
    Image = None

# Cartella dove salviamo le immagini generate (servite pubblicamente dal sito).
OUT_DIR = os.path.join(os.path.dirname(__file__), "static", "auto")

_FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
_FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

W, H = 1080, 1350
BG = (14, 17, 22)          # sfondo scuro
CARD = (22, 27, 34)
GREEN = (34, 197, 94)
RED = (239, 68, 68)
TXT = (232, 238, 245)
MUT = (159, 176, 195)
BRAND = (61, 220, 132)
LINE = (38, 48, 60)


def _font(size, bold=True):
    path = _FONT_BOLD if bold else _FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _candles(d, specs, x0, y0, w, h):
    """Disegna una mini-serie di candele. specs = lista di (open, close, low, high)
    in unità 0..100 (0 = basso del riquadro, 100 = alto). Verde se close>open."""
    if not specs:
        return
    n = len(specs)
    slot = w / n
    cw = min(46, slot * 0.5)

    def yy(v):
        return y0 + h - (v / 100.0) * h

    for i, (o, c, lo, hi) in enumerate(specs):
        cx = x0 + slot * (i + 0.5)
        color = GREEN if c >= o else RED
        d.line([(cx, yy(hi)), (cx, yy(lo))], fill=color, width=6)
        top, bot = yy(max(o, c)), yy(min(o, c))
        if abs(bot - top) < 4:
            bot = top + 4
        d.rectangle([cx - cw / 2, top, cx + cw / 2, bot], fill=color)


def _base(title, subtitle, tag):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # header brand
    d.ellipse([60, 55, 118, 113], outline=BRAND, width=6)
    d.line([(74, 84), (104, 84)], fill=BRAND, width=6)
    d.text((135, 60), "VcriptoV", font=_font(46), fill=TXT)
    d.text((137, 112), "segnali crypto", font=_font(26, False), fill=MUT)
    # title
    d.text((60, 195), title, font=_font(58), fill=TXT)
    if subtitle:
        d.text((60, 270), subtitle, font=_font(30, False), fill=BRAND)
    d.line([(60, 320), (W - 60, 320)], fill=LINE, width=3)
    # footer
    d.line([(60, H - 150), (W - 60, H - 150)], fill=LINE, width=3)
    d.text((60, H - 122), tag, font=_font(27, False), fill=MUT)
    d.text((60, H - 80), "👉  link in bio", font=_font(30), fill=BRAND)
    return img, d


def _wrap(d, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# --- Libreria DIDATTICA: pattern di candele + concetti (sempreverdi) -----------
# Ogni voce: titolo, sottotitolo, spiegazione, e una mini-serie di candele che la
# rappresenta. È generica (educativa), NON i tuoi segnali live.
PATTERNS = [
    {"title": "Engulfing rialzista", "sub": "Pattern di inversione ↑",
     "expl": "Una candela verde grande ingloba del tutto la rossa precedente: chi "
             "compra ha ripreso il controllo. Spesso segna la fine di una discesa.",
     "candles": [(70, 55, 50, 72), (60, 48, 44, 62), (49, 44, 40, 51),
                 (44, 62, 42, 64), (46, 30, 44, 48), (31, 66, 29, 68)]},
    {"title": "Engulfing ribassista", "sub": "Pattern di inversione ↓",
     "expl": "Una candela rossa grande ingloba la verde precedente: chi vende prende "
             "il sopravvento. Spesso indica la fine di una salita.",
     "candles": [(35, 50, 33, 52), (48, 60, 46, 62), (58, 64, 56, 66),
                 (64, 50, 48, 66), (52, 68, 50, 70), (69, 40, 38, 71)]},
    {"title": "Martello (Hammer)", "sub": "Possibile rimbalzo dal basso",
     "expl": "Corpo piccolo in alto e lunga ombra sotto: il prezzo è sceso ma è "
             "stato ricomprato. Dopo una discesa può anticipare un rimbalzo.",
     "candles": [(70, 60, 58, 72), (60, 50, 48, 62), (50, 44, 42, 52),
                 (44, 47, 20, 49), (47, 58, 45, 60)]},
    {"title": "Stella cadente", "sub": "Possibile inversione dall'alto",
     "expl": "Corpo piccolo in basso e lunga ombra sopra: il prezzo è salito ma è "
             "stato respinto. Dopo una salita può anticipare una discesa.",
     "candles": [(30, 40, 28, 42), (40, 50, 38, 52), (50, 56, 48, 58),
                 (56, 53, 51, 80), (53, 42, 40, 55)]},
    {"title": "Tre soldati bianchi", "sub": "Forza rialzista",
     "expl": "Tre candele verdi consecutive, ognuna che chiude più in alto: segno "
             "di uno slancio deciso al rialzo dopo una fase debole.",
     "candles": [(38, 34, 32, 40), (34, 48, 32, 50), (48, 62, 46, 64), (62, 76, 60, 78)]},
    {"title": "Tre corvi neri", "sub": "Forza ribassista",
     "expl": "Tre candele rosse consecutive, ognuna che chiude più in basso: slancio "
             "deciso al ribasso. Meglio non comprare 'contro corrente'.",
     "candles": [(64, 68, 62, 70), (68, 54, 52, 70), (54, 40, 38, 56), (40, 26, 24, 42)]},
    {"title": "Supporto e resistenza", "sub": "I livelli chiave",
     "expl": "Il supporto è un 'pavimento' dove il prezzo rimbalza; la resistenza un "
             "'soffitto' dove si ferma. Si compra vicino al supporto, non sui massimi.",
     "candles": [(35, 45, 30, 48), (45, 38, 32, 47), (38, 46, 31, 49),
                 (46, 40, 33, 48), (40, 55, 38, 66), (55, 62, 52, 68)]},
    {"title": "Non inseguire il prezzo", "sub": "Gestione del rischio",
     "expl": "Se una moneta è già corsa tanto, comprare 'sul treno in corsa' è "
             "rischioso: spesso arriva uno storno. Meglio aspettare un ritracciamento.",
     "candles": [(30, 40, 28, 42), (40, 55, 38, 57), (55, 72, 53, 74),
                 (72, 88, 70, 90), (88, 74, 72, 90)]},
    {"title": "Usa sempre lo stop-loss", "sub": "Regola d'oro",
     "expl": "Lo stop-loss chiude il trade se va storto, limitando la perdita. È la "
             "differenza tra perdere poco ed esplodere il conto. Rispettalo, sempre.",
     "candles": [(60, 52, 50, 62), (52, 44, 34, 54), (44, 40, 30, 46), (40, 46, 30, 48)]},
    {"title": "Doji: indecisione", "sub": "Il mercato è in bilico",
     "expl": "Apertura e chiusura quasi uguali: né compratori né venditori vincono. "
             "Spesso precede un movimento deciso: si aspetta la conferma.",
     "candles": [(40, 48, 38, 50), (48, 55, 46, 57), (55, 54, 48, 62), (54, 44, 42, 56)]},
    # --- Consigli / gestione del rischio (sempreverdi) ---
    {"title": "Non mettere tutto in una moneta", "sub": "Diversifica",
     "expl": "Se punti tutto su una sola cripto e va male, perdi tutto. Dividere su "
             "più monete riduce il rischio: un colpo storto non ti azzera.",
     "candles": [(40, 52, 38, 54), (52, 46, 44, 55), (46, 58, 44, 60), (58, 50, 48, 61)]},
    {"title": "DCA: compra a piccole rate", "sub": "Strategia da principianti",
     "expl": "Invece di entrare tutto in una volta, comprare un po' alla volta media "
             "il prezzo e toglie l'ansia di 'sbagliare il momento'. Semplice ed efficace.",
     "candles": [(60, 52, 50, 62), (52, 46, 44, 54), (46, 50, 43, 52), (50, 58, 48, 60)]},
    {"title": "Le emozioni fanno perdere", "sub": "Testa fredda",
     "expl": "Comprare per FOMO sui massimi e vendere in panico sui minimi è l'errore "
             "n°1. Un piano con regole (e stop) batte l'istinto quasi sempre.",
     "candles": [(30, 44, 28, 46), (44, 62, 42, 64), (62, 80, 60, 82), (80, 58, 56, 82)]},
    {"title": "Prendi i guadagni (take profit)", "sub": "Non aspettare troppo",
     "expl": "Un profitto non incassato non è tuo finché non chiudi. Fissare un target "
             "e rispettarlo evita di riconsegnare al mercato quello che avevi guadagnato.",
     "candles": [(35, 48, 33, 50), (48, 60, 46, 62), (60, 72, 58, 74), (72, 70, 66, 78)]},
    {"title": "Pochi trade buoni > tanti a caso", "sub": "Qualità, non quantità",
     "expl": "Non serve operare tutto il giorno. Aspettare solo le occasioni chiare, "
             "con trend e conferma, rende più che rincorrere ogni movimento.",
     "candles": [(45, 43, 41, 47), (43, 45, 41, 47), (45, 44, 42, 47), (44, 58, 42, 60)]},
    {"title": "Segui il trend, non le news", "sub": "Il grafico prima di tutto",
     "expl": "Le notizie arrivano quando il movimento è già avvenuto. Il trend sulle "
             "medie mobili dice dove sta andando davvero il prezzo: quello conta.",
     "candles": [(34, 40, 32, 42), (40, 50, 38, 52), (50, 58, 48, 60), (58, 66, 56, 68)]},
    # --- Cosa fa VcriptoV (prodotto) ---
    {"title": "Crypto senza capirci niente?", "sub": "Ci pensa VcriptoV",
     "expl": "Il bot analizza il mercato per te e ti manda il segnale su Telegram: "
             "cosa comprare, dove mettere stop e target. Tu non devi studiare grafici.",
     "candles": [(40, 52, 38, 54), (52, 64, 50, 66), (64, 60, 56, 68), (60, 72, 58, 74)]},
    {"title": "Ricevi il segnale, tocca, fatto", "sub": "Investi con un tocco",
     "expl": "Arriva il segnale su Telegram con i tasti Investi / Non investire. Un "
             "tocco e (se colleghi il tuo exchange) l'ordine parte da solo, con stop e target.",
     "candles": [(38, 50, 36, 52), (50, 46, 44, 53), (46, 58, 44, 60), (58, 68, 56, 70)]},
    {"title": "Guadagni anche quando scende", "sub": "Segnali long e short",
     "expl": "Un mercato che scende non è un problema: con i segnali short si può "
             "puntare anche sul ribasso. L'importante è seguire il trend, in su o in giù.",
     "candles": [(66, 54, 52, 68), (54, 42, 40, 56), (42, 30, 28, 44), (30, 22, 20, 32)]},
]


def _new_path(prefix, ext="png"):
    os.makedirs(OUT_DIR, exist_ok=True)
    return os.path.join(OUT_DIR, f"{prefix}_{int(time.time())}.{ext}")


# --- REEL (video) --------------------------------------------------------------
# I Reel (video verticali) sono ciò che l'algoritmo spinge agli sconosciuti → fanno
# crescere il profilo. Qui trasformiamo una scheda in un breve video 9:16 con uno
# zoom LENTO e sobrio (Ken Burns): interessante, non una "bambinata".
try:
    import numpy as _np
    import imageio.v2 as _imageio
    _VIDEO_OK = True
except Exception:
    _VIDEO_OK = False

REEL_W, REEL_H = 1080, 1920

# INTERRUTTORE VIDEO. Su Render free tier (512MB) il montaggio video con ffmpeg,
# sommato al server già attivo, sfora la memoria e fa riavviare l'istanza (email
# "exceeded its memory limit"). Finché si resta su 512MB pubblichiamo IMMAGINI
# (funzionano perfettamente, zero problemi). Per riattivare i reel serve più RAM
# (es. Render Standard 2GB): allora basta rimettere questo a True.
VIDEO_ENABLED = False


def video_available() -> bool:
    return _VIDEO_OK and VIDEO_ENABLED


def _card_to_reel(card, out_path, seconds=5, fps=24, zoom_end=1.08, steps=16):
    # Reel con ZOOM (Ken Burns) MA leggero per i 512MB del free tier. Trucco: NON
    # ingrandisco 120 fotogrammi (era quello che faceva saturare la memoria →
    # email Render "exceeded its memory limit"). Preparo UNA sola immagine un po'
    # più grande e poi, per ~16 passi di zoom, ne RITAGLIO un pezzo sempre più
    # stretto e lo riporto a misura: pochi ridimensionamenti, un fotogramma alla
    # volta in RAM. Lo zoom resta fluido all'occhio, la memoria resta bassa.
    import gc as _gc
    base = Image.new("RGB", (REEL_W, REEL_H), BG)
    base.paste(card, ((REEL_W - card.width) // 2, (REEL_H - card.height) // 2))
    # Immagine sorgente leggermente ingrandita, creata UNA volta sola (zoom nitido).
    big = base.resize((int(REEL_W * zoom_end), int(REEL_H * zoom_end)), Image.LANCZOS)
    try:
        base.close()
    except Exception:
        pass
    total = max(1, int(seconds * fps))
    steps = max(2, min(steps, total))
    bw, bh = big.size
    w = _imageio.get_writer(out_path, fps=fps, codec="libx264", quality=7,
                            macro_block_size=1, ffmpeg_params=["-pix_fmt", "yuv420p"])
    try:
        for s in range(steps):
            z = 1.0 + (zoom_end - 1.0) * (s / (steps - 1))
            # Ritaglio da 'big' che, riportato a misura, dà lo zoom z (z=1 tutta
            # l'immagine, z=max ritaglio centrale più stretto = più "vicino").
            cw, ch = int(REEL_W * zoom_end / z), int(REEL_H * zoom_end / z)
            x0, y0 = (bw - cw) // 2, (bh - ch) // 2
            fr = big.crop((x0, y0, x0 + cw, y0 + ch)).resize((REEL_W, REEL_H), Image.BILINEAR)
            arr = _np.asarray(fr)
            reps = total // steps + (1 if s < total % steps else 0)
            for _ in range(reps):
                w.append_data(arr)
            del fr, arr
            _gc.collect()
    finally:
        w.close()
        try:
            big.close()
        except Exception:
            pass
        _gc.collect()


def make_educational_reel(index: int):
    """Reel didattico (video). Ritorna (path_mp4, caption) o (None, None)."""
    if Image is None or not _VIDEO_OK:
        return None, None
    try:
        path, caption = make_educational(index)
        if not path:
            return None, None
        card = Image.open(path).convert("RGB")
        out = _new_path("reeledu", "mp4")
        _card_to_reel(card, out)
        try:
            os.remove(path)   # tengo solo il video
        except Exception:
            pass
        return out, caption
    except Exception:
        return None, None


def make_signal_reel(coin, is_buy, price, sl, tp, risk="medio", gain_pct=None,
                     example_stake=10000):
    """Reel-segnale (video). Ritorna (path_mp4, caption) o (None, None)."""
    if Image is None or not _VIDEO_OK:
        return None, None
    try:
        path, caption = make_signal_card(coin, is_buy, price, sl, tp, risk,
                                         gain_pct=gain_pct, example_stake=example_stake)
        if not path:
            return None, None
        card = Image.open(path).convert("RGB")
        out = _new_path("reelsig", "mp4")
        _card_to_reel(card, out)
        try:
            os.remove(path)
        except Exception:
            pass
        return out, caption
    except Exception:
        return None, None


def make_educational(index: int):
    """Crea la scheda didattica numero `index` (a rotazione). Ritorna (path, caption)
    o (None, None)."""
    if Image is None:
        return None, None
    try:
        item = PATTERNS[index % len(PATTERNS)]
        img, d = _base(item["title"], item.get("sub", ""),
                       "Impara con VcriptoV • educativo, non consulenza")
        # spiegazione a capo automatico
        y = 355
        for line in _wrap(d, item["expl"], _font(32, False), W - 120):
            d.text((60, y), line, font=_font(32, False), fill=TXT)
            y += 46
        # riquadro con le candele
        py = y + 30
        ph = H - 150 - py - 30
        d.rounded_rectangle([60, py, W - 60, py + ph], 20, fill=CARD)
        _candles(d, item["candles"], 110, py + 40, W - 220, ph - 80)
        path = _new_path("edu")
        img.save(path, "PNG")
        caption = (f"{item['title']} — {item.get('sub','')}\n\n{item['expl']}\n\n"
                   "📊 Segnali crypto automatici su VcriptoV — link in bio.\n"
                   "#crypto #trading #bitcoin #cripto #investimenti #vcriptov")
        return path, caption
    except Exception:
        return None, None


_GENERIC_CANDLES = [
    [(38, 34, 32, 40), (34, 48, 32, 50), (48, 62, 46, 64), (62, 76, 60, 78)],
    [(35, 45, 30, 48), (45, 38, 32, 47), (38, 46, 31, 49), (46, 58, 44, 66)],
    [(60, 52, 50, 62), (52, 58, 48, 60), (58, 50, 46, 62), (50, 64, 48, 66)],
    [(40, 52, 38, 54), (52, 46, 44, 55), (46, 58, 44, 60), (58, 68, 56, 70)],
]


def make_ai_educational(topic_hint: str = ""):
    """Contenuto didattico NUOVO scritto dall'assistente AI (così i contenuti non
    finiscono mai). Ritorna (path, caption) o (None, None) se l'AI non è configurata
    o fallisce (in tal caso chi chiama usa la libreria fissa)."""
    if Image is None:
        return None, None
    try:
        import json as _json
        import random as _random
        from app import ai_api_key
        import ai_assistant
        key = ai_api_key()
        if not ai_assistant.is_configured(key):
            return None, None
        prompt = (
            "Genera UN consiglio breve ed 'evergreen' su crypto/trading/finanza per "
            "principianti, per un post social. Deve essere sensato e vario (evita i "
            "soliti banali). Rispondi SOLO in JSON valido con queste chiavi: "
            '{"title": "max 5 parole", "sub": "max 5 parole", '
            '"expl": "max 45 parole, chiaro"}. '
            "Niente promesse di guadagno. In italiano."
            + (f" Tema di oggi: {topic_hint}." if topic_hint else "")
        )
        res = ai_assistant.ask_ai(prompt, api_key=key, lang="it")
        if not (res.get("ok") and res.get("answer")):
            return None, None
        raw = res["answer"]
        i, j = raw.find("{"), raw.rfind("}")
        if i < 0 or j < 0:
            return None, None
        data = _json.loads(raw[i:j + 1])
        title = (data.get("title") or "").strip()[:38]
        sub = (data.get("sub") or "").strip()[:38]
        expl = (data.get("expl") or "").strip()
        if not (title and expl):
            return None, None
        img, d = _base(title, sub, "Impara con VcriptoV • educativo, non consulenza")
        y = 355
        for line in _wrap(d, expl, _font(32, False), W - 120)[:6]:
            d.text((60, y), line, font=_font(32, False), fill=TXT)
            y += 46
        py = y + 30
        ph = H - 150 - py - 30
        if ph > 160:
            d.rounded_rectangle([60, py, W - 60, py + ph], 20, fill=CARD)
            _candles(d, _random.choice(_GENERIC_CANDLES), 110, py + 40, W - 220, ph - 80)
        path = _new_path("aiedu")
        img.save(path, "PNG")
        caption = (f"{title} — {sub}\n\n{expl}\n\n"
                   "📊 Segnali crypto automatici su VcriptoV — link in bio.\n"
                   "#crypto #trading #bitcoin #cripto #investimenti #vcriptov")
        return path, caption
    except Exception:
        return None, None


def make_ai_educational_reel(topic_hint: str = ""):
    """Reel didattico con testo NUOVO dall'AI. (path_mp4, caption) o (None, None)."""
    if Image is None or not _VIDEO_OK:
        return None, None
    try:
        path, caption = make_ai_educational(topic_hint)
        if not path:
            return None, None
        card = Image.open(path).convert("RGB")
        out = _new_path("reelai", "mp4")
        _card_to_reel(card, out)
        try:
            os.remove(path)
        except Exception:
            pass
        return out, caption
    except Exception:
        return None, None


def make_signal_card(coin: str, is_buy: bool, price: float, sl: float, tp: float,
                     risk: str = "medio", gain_pct: float | None = None,
                     example_stake: int = 10000):
    """Crea la scheda-segnale. Se `gain_pct` è dato, mostra in grande un ESEMPIO in
    euro ("con 10.000€ avrebbe reso +X€") — chiaramente etichettato come esempio,
    non come risultato reale. Ritorna (path, caption) o (None, None)."""
    if Image is None:
        return None, None
    try:
        has_ex = gain_pct is not None and gain_pct > 0
        subtitle = (f"Segnale andato a +{gain_pct:.0f}% 🚀" if has_ex else "")
        img, d = _base("Segnale del giorno", subtitle,
                       "Non è consulenza finanziaria • i risultati passati non garantiscono quelli futuri")
        d.rounded_rectangle([60, 360, W - 60, 360 + 660], 24, fill=CARD)
        verso = "🟢 LONG" if is_buy else "🔴 SHORT"
        d.text((110, 400), verso, font=_font(56), fill=GREEN if is_buy else RED)
        d.text((110, 480), coin, font=_font(64), fill=TXT)
        try:
            pstr = f"{price:,.4f}".rstrip("0").rstrip(".")
        except Exception:
            pstr = str(price)
        y = 590
        if has_ex:
            euros = int(round(example_stake * gain_pct / 100.0))
            d.text((110, y), f"+{euros:,.0f}€".replace(",", "."),
                   font=_font(82), fill=GREEN)
            d.text((113, y + 96),
                   f"con {example_stake:,.0f}€".replace(",", ".")
                   + f" avresti guadagnato (+{gain_pct:.0f}%)", font=_font(28, False), fill=MUT)
            y += 165
        rows = [("Ingresso", f"{pstr} USDT", TXT),
                ("🛑 Stop-loss", f"-{sl:.0f}%", RED),
                ("🎯 Target", f"+{tp:.0f}%", GREEN),
                ("📊 Rischio", risk, MUT)]
        for k, v, c in rows:
            d.text((110, y), k, font=_font(34, False), fill=MUT)
            d.text((W - 110, y), v, font=_font(38), fill=c, anchor="ra")
            y += 72
        path = _new_path("sig")
        img.save(path, "PNG")
        verso_txt = "LONG (comprare)" if is_buy else "SHORT (vendere)"
        ex_line = ""
        if has_ex:
            euros = int(round(example_stake * gain_pct / 100.0))
            ex_line = (f"💶 Con {example_stake:,.0f}€".replace(",", ".")
                       + f" avresti guadagnato +{euros:,.0f}€".replace(",", ".")
                       + f" (segnale reale andato a +{gain_pct:.0f}%).\n")
        caption = (f"Segnale {coin} — {verso_txt}\n"
                   f"Ingresso {pstr} • Stop -{sl:.0f}% • Target +{tp:.0f}% • rischio {risk}.\n"
                   + ex_line +
                   "\n⚠️ Non è consulenza finanziaria; i risultati passati non garantiscono quelli futuri.\n"
                   "Segnali automatici su VcriptoV — link in bio.\n"
                   "#crypto #trading #bitcoin #cripto #segnali #vcriptov")
        return path, caption
    except Exception:
        return None, None


def cleanup_old(keep_seconds: int = 7 * 24 * 3600):
    """Cancella le immagini vecchie (già pubblicate) per non riempire il disco."""
    try:
        now = time.time()
        for name in os.listdir(OUT_DIR):
            p = os.path.join(OUT_DIR, name)
            try:
                if now - os.path.getmtime(p) > keep_seconds:
                    os.remove(p)
            except Exception:
                pass
    except Exception:
        pass
