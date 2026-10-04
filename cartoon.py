"""
REEL "CARTOON" di VcriptoV — stile video-spiegazione virale: fondo crema, omino
disegnato che PARLA (voce inglese), una parola gialla alla volta al centro.

Il personaggio è nostro: testa tonda, abito scuro, PAPILLON ORO (colore VcriptoV)
e spilla "V". Espressioni (neutral, happy, sad, surprised, worried), bocca che
segue la voce, sbatte le palpebre, gesticola. Ogni scena ha i suoi oggetti.

Pensato per Render free (CPU minima): il personaggio è fatto a PEZZI disegnati una
volta sola per scena (corpo, braccio, testa con 5 aperture di bocca × occhi
aperti/chiusi) e poi solo incollati fotogramma per fotogramma. Video 720×1280.

Script (lo manda il sito):
  {"title": "...", "scenes": [
     {"say": "frase detta", "pose": "stand|phone|sit|point|wave",
      "face": "neutral|happy|sad|surprised|worried",
      "props": ["clock", "bench", "suitcase", "sign", "coins"],
      "screen": {"type": "chat", "lines": ["Invest $100", "get $1,000 tomorrow"]}
              | {"type": "chart", "dir": "up|down", "label": "+900%"}
              | {"type": "alert", "title": "WITHDRAWAL BLOCKED", "sub": "Pay a $300 fee"},
      "board": "26%"}, ...]}
"""

import asyncio
import gc
import hashlib
import math
import os
import random
import re
import subprocess
import time
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT_W, OUT_H = 720, 1280
R = OUT_W / 1080                 # si disegna in coordinate 1080×1920, si esce a 720×1280
FPS = 24
SR = 24000
GAP = 0.22
VOICE = os.environ.get("CARTOON_VOICE", "en-US-AndrewNeural")
VOICES = {"en": VOICE, "it": os.environ.get("CARTOON_VOICE_IT", "it-IT-DiegoNeural")}
VOICE_RATE = os.environ.get("CARTOON_VOICE_RATE", "+0%")   # ritmo naturale (meno "robot")
MUSIC_VOL = float(os.environ.get("CARTOON_MUSIC_VOL", "0.10"))

CREAM = (244, 237, 226)
INK = (48, 48, 52)
LINE = (128, 124, 118)
SOFT = (226, 220, 210)
SUIT = (30, 30, 35)
WHITE = (253, 253, 251)
SHADE = (218, 216, 212)
GOLD = (217, 178, 90)
GOLD_D = (150, 116, 48)
YEL = (250, 214, 64)
GREEN = (46, 168, 98)
GREEN_GLOW = (90, 230, 150)
BILL = (118, 178, 128)      # verde banconota
BILL_D = (70, 120, 82)
RED = (212, 70, 70)

# Varianti di SFONDO (tinta di base, alone). Scelte a caso per episodio: così i
# video non sembrano tutti uguali, ma restano tutti nello stile VcriptoV.
BG_THEMES = [
    {"base": (244, 237, 226), "glow": (255, 250, 236)},   # crema classico
    {"base": (240, 238, 232), "glow": (250, 250, 246)},   # grigio caldo
    {"base": (236, 241, 238), "glow": (248, 252, 250)},   # menta chiarissima
    {"base": (235, 238, 244), "glow": (247, 250, 255)},   # cielo tenue
    {"base": (245, 235, 232), "glow": (255, 248, 244)},   # pesca chiarissimo
]

_HERE = os.path.dirname(os.path.abspath(__file__))
_FONTS = os.path.join(_HERE, "static", "fonts")
OUT_DIR = os.path.join(_HERE, "static", "auto")
_fc = {}

POSES = ("stand", "phone", "sit", "point", "wave")
FACES = ("neutral", "happy", "sad", "surprised", "worried", "hyped")
PROPS = ("clock", "bench", "suitcase", "sign", "coins", "cash", "laptop", "mic", "rocket", "trophy")


def font(size, kind="Inter-ExtraBold"):
    k = (int(size), kind)
    if k not in _fc:
        try:
            _fc[k] = ImageFont.truetype(os.path.join(_FONTS, kind + ".ttf"), max(1, int(size)))
        except Exception:
            _fc[k] = ImageFont.truetype("LiberationSans-Bold.ttf", max(1, int(size)))
    return _fc[k]


class Pen:
    """Disegno in coordinate 1080×1920 su un'immagine scalata s volte e traslata."""

    def __init__(self, img, s=1.0, off=(0, 0)):
        self.img, self.d, self.s, self.o = img, ImageDraw.Draw(img), s, off

    def P(self, x, y):
        return ((x - self.o[0]) * self.s, (y - self.o[1]) * self.s)

    def B(self, x0, y0, x1, y1):
        return [*self.P(x0, y0), *self.P(x1, y1)]

    def circle(self, c, r, fill=None, outline=None, w=4):
        self.d.ellipse(self.B(c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=fill,
                       outline=outline, width=max(1, int(w * self.s)) if outline else 0)

    def ellipse(self, box, fill=None, outline=None, w=4):
        self.d.ellipse(self.B(*box), fill=fill, outline=outline,
                       width=max(1, int(w * self.s)) if outline else 0)

    def line(self, pts, fill, w=4, caps=True):
        self.d.line([self.P(*p) for p in pts], fill=fill, width=max(1, int(w * self.s)), joint="curve")
        if caps:
            for p in (pts[0], pts[-1]):
                self.circle(p, w / 2, fill=fill)

    def poly(self, pts, fill=None, outline=None, w=4):
        self.d.polygon([self.P(*p) for p in pts], fill=fill)
        if outline:
            self.line(list(pts) + [pts[0]], outline, w)

    def rrect(self, box, r, fill=None, outline=None, w=4):
        self.d.rounded_rectangle(self.B(*box), radius=int(r * self.s), fill=fill, outline=outline,
                                 width=max(1, int(w * self.s)) if outline else 0)

    def arc(self, box, a0, a1, fill, w=4):
        self.d.arc(self.B(*box), a0, a1, fill=fill, width=max(1, int(w * self.s)))

    def text(self, xy, txt, size, fill, anchor="mm", kind="Inter-ExtraBold", stroke=0, sfill=None):
        self.d.text(self.P(*xy), txt, font=font(size * self.s, kind), fill=fill, anchor=anchor,
                    stroke_width=int(stroke * self.s), stroke_fill=sfill)

    def fit(self, txt, size, max_w, kind="Inter-ExtraBold"):
        """Dimensione che fa stare il testo in max_w (coordinate 1080)."""
        w = self.d.textlength(txt, font=font(size * self.s, kind)) / self.s
        return size if w <= max_w else size * max_w / max(w, 1)


K = 1.28   # scala del personaggio (e di panchina/valigia/telefono)


def scaled(pen, cx, gy, k=K):
    """Pen che ingrandisce di k attorno al punto (cx, gy) (i piedi del personaggio)."""
    q = Pen.__new__(Pen)
    q.img, q.d, q.s = pen.img, pen.d, pen.s * k
    q.o = (cx - (cx - pen.o[0]) / k, gy - (gy - pen.o[1]) / k)
    return q


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


# ==============================================================================
#  IMPAGINAZIONE (zona sicura dei reel: Instagram copre ~220px sopra e ~380 sotto)
# ==============================================================================

BOX = (40, 300, 1040, 1230)      # zona del personaggio e degli oggetti
GROUND = 1190
CAPTION_Y = 1380
CHAR_X = {"phone": 650, "sit": 540, "point": 400, "wave": 500, "stand": 540}


def _char_x(sc):
    pose = sc.get("pose", "stand")
    if pose == "stand" and (sc.get("board") or "sign" in sc.get("props", [])):
        return 400
    return CHAR_X.get(pose, 540)


def _geom(pose, cx, gy):
    sit = pose == "sit"
    hy = gy - (180 if sit else 205)      # fianchi
    sy = hy - 215                        # spalle
    return hy, sy, (cx, sy - 100)        # centro testa


def _sprite(draw_fn):
    """Disegna draw_fn(pen) a 2x sulla zona BOX, rimpicciolisce e ritaglia.
    Ritorna (immagine RGBA, (x, y) nel fotogramma) oppure None se vuota."""
    bw, bh = BOX[2] - BOX[0], BOX[3] - BOX[1]
    img = Image.new("RGBA", (int(bw * R * 2), int(bh * R * 2)), (0, 0, 0, 0))
    draw_fn(Pen(img, R * 2, BOX[:2]))
    img = img.reduce(2)
    bb = img.getbbox()
    if not bb:
        return None
    return img.crop(bb), (int(BOX[0] * R) + bb[0], int(BOX[1] * R) + bb[1])


# ==============================================================================
#  PERSONAGGIO (a pezzi)
# ==============================================================================

BROWS = {"neutral": (0, 0), "happy": (-8, -12), "sad": (-12, 5), "worried": (-12, 3),
         "surprised": (-20, -18)}


def _arm(pen, sh, el, hand):
    pen.line([sh, el, hand], INK, 52)
    pen.line([sh, el, hand], SUIT, 42)
    pen.circle(hand, 26, fill=WHITE, outline=INK, w=4)


def _left_arm(pose, cx, hy, sy):
    if pose == "phone":
        return (cx - 150, sy + 210), (cx - 150, sy + 125)
    if pose == "sit":
        return (cx - 120, sy + 160), (cx - 58, hy + 34)
    return (cx - 128, sy + 150), (cx - 122, hy + 8)


def _right_arm(pose, cx, hy, sy, g):
    """Braccio destro; g in 0..1 = gesto (parlando) / fase del saluto."""
    if pose == "wave":
        return (cx + 175, sy + 60), (cx + 187 + 36 * g, sy - 70)
    if pose == "point":
        return (cx + 160, sy + 90), (cx + 225, sy - 26 + 12 * g)
    if pose == "sit":
        return (cx + 120, sy + 160), (cx + 58, hy + 34)
    if g <= 0:
        return (cx + 128, sy + 150), (cx + 122, hy + 8)
    return (cx + 150, sy + 180), (cx + 160 + 15 * g, sy + 120 - 80 * g)


def draw_legs(pen, cx, gy, pose):
    hy, sy, hc = _geom(pose, cx, gy)
    pen.ellipse((cx - 150, gy - 14, cx + 150, gy + 14), fill=SOFT)
    for side in (-1, 1):
        x0, x1 = (cx + 12, cx + 72) if side > 0 else (cx - 72, cx - 12)
        pen.rrect((x0, hy - 20, x1, gy - 24), 14, fill=SUIT, outline=INK, w=3)
        pen.ellipse((x0 - 14 if side < 0 else x0 - 4, gy - 34, x1 + 4 if side < 0 else x1 + 14, gy + 2),
                    fill=(22, 22, 26), outline=INK, w=3)


def draw_torso(pen, cx, gy, pose):
    hy, sy, hc = _geom(pose, cx, gy)
    pen.poly([(cx - 104, sy + 10), (cx + 104, sy + 10), (cx + 92, hy + 6), (cx - 92, hy + 6)],
             fill=SUIT, outline=INK, w=4)
    pen.circle((cx - 86, sy + 32), 26, fill=SUIT)
    pen.circle((cx + 86, sy + 32), 26, fill=SUIT)
    pen.poly([(cx - 40, sy + 2), (cx + 40, sy + 2), (cx, sy + 108)], fill=WHITE)
    pen.line([(cx - 40, sy + 2), (cx - 6, sy + 128)], (70, 70, 76), 4)
    pen.line([(cx + 40, sy + 2), (cx + 6, sy + 128)], (70, 70, 76), 4)
    for by in (sy + 150, sy + 190):
        pen.circle((cx, by), 5, fill=(80, 80, 86))
    pen.circle((cx + 58, sy + 70), 13, fill=GOLD, outline=GOLD_D, w=2)
    pen.text((cx + 58, sy + 71), "V", 15, GOLD_D)
    by = sy + 14
    pen.poly([(cx, by), (cx - 42, by - 20), (cx - 42, by + 20)], fill=GOLD, outline=GOLD_D, w=3)
    pen.poly([(cx, by), (cx + 42, by - 20), (cx + 42, by + 20)], fill=GOLD, outline=GOLD_D, w=3)
    pen.circle((cx, by), 10, fill=GOLD_D)
    el, hand = _left_arm(pose, cx, hy, sy)
    _arm(pen, (cx - 92, sy + 34), el, hand)
    return hand


def draw_right_arm(pen, cx, gy, pose, g):
    hy, sy, hc = _geom(pose, cx, gy)
    el, hand = _right_arm(pose, cx, hy, sy, g)
    _arm(pen, (cx + 92, sy + 34), el, hand)


def draw_head(pen, cx, gy, pose, face, mouth_q, blink):
    """mouth_q: 0 = bocca chiusa (espressione), 1..4 = aperta mentre parla."""
    hy, sy, hc = _geom(pose, cx, gy)
    r = 118
    pen.circle(hc, r, fill=WHITE)
    pen.arc((hc[0] - r + 9, hc[1] - r + 9, hc[0] + r - 9, hc[1] + r - 9), 10, 120, SHADE, 16)
    pen.circle(hc, r, outline=INK, w=4)
    ey = hc[1] + 2
    for s in (-1, 1):
        x = hc[0] + s * 36
        if blink:
            pen.line([(x - 10, ey), (x + 10, ey)], INK, 5)
        elif face == "hyped":
            # occhi verdi che "brillano" (stile gasato, come i video virali)
            pen.circle((x, ey), 19, fill=(14, 40, 24))
            pen.circle((x, ey), 13, fill=GREEN_GLOW)
            pen.circle((x, ey), 6, fill=(230, 255, 240))
        elif face == "surprised":
            pen.circle((x, ey), 12, fill=INK)
            pen.circle((x + 3, ey - 4), 3.5, fill=WHITE)
        else:
            pen.ellipse((x - 8, ey - 12, x + 8, ey + 12), fill=INK)
            pen.circle((x + 2, ey - 5), 3, fill=WHITE)
        bi, bo = BROWS.get(face, (0, 0))
        lift = -2 * mouth_q
        pen.line([(hc[0] + s * 16, ey - 34 + bi + lift), (hc[0] + s * 54, ey - 34 + bo + lift)], INK, 5)
        if face in ("sad", "worried"):
            pen.arc((x - 13, ey + 8, x + 13, ey + 24), 200, 340, LINE, 3)
    mx, my = hc[0], hc[1] + 50
    if mouth_q > 0:
        lv = mouth_q / 4
        h = 6 + 30 * lv
        wdt = 22 + 6 * lv
        pen.ellipse((mx - wdt, my - h / 2, mx + wdt, my + h / 2), fill=(70, 34, 34), outline=INK, w=3)
        if h > 16:
            pen.ellipse((mx - 12, my + h / 2 - 11, mx + 12, my + h / 2 - 2), fill=(210, 100, 100))
    elif face == "happy":
        pen.arc((mx - 30, my - 26, mx + 30, my + 14), 15, 165, INK, 5)
    elif face == "sad":
        pen.arc((mx - 22, my - 2, mx + 22, my + 24), 205, 335, INK, 5)
    elif face == "surprised":
        pen.ellipse((mx - 12, my - 14, mx + 12, my + 14), fill=(70, 34, 34), outline=INK, w=3)
    elif face == "worried":
        pen.line([(mx - 20, my + 4), (mx - 7, my - 2), (mx + 7, my + 4), (mx + 20, my - 2)], INK, 4)
    elif face == "hyped":
        pen.arc((mx - 34, my - 30, mx + 34, my + 16), 10, 170, INK, 6)   # sorrisone
    else:
        pen.arc((mx - 18, my - 12, mx + 18, my + 8), 25, 155, INK, 5)


# ==============================================================================
#  OGGETTI
# ==============================================================================

def prop_clock_face(pen, c, r):
    pen.circle((c[0] + 8, c[1] + 10), r, fill=SOFT)
    pen.circle(c, r, fill=(238, 236, 232), outline=LINE, w=6)
    pen.circle(c, r - 16, outline=SOFT, w=3)
    for k in range(12):
        a = k * math.pi / 6
        ln = 18 if k % 3 == 0 else 10
        pen.line([(c[0] + (r - 22) * math.sin(a), c[1] - (r - 22) * math.cos(a)),
                  (c[0] + (r - 22 - ln) * math.sin(a), c[1] - (r - 22 - ln) * math.cos(a))], LINE, 4)


def prop_clock_hands(pen, c, r, t):
    am, ah = t * 1.6, 2.1 + t * 0.13
    pen.line([c, (c[0] + (r - 40) * math.sin(am), c[1] - (r - 40) * math.cos(am))], INK, 6)
    pen.line([c, (c[0] + (r - 70) * math.sin(ah), c[1] - (r - 70) * math.cos(ah))], INK, 8)
    pen.circle(c, 9, fill=INK)


def prop_bench(pen, cx, gy):
    seat = gy - 205
    for x in (cx - 250, cx + 230):
        pen.rrect((x, seat, x + 22, gy), 6, fill=(200, 196, 190), outline=LINE, w=3)
    for k in range(3):
        y = seat - 170 + k * 52
        pen.rrect((cx - 290, y, cx + 290, y + 34), 8, fill=(232, 228, 222), outline=LINE, w=3)
    pen.rrect((cx - 300, seat - 8, cx + 300, seat + 26), 8, fill=(222, 218, 212), outline=LINE, w=3)


def prop_suitcase(pen, x, gy):
    pen.rrect((x, gy - 150, x + 120, gy - 6), 12, fill=(214, 210, 204), outline=LINE, w=4)
    pen.rrect((x + 34, gy - 178, x + 86, gy - 150), 10, outline=LINE, w=5)
    for k in range(1, 4):
        pen.line([(x + 30 * k, gy - 146), (x + 30 * k, gy - 10)], LINE, 3)


def prop_sign(pen, cx, cy, s=1.0):
    pts = [(cx, cy - 150 * s), (cx + 140 * s, cy + 100 * s), (cx - 140 * s, cy + 100 * s)]
    pen.line([(cx, cy + 100 * s), (cx, cy + 330 * s)], LINE, 14)
    pen.poly(pts, fill=YEL, outline=INK, w=8)
    pen.text((cx, cy + 25 * s), "!", 150 * s, INK)


def prop_board(pen, cx, cy, txt):
    """Lavagna su cavalletto con una scritta/numero grande (es. '26%')."""
    pen.line([(cx - 120, cy + 170), (cx - 160, cy + 470)], LINE, 12)
    pen.line([(cx + 120, cy + 170), (cx + 160, cy + 470)], LINE, 12)
    pen.rrect((cx - 190 + 8, cy - 170 + 10, cx + 190 + 8, cy + 170 + 10), 18, fill=SOFT)
    pen.rrect((cx - 190, cy - 170, cx + 190, cy + 170), 18, fill=WHITE, outline=INK, w=6)
    txt = str(txt)[:14]
    lines = [txt] if len(txt) <= 6 else re.sub(r"\s+", " ", txt).split(" ", 1)
    size = 140 if len(lines) == 1 else 76
    for i, ln in enumerate(lines[:2]):
        y = cy + (0 if len(lines) == 1 else (-48 + 96 * i))
        pen.text((cx, y), ln, pen.fit(ln, size, 330), INK)


def prop_coins(pen, x, gy):
    for col, n in ((0, 5), (70, 3), (-60, 2)):
        for k in range(n):
            y = gy - 20 - k * 22
            pen.ellipse((x + col - 46, y - 16, x + col + 46, y + 16), fill=GOLD, outline=GOLD_D, w=3)


def prop_cash_stacks(pen, x, gy, seed=0):
    """Mazzette di banconote verdi accanto al personaggio (parte FERMA; le
    banconote che volano le disegna frame() a parte). Numero/altezza variano."""
    rnd = random.Random(seed)
    cols = [(x - 70, 4 + rnd.randint(0, 2)), (x + 30, 3 + rnd.randint(0, 2)), (x + 120, 2 + rnd.randint(0, 2))]
    for bx, n in cols:
        for k in range(n):
            y = gy - 18 - k * 20
            pen.rrect((bx - 52, y - 15, bx + 52, y + 15), 4, fill=BILL, outline=BILL_D, w=3)
            pen.circle((bx, y), 8, fill=BILL_D)


LAPTOP_C = (838, 760)        # centro dello schermo (lato destro, non copre il personaggio)


def prop_laptop(pen):
    """Portatile aperto sul lato (lo SCHERMO con le views lo anima frame())."""
    cx, cy = LAPTOP_C
    by = cy + 108
    pen.poly([(cx - 150, by), (cx + 150, by), (cx + 180, by + 64), (cx - 180, by + 64)],
             fill=(40, 42, 48), outline=INK, w=4)               # base/tastiera
    pen.rrect((cx - 150, cy - 118, cx + 150, by), 10, fill=(26, 28, 32), outline=INK, w=4)   # cornice
    pen.rrect(laptop_screen_rect(), 6, fill=WHITE)                                           # schermo


def laptop_screen_rect():
    cx, cy = LAPTOP_C
    return (cx - 134, cy - 104, cx + 134, cy + 98)


def prop_mic(pen, x, gy):
    """Microfono da podcast su braccetto (scena intervista)."""
    top = gy - 470
    pen.line([(x, gy - 20), (x, top + 120)], (60, 62, 68), 10)
    pen.line([(x, top + 120), (x - 70, top + 70)], (60, 62, 68), 8)
    pen.rrect((x - 110, top, x - 30, top + 120), 34, fill=(34, 36, 40), outline=INK, w=4)
    for k in range(5):
        pen.line([(x - 104, top + 16 + k * 20), (x - 36, top + 16 + k * 20)], (70, 72, 78), 3)


def prop_rocket(pen, x, gy, t=0.0):
    """Razzo (per 'alle stelle/virale'): sale e trema un po'."""
    y = gy - 120 - (t * 220 % 260)
    pen.poly([(x, y - 90), (x + 34, y + 10), (x - 34, y + 10)], fill=(226, 90, 80), outline=INK, w=4)
    pen.rrect((x - 34, y + 10, x + 34, y + 120), 12, fill=WHITE, outline=INK, w=4)
    pen.circle((x, y + 44), 18, fill=(120, 170, 255), outline=INK, w=3)
    pen.poly([(x - 34, y + 90), (x - 70, y + 140), (x - 34, y + 120)], fill=(226, 90, 80), outline=INK, w=3)
    pen.poly([(x + 34, y + 90), (x + 70, y + 140), (x + 34, y + 120)], fill=(226, 90, 80), outline=INK, w=3)
    for k in range(3):
        fy = y + 125 + k * 26
        pen.poly([(x - 16 + k, fy), (x + 16 - k, fy), (x, fy + 34 - k * 8)], fill=(250, 190, 60))


def prop_trophy(pen, cx, cy, s=1.0):
    pen.rrect((cx - 70 * s, cy - 60 * s, cx + 70 * s, cy + 50 * s), 16 * s, fill=GOLD, outline=GOLD_D, w=4)
    pen.arc((cx - 120 * s, cy - 60 * s, cx - 40 * s, cy + 30 * s), 90, 270, GOLD_D, int(10 * s))
    pen.arc((cx + 40 * s, cy - 60 * s, cx + 120 * s, cy + 30 * s), 270, 90, GOLD_D, int(10 * s))
    pen.rrect((cx - 26 * s, cy + 50 * s, cx + 26 * s, cy + 95 * s), 6 * s, fill=GOLD_D)
    pen.rrect((cx - 64 * s, cy + 95 * s, cx + 64 * s, cy + 120 * s), 8 * s, fill=INK)
    pen.text((cx, cy - 2 * s), "#1", 48 * s, GOLD_D)


def _seed(script) -> int:
    base = str(script.get("title") or "") + str(script.get("part") or "") + str(script.get("lang") or "")
    return int(hashlib.md5(base.encode("utf-8")).hexdigest()[:8], 16)


def make_background(seed=0):
    """Sfondo dell'episodio: tinta + alone morbido + puntini tenui che fluttuano.
    Variato per episodio (seed) così i video non sembrano tutti uguali."""
    rnd = random.Random(seed)
    th = BG_THEMES[rnd.randrange(len(BG_THEMES))]
    base, glow = th["base"], th["glow"]
    yy = np.linspace(0, 1, OUT_H)[:, None]
    xx = np.linspace(0, 1, OUT_W)[None, :]
    gx, gy = rnd.uniform(0.3, 0.7), rnd.uniform(0.18, 0.42)       # centro dell'alone
    d = np.sqrt((xx - gx) ** 2 + ((yy - gy) * (OUT_H / OUT_W)) ** 2)
    halo = np.clip(1 - d / 0.75, 0, 1) ** 1.6
    img = np.empty((OUT_H, OUT_W, 3), dtype=np.float32)
    for c in range(3):
        img[:, :, c] = base[c] + (glow[c] - base[c]) * halo
    arr = np.clip(img, 0, 255).astype(np.uint8)
    bg = Image.fromarray(arr, "RGB")
    pen = Pen(bg, R)
    for _ in range(rnd.randint(16, 26)):                           # puntini tenui
        px, py, r_ = rnd.uniform(40, 1040), rnd.uniform(330, 1200), rnd.uniform(3, 8)
        shade = tuple(max(0, c - 14) for c in base)
        pen.circle((px, py), r_, fill=shade)
    return bg


def _wrap(pen, text, size, max_w, kind):
    f = font(size * pen.s, kind)
    rows, cur = [], ""
    for w in str(text).split():
        t = (cur + " " + w).strip()
        if not cur or pen.d.textlength(t, font=f) / pen.s <= max_w:
            cur = t
        else:
            rows.append(cur)
            cur = w
    if cur:
        rows.append(cur)
    if len(rows) > 2:
        rows = [rows[0], " ".join(rows[1:])]
    return rows


def _phone_box(hand):
    hx, hy = hand
    return (hx - 300, hy - 330, hx - 20, hy + 190)


def phone_frame(pen, box):
    x0, y0, x1, y1 = box
    pen.rrect((x0 + 8, y0 + 10, x1 + 8, y1 + 10), 34, fill=SOFT)
    pen.rrect(box, 34, fill=(36, 36, 40), outline=INK, w=4)
    pen.rrect((x0 + 12, y0 + 30, x1 - 12, y1 - 22), 22, fill=WHITE)
    pen.rrect(((x0 + x1) / 2 - 30, y0 + 12, (x0 + x1) / 2 + 30, y0 + 22), 5, fill=(70, 70, 76))


def phone_screen(pen, box, scr, p):
    x0, y0, x1, y1 = box[0] + 12, box[1] + 30, box[2] - 12, box[3] - 22
    cx = (x0 + x1) / 2
    typ = (scr or {}).get("type", "chat")
    if typ == "chart":
        up = (scr.get("dir") or "up") != "down"
        pts = ([(0, 0.15), (0.15, 0.2), (0.3, 0.18), (0.45, 0.38), (0.6, 0.45), (0.75, 0.7), (1, 0.95)] if up else
               [(0, 0.9), (0.15, 0.82), (0.3, 0.86), (0.45, 0.6), (0.6, 0.55), (0.75, 0.3), (1, 0.08)])
        q = [(x0 + 24 + (x1 - x0 - 48) * a, y1 - 40 - (y1 - y0 - 170) * b) for a, b in pts]
        f = ease(p * 1.4)
        tot = len(q) - 1
        n = int(tot * f)
        seg = q[:n + 1]
        if n < tot:
            k = tot * f - n
            a, b = q[n], q[n + 1]
            seg.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
        if len(seg) >= 2:
            pen.line(seg, GREEN if up else RED, 9)
        label = str(scr.get("label") or ("+100%" if up else "-80%"))[:9]
        m = re.match(r"^([+\-]?)(\d+)(.*)$", label)
        if m and f < 1:
            label = f"{m.group(1)}{int(int(m.group(2)) * f)}{m.group(3)}"
        pen.text((cx, y0 + 58), label, pen.fit(label, 54, x1 - x0 - 30), GREEN if up else RED)
        if scr.get("sub"):
            pen.text((cx, y0 + 104), str(scr["sub"])[:22], 22, LINE, kind="Inter-SemiBold")
    elif typ == "alert":
        lx = cx
        pen.rrect((lx - 48, y0 + 120, lx + 48, y0 + 200), 12, fill=RED, outline=INK, w=3)
        pen.arc((lx - 32, y0 + 64, lx + 32, y0 + 150), 180, 360, INK, 10)
        title = str(scr.get("title") or "BLOCKED")[:24].upper()
        words = title.split()
        lines = [" ".join(words[:len(words) // 2 or 1]), " ".join(words[len(words) // 2 or 1:])]
        for i, ln in enumerate([x for x in lines if x]):
            pen.text((cx, y0 + 250 + 38 * i), ln, pen.fit(ln, 30, x1 - x0 - 30), RED)
        if p > 0.3 and scr.get("sub"):
            sub = str(scr["sub"])[:26]
            pen.rrect((x0 + 18, y0 + 340, x1 - 18, y0 + 410), 16, fill=(250, 232, 232))
            pen.text((cx, y0 + 375), sub, pen.fit(sub, 20, x1 - x0 - 60, "Inter-SemiBold"), INK,
                     kind="Inter-SemiBold")
    else:  # chat: fumetti che compaiono uno dopo l'altro
        lines = [str(x)[:44] for x in (scr or {}).get("lines") or ["Hey!", "Got a minute?"]][:3]
        y = y0 + 24
        for i, ln in enumerate(lines):
            if ease(p * (len(lines) + 0.5) - i) <= 0:
                break
            mine = i % 2 == 1
            kind = "Inter-ExtraBold" if mine else "Inter-SemiBold"
            bx0, bx1 = (x0 + 44, x1 - 12) if mine else (x0 + 12, x1 - 44)
            rows = _wrap(pen, ln, 26, bx1 - bx0 - 28, kind)[:2]
            fs = min(pen.fit(r_, 26, bx1 - bx0 - 28, kind) for r_ in rows)
            bh = 26 + 34 * len(rows)
            pen.rrect((bx0, y, bx1, y + bh), 20, fill=(214, 240, 222) if mine else (232, 232, 236))
            for j, r_ in enumerate(rows):
                pen.text((bx0 + 14, y + 30 + 34 * j), r_, fs, GREEN if mine else INK, "lm", kind)
            y += bh + 18


# ==============================================================================
#  VOCE (gratis, Microsoft Edge) + musica leggera generata qui (nessun diritto)
# ==============================================================================

def _ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _tts(text, out_mp3, voice=None):
    import edge_tts
    words = []

    async def run():
        comm = edge_tts.Communicate(text, voice or VOICE, rate=VOICE_RATE, boundary="WordBoundary")
        with open(out_mp3, "wb") as f:
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    s = ch["offset"] / 1e7
                    words.append((s, s + ch["duration"] / 1e7, ch["text"]))

    asyncio.run(run())
    if not words or os.path.getsize(out_mp3) < 1000:
        raise RuntimeError("voce vuota")
    return words


def _decode(mp3):
    raw = subprocess.run([_ffmpeg(), "-v", "error", "-i", mp3, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16)


def _music(seconds):
    """Sottofondo leggero tipo 'spiegazione': pizzicato in minore + basso morbido."""
    n = int(seconds * SR)
    a = np.zeros(n, dtype=np.float32)
    step = 60 / 100 / 2
    mel = [220.0, 261.63, 329.63, 261.63, 246.94, 293.66, 349.23, 293.66,
           220.0, 261.63, 329.63, 392.0, 349.23, 329.63, 293.66, 246.94]
    bass = [110.0, 110.0, 123.47, 98.0]
    for k in range(int(seconds / step) + 1):
        i = int(k * step * SR)
        m = min(n - i, int(0.32 * SR))
        if m <= 0:
            continue
        tt = np.arange(m) / SR
        f = mel[k % len(mel)]
        a[i:i + m] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 11) * 0.5
        if k % 4 == 0:
            mb = min(n - i, int(step * 4 * SR))
            tb = np.arange(mb) / SR
            a[i:i + mb] += np.sin(2 * np.pi * bass[(k // 8) % 4] * tb) * np.exp(-tb * 2.2) * 0.45
    fade = int(0.6 * SR)
    a[-fade:] *= np.linspace(1, 0, fade)
    return a / max(1e-6, float(np.max(np.abs(a))))


def _sting():
    """Suono d'apertura SEMPRE uguale (riconoscibile come 'sigla' della serie):
    una salita veloce e due rintocchi."""
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    sweep = np.sin(2 * np.pi * (300 * t + 900 * t * t)) * np.exp(-t * 5) * (t < 0.35)
    out = sweep * 0.6
    for start, f in ((0.32, 880.0), (0.5, 1318.5)):
        i = int(start * SR)
        tt = np.arange(n - i) / SR
        out[i:] += (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 6) * 0.5
    return out.astype(np.float32) / max(1e-6, float(np.max(np.abs(out))))


def _with_intro(script):
    """Se lo script è una puntata di una serie ("part"), aggiungo l'apertura fissa:
    'Crypto money method, number N.' con il numero sulla lavagna."""
    part = script.get("part")
    if not part or (script["scenes"] and script["scenes"][0].get("intro")):
        return script
    series = str(script.get("series") or "Crypto money method")[:40]
    say = script.get("intro_say") or (f"{series}, numero {int(part)}." if script.get("lang") == "it"
                                      else f"{series}, number {int(part)}.")
    # Apertura FISSA della serie, ma con 4 composizioni diverse a rotazione (seed):
    # NON è lo "sfogliare i soldi" del video di riferimento. Resta riconoscibile
    # (titolo + #N) ma cambia aspetto da un episodio all'altro.
    variants = [
        {"pose": "point", "face": "happy", "board": f"#{int(part)}"},
        {"pose": "stand", "face": "hyped", "board": f"#{int(part)}", "props": ["trophy"]},
        {"pose": "stand", "face": "happy", "props": ["laptop"], "board": f"#{int(part)}"},
        {"pose": "wave", "face": "hyped", "board": f"#{int(part)}"},
    ]
    v = variants[_seed(script) % len(variants)]
    intro = dict(v, say=str(say)[:120], title=series, intro=True)
    return dict(script, scenes=[intro] + list(script["scenes"]))


_BADGE = {}


def _badge_img(txt):
    if txt not in _BADGE:
        f = font(30 * R)
        w = int(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(txt, font=f)) + int(36 * R)
        h = int(52 * R)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=YEL + (255,), outline=(20, 20, 20, 255),
                            width=max(2, int(3 * R)))
        d.text((w / 2, h / 2), txt, font=f, fill=(20, 20, 20), anchor="mm")
        _BADGE[txt] = img
    return _BADGE[txt]


def build_audio(script, workdir):
    parts, words, spans, t = [], [], [], 0.35
    for i, sc in enumerate(script["scenes"]):
        mp3 = os.path.join(workdir, f"s{i}.mp3")
        seg = _tts(sc["say"].strip(), mp3, VOICES.get(script.get("lang") or "en", VOICE))
        pcm = _decode(mp3)
        dur = len(pcm) / SR
        words += [(t + a, t + b, w) for a, b, w in seg]
        spans.append((t, t + dur))
        parts.append((t, pcm))
        t += dur + GAP
    total = t + 0.6
    voice = np.zeros(int(total * SR), dtype=np.float32)
    for st, pcm in parts:
        a = int(st * SR)
        seg = pcm[: max(0, len(voice) - a)].astype(np.float32) / 32768
        voice[a:a + len(seg)] = seg
    mix = voice + MUSIC_VOL * _music(total)[: len(voice)]
    if script.get("part"):
        st_ = _sting()
        mix[: len(st_)] += 0.5 * st_[: len(mix)]
    mix = np.clip(mix / max(1.0, float(np.max(np.abs(mix)))), -1, 1)
    wav = os.path.join(workdir, "audio.wav")
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix * 32000).astype("<i2").tobytes())
    hop = SR // FPS
    nfr = int(total * FPS) + 1
    lv = np.array([math.sqrt(float((voice[f * hop:(f + 1) * hop] ** 2).mean() or 0)) for f in range(nfr)])
    peak = float(np.percentile(lv[lv > 0], 92)) if (lv > 0).any() else 1.0
    lv = np.convolve(np.clip(lv / max(peak, 1e-6), 0, 1), [0.25, 0.5, 0.25], mode="same")
    return wav, words, spans, total, lv


# ==============================================================================
#  SCENE (pezzi pronti) + MONTAGGIO
# ==============================================================================

class Scene:
    def __init__(self, sc, bg=None, seed=0):
        self.sc = sc
        self.seed = seed
        self.pose = sc.get("pose") if sc.get("pose") in POSES else "stand"
        self.face = sc.get("face") if sc.get("face") in FACES else "neutral"
        self.props = [p for p in (sc.get("props") or []) if p in PROPS]
        self.cx = _char_x(sc)
        cx, gy = self.cx, GROUND
        self.bg = (bg.copy() if bg is not None else Image.new("RGB", (OUT_W, OUT_H), CREAM))
        if not sc.get("title"):
            Pen(self.bg, R).text((540, 236), "VcriptoV", 28, (190, 182, 170))
        hand = {}

        def back(pen):
            if "clock" in self.props:
                prop_clock_face(pen, (cx + 260, 470), 125)
            if "bench" in self.props:
                prop_bench(scaled(pen, cx, gy), cx, gy)
            if "suitcase" in self.props:
                prop_suitcase(scaled(pen, cx, gy), cx + 150, gy)
            if "cash" in self.props:
                prop_cash_stacks(scaled(pen, cx, gy), cx + 200, gy, seed)
            if "laptop" in self.props:
                prop_laptop(pen)
            if "mic" in self.props:
                prop_mic(pen, 250, gy)
            if "trophy" in self.props:
                prop_trophy(pen, 850, 560, 1.0)
            if "sign" in self.props:
                prop_sign(pen, 840, 640, 1.1)
            elif sc.get("board"):
                prop_board(pen, 820, 600, sc["board"])
            if "coins" in self.props:
                prop_coins(pen, 900, gy)
            draw_legs(scaled(pen, cx, gy), cx, gy, self.pose)

        self._paste(self.bg, _sprite(back), 0)
        if sc.get("title"):   # titolo grande della serie (scena d'apertura)
            tp = Pen(self.bg, R)
            tt = str(sc["title"]).upper()[:28]
            tp.text((540, 305), tt, tp.fit(tt, 62, 960), INK)

        def torso(pen):
            cp = scaled(pen, cx, gy)
            hand["left"] = draw_torso(cp, cx, gy, self.pose)
            if self.pose == "phone":
                phone_frame(cp, _phone_box(hand["left"]))

        self.torso = _sprite(torso)
        self.hand = hand.get("left")
        self._cache = {}

    @staticmethod
    def _paste(frame, spr, dy, dx=0):
        if spr:
            img, (x, y) = spr
            frame.paste(img, (x + dx, y + dy), img)

    def _get(self, key, fn):
        if key not in self._cache:
            self._cache[key] = _sprite(fn)
        return self._cache[key]

    def frame(self, t, p, mouth, talking):
        cx, gy = self.cx, GROUND
        fr = self.bg.copy()
        if "clock" in self.props:
            step = round(t * 4) / 4
            self._paste(fr, self._get(("clock", step), lambda pen: prop_clock_hands(pen, (cx + 260, 470), 125, step)), 0)
        if "coins" in self.props:
            d = ImageDraw.Draw(fr)
            for k in range(3):
                ph = (t * 0.6 + k / 3) % 1
                col = tuple(int(c1 + (c2 - c1) * ph) for c1, c2 in zip(GOLD_D, CREAM))
                d.text(((860 + k * 40) * R, (GROUND - 160 - 380 * ph) * R), "$", font=font(54 * R), fill=col,
                       anchor="mm")
        if "cash" in self.props:
            # banconote verdi che cadono, sparse su tutta la larghezza (la nostra
            # versione dei "soldi che piovono", diversa da quella del riferimento)
            pen = Pen(fr, R)
            rnd = random.Random(self.seed ^ 0x9E3779B9)
            for k in range(9):
                bx = rnd.uniform(60, 1020)
                ph = (t * (0.35 + rnd.random() * 0.3) + rnd.random()) % 1
                by = 300 + ph * 940
                ang = math.sin(t * 2 + k)
                pen.poly([(bx - 34, by - 12 + ang * 6), (bx + 34, by - 12 - ang * 6),
                          (bx + 34, by + 12 - ang * 6), (bx - 34, by + 12 + ang * 6)],
                         fill=BILL, outline=BILL_D, w=2)
                pen.circle((bx, by), 5, fill=BILL_D)
        if "rocket" in self.props:
            prop_rocket(Pen(fr, R), 880, GROUND, t)
        if "laptop" in self.props:
            d = ImageDraw.Draw(fr)
            x0, y0, x1, y1 = [v * R for v in laptop_screen_rect()]
            base_v = (self.sc.get("screen") or {}).get("views") if isinstance(self.sc.get("screen"), dict) else None
            try:
                target = int(str(base_v).replace(".", "").replace(",", "")) if base_v else 9876543
            except ValueError:
                target = 9876543
            shown = int(target * min(1.0, 0.15 + t * 0.5))
            cxs = (x0 + x1) / 2
            d.text((cxs, y0 + (y1 - y0) * 0.36), f"{shown:,}".replace(",", "."), font=font(44 * R), fill=GREEN,
                   anchor="mm")
            d.text((cxs, y0 + (y1 - y0) * 0.62), "VIEWS", font=font(30 * R), fill=LINE, anchor="mm")
        # Movimento più vivo: oltre al "respiro" su e giù (bob), un leggero
        # dondolio laterale di tutto il corpo (sway) e un cenno in più della testa.
        # Così non sembra un robot fermo che muove solo la bocca. Tutte le parti
        # condividono lo stesso sway, così niente si stacca dal corpo.
        bob = int(round(4 * R * math.sin(t * 2 * math.pi * 0.75)))
        sway = int(round(3 * R * math.sin(t * 2 * math.pi * 0.33 + self.seed * 0.7)))
        self._paste(fr, self.torso, bob, sway)
        if self.pose == "phone" and self.hand:
            ps = round(min(1.0, p) * 20) / 20
            scr = self.sc.get("screen") or {}
            self._paste(fr, self._get(("screen", ps), lambda pen: phone_screen(
                scaled(pen, cx, gy), _phone_box(self.hand), scr, ps)), bob, sway)
            hx, hy = self.hand
            self._paste(fr, self._get("thumb", lambda pen: scaled(pen, cx, gy).circle(
                (hx - 22, hy + 10), 26, fill=WHITE, outline=INK, w=4)), bob, sway)
        if self.pose == "wave":
            g = (math.sin(t * 6.5) + 1) / 2
        elif self.pose == "point":
            g = (math.sin(t * 4) + 1) / 2
        elif talking and self.pose in ("stand", "phone"):
            g = mouth * (0.6 + 0.4 * math.sin(t * 5))
        else:
            g = 0.0
        gq = round(g * 3) / 3
        self._paste(fr, self._get(("arm", gq), lambda pen: draw_right_arm(scaled(pen, cx, gy), cx, gy, self.pose, gq)),
                    bob, sway)
        mq = int(round(min(1.0, mouth * 1.15) * 4)) if talking and mouth > 0.08 else 0
        blink = (t % 3.4) < 0.11
        # la testa accenna un po' di più del corpo (cenno naturale mentre parla)
        head_dy = bob + int(round(2 * R * math.sin(t * 2 * math.pi * 0.9 + 0.6)))
        self._paste(fr, self._get(("head", mq, blink), lambda pen: draw_head(
            scaled(pen, cx, gy), cx, gy, self.pose, self.face, mq, blink)), head_dy, sway)
        return fr


_CAP = {}


def _caption_img(word, step):
    k = (word, step)
    if k not in _CAP:
        size = 128 * (0.82 + 0.06 * step) * R
        f = font(size)
        tw = ImageDraw.Draw(Image.new("L", (1, 1))).textlength(word, font=f)
        if tw > OUT_W - 90:
            f = font(size * (OUT_W - 90) / tw)
        sw = max(3, int(13 * R))
        bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), word, font=f, stroke_width=sw)
        img = Image.new("RGBA", (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((2 - bb[0], 2 - bb[1]), word, font=f, fill=YEL, stroke_width=sw,
                                 stroke_fill=(20, 20, 20))
        if len(_CAP) > 400:
            _CAP.clear()
        _CAP[k] = img
    return _CAP[k]


def _clean_word(w):
    return re.sub(r"[^\w$€%+\-'.,]", "", w).strip(".,")


def valid_script(s) -> bool:
    try:
        sc = s["scenes"]
        return 2 <= len(sc) <= 9 and all(isinstance(x.get("say"), str) and 3 <= len(x["say"]) <= 240 for x in sc)
    except Exception:
        return False


def render(script, out_mp4, workdir):
    """Crea il video (voce + musica). Ritorna la durata in secondi."""
    import imageio.v2 as iio
    os.makedirs(workdir, exist_ok=True)
    script = _with_intro(script)
    badge = (f"{str(script.get('series') or 'Crypto money method').upper()[:24]} #{int(script['part'])}"
             if script.get("part") else None)
    wav, words, spans, total, mouth = build_audio(script, workdir)
    seed = _seed(script)
    bg = make_background(seed)
    scenes = [Scene(sc, bg=bg, seed=seed + i) for i, sc in enumerate(script["scenes"])]
    silent = os.path.join(workdir, "video.mp4")
    wr = iio.get_writer(silent, fps=FPS, codec="libx264", quality=7, macro_block_size=1,
                        ffmpeg_params=["-preset", "ultrafast", "-threads", "1", "-bf", "0",
                                       "-pix_fmt", "yuv420p"])
    n = int(total * FPS)
    wi = 0
    try:
        for fi in range(n):
            t = fi / FPS
            si = 0
            for k, (a, b) in enumerate(spans):
                if t >= a - GAP / 2:
                    si = k
            a, b = spans[si]
            p = max(0.0, min(1.0, (t - a) / max(0.8, b - a)))
            lvl = float(mouth[min(fi, len(mouth) - 1)])
            talking = a - 0.05 <= t <= b + 0.05
            fr = scenes[si].frame(t, p, lvl, talking)
            # CAMERA VIVA: non più una schermata ferma. Oltre al "punch-in" a inizio
            # scena, una lenta carrellata continua (zoom + pan) per tutta la scena,
            # con direzione decisa dal numero di scena. È quello che trasforma
            # l'immagine statica in qualcosa di cinematografico.
            u = max(0.0, min(1.0, (t - a) / max(0.1, b - a)))
            punch = 0.06 * (1 - ease((t - a + GAP / 2) / 0.28))
            z = 1.05 + 0.05 * u + punch
            _rc = random.Random((si + 1) * 2654435761 & 0xFFFFFFFF)
            dirx, diry = _rc.random() - 0.5, _rc.random() - 0.5
            big = fr.resize((int(OUT_W * z), int(OUT_H * z)), Image.BILINEAR)
            maxl, maxt = big.width - OUT_W, big.height - OUT_H
            l = int(max(0, min(maxl, maxl * (0.5 + dirx * 0.7 * (u - 0.5)))))
            tp = int(max(0, min(maxt, maxt * (0.5 + diry * 0.7 * (u - 0.5)))))
            fr = big.crop((l, tp, l + OUT_W, tp + OUT_H))
            while wi + 1 < len(words) and t >= words[wi + 1][0]:
                wi += 1
            if words:
                w0, w1, wd = words[wi]
                wd = _clean_word(wd)
                if wd and w0 - 0.05 <= t <= w1 + 0.25:
                    img = _caption_img(wd, min(3, int((t - w0) / 0.035)))
                    fr.paste(img, (int((OUT_W - img.width) / 2), int(CAPTION_Y * R - img.height / 2)), img)
            if badge and si > 0:    # numero della puntata sempre visibile (dopo l'apertura)
                bi = _badge_img(badge)
                fr.paste(bi, (int((OUT_W - bi.width) / 2), int(285 * R)), bi)
            wr.append_data(np.asarray(fr))
            del fr
            if fi % 96 == 0:
                gc.collect()
    finally:
        wr.close()
    # volume uniforme e alto come i video dei social (-14 LUFS), stereo
    subprocess.run([_ffmpeg(), "-v", "error", "-y", "-i", silent, "-i", wav, "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ac", "2", "-c:a", "aac",
                    "-b:a", "128k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    return total


SAMPLE = {
    "title": "The $100 crypto scam",
    "scenes": [
        {"say": "You get a message: send me one hundred dollars in crypto, and tomorrow I'll send you back a thousand.",
         "pose": "phone", "face": "surprised",
         "screen": {"type": "chat", "lines": ["Send me $100 in crypto", "get $1,000 tomorrow"]}},
        {"say": "You try it. And on day one, your balance goes up nine hundred percent!",
         "pose": "phone", "face": "happy", "props": ["coins"],
         "screen": {"type": "chart", "dir": "up", "label": "+900%", "sub": "your balance"}},
        {"say": "But when you try to withdraw, they say you must pay a three hundred dollar fee to unlock it.",
         "pose": "phone", "face": "worried",
         "screen": {"type": "alert", "title": "Withdrawal blocked", "sub": "Pay a $300 fee"}},
        {"say": "You pay. You wait. And the profile disappears, together with your money.",
         "pose": "sit", "face": "sad", "props": ["clock", "bench", "suitcase"]},
        {"say": "Simple rule: nobody legit asks you for money to give you back your own money.",
         "pose": "point", "face": "neutral", "props": ["sign"]},
        {"say": "Follow me, so nobody scams you with crypto again.", "pose": "wave", "face": "happy"},
    ],
}


def make_cartoon_reel(script):
    """Entrata pubblica: crea il reel e ritorna il percorso dell'mp4."""
    import shutil
    import tempfile
    if not valid_script(script):
        script = SAMPLE
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"cartoon_{int(time.time() * 1000)}.mp4")
    work = tempfile.mkdtemp(prefix="cartoon_")
    try:
        render(script, out, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out


if __name__ == "__main__":
    import sys
    t0 = time.time()
    print(make_cartoon_reel(SAMPLE), f"{time.time() - t0:.1f}s")
