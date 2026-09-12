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
import random
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
# --- Stile "quaderno / disegnato a mano" (foglio di carta, evidenziatore, candele
# disegnate). Colori tenui su carta chiara, come gli appunti a mano. ---
BG = (246, 241, 228)       # carta color crema
CARD = (238, 231, 212)     # riquadro (nota) leggermente più scuro
GREEN = (56, 158, 92)      # verde "pennarello"
RED = (206, 82, 70)        # rosso "pennarello"
TXT = (44, 45, 52)         # inchiostro scuro
MUT = (120, 118, 120)      # grigio matita
BRAND = (44, 150, 96)      # accento verde
LINE = (206, 212, 222)     # righe del quaderno (azzurrino tenue)
HILITE = (255, 230, 110)   # evidenziatore giallo
MARGIN = (223, 156, 156)   # riga rossa del margine
INK = TXT


def _font(size, bold=True):
    path = _FONT_BOLD if bold else _FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _sk_line(d, p1, p2, fill, width=4, jitter=2.0, passes=2):
    """Linea 'disegnata a mano': due passate con piccoli scostamenti casuali, così
    sembra tracciata a penna invece che al computer."""
    (x1, y1), (x2, y2) = p1, p2
    for _ in range(passes):
        def j():
            return random.uniform(-jitter, jitter)
        d.line([(x1 + j(), y1 + j()), (x2 + j(), y2 + j())], fill=fill, width=width)


def _sk_rect(d, box, fill=None, outline=None, width=3, jitter=1.8):
    """Rettangolo riempito con contorno 'a mano' (quattro linee sketchate)."""
    x0, y0, x1, y1 = box
    if fill is not None:
        d.rectangle([x0, y0, x1, y1], fill=fill)
    if outline is not None:
        _sk_line(d, (x0, y0), (x1, y0), outline, width, jitter)
        _sk_line(d, (x1, y0), (x1, y1), outline, width, jitter)
        _sk_line(d, (x1, y1), (x0, y1), outline, width, jitter)
        _sk_line(d, (x0, y1), (x0, y0), outline, width, jitter)


def _candles(d, specs, x0, y0, w, h):
    """Disegna una mini-serie di candele DISEGNATE A MANO: corpo colorato con
    contorno d'inchiostro e stoppino sketchato. specs = (open, close, low, high)
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
        # stoppino (wick) a mano, in inchiostro scuro
        _sk_line(d, (cx, yy(hi)), (cx, yy(lo)), INK, 4, jitter=1.5)
        top, bot = yy(max(o, c)), yy(min(o, c))
        if abs(bot - top) < 8:
            bot = top + 8
        # corpo: riempito col colore + contorno d'inchiostro disegnato a mano
        _sk_rect(d, (cx - cw / 2, top, cx + cw / 2, bot),
                 fill=color, outline=INK, width=3, jitter=1.5)


def _base(title, subtitle, tag):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # --- foglio di quaderno: righe orizzontali tenui + margine rosso a sinistra ---
    y = 140
    while y < H - 30:
        d.line([(30, y), (W - 30, y)], fill=LINE, width=2)
        y += 58
    d.line([(48, 30), (48, H - 30)], fill=MARGIN, width=3)
    # --- header: cerchio "logo" disegnato a mano + nome ---
    _sk_rect(d, (60, 55, 118, 113), outline=INK, width=5, jitter=1.4)
    _sk_line(d, (74, 84), (104, 84), GREEN, 6, jitter=1.2)
    d.text((135, 60), "VcriptoV", font=_font(46), fill=INK)
    d.text((137, 112), "crypto signals", font=_font(26, False), fill=MUT)
    # --- titolo con EVIDENZIATORE giallo dietro (come gli appunti) ---
    tf = _font(58)
    try:
        bb = d.textbbox((60, 195), title, font=tf)
        d.rectangle([bb[0] - 8, bb[1] + 14, min(bb[2] + 14, W - 40), bb[3] + 2], fill=HILITE)
    except Exception:
        pass
    d.text((60, 195), title, font=tf, fill=INK)
    if subtitle:
        d.text((60, 272), subtitle, font=_font(30, False), fill=BRAND)
    _sk_line(d, (60, 322), (W - 60, 322), INK, 3, jitter=1.2)
    # --- footer ---
    _sk_line(d, (60, H - 150), (W - 60, H - 150), INK, 3, jitter=1.2)
    d.text((60, H - 122), tag, font=_font(27, False), fill=MUT)
    d.text((60, H - 80), "→  link in bio", font=_font(30), fill=BRAND)
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
    {"title": "Bullish Engulfing", "sub": "Reversal pattern ↑",
     "expl": "A big green candle completely swallows the previous red one: buyers "
             "took back control. Often marks the end of a downtrend.",
     "candles": [(70, 55, 50, 72), (60, 48, 44, 62), (49, 44, 40, 51),
                 (44, 62, 42, 64), (46, 30, 44, 48), (31, 66, 29, 68)]},
    {"title": "Bearish Engulfing", "sub": "Reversal pattern ↓",
     "expl": "A big red candle swallows the previous green one: sellers take over. "
             "Often signals the end of an uptrend.",
     "candles": [(35, 50, 33, 52), (48, 60, 46, 62), (58, 64, 56, 66),
                 (64, 50, 48, 66), (52, 68, 50, 70), (69, 40, 38, 71)]},
    {"title": "Hammer", "sub": "Possible bounce from below",
     "expl": "Small body on top and a long lower wick: price dropped but got bought "
             "back. After a fall it can signal a bounce.",
     "candles": [(70, 60, 58, 72), (60, 50, 48, 62), (50, 44, 42, 52),
                 (44, 47, 20, 49), (47, 58, 45, 60)]},
    {"title": "Shooting Star", "sub": "Possible reversal from the top",
     "expl": "Small body at the bottom and a long upper wick: price rose but got "
             "rejected. After a rally it can signal a drop.",
     "candles": [(30, 40, 28, 42), (40, 50, 38, 52), (50, 56, 48, 58),
                 (56, 53, 51, 80), (53, 42, 40, 55)]},
    {"title": "Three White Soldiers", "sub": "Bullish strength",
     "expl": "Three green candles in a row, each closing higher: a sign of strong "
             "upward momentum after a weak phase.",
     "candles": [(38, 34, 32, 40), (34, 48, 32, 50), (48, 62, 46, 64), (62, 76, 60, 78)]},
    {"title": "Three Black Crows", "sub": "Bearish strength",
     "expl": "Three red candles in a row, each closing lower: strong downward "
             "momentum. Better not to buy 'against the tide'.",
     "candles": [(64, 68, 62, 70), (68, 54, 52, 70), (54, 40, 38, 56), (40, 26, 24, 42)]},
    {"title": "Support & Resistance", "sub": "The key levels",
     "expl": "Support is a 'floor' where price bounces; resistance a 'ceiling' where "
             "it stalls. Buy near support, not at the highs.",
     "candles": [(35, 45, 30, 48), (45, 38, 32, 47), (38, 46, 31, 49),
                 (46, 40, 33, 48), (40, 55, 38, 66), (55, 62, 52, 68)]},
    {"title": "Don't chase the price", "sub": "Risk management",
     "expl": "If a coin has already run a lot, jumping on the moving train is risky: "
             "a pullback often comes. Better to wait for a retracement.",
     "candles": [(30, 40, 28, 42), (40, 55, 38, 57), (55, 72, 53, 74),
                 (72, 88, 70, 90), (88, 74, 72, 90)]},
    {"title": "Always use a stop-loss", "sub": "Golden rule",
     "expl": "A stop-loss closes the trade if it goes wrong, capping your loss. It's "
             "the difference between losing little and blowing up your account.",
     "candles": [(60, 52, 50, 62), (52, 44, 34, 54), (44, 40, 30, 46), (40, 46, 30, 48)]},
    {"title": "Doji: indecision", "sub": "The market is on the fence",
     "expl": "Open and close almost equal: neither buyers nor sellers win. Often "
             "precedes a strong move: wait for confirmation.",
     "candles": [(40, 48, 38, 50), (48, 55, 46, 57), (55, 54, 48, 62), (54, 44, 42, 56)]},
    # --- Tips / risk management (evergreen) ---
    {"title": "Don't put it all in one coin", "sub": "Diversify",
     "expl": "Bet everything on one crypto and if it goes bad, you lose it all. "
             "Splitting across coins lowers the risk: one bad hit won't wipe you out.",
     "candles": [(40, 52, 38, 54), (52, 46, 44, 55), (46, 58, 44, 60), (58, 50, 48, 61)]},
    {"title": "DCA: buy in small amounts", "sub": "Beginner strategy",
     "expl": "Instead of entering all at once, buying a bit at a time averages your "
             "price and removes the stress of timing it wrong. Simple and effective.",
     "candles": [(60, 52, 50, 62), (52, 46, 44, 54), (46, 50, 43, 52), (50, 58, 48, 60)]},
    {"title": "Emotions make you lose", "sub": "Cool head",
     "expl": "Buying out of FOMO at the highs and panic-selling at the lows is mistake "
             "#1. A plan with rules (and stops) beats instinct almost every time.",
     "candles": [(30, 44, 28, 46), (44, 62, 42, 64), (62, 80, 60, 82), (80, 58, 56, 82)]},
    {"title": "Take your profits", "sub": "Don't wait too long",
     "expl": "An unrealized profit isn't yours until you close. Setting a target and "
             "respecting it keeps you from handing back what you'd earned.",
     "candles": [(35, 48, 33, 50), (48, 60, 46, 62), (60, 72, 58, 74), (72, 70, 66, 78)]},
    {"title": "Few good trades > many random", "sub": "Quality, not quantity",
     "expl": "You don't need to trade all day. Waiting only for clear setups, with "
             "trend and confirmation, pays more than chasing every move.",
     "candles": [(45, 43, 41, 47), (43, 45, 41, 47), (45, 44, 42, 47), (44, 58, 42, 60)]},
    {"title": "Follow the trend, not the news", "sub": "Chart first",
     "expl": "News arrives after the move already happened. The trend on moving "
             "averages shows where price is really going: that's what matters.",
     "candles": [(34, 40, 32, 42), (40, 50, 38, 52), (50, 58, 48, 60), (58, 66, 56, 68)]},
    # --- What VcriptoV does (product) ---
    {"title": "Crypto but clueless?", "sub": "VcriptoV's got you",
     "expl": "The bot analyzes the market for you and sends the signal on Telegram: "
             "what to buy, where to set stop and target. No chart studying needed.",
     "candles": [(40, 52, 38, 54), (52, 64, 50, 66), (64, 60, 56, 68), (60, 72, 58, 74)]},
    {"title": "Get the signal, tap, done", "sub": "Invest with one tap",
     "expl": "The signal lands on Telegram with Invest / Skip buttons. One tap and "
             "(if you connect your exchange) the order fires by itself, with stop and target.",
     "candles": [(38, 50, 36, 52), (50, 46, 44, 53), (46, 58, 44, 60), (58, 68, 56, 70)]},
    {"title": "Profit even when it drops", "sub": "Long and short signals",
     "expl": "A falling market isn't a problem: with short signals you can bet on the "
             "downside too. What matters is following the trend, up or down.",
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


def _finalize_reel(raw_path, out_path):
    """Rende il video PRONTO per Instagram e per aprirsi ovunque (anche iPhone):
    aggiunge una TRACCIA AUDIO muta (i Reel di solito la pretendono) e sposta il
    'moov atom' all'inizio (+faststart, così parte subito in streaming). Se per
    qualsiasi motivo ffmpeg non ci riesce, tengo comunque il video grezzo: meglio
    un reel senza rifiniture che nessun reel."""
    import os as _os
    import subprocess as _sp
    try:
        import imageio_ffmpeg as _iff
        ff = _iff.get_ffmpeg_exe()
        cmd = [ff, "-y", "-i", raw_path,
               "-f", "lavfi", "-i",
               "anullsrc=channel_layout=stereo:sample_rate=44100", "-shortest",
               "-c:v", "libx264", "-profile:v", "main", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k",
               "-movflags", "+faststart", out_path]
        r = _sp.run(cmd, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
        if r.returncode == 0 and _os.path.exists(out_path) and _os.path.getsize(out_path) > 0:
            try:
                _os.remove(raw_path)
            except Exception:
                pass
            return out_path
    except Exception:
        pass
    # Ripiego: uso il video grezzo così com'è (senza audio/faststart).
    try:
        if raw_path != out_path:
            _os.replace(raw_path, out_path)
    except Exception:
        return raw_path
    return out_path


def _card_to_reel(card, out_path, seconds=5, fps=24, steps=60):
    # Reel con MOVIMENTO VERO (Ken Burns): zoom DECISO + PANORAMICA in diagonale,
    # così si vede chiaramente che è un video e non una foto ferma. Resta leggero
    # per i 512MB del free tier con lo stesso trucco: preparo UNA sola immagine più
    # grande e per ~60 passi ne RITAGLIO una finestra che si stringe e SCORRE; un
    # fotogramma alla volta in RAM, quindi la memoria resta bassa.
    import gc as _gc
    Z_MAX = 1.32                 # quanto ingrandisco l'immagine sorgente (spazio per pan)
    Z0, Z1 = 1.14, 1.30          # lo zoom va da 1.14 a 1.30 (sempre "dentro" = c'è pan)
    base = Image.new("RGB", (REEL_W, REEL_H), BG)
    base.paste(card, ((REEL_W - card.width) // 2, (REEL_H - card.height) // 2))
    big = base.resize((int(REEL_W * Z_MAX), int(REEL_H * Z_MAX)), Image.LANCZOS)
    try:
        base.close()
    except Exception:
        pass
    total = max(1, int(seconds * fps))
    steps = max(2, min(steps, total))
    bw, bh = big.size
    raw_path = out_path + ".raw.mp4"
    w = _imageio.get_writer(raw_path, fps=fps, codec="libx264", quality=7,
                            macro_block_size=1, ffmpeg_params=["-pix_fmt", "yuv420p"])
    try:
        for s in range(steps):
            t = s / (steps - 1)                 # avanzamento 0 → 1
            # ease-in-out morbido, così il movimento non "scatta" all'inizio/fine
            e = t * t * (3 - 2 * t)
            z = Z0 + (Z1 - Z0) * e               # zoom che aumenta
            cw, ch = int(REEL_W * Z_MAX / z), int(REEL_H * Z_MAX / z)
            # PANORAMICA: la finestra scorre in diagonale da alto-sx a basso-dx,
            # usando tutto lo spazio disponibile (quello che avanza tra 'big' e la
            # finestra ritagliata). È questo scorrimento che fa "muovere" il video.
            x0 = int((bw - cw) * (0.12 + 0.76 * e))
            y0 = int((bh - ch) * (0.15 + 0.70 * e))
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
    # Rifinitura per Instagram (audio muto + faststart). Il file finale resta in
    # out_path, così chi ha chiamato la funzione lo trova dov'è previsto.
    _finalize_reel(raw_path, out_path)


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
                       "Learn with VcriptoV • educational, not financial advice")
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
                   "📊 Automatic crypto signals on VcriptoV — link in bio.\n"
                   "#crypto #trading #bitcoin #cryptocurrency #investing #vcriptov")
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
            "Generate ONE short, evergreen tip about crypto/trading/finance for "
            "beginners, for a social post. It must be sensible and varied (avoid the "
            "usual clichés). Reply ONLY with valid JSON with these keys: "
            '{"title": "max 5 words", "sub": "max 5 words", '
            '"expl": "max 45 words, clear"}. '
            "No profit promises. In English."
            + (f" Today's theme: {topic_hint}." if topic_hint else "")
        )
        res = ai_assistant.ask_ai(prompt, api_key=key, lang="en")
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
        img, d = _base(title, sub, "Learn with VcriptoV • educational, not financial advice")
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
                   "📊 Automatic crypto signals on VcriptoV — link in bio.\n"
                   "#crypto #trading #bitcoin #cryptocurrency #investing #vcriptov")
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
        risk_en = {"basso": "low", "medio": "medium", "alto": "high"}.get(risk, risk)
        subtitle = (f"This signal hit +{gain_pct:.0f}%" if has_ex else "")
        img, d = _base("Signal of the day", subtitle,
                       "Not financial advice • past results don't guarantee future ones")
        d.rounded_rectangle([60, 360, W - 60, 360 + 660], 24, fill=CARD)
        vcol = GREEN if is_buy else RED
        # pallino disegnato a mano (verde=long, rosso=short) + etichetta
        d.ellipse([112, 410, 150, 448], fill=vcol, outline=INK, width=3)
        d.text((170, 400), "LONG" if is_buy else "SHORT", font=_font(56), fill=vcol)
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
                   f"with €{example_stake:,.0f}".replace(",", ".")
                   + f" you'd have made (+{gain_pct:.0f}%)", font=_font(28, False), fill=MUT)
            y += 165
        rows = [("Entry", f"{pstr} USDT", TXT),
                ("Stop-loss", f"-{sl:.0f}%", RED),
                ("Target", f"+{tp:.0f}%", GREEN),
                ("Risk", risk_en, MUT)]
        for k, v, c in rows:
            d.text((110, y), k, font=_font(34, False), fill=MUT)
            d.text((W - 110, y), v, font=_font(38), fill=c, anchor="ra")
            y += 72
        path = _new_path("sig")
        img.save(path, "PNG")
        verso_txt = "LONG (buy)" if is_buy else "SHORT (sell)"
        ex_line = ""
        if has_ex:
            euros = int(round(example_stake * gain_pct / 100.0))
            ex_line = (f"💶 With €{example_stake:,.0f}".replace(",", ".")
                       + f" you'd have made +€{euros:,.0f}".replace(",", ".")
                       + f" (real signal that hit +{gain_pct:.0f}%).\n")
        caption = (f"{coin} signal — {verso_txt}\n"
                   f"Entry {pstr} • Stop -{sl:.0f}% • Target +{tp:.0f}% • risk {risk_en}.\n"
                   + ex_line +
                   "\n⚠️ Not financial advice; past results don't guarantee future ones.\n"
                   "Automatic signals on VcriptoV — link in bio.\n"
                   "#crypto #trading #bitcoin #cryptocurrency #signals #vcriptov")
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
