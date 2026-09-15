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


def _finalize_reel(raw_path, out_path, audio_path=None):
    """Rende il video PRONTO per Instagram e per aprirsi ovunque (anche iPhone):
    aggiunge l'AUDIO (la musichetta di sottofondo se c'è, altrimenti una traccia
    muta — i Reel di solito la pretendono) e sposta il 'moov atom' all'inizio
    (+faststart, così parte subito in streaming). NON ri-codifico il video (sarebbe
    un secondo x264 = picco di RAM sui 512MB): COPIO il flusso già pronto e aggiungo
    solo l'audio. Se ffmpeg non ci riesce, tengo il video grezzo."""
    import os as _os
    import subprocess as _sp
    try:
        import imageio_ffmpeg as _iff
        ff = _iff.get_ffmpeg_exe()
        if audio_path and _os.path.exists(audio_path):
            audio_in = ["-i", audio_path]           # la musichetta di sottofondo
            abr = "128k"
        else:
            audio_in = ["-f", "lavfi", "-i",
                        "anullsrc=channel_layout=stereo:sample_rate=44100"]
            abr = "96k"
        cmd = ([ff, "-y", "-i", raw_path] + audio_in +
               ["-shortest", "-c:v", "copy", "-c:a", "aac", "-b:a", abr,
                "-movflags", "+faststart", out_path])
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


_LOGO_RGBA = {"img": None, "tried": False}


def _corner_logo_base():
    """Carica il LOGO VERO (static/logo.png) UNA volta e lo trasforma in un timbro
    color inchiostro con trasparenza (lo scudo pieno, lo sfondo trasparente), così
    si posa bene sulla scheda color crema. In cache: si prepara una volta sola."""
    if _LOGO_RGBA["tried"]:
        return _LOGO_RGBA["img"]
    _LOGO_RGBA["tried"] = True
    try:
        import os as _os
        p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "static", "logo.png")
        L = _np.asarray(Image.open(p).convert("L")).astype("float32")
        bg = float(_np.median(_np.concatenate([L[0], L[-1], L[:, 0], L[:, -1]])))
        # lo scudo è PIÙ SCURO dello sfondo: l'opacità è quanto un pixel è più scuro
        alpha = _np.clip((bg - L) / max(1.0, bg - float(L.min())), 0, 1) ** 0.8
        rgba = _np.zeros((L.shape[0], L.shape[1], 4), dtype="uint8")
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = INK[0], INK[1], INK[2]
        rgba[..., 3] = (alpha * 255).astype("uint8")
        _LOGO_RGBA["img"] = Image.fromarray(rgba, "RGBA")
    except Exception:
        _LOGO_RGBA["img"] = None
    return _LOGO_RGBA["img"]


def _paste_corner_logo(frame, cx, cy, s):
    """Posa il logo vero, scalato di 's' (per la pulsazione), centrato in (cx, cy).
    Se il file non c'è, disegna un piccolo scudo di ripiego."""
    logo = _corner_logo_base()
    if logo is not None:
        sz = max(8, int(120 * s))
        lg = logo.resize((sz, sz), Image.LANCZOS)
        frame.paste(lg, (int(cx - sz / 2), int(cy - sz / 2)), lg)
        return
    d = ImageDraw.Draw(frame)          # ripiego se manca logo.png
    half = 30 * s
    lw = max(3, int(5 * s))
    d.line([(cx - half * 0.5, cy - half * 0.18), (cx, cy + half * 0.52)], fill=GREEN, width=lw)
    d.line([(cx, cy + half * 0.52), (cx + half * 0.5, cy - half * 0.18)], fill=GREEN, width=lw)


def _make_bg_music(path, seconds=5.0, sr=44100):
    """Crea una MUSICHETTA di sottofondo dolce (arpeggio morbido in La minore +
    un 'tappeto' grave leggero), a volume basso: rende il reel più carino senza
    diventare fastidioso. La genero io, così non ci sono problemi di diritti."""
    import wave as _wave
    n_total = int(seconds * sr)
    audio = _np.zeros(n_total, dtype=_np.float32)
    notes = [220.00, 261.63, 329.63, 392.00, 329.63, 261.63]  # La do mi sol mi do
    step = 0.45
    tt, i = 0.0, 0
    while tt < seconds:
        f = notes[i % len(notes)]
        n = int(step * sr)
        et = _np.linspace(0, step, n, endpoint=False)
        env = _np.minimum(et / 0.04, 1.0) * _np.exp(-3.0 * et)   # attacco dolce + coda
        tone = _np.sin(2 * _np.pi * f * et) * env * 0.22
        idx = int(tt * sr)
        end = min(idx + n, n_total)
        audio[idx:end] += tone[:end - idx]
        tt += step
        i += 1
    tfull = _np.linspace(0, seconds, n_total, endpoint=False)
    audio += (_np.sin(2 * _np.pi * 110.0 * tfull) +
              0.5 * _np.sin(2 * _np.pi * 220.0 * tfull)) * 0.05   # tappeto grave
    fade = int(0.15 * sr)
    audio[:fade] *= _np.linspace(0, 1, fade)
    audio[-fade:] *= _np.linspace(1, 0, fade)
    peak = float(_np.max(_np.abs(audio))) or 1.0
    pcm = ((audio / peak) * 0.5 * 32767).astype("<i2")
    with _wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return path


def _card_to_reel(card, out_path, seconds=5, fps=24):
    # Reel come li vuole il proprietario: la SCHEDA sta FERMA (niente zoom, niente
    # panoramica) e l'UNICA cosa che si muove è il LOGO in alto a destra, piccolo,
    # che PULSA. In più una musichetta di sottofondo. Leggerissimo per i 512MB:
    # il frame è quasi identico (x264 lo comprime a nulla) e disegno solo il
    # logo, un fotogramma alla volta in RAM.
    import gc as _gc
    import math as _math
    base = Image.new("RGB", (REEL_W, REEL_H), BG)
    base.paste(card, ((REEL_W - card.width) // 2, (REEL_H - card.height) // 2))
    total = max(1, int(seconds * fps))
    cx, cy = REEL_W - 96, 116          # angolo in alto a destra
    raw_path = out_path + ".raw.mp4"
    w = _imageio.get_writer(
        raw_path, fps=fps, codec="libx264", quality=7, macro_block_size=1,
        ffmpeg_params=[
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-threads", "1",
            "-bf", "0",
            "-x264-params", "rc-lookahead=5:sync-lookahead=0:ref=1:me=dia:subme=1",
        ])
    try:
        for fidx in range(total):
            t = fidx / fps
            # pulsazione morbida (respiro): la scala oscilla ~0.9 → ~1.12
            s = 1.0 + 0.11 * _math.sin(2 * _math.pi * t / 1.6)
            fr = base.copy()
            _paste_corner_logo(fr, cx, cy, s)
            w.append_data(_np.asarray(fr))
            del fr
            _gc.collect()
    finally:
        w.close()
        try:
            base.close()
        except Exception:
            pass
        _gc.collect()
    # musichetta di sottofondo (se qualcosa va storto, resta l'audio muto) + faststart
    music = out_path + ".wav"
    try:
        _make_bg_music(music, seconds)
    except Exception:
        music = None
    _finalize_reel(raw_path, out_path, music)
    if music:
        try:
            import os as _os
            _os.remove(music)
        except Exception:
            pass


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


_EDU_FOOTER = "Learn with VcriptoV • educational, not financial advice"
_EDU_TAGS = ("\n\n📊 Automatic crypto signals on VcriptoV — link in bio.\n"
             "#crypto #trading #bitcoin #candlestick #investing #vcriptov")

# Regole di trading (per il modello 'lista di regole')
RULES = [
    ("Always use a stop-loss", "Decide your max loss BEFORE you enter. No stop, no trade."),
    ("Don't chase the price", "Already ran a lot? Wait for a pullback. Chasing gets you trapped."),
    ("Take your profits", "A gain isn't real until you close. Bank part of it on the way up."),
    ("Follow the trend", "Trade WITH the direction, not against it. The trend is your friend."),
    ("Risk small per trade", "Never risk more than 1–2% on one idea. Survive first, win later."),
    ("Don't put it all in one coin", "Spread it out. One bad bet shouldn't wipe you out."),
    ("Emotions lose money", "Fear and greed are the enemy. Follow the plan, not the feeling."),
]


def _signal_of(item):
    """Deduce BUY / SELL / WAIT dal pattern (dalla freccia nel sottotitolo o dal testo)."""
    sub = item.get("sub", "")
    s = (sub + " " + item.get("title", "") + " " + item.get("expl", "")).lower()
    if "↑" in sub or "bullish" in s or "bounce" in s or "buyers" in s:
        return "BUY"
    if "↓" in sub or "bearish" in s or "drop" in s or "sellers" in s or "reject" in s:
        return "SELL"
    return "WAIT"


def _fit(d, text, font, max_w):
    """Accorcia il testo con … finché entra nella larghezza."""
    if d.textlength(text, font=font) <= max_w:
        return text
    while text and d.textlength(text + "…", font=font) > max_w:
        text = text[:-1]
    return text + "…"


def _tag(d, cx, y, kind, fs=26):
    """Etichetta BUY/SELL/WAIT evidenziata (verde/rosso/giallo)."""
    col = {"BUY": (26, 110, 60), "SELL": (150, 40, 34), "WAIT": (120, 92, 30)}[kind]
    bg = {"BUY": (200, 236, 210), "SELL": (246, 205, 199), "WAIT": HILITE}[kind]
    f = _font(fs)
    tw = d.textlength(kind, font=f)
    pad = 12
    box = [cx - tw / 2 - pad, y, cx + tw / 2 + pad, y + fs + 12]
    d.rounded_rectangle(box, 8, fill=bg)
    _sk_rect(d, box, outline=INK, width=2, jitter=1.0)
    d.text((cx - tw / 2, y + 5), kind, font=f, fill=col)


def _mini_panel(d, x0, y0, x1, y1, item, tag=True):
    """Riquadro con: nome del pattern, mini-candele disegnate, etichetta BUY/SELL."""
    _sk_rect(d, (x0, y0, x1, y1), outline=INK, width=4, jitter=1.3)
    f = _font(30)
    name = _fit(d, item["title"], f, (x1 - x0) - 24)
    d.text((x0 + ((x1 - x0) - d.textlength(name, font=f)) / 2, y0 + 12), name, font=f, fill=INK)
    tag_h = 46 if tag else 6
    cy0, cy1 = y0 + 56, y1 - tag_h - 10
    _candles(d, item.get("candles", [])[:6], x0 + 16, cy0, (x1 - x0) - 32, max(30, cy1 - cy0))
    if tag:
        k = _signal_of(item)
        _tag(d, (x0 + x1) / 2, y1 - tag_h - 2, k, fs=24)


def _edu_single(index):
    item = PATTERNS[index % len(PATTERNS)]
    img, d = _base(item["title"], item.get("sub", ""), _EDU_FOOTER)
    y = 355
    for line in _wrap(d, item["expl"], _font(32, False), W - 120):
        d.text((60, y), line, font=_font(32, False), fill=TXT)
        y += 46
    py = y + 30
    ph = H - 150 - py - 30
    d.rounded_rectangle([60, py, W - 60, py + ph], 20, fill=CARD)
    _candles(d, item["candles"], 110, py + 40, W - 220, ph - 80)
    caption = f"{item['title']} — {item.get('sub','')}\n\n{item['expl']}" + _EDU_TAGS
    return img, caption


def _edu_grid4(index):
    items = [PATTERNS[(index + i) % len(PATTERNS)] for i in range(4)]
    img, d = _base("Candlestick Patterns", "4 setups to know", _EDU_FOOTER)
    gx0, gy0, gx1, gy1 = 60, 360, W - 60, H - 175
    mx, my, g = (gx0 + gx1) // 2, (gy0 + gy1) // 2, 16
    cells = [(gx0, gy0, mx - g, my - g), (mx + g, gy0, gx1, my - g),
             (gx0, my + g, mx - g, gy1), (mx + g, my + g, gx1, gy1)]
    for cell, it in zip(cells, items):
        _mini_panel(d, *cell, it, tag=True)
    caption = ("Candlestick patterns 101 — 4 setups to know:\n • " +
               "\n • ".join(f"{it['title']} → {_signal_of(it)}" for it in items) + _EDU_TAGS)
    return img, caption


def _edu_signals6(index):
    items = [PATTERNS[(index + i) % len(PATTERNS)] for i in range(6)]
    img, d = _base("Patterns & Signals", "buy / sell at a glance", _EDU_FOOTER)
    gx0, gy0, gx1, gy1 = 60, 360, W - 60, H - 175
    g = 14
    colw = (gx1 - gx0 - g) // 2
    rowh = (gy1 - gy0 - 2 * g) // 3
    cells = []
    for r in range(3):
        for c in range(2):
            x0 = gx0 + c * (colw + g)
            y0 = gy0 + r * (rowh + g)
            cells.append((x0, y0, x0 + colw, y0 + rowh))
    for cell, it in zip(cells, items):
        _mini_panel(d, *cell, it, tag=True)
    caption = ("Candlestick patterns & their signals:\n • " +
               "\n • ".join(f"{it['title']} → {_signal_of(it)}" for it in items) + _EDU_TAGS)
    return img, caption


def _edu_rules(index):
    img, d = _base("Trading rules", "the basics that keep you alive", _EDU_FOOTER)
    rules = [RULES[(index + i) % len(RULES)] for i in range(5)]
    y = 372
    row = (H - 175 - y) // 5
    tf, bf = _font(34), _font(27, False)
    for i, (title, txt) in enumerate(rules):
        cyc = y + i * row + 26
        d.ellipse([66, cyc - 26, 66 + 52, cyc + 26], fill=HILITE, outline=INK, width=3)
        num = str(i + 1)
        d.text((66 + (52 - d.textlength(num, font=tf)) / 2, cyc - 22), num, font=tf, fill=INK)
        d.text((146, cyc - 30), _fit(d, title, tf, W - 200), font=tf, fill=INK)
        d.text((146, cyc + 8), _fit(d, txt, bf, W - 200), font=bf, fill=MUT)
    caption = ("Trading rules that keep you alive:\n • " +
               "\n • ".join(t for t, _ in rules) + _EDU_TAGS)
    return img, caption


# Modelli di scheda che RUOTANO, così i contenuti non sono mai tutti uguali.
_EDU_LAYOUTS = (_edu_single, _edu_grid4, _edu_rules, _edu_signals6)


def make_educational(index: int):
    """Crea la scheda didattica numero `index`. RUOTA tra vari MODELLI (singolo,
    griglia 2×2, regole, griglia segnali) così ogni contenuto è diverso.
    Ritorna (path, caption) o (None, None)."""
    if Image is None:
        return None, None
    try:
        layout = _EDU_LAYOUTS[index % len(_EDU_LAYOUTS)]
        img, caption = layout(index)
        path = _new_path("edu")
        img.save(path, "PNG")
        return path, caption
    except Exception:
        return None, None


_GENERIC_CANDLES = [
    [(38, 34, 32, 40), (34, 48, 32, 50), (48, 62, 46, 64), (62, 76, 60, 78)],
    [(35, 45, 30, 48), (45, 38, 32, 47), (38, 46, 31, 49), (46, 58, 44, 66)],
    [(60, 52, 50, 62), (52, 58, 48, 60), (58, 50, 46, 62), (50, 64, 48, 66)],
    [(40, 52, 38, 54), (52, 46, 44, 55), (46, 58, 44, 60), (58, 68, 56, 70)],
]


# ==============================================================================
#  STILI GRAFICI MULTIPLI — così i post NON sono mai tutti uguali
# ------------------------------------------------------------------------------
#  Ogni "tip" (titolo + sottotitolo + spiegazione) può essere disegnato in stili
#  molto diversi tra loro (quaderno, neon scuro, gradiente, minimale, terminale).
#  Uno stile diverso a rotazione a ogni post → il profilo sembra vario e curato,
#  non lo stesso template ripetuto. Tutto in Pillow, robusto: se uno stile fallisce
#  si ripiega sul quaderno (che c'è sempre).
# ==============================================================================

_FONT_FILES = {
    "sansB": ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "sans":  ["/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "serifB": ["/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
    "serif": ["/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "monoB": ["/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
    "mono":  ["/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
}
_FONT_CACHE = {}


def _f(size, fam="sansB"):
    key = (size, fam)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    font = None
    for p in _FONT_FILES.get(fam, []):
        try:
            font = ImageFont.truetype(p, size)
            break
        except Exception:
            continue
    if font is None:
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
    _FONT_CACHE[key] = font
    return font


def _draw_wrapped(d, x, y, text, font, fill, max_w, line_h, max_lines=99, center=False, cx=None):
    """Scrive `text` andando a capo dentro `max_w`. Ritorna la y finale."""
    for i, line in enumerate(_wrap(d, text, font, max_w)):
        if i >= max_lines:
            break
        if center and cx is not None:
            tw = d.textlength(line, font=font)
            d.text((cx - tw / 2, y), line, font=font, fill=fill)
        else:
            d.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


def _vgrad(w, h, top, bottom):
    """Sfondo con gradiente verticale (solo Pillow, niente numpy)."""
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for yy in range(h):
        t = yy / max(1, h - 1)
        d.line([(0, yy), (w, yy)],
               fill=(int(top[0] + (bottom[0] - top[0]) * t),
                     int(top[1] + (bottom[1] - top[1]) * t),
                     int(top[2] + (bottom[2] - top[2]) * t)))
    return img


def _series(seed, n=30, up=True):
    """Serie di valori 0..1 morbida e in trend (per le linee/sparkline)."""
    rnd = random.Random(hash(("s", seed)) & 0xFFFFFFFF)
    v = 0.32 if up else 0.68
    drift = (0.42 if up else -0.42) / n
    out = []
    for _ in range(n):
        v += drift + rnd.uniform(-0.045, 0.045)
        v = max(0.08, min(0.92, v))
        out.append(v)
    return out


def _gen_candles(seed, n=7, up=True):
    """Candele (o,c,lo,hi) in unità 0..100, in trend, diverse per ogni titolo."""
    rnd = random.Random(hash(("c", seed)) & 0xFFFFFFFF)
    base = 28.0 if up else 72.0
    out = []
    for _ in range(n):
        o = max(10, min(90, base + rnd.uniform(-5, 5)))
        move = (rnd.uniform(3, 11) if up else -rnd.uniform(3, 11)) + rnd.uniform(-4, 4)
        c = max(8, min(92, o + move))
        lo = max(3, min(o, c) - rnd.uniform(2, 6))
        hi = min(97, max(o, c) + rnd.uniform(2, 6))
        out.append((o, c, lo, hi))
        base = max(14, min(86, c + (rnd.uniform(0, 6) if up else -rnd.uniform(0, 6))))
    return out


def _sparkline(d, box, vals, color, width=6, glow=None, dot=True):
    """Linea morbida dentro `box` (x0,y0,x1,y1). `glow` = colore alone opzionale."""
    x0, y0, x1, y1 = box
    n = len(vals)
    pts = [(x0 + (x1 - x0) * i / (n - 1), y1 - (y1 - y0) * v) for i, v in enumerate(vals)]
    try:
        if glow:
            for gw in (width + 12, width + 6):
                d.line(pts, fill=glow, width=gw, joint="curve")
        d.line(pts, fill=color, width=width, joint="curve")
    except TypeError:  # Pillow più vecchio senza joint="curve"
        if glow:
            for gw in (width + 12, width + 6):
                d.line(pts, fill=glow, width=gw)
        d.line(pts, fill=color, width=width)
    if dot:
        px, py = pts[-1]
        r = width + 4
        d.ellipse([px - r, py - r, px + r, py + r], fill=color)


def _candles_on(d, box, specs, up_col, down_col, wick_col):
    """Candele dentro `box` con colori a piacere (per fondi scuri o chiari)."""
    x0, y0, x1, y1 = box
    n = len(specs)
    slot = (x1 - x0) / n
    cw = min(52, slot * 0.52)

    def yy(v):
        return y1 - (v / 100.0) * (y1 - y0)

    for i, (o, c, lo, hi) in enumerate(specs):
        cx = x0 + slot * (i + 0.5)
        col = up_col if c >= o else down_col
        d.line([(cx, yy(hi)), (cx, yy(lo))], fill=wick_col, width=3)
        top, bot = yy(max(o, c)), yy(min(o, c))
        if abs(bot - top) < 8:
            bot = top + 8
        d.rounded_rectangle([cx - cw / 2, top, cx + cw / 2, bot], 4, fill=col)


def _uptrend(title, sub, expl):
    """Indovina se il tip è 'positivo/rialzista' per orientare il grafichino."""
    s = (title + " " + sub + " " + expl).lower()
    neg = ("don't", "not", "lose", "loss", "avoid", "panic", "mistake", "risk",
           "fear", "drop", "bear", "wipe", "never", "stop-loss", "stop loss")
    return not any(w in s for w in neg)


# ---- STILE 1: quaderno (il classico VcriptoV) --------------------------------
def _style_notebook(title, sub, expl):
    img, d = _base(title, sub, "Learn with VcriptoV • educational, not financial advice")
    y = 355
    for line in _wrap(d, expl, _font(32, False), W - 120)[:6]:
        d.text((60, y), line, font=_font(32, False), fill=TXT)
        y += 46
    py = y + 30
    ph = H - 150 - py - 30
    if ph > 160:
        d.rounded_rectangle([60, py, W - 60, py + ph], 20, fill=CARD)
        _candles(d, _gen_candles(title, 7, _uptrend(title, sub, expl)),
                 110, py + 40, W - 220, ph - 80)
    return img


# ---- STILE 2: neon su fondo scuro (look "crypto/tech") -----------------------
def _style_neon(title, sub, expl):
    BG2 = (11, 14, 20)
    NEON = (54, 245, 160)
    CYAN = (96, 214, 255)
    GRID = (24, 30, 42)
    GREY = (168, 176, 190)
    img = Image.new("RGB", (W, H), BG2)
    d = ImageDraw.Draw(img)
    for gx in range(0, W, 60):
        d.line([(gx, 0), (gx, H)], fill=GRID, width=1)
    for gy in range(0, H, 60):
        d.line([(0, gy), (W, gy)], fill=GRID, width=1)
    d.ellipse([60, 66, 104, 110], outline=NEON, width=5)
    d.line([(72, 92), (92, 92)], fill=NEON, width=6)
    d.text((122, 64), "VcriptoV", font=_f(44, "sansB"), fill=(240, 244, 250))
    d.text((124, 112), "crypto signals", font=_f(26, "sans"), fill=GREY)
    y = 210
    y = _draw_wrapped(d, 60, y, title, _f(84, "sansB"), NEON, W - 120, 92, max_lines=3)
    if sub:
        d.text((62, y + 6), sub.upper(), font=_f(30, "monoB"), fill=CYAN)
        y += 56
    y += 24
    y = _draw_wrapped(d, 60, y, expl, _f(37, "sans"), (214, 220, 230), W - 120, 52, max_lines=6)
    py = max(y + 34, H - 520)
    d.rounded_rectangle([60, py, W - 60, H - 170], 26, fill=(17, 22, 31),
                        outline=(38, 48, 64), width=2)
    _sparkline(d, (110, py + 60, W - 110, H - 230),
               _series(title, 30, _uptrend(title, sub, expl)),
               NEON, width=7, glow=(20, 90, 66))
    d.line([(60, H - 150), (W - 60, H - 150)], fill=(38, 48, 64), width=2)
    d.text((60, H - 128), "educational • not financial advice", font=_f(24, "sans"), fill=GREY)
    d.text((60, H - 92), "→  link in bio", font=_f(30, "sansB"), fill=NEON)
    return img


# ---- STILE 3: gradiente audace (moderno, colori vivaci) ----------------------
_GRADS = [((99, 63, 214), (39, 24, 92)),    # viola → indaco
          ((17, 153, 142), (56, 239, 125)),  # verde acqua → verde
          ((255, 126, 95), (254, 180, 123)),  # arancio → pesca
          ((41, 128, 185), (109, 213, 250)),  # blu → azzurro
          ((131, 58, 180), (253, 89, 118))]   # magenta → rosa


def _style_gradient(title, sub, expl):
    top, bot = random.choice(_GRADS)
    img = _vgrad(W, H, top, bot).convert("RGBA")
    d = ImageDraw.Draw(img)
    WHITE = (255, 255, 255)
    SOFT = (255, 255, 255, 235)
    d.ellipse([60, 66, 104, 110], outline=WHITE, width=5)
    d.line([(72, 92), (92, 92)], fill=WHITE, width=6)
    d.text((122, 66), "VcriptoV", font=_f(42, "sansB"), fill=WHITE)
    # pill sottotitolo (bianco pieno + testo scuro, così è sempre leggibile)
    y = 210
    if sub:
        pf = _f(28, "sansB")
        tw = d.textlength(sub.upper(), font=pf)
        d.rounded_rectangle([60, y, 60 + tw + 44, y + 50], 25, fill=(255, 255, 255, 255))
        d.text((82, y + 9), sub.upper(), font=pf, fill=(30, 32, 44))
        y += 78
    y = _draw_wrapped(d, 60, y, title, _f(90, "serifB"), WHITE, W - 120, 98, max_lines=3)
    # scheda semi-trasparente con la spiegazione
    py = y + 34
    card_h = 0
    tmp = _wrap(d, expl, _f(38, "sans"), W - 200)[:6]
    card_h = 60 + len(tmp) * 54
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([60, py, W - 60, py + card_h], 26, fill=(0, 0, 0, 70))
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img)
    ty = py + 30
    for line in tmp:
        d.text((100, ty), line, font=_f(38, "sans"), fill=SOFT)
        ty += 54
    _sparkline(d, (100, py + card_h + 40, W - 100, H - 210),
               _series(title, 26, _uptrend(title, sub, expl)),
               WHITE, width=6, glow=(255, 255, 255, 60))
    d.text((60, H - 92), "→  link in bio", font=_f(30, "sansB"), fill=WHITE)
    return img.convert("RGB")


# ---- STILE 4: minimale chiaro (editoriale, elegante) -------------------------
def _style_minimal(title, sub, expl):
    BG4 = (246, 245, 241)
    INK4 = (26, 28, 32)
    ACC = (44, 150, 96)
    GREY = (120, 124, 130)
    img = Image.new("RGB", (W, H), BG4)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=ACC)
    d.text((60, 70), "VcriptoV", font=_f(40, "serifB"), fill=INK4)
    d.text((62, 120), "crypto signals", font=_f(24, "sans"), fill=GREY)
    if sub:
        d.text((62, 210), sub.upper(), font=_f(28, "sansB"), fill=ACC)
    y = 258
    y = _draw_wrapped(d, 60, y, title, _f(88, "serifB"), INK4, W - 120, 94, max_lines=3)
    d.line([(62, y + 20), (240, y + 20)], fill=ACC, width=4)
    y += 60
    y = _draw_wrapped(d, 60, y, expl, _f(37, "sans"), (62, 66, 72), W - 120, 52, max_lines=6)
    _sparkline(d, (62, max(y + 40, H - 430), W - 62, H - 200),
               _series(title, 28, _uptrend(title, sub, expl)),
               ACC, width=6, glow=None)
    d.line([(60, H - 150), (W - 60, H - 150)], fill=(214, 212, 205), width=2)
    d.text((60, H - 128), "educational • not financial advice", font=_f(24, "sans"), fill=GREY)
    d.text((60, H - 92), "→  link in bio", font=_f(30, "sansB"), fill=ACC)
    return img


# ---- STILE 5: pannello "terminale" scuro (candele) ---------------------------
def _style_ticker(title, sub, expl):
    BG5 = (15, 21, 36)
    PANEL = (20, 28, 46)
    BORD = (44, 56, 82)
    WHITE = (236, 240, 248)
    AMBER = (255, 196, 87)
    GREEN2 = (49, 208, 138)
    RED2 = (255, 107, 107)
    GREY = (150, 160, 180)
    img = Image.new("RGB", (W, H), BG5)
    d = ImageDraw.Draw(img)
    # header con "chip" mono e pallino LIVE
    d.rounded_rectangle([60, 64, 250, 116], 10, fill=PANEL, outline=BORD, width=2)
    d.text((80, 76), "VCRIPTOV", font=_f(28, "monoB"), fill=WHITE)
    d.ellipse([W - 190, 80, W - 172, 98], fill=GREEN2)
    d.text((W - 160, 76), "LIVE", font=_f(26, "monoB"), fill=GREEN2)
    y = 200
    y = _draw_wrapped(d, 60, y, title, _f(78, "sansB"), WHITE, W - 120, 88, max_lines=3)
    if sub:
        d.text((62, y + 4), sub.upper(), font=_f(28, "monoB"), fill=AMBER)
        y += 52
    y += 20
    y = _draw_wrapped(d, 60, y, expl, _f(35, "sans"), (206, 214, 228), W - 120, 50, max_lines=5)
    py = max(y + 30, H - 560)
    d.rounded_rectangle([60, py, W - 60, H - 170], 20, fill=PANEL, outline=BORD, width=2)
    # righe griglia orizzontali del "grafico"
    for k in range(1, 5):
        gy = py + 40 + (H - 210 - py - 40) * k / 5
        d.line([(90, gy), (W - 90, gy)], fill=(30, 40, 62), width=1)
    _candles_on(d, (110, py + 40, W - 110, H - 210),
                _gen_candles(title, 8, _uptrend(title, sub, expl)),
                GREEN2, RED2, (95, 108, 135))
    d.text((60, H - 128), "educational • not financial advice", font=_f(24, "mono"), fill=GREY)
    d.text((60, H - 92), "→  link in bio", font=_f(30, "monoB"), fill=AMBER)
    return img


_TIP_STYLES = (_style_notebook, _style_neon, _style_gradient, _style_minimal, _style_ticker)


def _next_style_index():
    """Contatore persistente su file: fa RUOTARE gli stili così due post di fila
    non hanno mai lo stesso look. Se il file non è scrivibile, sceglie a caso."""
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        p = os.path.join(OUT_DIR, ".stylecounter")
        n = 0
        try:
            with open(p) as fh:
                n = int((fh.read() or "0").strip() or 0)
        except Exception:
            n = random.randint(0, 9999)
        n += 1
        try:
            with open(p, "w") as fh:
                fh.write(str(n))
        except Exception:
            pass
        return n
    except Exception:
        return random.randint(0, 9999)


def _render_tip(title, sub, expl, idx=None):
    """Disegna il tip in UNO stile a rotazione. Ripiego sicuro: il quaderno."""
    if idx is None:
        idx = _next_style_index()
    style = _TIP_STYLES[idx % len(_TIP_STYLES)]
    try:
        img = style(title, sub, expl)
        if img is not None:
            return img
    except Exception:
        pass
    try:
        return _style_notebook(title, sub, expl)
    except Exception:
        return None


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
        img = _render_tip(title, sub, expl)
        if img is None:
            return None, None
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


def make_custom(title: str, sub: str, expl: str):
    """Crea una scheda-immagine dal TESTO fornito dal sito (già scritto dall'AI lì:
    qui NON serve l'AI). Serve per i reel 'sempre diversi' su Instagram. Ritorna
    (path, None) o (None, None)."""
    if Image is None:
        return None, None
    try:
        import random as _random
        title = (title or "").strip()[:38]
        sub = (sub or "").strip()[:38]
        expl = (expl or "").strip()
        if not (title and expl):
            return None, None
        img = _render_tip(title, sub, expl)
        if img is None:
            return None, None
        path = _new_path("custom")
        img.save(path, "PNG")
        return path, None
    except Exception:
        return None, None


def make_custom_reel(title: str, sub: str, expl: str):
    """Reel (video) dalla scheda-testo fornita dal sito. (path_mp4, None) o (None, None)."""
    if Image is None or not _VIDEO_OK:
        return None, None
    try:
        path, _ = make_custom(title, sub, expl)
        if not path:
            return None, None
        card = Image.open(path).convert("RGB")
        out = _new_path("reelcustom", "mp4")
        _card_to_reel(card, out)
        try:
            os.remove(path)
        except Exception:
            pass
        return out, None
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


def cleanup_old(keep_seconds: int = 2 * 3600, keep_last: int = 6):
    """Cancella i video/immagini già pubblicati per NON riempire il disco.
    Instagram scarica il video in pochi minuti, quindi NON serve conservarlo:
    - cancella tutto ciò che ha più di `keep_seconds` (default 2 ore);
    - e comunque tiene al massimo gli ultimi `keep_last` file (i più recenti).
    Così, anche generando tanti video (es. molti tentativi), il disco resta piccolo."""
    try:
        now = time.time()
        entries = []
        for name in os.listdir(OUT_DIR):
            p = os.path.join(OUT_DIR, name)
            try:
                entries.append((os.path.getmtime(p), p))
            except Exception:
                pass
        # 1) via i più vecchi della soglia di tempo
        for mt, p in entries:
            if now - mt > keep_seconds:
                try:
                    os.remove(p)
                except Exception:
                    pass
        # 2) se ne restano ancora troppi, tieni solo gli ultimi keep_last (per data)
        remaining = [(mt, p) for mt, p in entries if os.path.exists(p)]
        remaining.sort(reverse=True)   # più recenti per primi
        for mt, p in remaining[keep_last:]:
            try:
                os.remove(p)
            except Exception:
                pass
    except Exception:
        pass
