"""
FORMATI DI REEL diversi tra loro (il sito sceglie quale fare e manda testi e dati).

  market  → "CRYPTO TODAY": prezzo di Bitcoin che scorre fino al valore vero e barre
            delle monete che salgono/scendono di più (dati veri)
  quiz    → domanda + 3 risposte + conto alla rovescia + soluzione (fa commentare)
  myth    → MITO (rosso, timbro X) contro REALTÀ (verde, spunta)
  top5    → classifica da 5 a 1, sfondo chiaro, numeri enormi
  fng     → indicatore Paura & Avidità con la lancetta che oscilla (dato vero)
  candles → lezione: le candele si disegnano una a una e il pattern si illumina
  chat    → come arriva un segnale su Telegram (telefono, messaggio, pulsanti) — ESEMPIO
  promo   → inserzione animata (promo_reel.py)

Ogni formato ha il suo stile grafico, così il profilo non sembra sempre uguale.
Un fotogramma alla volta in RAM (512MB), x264 ultrafast, musica generata qui.
"""
from __future__ import annotations

import gc
import math
import os
import random
import time

import numpy as np
from PIL import Image, ImageDraw

from promo_reel import FPS, H, OUT_DIR, W, _beat, _ease, _f, _logo_white, _smooth

WHITE = (245, 247, 250)
BLACK = (12, 12, 14)
GREEN = (22, 199, 132)
RED = (234, 57, 67)
GREY = (140, 146, 156)


# ------------------------------------------------------------------ utilità
def _wrap(d, text, font, max_w):
    words, lines, cur = str(text).split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def _text_block(d, text, font, fill, cx, y, max_w, lh, max_lines=6):
    for line in _wrap(d, text, font, max_w)[:max_lines]:
        tw = d.textlength(line, font=font)
        d.text((cx - tw / 2, y), line, font=font, fill=fill)
        y += lh
    return y


def _solid(col):
    return Image.new("RGB", (W, H), col)


def _grad(top, bot):
    g = np.linspace(0, 1, H)[:, None, None]
    arr = np.array(top)[None, None, :] * (1 - g) + np.array(bot)[None, None, :] * g
    return Image.fromarray(np.repeat(arr, W, axis=1).astype("uint8"), "RGB")


def _brand(ov, d, dark=True):
    logo = _logo_white()
    col = WHITE if dark else BLACK
    if logo and dark:
        ov.alpha_composite(logo, (54, 60))
        d.text((154, 84), "VCRIPTOV", font=_f(38), fill=col + (255,))
    else:
        d.text((60, 84), "VCRIPTOV", font=_f(38), fill=col + (255,))


def _footer(d, dark=True, text="Educational, not financial advice"):
    f = _f(24, False)
    d.text((W / 2 - d.textlength(text, font=f) / 2, H - 52), text, font=f,
           fill=((120, 126, 136, 255) if dark else (90, 90, 96, 255)))


STILL = {"on": False}      # True = invece del video salva l'immagine finale (post 4:5)


def _encode(draw, bg, seconds, out_path, bpm_seed=0):
    """draw(t, ov, d) disegna gli elementi del fotogramma su un livello trasparente."""
    import imageio.v2 as imageio
    from content import _finalize_reel
    from promo_reel import StillWriter
    raw = out_path + ".raw.mp4"
    frames = range(int(seconds * FPS))
    if STILL["on"]:
        frames = [int(seconds * FPS) - 2]
        w = StillWriter(out_path)
    else:
        w = imageio.get_writer(raw, fps=FPS, codec="libx264", quality=7, macro_block_size=1,
                               ffmpeg_params=["-preset", "ultrafast", "-threads", "1", "-bf", "0"])
    try:
        for fi in frames:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            draw(fi / FPS, ov, d)
            fr = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
            w.append_data(np.asarray(fr))
            del fr, ov, d
            if fi % 24 == 0:
                gc.collect()
    finally:
        w.close()
    if STILL["on"]:
        return out_path
    music = out_path + ".wav"
    try:
        _beat(music, seconds)
    except Exception:
        music = None
    _finalize_reel(raw, out_path, music)
    if music and os.path.exists(music):
        os.remove(music)
    return out_path


def _fmt_price(p):
    p = float(p or 0)
    if p >= 1000:
        return f"{p:,.0f}"
    if p >= 1:
        return f"{p:,.2f}"
    return f"{p:.4g}"


# ------------------------------------------------------------------ market
def _market(data, out):
    coins = data.get("movers") or []
    btc = data.get("btc") or {}
    date = data.get("date") or time.strftime("%d/%m/%Y")
    bg = _grad((10, 12, 22), (14, 18, 34))
    ups = [c for c in coins if (c.get("ch24") or 0) >= 0][:3]
    downs = [c for c in coins if (c.get("ch24") or 0) < 0][:3]
    rows = ups + downs
    mx = max([abs(c.get("ch24") or 0) for c in rows] + [1])

    def draw(t, ov, d):
        _brand(ov, d)
        # banner "breaking"
        p = _ease(t / 0.4)
        if p > 0.01:
            bw = W * min(1, p)
            d.rectangle([0, 190, bw, 300], fill=(234, 57, 67, 255))
            d.text((60, 205), "CRYPTO TODAY", font=_f(76), fill=WHITE + (255,))
            d.text((W - 60 - d.textlength(date, font=_f(36, False)), 232), date, font=_f(36, False), fill=WHITE + (230,))
        # prezzo BTC che scorre
        if btc.get("price"):
            q = _smooth((t - 0.5) / 1.6)
            if q > 0:
                d.text((60, 360), "BITCOIN", font=_f(46), fill=GREY + (255,))
                val = "$" + _fmt_price(btc["price"] * (0.9 + 0.1 * q))
                d.text((60, 420), val, font=_f(150), fill=WHITE + (255,))
                ch = btc.get("ch24")
                if ch is not None and q > 0.95:
                    col = GREEN if ch >= 0 else RED
                    d.text((64, 590), f"{'▲' if ch >= 0 else '▼'} {abs(ch):.1f}% in 24h", font=_f(54), fill=col + (255,))
        # barre delle monete
        d.text((60, 720), "WHO'S UP, WHO'S DOWN", font=_f(44), fill=GREY + (int(255 * min(1, max(0, (t - 2.2) * 3))),))
        for i, c in enumerate(rows):
            q = _ease((t - 2.5 - 0.35 * i) / 0.6)
            if q <= 0.01:
                continue
            y = 800 + i * 150
            ch = c.get("ch24") or 0
            col = GREEN if ch >= 0 else RED
            bw = (W - 520) * abs(ch) / mx * min(1, q)
            d.text((60, y + 18), c.get("sym", "?")[:6], font=_f(56), fill=WHITE + (255,))
            d.rounded_rectangle([270, y + 10, 270 + max(24, bw), y + 100], 18, fill=col + (255,))
            d.text((290 + max(24, bw), y + 26), f"{ch:+.1f}%", font=_f(48), fill=col + (255,))
        if t > 6.5:
            a = int(255 * min(1, (t - 6.5) * 2))
            _text_block(d, "Analysis of every coin: link in bio", _f(46), WHITE + (a,), W / 2, 1760, W - 120, 56)
        _footer(d)
    return _encode(draw, bg, 9.0, out)


# ------------------------------------------------------------------ quiz
def _quiz(data, out):
    q = data.get("q") or "What does a stop-loss do?"
    opts = (data.get("options") or ["Sells if the price drops too far", "Buys more", "Locks your account"])[:3]
    ans = int(data.get("answer") or 0) % len(opts)
    expl = data.get("expl") or ""
    bg = _solid((255, 214, 10))

    def draw(t, ov, d):
        d.text((60, 84), "VCRIPTOV", font=_f(38), fill=BLACK + (255,))
        p = _ease(t / 0.45)
        if p > 0.01:
            s = int(120 * (0.6 + 0.4 * p))
            tag = "CRYPTO QUIZ"
            d.rounded_rectangle([W / 2 - 300, 200, W / 2 + 300, 200 + s + 20], 30, fill=BLACK + (255,))
            d.text((W / 2 - d.textlength(tag, font=_f(int(s * .6))) / 2, 214 + s * .12), tag, font=_f(int(s * .6)),
                   fill=(255, 214, 10, 255))
        if t > 0.6:
            n = int(len(q) * min(1, (t - 0.6) / 1.2))       # la domanda si "scrive"
            _text_block(d, q[:n], _f(72), BLACK + (255,), W / 2, 420, W - 120, 86, 4)
        reveal = t > 6.2 and not STILL["on"]           # nel post la risposta resta nascosta: si commenta
        for i, o in enumerate(opts):
            e = _ease((t - 2.0 - 0.3 * i) / 0.5)
            if e <= 0.01:
                continue
            y = 850 + i * 190
            x = 60 + 400 * (1 - e)
            good = reveal and i == ans
            bad = reveal and i != ans
            fill = (GREEN + (255,)) if good else ((255, 255, 255, 110) if bad else (255, 255, 255, 255))
            d.rounded_rectangle([x, y, x + W - 120, y + 150], 36, fill=fill, outline=BLACK + (255,), width=5)
            d.text((x + 36, y + 38), "ABC"[i], font=_f(64), fill=BLACK + (255,))
            lines = _wrap(d, o, _f(46), W - 320)[:2]
            for k, ln in enumerate(lines):
                d.text((x + 120, y + (48 if len(lines) == 1 else 26) + k * 52), ln, font=_f(46),
                       fill=BLACK + (120 if bad else 255,))
        if 3.4 < t <= 6.2 and not STILL["on"]:              # conto alla rovescia
            k = 3 - int((t - 3.4) / 0.93)
            fr = ((t - 3.4) % 0.93) / 0.93
            r = 110 * (1 + 0.15 * (1 - fr))
            d.ellipse([W / 2 - r, 1480 - r, W / 2 + r, 1480 + r], fill=BLACK + (255,))
            txt = str(max(1, k))
            d.text((W / 2 - d.textlength(txt, font=_f(130)) / 2, 1400), txt, font=_f(130), fill=(255, 214, 10, 255))
        if reveal and expl:
            a = int(255 * min(1, (t - 6.4) * 2))
            _text_block(d, expl, _f(44, False), BLACK + (a,), W / 2, 1450, W - 140, 54, 4)
        if STILL["on"]:
            _text_block(d, "A, B or C? Answer in the comments", _f(62), BLACK + (255,), W / 2, 1500, W - 120, 72)
        elif t > 7.8:
            _text_block(d, "Did you get it? Tell me in the comments", _f(42), BLACK + (255,), W / 2, 1760, W - 120, 50)
        _footer(d, dark=False)
    return _encode(draw, bg, 10.0, out)


# ------------------------------------------------------------------ mito / realtà
def _myth(data, out):
    items = (data.get("items") or [["Crypto is just a scam", "Scams exist, but Bitcoin is an open, verifiable network"]])[:2]
    bg = _solid((15, 15, 18))
    slot = 4.6

    def draw(t, ov, d):
        i = min(len(items) - 1, int(t / slot))
        lt = t - i * slot
        myth, real = items[i]
        # metà alta rossa, metà bassa verde (entrano scorrendo)
        pa = _ease(lt / 0.4)
        d.rectangle([0, 0, W, int(H / 2 * pa)], fill=(120, 18, 26, 255))
        pb = _ease((lt - 1.6) / 0.4)
        if pb > 0.01:
            d.rectangle([0, H - int(H / 2 * pb), W, H], fill=(8, 92, 60, 255))
        if pa > 0.5:
            d.text((60, 160), "MYTH", font=_f(110), fill=WHITE + (255,))
            _text_block(d, f"“{myth}”", _f(64), WHITE + (255,), W / 2, 360, W - 140, 78, 5)
            s = _ease((lt - 0.8) / 0.3)                      # timbro X
            if s > 0.01:
                r = 110 * (2 - s)
                cx, cy = W - 170, 220
                d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=(255, 255, 255, 255), width=22)
                d.line([(cx - r, cy + r), (cx + r, cy - r)], fill=(255, 255, 255, 255), width=22)
        if pb > 0.5:
            d.text((60, H / 2 + 70), "REALITY", font=_f(110), fill=WHITE + (255,))
            _text_block(d, real, _f(58), WHITE + (255,), W / 2, H / 2 + 270, W - 140, 72, 6)
            s = _ease((lt - 2.2) / 0.3)
            if s > 0.01:
                cx, cy = W - 170, H / 2 + 130
                d.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=WHITE + (255,))
                d.line([(cx - 45, cy), (cx - 10, cy + 40), (cx + 50, cy - 35)], fill=(8, 92, 60, 255), width=18)
        d.text((W / 2 - d.textlength("VCRIPTOV", font=_f(30)) / 2, H / 2 - 18), "VCRIPTOV", font=_f(30),
               fill=(255, 255, 255, 120))
        _footer(d)
    return _encode(draw, bg, slot * len(items), out)


# ------------------------------------------------------------------ top 5
def _top5(data, out):
    title = data.get("title") or "5 mistakes crypto beginners make"
    items = (data.get("items") or ["Investing money you need", "No stop-loss", "Chasing pumps",
                                   "Following random tips", "Keeping it all on an exchange"])[:5]
    accent = random.Random(title).choice([(255, 90, 54), (36, 99, 235), (22, 163, 74), (147, 51, 234)])
    bg = _solid((250, 249, 246))
    step = 1.35

    def draw(t, ov, d):
        d.text((60, 84), "VCRIPTOV", font=_f(38), fill=BLACK + (255,))
        p = _ease(t / 0.5)
        if p > 0.01:
            d.rectangle([60, 200, 60 + 14, 200 + 150 * p], fill=accent + (255,))
            _text_block(d, title.upper(), _f(70), BLACK + (255,), W / 2 + 10, 200, W - 170, 82, 3)
        n = len(items)
        for k in range(n):                                     # dal 5 all'1
            e = _ease((t - 1.0 - step * k) / 0.45)
            if e <= 0.01:
                continue
            num = n - k
            y = 520 + k * 240
            x = 60 - 300 * (1 - e)
            d.text((x, y - 20), str(num), font=_f(190), fill=accent + (255,))
            _lines = _wrap(d, items[num - 1], _f(56), W - 330)[:2]
            for j, ln in enumerate(_lines):
                d.text((x + 190, y + 40 + j * 64 - (20 if len(_lines) > 1 else 0)), ln, font=_f(56), fill=BLACK + (255,))
        if t > 1.0 + step * n:
            a = int(255 * min(1, (t - 1.0 - step * n) * 2))
            _text_block(d, ("Save this post so you don't forget" if STILL["on"] else "Save this video so you don't forget"), _f(44), accent + (a,), W / 2, 1760, W - 120, 52)
        _footer(d, dark=False)
    return _encode(draw, bg, 1.0 + step * len(items) + 2.0, out)


# ------------------------------------------------------------------ paura & avidità
def _fng(data, out):
    v = max(0, min(100, int(data.get("value") or 50)))
    label = data.get("label") or ""
    prev = data.get("prev")
    bg = _grad((8, 8, 12), (22, 22, 30))
    cx, cy, R = W / 2, 1050, 400

    def col_at(x):
        if x < 25:
            return (234, 57, 67)
        if x < 45:
            return (245, 140, 50)
        if x < 56:
            return (240, 200, 60)
        if x < 76:
            return (140, 200, 70)
        return (22, 199, 132)

    def draw(t, ov, d):
        _brand(ov, d)
        _text_block(d, "FEAR OR GREED?", _f(88), WHITE + (255,), W / 2, 220, W - 100, 100)
        _text_block(d, "The crypto market mood today", _f(44, False), GREY + (255,), W / 2, 340, W - 100, 52)
        for k in range(0, 100):                               # arco colorato
            a0 = math.pi + math.pi * k / 100
            a1 = math.pi + math.pi * (k + 1.2) / 100
            d.arc([cx - R, cy - R, cx + R, cy + R], math.degrees(a0), math.degrees(a1), fill=col_at(k) + (255,), width=70)
        # lancetta: parte da 0, oscilla e si ferma sul valore vero
        p = _smooth((t - 0.6) / 2.4)
        wob = math.sin((t - 0.6) * 9) * 8 * max(0, 1 - (t - 0.6) / 3.2) if t > 0.6 else 0
        val = v * p + (wob if p > 0.3 else 0)
        ang = math.pi + math.pi * max(0, min(100, val)) / 100
        ex, ey = cx + math.cos(ang) * (R - 60), cy + math.sin(ang) * (R - 60)
        d.line([(cx, cy), (ex, ey)], fill=WHITE + (255,), width=16)
        d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=WHITE + (255,))
        num = str(int(round(max(0, min(100, val)))))
        d.text((cx - d.textlength(num, font=_f(200)) / 2, cy + 60), num, font=_f(200), fill=col_at(v) + (255,))
        if t > 3.2:
            a = int(255 * min(1, (t - 3.2) * 2))
            _text_block(d, label.upper(), _f(80), col_at(v) + (a,), W / 2, cy + 300, W - 100, 90)
            if prev is not None:
                _text_block(d, f"Yesterday: {prev}", _f(44, False), GREY + (a,), W / 2, cy + 410, W - 100, 52)
        if t > 5.0:
            a = int(255 * min(1, (t - 5.0) * 2))
            msg = ("When everyone is scared… what do you do?" if v < 45 else
                   "When everyone is greedy… watch the risk" if v > 55 else "Undecided market: patience")
            _text_block(d, msg, _f(46), WHITE + (a,), W / 2, 1730, W - 120, 56)
        _footer(d)
    return _encode(draw, bg, 8.0, out)


# ------------------------------------------------------------------ candele
_PATTERNS = {
    "martello": ([(60, 56, 50, 62), (56, 52, 47, 57), (52, 48, 43, 53), (48, 49, 36, 50), (49, 55, 48, 56), (55, 60, 54, 61)], [3], True),
    "engulfing rialzista": ([(62, 58, 56, 63), (58, 54, 52, 59), (54, 50, 49, 55), (50, 48, 47, 51), (47, 55, 46, 56), (55, 60, 54, 61)], [3, 4], True),
    "stella cadente": ([(40, 45, 39, 46), (45, 50, 44, 51), (50, 54, 49, 55), (54, 53, 52, 66), (53, 48, 47, 54), (48, 44, 43, 49)], [3], False),
    "engulfing ribassista": ([(40, 45, 39, 46), (45, 50, 44, 51), (50, 53, 49, 54), (53, 55, 52, 56), (56, 47, 46, 57), (47, 42, 41, 48)], [3, 4], False),
    "doppio minimo": ([(60, 52, 50, 61), (52, 45, 44, 53), (45, 52, 44, 53), (52, 46, 45, 53), (46, 53, 45, 54), (53, 60, 52, 61)], [1, 3], True),
    "doppio massimo": ([(40, 48, 39, 49), (48, 55, 47, 56), (55, 48, 47, 56), (48, 54, 47, 55), (54, 47, 46, 55), (47, 40, 39, 48)], [1, 3], False),
}


# nomi inglesi (dal sito) → disegno del pattern
_PATTERN_EN = {"hammer": "martello", "bullish engulfing": "engulfing rialzista", "shooting star": "stella cadente",
               "bearish engulfing": "engulfing ribassista", "double bottom": "doppio minimo",
               "double top": "doppio massimo"}


def _candles(data, out):
    name = (data.get("pattern") or "hammer").lower()
    candles, hi_idx, bull = _PATTERNS.get(_PATTERN_EN.get(name, name), _PATTERNS["martello"])
    desc = data.get("desc") or ("Spesso segnala un possibile rimbalzo." if bull else "Spesso segnala un possibile calo.")
    bg = _grad((12, 16, 20), (6, 10, 14))
    x0, x1, y0, y1 = 110, W - 110, 1350, 650
    lo = min(c[2] for c in candles) - 3
    hi = max(c[3] for c in candles) + 3
    Y = lambda v: y0 - (y0 - y1) * (v - lo) / (hi - lo)  # noqa: E731
    cw = (x1 - x0) / len(candles)

    def draw(t, ov, d):
        _brand(ov, d)
        _text_block(d, "READ THE CHART", _f(56), GREY + (255,), W / 2, 200, W - 100, 64)
        p = _ease((t - 0.2) / 0.5)
        if p > 0.01:
            _text_block(d, name.upper(), _f(int(100 * (0.6 + 0.4 * p))), WHITE + (255,), W / 2, 280, W - 80, 110)
        for gy in range(y1, y0 + 1, 140):
            d.line([(x0, gy), (x1, gy)], fill=(255, 255, 255, 18), width=2)
        for i, (o, c, lw, hg) in enumerate(candles):
            e = _ease((t - 1.0 - 0.45 * i) / 0.35)
            if e <= 0.01:
                continue
            cx_ = x0 + cw * (i + 0.5)
            col = GREEN if c >= o else RED
            top, bot = Y(max(o, c)), Y(min(o, c))
            mid = (top + bot) / 2
            top, bot = mid - (mid - top) * e, mid + (bot - mid) * e
            d.line([(cx_, Y(hg)), (cx_, Y(lw))], fill=col + (255,), width=6)
            d.rectangle([cx_ - cw * 0.3, top, cx_ + cw * 0.3, max(top + 6, bot)], fill=col + (255,))
        ht = 1.0 + 0.45 * len(candles) + 0.3
        if t > ht:                                          # evidenzio il pattern
            a = int(255 * min(1, (t - ht) * 2.5))
            xa = x0 + cw * min(hi_idx) + 6
            xb = x0 + cw * (max(hi_idx) + 1) - 6
            d.rounded_rectangle([xa, y1 - 30, xb, y0 + 30], 24, outline=(255, 214, 10, a), width=8)
            arrow = "▲ possible move up" if bull else "▼ possible move down"
            d.text((W / 2 - d.textlength(arrow, font=_f(60)) / 2, y0 + 70), arrow, font=_f(60),
                   fill=(GREEN if bull else RED) + (a,))
        if t > ht + 0.8:
            a = int(255 * min(1, (t - ht - 0.8) * 2))
            _text_block(d, desc, _f(46, False), WHITE + (a,), W / 2, 1580, W - 140, 56, 3)
            _text_block(d, "Follow for more lessons", _f(42), (255, 214, 10, a), W / 2, 1790, W - 120, 50)
        _footer(d)
    return _encode(draw, bg, 1.0 + 0.45 * len(candles) + 4.5, out)


# ------------------------------------------------------------------ chat telegram
def _chat(data, out):
    coin = (data.get("coin") or "BTC")[:6]
    buy = bool(data.get("is_buy", True))
    entry = data.get("entry") or ""
    sl = data.get("sl") or 5
    tp = data.get("tp") or 10
    bg = _grad((24, 36, 52), (14, 20, 30))
    px0, py0, px1, py1 = 150, 250, W - 150, 1650          # telefono

    def draw(t, ov, d):
        _text_block(d, "HOW A SIGNAL REACHES YOU", _f(56), WHITE + (255,), W / 2, 110, W - 80, 64)
        d.rounded_rectangle([px0, py0, px1, py1], 70, fill=(10, 14, 20, 255), outline=(70, 80, 95, 255), width=10)
        d.rounded_rectangle([px0 + 24, py0 + 24, px1 - 24, py1 - 24], 52, fill=(22, 30, 42, 255))
        d.rectangle([px0 + 24, py0 + 90, px1 - 24, py0 + 200], fill=(33, 44, 60, 255))
        d.ellipse([px0 + 50, py0 + 110, px0 + 120, py0 + 180], fill=(42, 171, 238, 255))
        d.text((px0 + 140, py0 + 112), "VcriptoV Bot", font=_f(40), fill=WHITE + (255,))
        d.text((px0 + 140, py0 + 158), "bot", font=_f(26, False), fill=GREY + (255,))
        by = py0 + 250
        if 0.8 < t < 2.2:                                    # "sta scrivendo…"
            d.rounded_rectangle([px0 + 50, by, px0 + 240, by + 80], 36, fill=(40, 52, 70, 255))
            for k in range(3):
                r = 10 + 4 * math.sin(t * 10 - k)
                cxk = px0 + 95 + k * 50
                d.ellipse([cxk - r, by + 40 - r, cxk + r, by + 40 + r], fill=(200, 210, 220, 255))
        e = _ease((t - 2.2) / 0.4)
        if e > 0.01:
            mx0, mx1 = px0 + 50, px1 - 70
            my1 = by + 560
            d.rounded_rectangle([mx0, by, mx1, by + (my1 - by) * min(1, e)], 30, fill=(43, 82, 120, 255))
            if e > 0.8:
                col = GREEN if buy else RED
                d.text((mx0 + 30, by + 26), "NEW SIGNAL", font=_f(34), fill=(255, 214, 10, 255))
                d.text((mx0 + 30, by + 80), f"{coin} — {'LONG' if buy else 'SHORT'}", font=_f(64), fill=col + (255,))
                y = by + 180
                for k, v in (("Entry", entry), ("Stop-loss", f"-{sl}%"), ("Target", f"+{tp}%")):
                    if not v:
                        continue
                    d.text((mx0 + 30, y), k, font=_f(40, False), fill=(210, 220, 230, 255))
                    d.text((mx1 - 30 - d.textlength(str(v), font=_f(42)), y), str(v), font=_f(42), fill=WHITE + (255,))
                    y += 70
                d.text((mx0 + 30, y + 10), "Risk shown · you decide", font=_f(32, False), fill=(190, 200, 210, 255))
            if e > 0.9:
                bw = (mx1 - mx0 - 20) / 2
                press = 3.6 < t < 4.4
                for k, (lab, col) in enumerate((("Invest", GREEN), ("Don't invest", (90, 100, 115)))):
                    xa = mx0 + k * (bw + 20)
                    sc = 0.94 if (press and k == 0) else 1
                    ya = my1 + 24
                    d.rounded_rectangle([xa + bw * (1 - sc) / 2, ya, xa + bw * (1 + sc) / 2, ya + 100 * sc], 26,
                                        fill=col + (255,))
                    d.text((xa + bw / 2 - d.textlength(lab, font=_f(38)) / 2, ya + 28), lab, font=_f(38), fill=WHITE + (255,))
                if t > 3.6:                                  # dito che tocca
                    fx, fy = mx0 + bw * 0.8, my1 + 150 + 40 * max(0, 1 - (t - 3.6) * 3)
                    d.ellipse([fx - 34, fy - 34, fx + 34, fy + 34], fill=(255, 255, 255, 90), outline=(255, 255, 255, 200), width=4)
                if t > 4.4:
                    a = int(255 * min(1, (t - 4.4) * 2))
                    d.rounded_rectangle([mx0, my1 + 160, mx1, my1 + 250], 30, fill=(22, 199, 132, a))
                    txt = "Order sent to YOUR exchange"
                    d.text((W / 2 - d.textlength(txt, font=_f(34)) / 2, my1 + 186), txt, font=_f(34), fill=WHITE + (a,))
        if t > 5.4:
            a = int(255 * min(1, (t - 5.4) * 2))
            _text_block(d, "Demo example · try VcriptoV, link in bio", _f(40), WHITE + (a,), W / 2, 1700, W - 100, 50)
        _footer(d)
    return _encode(draw, bg, 8.5, out)


RENDERERS = {"market": _market, "quiz": _quiz, "myth": _myth, "top5": _top5, "fng": _fng,
             "candles": _candles, "chat": _chat}


def render(kind: str, data: dict, out_path: str | None = None, still: bool = False) -> str:
    """Reel (mp4) o, con still=True, POST (png 4:5) dello stesso formato."""
    os.makedirs(OUT_DIR, exist_ok=True)
    ext = "png" if still else "mp4"
    out_path = out_path or os.path.join(OUT_DIR, f"{'post' if still else 'reel'}_{kind}_{int(time.time())}.{ext}")
    if kind == "promo":
        import promo_reel
        return promo_reel.render(int(data.get("index", 0) or 0), out_path, hook=data.get("hook"), still=still)[0]
    STILL["on"] = still
    try:
        return RENDERERS[kind](data or {}, out_path)
    finally:
        STILL["on"] = False
