"""
REEL "PUBBLICITÀ" di VcriptoV — video verticali ANIMATI in stile inserzione.

I vecchi reel erano una scheda ferma per 5 secondi (solo il logo pulsava): pochi
secondi di niente → ~30 visualizzazioni. Questi sono costruiti come le inserzioni
che funzionano sui social:
  • GANCIO nei primi 0,5 s: titolo ENORME che "esplode" sullo schermo (riga 1 al
    neon, riga 2 bianca);
  • 3 punti con la spunta che entrano uno alla volta;
  • grafico al NEON che si disegna salendo, con la freccia in cima;
  • una "notifica" del bot (pallino che pulsa) e l'invito finale che pulsa
    ("SCOPRI DI PIÙ → link in bio");
  • musica ritmata generata qui (niente diritti d'autore).

Leggero per i 512MB: un fotogramma alla volta in RAM, x264 "ultrafast".
Nessuna promessa di guadagno: solo cosa fa il servizio.
"""
from __future__ import annotations

import gc
import glob
import math
import os
import random
import time
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 24
SECONDS = 9.0
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "auto")

# Ogni video: titolo (2 righe), 3 punti, notifica del bot. Tutto vero, niente guadagni promessi.
HOOKS = [
    ("AUTOMATE", "YOUR TRADING", ["Fewer charts", "More time for you", "Signals on Telegram"],
     ("Signal bot active", "Works 24/7 · you don't")),
    ("THE BOT WORKS", "YOU LIVE", ["Scans the market 24/7", "Alerts you on Telegram", "You always decide"],
     ("New signal incoming", "Checked by the bot")),
    ("STOP STARING", "AT CHARTS", ["The bot watches for you", "You only get signals", "No screen anxiety"],
     ("Market under control", "24 hours a day")),
    ("YOUR MONEY", "STAYS YOURS", ["Funds on YOUR exchange", "No deposits with us", "Stop-loss always on"],
     ("Account linked safely", "API keys only")),
    ("CRYPTO SIGNALS", "ON AUTOPILOT", ["Entry, stop and target", "Explained simply", "Straight to Telegram"],
     ("Signal ready", "Tap to see it")),
    ("DON'T CHASE", "THE PUMPS", ["Clear rules", "Stop-loss on every trade", "Less emotion, more method"],
     ("The bot stays calm", "Even when you don't")),
    ("THE MARKET", "NEVER SLEEPS", ["Neither does the bot", "Messages you when needed", "You sleep easy"],
     ("Bot active at night", "Nonstop monitoring")),
    ("CRYPTO TRADING", "WITHOUT STRESS", ["Signals ready to go", "Risk always shown", "One tap and done"],
     ("Estimated risk: shown", "On every signal")),
    ("LEARN WHILE", "YOU INVEST", ["Every signal explained", "Glossary and guides", "Weekly podcast"],
     ("New lesson available", "Free on the site")),
    ("LESS SCREEN", "MORE LIFE", ["The bot does the boring part", "You get the alert", "You choose to enter"],
     ("Bot notification", "Now on Telegram")),
    ("64 COINS", "UNDER WATCH", ["Bitcoin, Ethereum, Solana…", "Daily analysis", "Alerts when it matters"],
     ("Scan complete", "64 coins analyzed")),
    ("TRY IT FREE", "FOR 3 DAYS", ["No commitment", "Link your exchange", "Cancel anytime"],
     ("Free trial active", "All features")),
]

THEMES = [  # (accento neon, sfondo alto, sfondo basso)
    ((57, 255, 20), (6, 8, 8), (4, 26, 12)),
    ((0, 229, 255), (5, 7, 12), (4, 18, 34)),
    ((255, 196, 0), (9, 8, 5), (30, 22, 4)),
    ((190, 110, 255), (8, 5, 12), (24, 10, 40)),
]
WHITE = (245, 247, 250)
GREY = (150, 156, 166)

_FONTS: dict = {}


def _font_path(bold=True):
    """Il font più "pieno" disponibile (Montserrat/Roboto Black se installati, poi Liberation)."""
    names = (["Montserrat-Black", "Montserrat-ExtraBold", "Roboto-Black", "Montserrat-Bold",
              "LiberationSans-Bold", "DejaVuSans-Bold"] if bold else
             ["Montserrat-SemiBold", "Montserrat-Medium", "Roboto-Medium", "LiberationSans-Regular", "DejaVuSans"])
    for n in names:
        hits = glob.glob(f"/usr/share/fonts/**/{n}.*tf", recursive=True)
        if hits:
            return hits[0]
    return None


def _f(size, bold=True):
    k = (size, bold)
    if k not in _FONTS:
        p = _font_path(bold)
        try:
            _FONTS[k] = ImageFont.truetype(p, size) if p else ImageFont.load_default()
        except Exception:
            _FONTS[k] = ImageFont.load_default()
    return _FONTS[k]


def _fit(text, max_w, start, bold=True):
    """La dimensione più grande con cui `text` sta in `max_w`."""
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    s = start
    while s > 40 and d.textlength(text, font=_f(s, bold)) > max_w:
        s -= 4
    return s


def _ease(t):  # 0..1 → 0..1 con rimbalzo morbido finale
    t = max(0.0, min(1.0, t))
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _background(theme):
    top, bot = theme[1], theme[2]
    g = np.linspace(0, 1, H)[:, None]
    arr = (np.array(top)[None, None, :] * (1 - g[..., None]) + np.array(bot)[None, None, :] * g[..., None])
    arr = np.repeat(arr, W, axis=1).astype("uint8")
    img = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(img)
    grid = tuple(min(255, c + 14) for c in bot)
    for x in range(0, W, 90):
        d.line([(x, 760), (x, 1500)], fill=grid, width=1)
    for y in range(760, 1500, 90):
        d.line([(0, y), (W, y)], fill=grid, width=1)
    return img


def _logo_white():
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "logo.png")
        L = np.asarray(Image.open(p).convert("L")).astype("float32")
        bg = float(np.median(np.concatenate([L[0], L[-1], L[:, 0], L[:, -1]])))
        a = np.clip((bg - L) / max(1.0, bg - float(L.min())), 0, 1) ** 0.8
        rgba = np.zeros((L.shape[0], L.shape[1], 4), dtype="uint8")
        rgba[..., :3] = 255
        rgba[..., 3] = (a * 255).astype("uint8")
        return Image.fromarray(rgba, "RGBA").resize((86, 86), Image.LANCZOS)
    except Exception:
        return None


def _chart_points(seed):
    rnd = random.Random(seed)
    n = 46
    x0, x1, y0, y1 = 70, W - 110, 1440, 830
    pts, v = [], 0.0
    for i in range(n):
        v += rnd.uniform(-0.55, 1.0)
        v = max(v, i * 0.35)
        pts.append(v)
    lo, hi = min(pts), max(pts)
    return [(x0 + (x1 - x0) * i / (n - 1), y0 - (y0 - y1) * (p - lo) / max(1e-6, hi - lo)) for i, p in enumerate(pts)]


def _partial(pts, frac):
    if frac <= 0:
        return pts[:1]
    total = len(pts) - 1
    k = frac * total
    i = int(k)
    out = pts[:i + 1]
    if i < total:
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        r = k - i
        out.append((ax + (bx - ax) * r, ay + (by - ay) * r))
    return out


def _beat(path, seconds, sr=22050):
    """Base ritmata (cassa, charleston, basso, arpeggio) generata qui: niente diritti."""
    n = int(seconds * sr)
    t = np.arange(n) / sr
    a = np.zeros(n, dtype=np.float32)
    bpm = 120
    step = 60 / bpm
    for k in range(int(seconds / step) + 1):          # cassa
        i = int(k * step * sr)
        m = min(n - i, int(0.25 * sr))
        if m <= 0:
            continue
        tt = np.arange(m) / sr
        a[i:i + m] += np.sin(2 * np.pi * (55 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12) * 0.9
    rnd = np.random.default_rng(3)
    for k in range(int(seconds / (step / 2)) + 1):    # charleston in levare
        if k % 2 == 0:
            continue
        i = int(k * step / 2 * sr)
        m = min(n - i, int(0.05 * sr))
        if m > 0:
            a[i:i + m] += rnd.uniform(-1, 1, m).astype(np.float32) * np.exp(-np.arange(m) / sr * 80) * 0.18
    notes = [110.0, 110.0, 130.81, 146.83]            # basso
    for k in range(int(seconds / step) + 1):
        i = int(k * step * sr)
        m = min(n - i, int(step * sr))
        if m > 0:
            tt = np.arange(m) / sr
            a[i:i + m] += np.sin(2 * np.pi * notes[(k // 2) % 4] * tt) * np.exp(-tt * 3) * 0.35
    arp = [440.0, 523.25, 659.25, 783.99]
    for k in range(int(seconds / (step / 4))):
        i = int(k * step / 4 * sr)
        m = min(n - i, int(step / 4 * sr))
        if m > 0 and k % 3 != 2:
            tt = np.arange(m) / sr
            a[i:i + m] += np.sin(2 * np.pi * arp[k % 4] * tt) * np.exp(-tt * 14) * 0.12
    fade = int(0.4 * sr)
    a[-fade:] *= np.linspace(1, 0, fade)
    a /= max(1e-6, float(np.max(np.abs(a))))
    pcm = (a * 0.8 * 32767).astype("<i2")
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return path


POST_W, POST_H = 1080, 1350


class StillWriter:
    """Al posto del video: salva UN fotogramma come immagine da post (4:5). Il
    fotogramma 9:16 viene rimpicciolito e i lati si allungano col colore del bordo,
    così lo sfondo continua senza stacchi."""

    def __init__(self, png_path):
        self.png_path = png_path

    def append_data(self, arr):
        img = Image.fromarray(np.asarray(arr)).convert("RGB")
        nh = POST_H
        nw = int(img.width * nh / img.height)
        small = np.asarray(img.resize((nw, nh), Image.LANCZOS))
        left = (POST_W - nw) // 2
        right = POST_W - nw - left
        canvas = np.concatenate([np.repeat(small[:, 3:4], left, axis=1), small,
                                 np.repeat(small[:, -4:-3], right, axis=1)], axis=1)
        Image.fromarray(canvas.astype("uint8")).save(self.png_path, "PNG", optimize=True)

    def close(self):
        pass


def caption_for(index: int) -> str:
    l1, l2, bullets, _n = HOOKS[index % len(HOOKS)]
    return (f"{l1.capitalize()} {l2.lower()} 🤖📈\n\n" + "\n".join(f"✅ {b}" for b in bullets) +
            "\n\n👉 Try VcriptoV: link in bio.\nEducational content, not financial advice: crypto trading "
            "is risky.\n\n#crypto #bitcoin #trading #cryptocurrency #tradingbot #investing #personalfinance "
            "#ethereum #vcriptov")


def render(index: int, out_path: str | None = None, hook=None, still=False) -> tuple[str, str]:
    """Crea il reel numero `index` (titolo, colori e grafico cambiano). `hook` = testi
    scelti dal sito [riga1, riga2, [3 punti], [notifica, sotto]]. Ritorna (mp4, didascalia)."""
    import imageio.v2 as imageio
    from content import _finalize_reel

    l1, l2, bullets, notif = HOOKS[index % len(HOOKS)]
    try:
        if hook and len(hook) == 4 and len(hook[2]) == 3 and len(hook[3]) == 2:
            l1, l2, bullets, notif = str(hook[0]), str(hook[1]), [str(b) for b in hook[2]], [str(n) for n in hook[3]]
    except (TypeError, ValueError):
        pass
    theme = THEMES[(index // len(HOOKS) + index) % len(THEMES)]
    acc = theme[0]
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = out_path or os.path.join(OUT_DIR, f"promo_{int(time.time())}_{index}.mp4")
    bg = _background(theme)
    logo = _logo_white()
    pts = _chart_points(index * 7 + 11)
    s1, s2 = _fit(l1, W - 110, 150), _fit(l2, W - 110, 150)
    s1 = s2 = min(s1, s2)
    fb = _f(56)
    total = int(SECONDS * FPS)
    raw = out_path + ".raw.mp4"
    frames = range(total)
    if still:                                   # post: solo l'ultimo fotogramma, come immagine
        out_path = os.path.splitext(out_path)[0] + ".png"
        frames = [total - 2]
    w = StillWriter(out_path) if still else imageio.get_writer(raw, fps=FPS, codec="libx264", quality=7, macro_block_size=1,
                           ffmpeg_params=["-pix_fmt", "yuv420p", "-preset", "ultrafast", "-threads", "1",
                                          "-bf", "0"])
    try:
        for fi in frames:
            t = fi / FPS
            fr = bg.copy()
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            # marchio in alto
            if logo:
                ov.alpha_composite(logo, (54, 70))
            d.text((154, 92), "VCRIPTOV", font=_f(40), fill=WHITE)
            d.text((156, 140), "automatic crypto signals", font=_f(26, False), fill=GREY)
            # grafico al neon che si disegna (dietro al testo)
            frac = _smooth((t - 0.8) / 4.2)
            line = _partial(pts, frac)
            if len(line) > 1:
                for wd, al in ((34, 28), (20, 60), (10, 140), (5, 255)):
                    d.line(line, fill=acc + (al,), width=wd, joint="curve")
                ex, ey = line[-1]
                r = 12 + 4 * math.sin(t * 8)
                d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=acc + (255,))
                d.ellipse([ex - 2.4 * r, ey - 2.4 * r, ex + 2.4 * r, ey + 2.4 * r], outline=acc + (90,), width=4)
            # titolo: "esplode" all'inizio, poi respira appena
            for k, (txt, col, y, size) in enumerate(((l1, acc, 250, s1), (l2, WHITE, 250 + s1 + 12, s2))):
                p = _ease((t - 0.05 - 0.28 * k) / 0.45)
                if p <= 0.01:
                    continue
                breathe = 1 + 0.015 * math.sin(t * 3.2) if t > 1.2 else 1
                sz = max(20, int(size * (0.55 + 0.45 * p) * breathe))
                f = _f(sz)
                tw = d.textlength(txt, font=f)
                a = int(255 * min(1, p * 1.4))
                if k == 0:     # alone neon sotto la riga colorata
                    d.text(((W - tw) / 2 + 3, y + 5), txt, font=f, fill=acc + (60,))
                d.text(((W - tw) / 2, y), txt, font=f, fill=col + (a,))
            # 3 punti con la spunta
            by = 250 + s1 + s2 + 80
            for k, b in enumerate(bullets):
                p = _ease((t - 1.3 - 0.45 * k) / 0.5)
                if p <= 0.01:
                    continue
                x = 70 - 120 * (1 - p)
                y = by + k * 92
                a = int(255 * min(1, p))
                d.ellipse([x, y, x + 58, y + 58], fill=acc + (a,))
                d.line([(x + 15, y + 30), (x + 26, y + 42), (x + 45, y + 18)], fill=(10, 12, 14, a), width=8)
                d.text((x + 84, y + 2), b, font=fb, fill=WHITE + (a,))
            # notifica del bot
            p = _ease((t - 3.2) / 0.5)
            if p > 0.01:
                cy = 1490 + 60 * (1 - p)
                a = int(235 * min(1, p))
                d.rounded_rectangle([90, cy, W - 90, cy + 150], 34, fill=(16, 20, 24, a), outline=acc + (int(a * .6),), width=3)
                pr = 16 + 5 * (0.5 + 0.5 * math.sin(t * 6))
                d.ellipse([150 - pr - 8, cy + 75 - pr - 8, 150 + pr + 8, cy + 75 + pr + 8], fill=acc + (int(50 * min(1, p)),))
                d.ellipse([150 - pr, cy + 75 - pr, 150 + pr, cy + 75 + pr], fill=acc + (a,))
                d.text((200, cy + 28), notif[0], font=_f(44), fill=WHITE + (a,))
                d.text((200, cy + 86), notif[1], font=_f(34, False), fill=GREY + (a,))
            # invito finale che pulsa
            p = _ease((t - 5.2) / 0.5)
            if p > 0.01:
                sc = 1 + 0.05 * math.sin((t - 5.2) * 6) if t > 5.7 else p
                bw, bh = 640 * sc, 124 * sc
                cx, cy = W / 2, 1735
                d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], int(bh / 2), fill=acc + (255,))
                f = _f(max(20, int(50 * sc)))
                txt = "LEARN MORE  →"
                tw = d.textlength(txt, font=f)
                d.text((cx - tw / 2, cy - 30 * sc), txt, font=f, fill=(8, 10, 12, 255))
                d.text((cx - d.textlength("link in bio", font=_f(30, False)) / 2, cy + bh / 2 + 14), "link in bio",
                       font=_f(30, False), fill=GREY + (int(255 * min(1, p)),))
            d.text((W / 2 - d.textlength("Educational, not financial advice", font=_f(24, False)) / 2, H - 50),
                   "Educational, not financial advice", font=_f(24, False), fill=(110, 116, 126, 255))
            fr = Image.alpha_composite(fr.convert("RGBA"), ov).convert("RGB")
            w.append_data(np.asarray(fr))
            del fr, ov, d
            if fi % 24 == 0:
                gc.collect()
    finally:
        w.close()
    if still:
        return out_path, caption_for(index)
    music = out_path + ".wav"
    try:
        _beat(music, SECONDS)
    except Exception:
        music = None
    _finalize_reel(raw, out_path, music)
    if music and os.path.exists(music):
        os.remove(music)
    return out_path, caption_for(index)


if __name__ == "__main__":
    import sys
    print(render(int(sys.argv[1]) if len(sys.argv) > 1 else 0, sys.argv[2] if len(sys.argv) > 2 else None))
