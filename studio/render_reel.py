"""Monta un reel verticale 1080x1920 da: intro Vadoo + immagini Vadoo + voce (Edge TTS gratis).

Uso:  python render_reel.py spec.json out.mp4

spec.json:
{
  "part": 1,
  "series": "HOW TO INVEST IN CRYPTO",
  "voice": "en-US-AndrewNeural", "rate": "+6%",
  "intro": "/percorso/intro.mp4",
  "img_dir": "/percorso/immagini",
  "scenes": [ {"say": "testo detto", "img": "intro" | "file.jpg" | ["a.jpg", "b.jpg"],
               "show": "testo sottotitolo opzionale (stesse parole, grafia diversa)"} ]
}
"""
import asyncio
import json
import math
import os
import re
import ssl
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import edge_tts
import edge_tts.communicate as _ec

_CA = os.environ.get("CCR_CA", "/root/.ccr/ca-bundle.crt")
if os.path.exists(_CA):                       # dietro al proxy dell'ambiente cloud
    _ec._SSL_CTX = ssl.create_default_context(cafile=_CA)

W, H, FPS = 1080, 1920, 30
SR = 48000
GOLD = (245, 197, 66)
WHITE = (255, 255, 255)
_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = next((d for d in (os.environ.get("FONT_DIR", ""), os.path.join(_HERE, "fonts"),
                             "/usr/share/fonts/opentype/inter") if d and os.path.exists(os.path.join(d, "Inter-Black.otf"))),
                "/usr/share/fonts/opentype/inter") + "/"
F_BLACK = FONT_DIR + "Inter-Black.otf"
F_XBOLD = FONT_DIR + "Inter-ExtraBold.otf"
GAP = 0.22          # pausa tra le frasi
LEAD = 0.30         # silenzio iniziale
TAIL = 0.9          # coda finale
XFADE = 0.28        # dissolvenza tra immagini
CAP_Y = 1235        # centro verticale dei sottotitoli (zona sicura dei reel)
# Nell'intro la bocca del lupo PARLA da 0,05 s a 4,55 s, poi si chiude (misurato fotogramma per
# fotogramma su intro.mp4). La frase si adatta alla bocca: la voce parte quando la bocca si apre
# e l'intro finisce quando la bocca si chiude (niente voce a bocca chiusa).
MOUTH = (0.05, 4.55)
INTRO_PAUSE = 0.18  # pausa fra "Come investire in crypto." e "Parte 153." (la voce da sola ne fa quasi 1 s)


# ------------------------------------------------------------------ voce
async def _tts(text, voice, rate, mp3):
    c = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append([ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]])
    return words


def tts_complete(text, words, mp3):
    """La voce di Edge a volte si INTERROMPE a metà senza errore (manca un pezzo di frase).
    Controllo che siano arrivate quasi tutte le parole, che l'ultima sia quella della frase e
    che l'audio arrivi fino in fondo all'ultima parola. Ritorna (ok, durata audio)."""
    dur = len(decode_audio(mp3)) / SR
    toks = re.findall(r"\w+", text.lower())
    if not toks:
        return True, dur
    if not words:
        return False, dur
    if len(text.split()) >= 6 and len(words) < 0.75 * len(text.split()):   # date e numeri = 1 parola sola
        return False, dur
    last = re.findall(r"\w+", " ".join(w[2] for w in words[-3:]).lower())
    if toks[-1] not in last:
        return False, dur
    return dur >= words[-1][0] + words[-1][1] - 0.05, dur


def tts(text, voice, rate, mp3):
    best = None
    for attempt in range(6):
        try:
            words = asyncio.run(_tts(text, voice, rate, mp3))
        except Exception as exc:  # rete instabile: riprovo
            print("tts retry", attempt, exc, flush=True)
            continue
        ok, dur = tts_complete(text, words, mp3)
        if ok:
            return words
        print(f"voce interrotta (tentativo {attempt + 1}): {len(words)} parole, {dur:.1f}s - {text[:60]}", flush=True)
        if best is None or dur > best[0]:
            best = (dur, words, open(mp3, "rb").read())
    if best is None:
        raise RuntimeError("TTS non raggiungibile")
    print("ATTENZIONE voce forse incompleta:", text[:60], flush=True)
    with open(mp3, "wb") as f:                     # tengo il tentativo più lungo
        f.write(best[2])
    return best[1]


def trim_silence(pcm, words):
    """Toglie il silenzio all'inizio e alla fine di una frase del TTS, così fra una frase e
    l'altra resta solo la pausa voluta (GAP): niente bocca che si muove a vuoto nell'intro.
    Misuro solo la parte che SI SENTE (tolgo i toni gravi e il ronzio che la voce lascia
    in coda, che prima contavano come voce); i tempi delle parole si spostano."""
    win = int(0.02 * SR)
    n = len(pcm) // win
    if n < 3:
        return pcm, words
    spec = np.fft.rfft(pcm)                             # via i toni gravi e il ronzio (< 300 Hz)
    spec[np.fft.rfftfreq(len(pcm), 1 / SR) < 300] = 0
    hp = np.fft.irfft(spec, len(pcm)).astype(np.float32)
    env = np.sqrt((hp[: n * win].reshape(n, win) ** 2).mean(axis=1))
    loud = np.nonzero(env > env.max() * 0.08)[0]
    if not len(loud):
        return pcm, words
    a = max(0, loud[0] * win - int(0.04 * SR))
    b = min(len(pcm), (loud[-1] + 1) * win + int(0.10 * SR))
    if words:                                          # mai tagliare dentro una parola
        a = min(a, max(0, int((words[0][0] - 0.02) * SR)))
        b = max(b, min(len(pcm), int((words[-1][0] + 0.15) * SR)))
    return pcm[a:b], [[max(0.0, w[0] - a / SR), w[1], w[2]] for w in words]


def decode_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


# ------------------------------------------------------------------ musica di sottofondo (sintetizzata)
def music_bed(seconds):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    # Am - F - C - G, accordi morbidi
    chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
    dur = 2.4
    hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    k = 0
    while k * dur < seconds:
        notes = chords[k % 4]
        a, b = int(k * dur * SR), min(n, int((k + 1) * dur * SR + 0.6 * SR))
        tt = t[a:b] - k * dur
        env = np.minimum(1, tt / 0.5) * np.exp(-np.maximum(0, tt - dur) / 0.25)
        seg = np.zeros(b - a, dtype=np.float32)
        for m in notes:
            f = hz(m - 12)
            seg += (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)
                    + 0.08 * np.sin(6 * np.pi * f * tt)).astype(np.float32)
        # arpeggio leggero
        for j in range(8):
            st = j * dur / 8
            m = notes[[0, 1, 2, 3, 2, 1, 2, 3][j]] + 12
            f = hz(m)
            tp = tt - st
            mask = tp >= 0
            pl = np.zeros_like(seg)
            pl[mask] = (np.sin(2 * np.pi * f * tp[mask]) * np.exp(-tp[mask] / 0.18)).astype(np.float32)
            seg += 0.35 * pl
        out[a:b] += seg * env.astype(np.float32)
        k += 1
    # passa-basso semplice per renderla morbida
    kernel = np.ones(24, dtype=np.float32) / 24
    out = np.convolve(out, kernel, mode="same")
    out /= (np.abs(out).max() + 1e-6)
    fade = np.minimum(1, t / 1.0) * np.minimum(1, (seconds - t) / 1.5)
    return (out * fade).astype(np.float32)


# ------------------------------------------------------------------ grafica
_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def cover(img, w, h):
    iw, ih = img.size
    s = max(w / iw, h / ih)
    img = img.resize((max(w, round(iw * s)), max(h, round(ih * s))), Image.LANCZOS)
    x, y = (img.size[0] - w) // 2, (img.size[1] - h) // 2
    return img.crop((x, y, x + w, y + h))


class KenBurns:
    """Zoom/pan lento su un'immagine 9:16."""

    def __init__(self, path, idx):
        flip = path.endswith(":flip")          # "foto.jpg:flip" = immagine specchiata (riuso)
        path = path[:-5] if flip else path
        base = cover(Image.open(path).convert("RGB"), W, H)
        if flip:
            base = base.transpose(Image.FLIP_LEFT_RIGHT)
        self.big = base.resize((int(W * 1.14), int(H * 1.14)), Image.LANCZOS)
        self.zoom_in = idx % 2 == 0
        self.dx = [0.0, 0.5, -0.5, 0.3][idx % 4]

    def frame(self, p):
        p = max(0.0, min(1.0, p))
        e = p * p * (3 - 2 * p)
        z = 1.0 + 0.12 * (e if self.zoom_in else 1 - e)    # 1.00 -> 1.12 (o al contrario)
        cw, ch = W * 1.14 / z, H * 1.14 / z
        bw, bh = self.big.size
        cx = bw / 2 + self.dx * (bw - cw) / 2 * (e - 0.5)
        cy = bh / 2
        cw, ch = min(cw, bw), min(ch, bh)
        cx = min(max(cx, cw / 2), bw - cw / 2)
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        return self.big.resize((W, H), Image.BILINEAR, box=box)


def draw_text_stroke(d, xy, text, f, fill, stroke=8, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))


def caption_layer(words, active):
    """Sottotitolo: parole MAIUSCOLE, quella detta in oro. Ritorna immagine RGBA."""
    size = 92
    while True:
        f = font(F_BLACK, size)
        space = f.getlength(" ")
        widths = [f.getlength(w) for w in words]
        total = sum(widths) + space * (len(words) - 1)
        if total <= 960 or size <= 60:
            break
        size -= 4
    layer = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # ombra morbida
    sh = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    x = (W - total) / 2
    for w, wd in zip(words, widths):
        ds.text((x + 4, 136), w, font=f, fill=(0, 0, 0, 170), anchor="lm", stroke_width=10, stroke_fill=(0, 0, 0, 170))
        x += wd + space
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    layer.alpha_composite(sh)
    x = (W - total) / 2
    for i, (w, wd) in enumerate(zip(words, widths)):
        col = GOLD if i == active else WHITE
        d.text((x, 130), w, font=f, fill=col, anchor="lm", stroke_width=9, stroke_fill=(0, 0, 0))
        x += wd + space
    return layer


def _norm(x):
    return "".join(ch for ch in x.lower() if ch.isalnum())


def align_punct(words, text):
    """Le parole del TTS non hanno punteggiatura: la riprendo dal testo originale."""
    toks = text.split()
    j = 0
    for w in words:
        nw = _norm(w[2])
        for k in range(j, min(j + 4, len(toks))):
            if nw and nw in _norm(toks[k]):
                tail = toks[k][len(toks[k].rstrip(".,?!:;")):]
                if _norm(toks[k]).endswith(nw) and tail:
                    w[2] = w[2].rstrip(".,?!:;") + tail[-1]
                j = k + 1
                break
    return words


def apply_show(words, repl):
    """repl = {"fifty percent": "50%"}: unisce le parole dette nel testo da mostrare."""
    for frm, to in repl.items():
        target = [_norm(x) for x in frm.split()]
        i = 0
        while i <= len(words) - len(target):
            if [_norm(w[2]) for w in words[i:i + len(target)]] == target:
                last = words[i + len(target) - 1]
                punct = last[2][len(last[2].rstrip(".,?!:;")):]
                merged = [words[i][0], last[0] + last[1] - words[i][0], to + punct]
                words[i:i + len(target)] = [merged]
            i += 1
    return words


def chunk_words(words, max_words=3, max_chars=17):
    """Raggruppa le parole in blocchi brevi da sottotitolo."""
    chunks, cur = [], []
    for w in words:
        txt = w[2]
        cand = cur + [w]
        chars = sum(len(x[2]) for x in cand) + len(cand) - 1
        if cur and (len(cand) > max_words or chars > max_chars):
            chunks.append(cur)
            cur = [w]
        else:
            cur = cand
        if txt.endswith((".", ",", "?", "!", ":")):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def intro_title_layer(series, part, alpha, part_label="PART", badge=None):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # badge PART N
    f = font(F_BLACK, 64)
    label = badge or f"{part_label} {part}"
    tw = f.getlength(label)
    bx0, by0 = (W - tw) / 2 - 38, 236
    d.rounded_rectangle((bx0, by0, bx0 + tw + 76, by0 + 96), radius=48, fill=GOLD + (255,))
    d.text((W / 2, by0 + 50), label, font=f, fill=(15, 15, 20), anchor="mm")
    # titolo serie (due righe se serve)
    words = series.split()
    lines = [" ".join(words[: len(words) // 2 + len(words) % 2]), " ".join(words[len(words) // 2 + len(words) % 2:])] \
        if font(F_BLACK, 96).getlength(series) > 980 else [series]
    y = 470 if len(lines) == 1 else 425
    for i, ln in enumerate(lines):
        size = 96
        while font(F_BLACK, size).getlength(ln) > 1000:
            size -= 4
        col = WHITE if i == 0 else GOLD
        draw_text_stroke(d, (W / 2, y + i * 108), ln, font(F_BLACK, size), col, stroke=10)
    if alpha < 1:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer.putalpha(a)
    return layer


def read_intro_frames(path):
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "json", path], capture_output=True, check=True).stdout
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={FPS},scale=1080:1080:flags=lanczos",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (1080 * 1080 * 3)
    arr = np.frombuffer(raw, dtype=np.uint8)[: n * 1080 * 1080 * 3].reshape(n, 1080, 1080, 3)
    return arr


def intro_frame(sq, series, part, t, part_label="PART", badge=None):
    fg = Image.fromarray(sq)
    bg = fg.resize((H, H), Image.BILINEAR).crop(((H - W) // 2, 0, (H - W) // 2 + W, H))
    bg = bg.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
    bg = Image.eval(bg, lambda v: int(v * 0.42))
    canvas = bg.convert("RGBA")
    # bordo oro sottile attorno al riquadro
    y0 = 610
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, y0 - 6, W, y0 + 1080 + 6), fill=GOLD + (255,))
    canvas.paste(fg, (0, y0))
    alpha = min(1.0, max(0.0, (t - 0.15) / 0.35))
    if alpha > 0:
        canvas.alpha_composite(intro_title_layer(series, part, alpha, part_label, badge))
    return canvas


# ------------------------------------------------------------------ montaggio
def build(spec_path, out_path):
    spec = json.load(open(spec_path))
    work = os.path.splitext(out_path)[0] + "_work"
    os.makedirs(work, exist_ok=True)
    voice, rate = spec.get("voice", "en-US-AndrewNeural"), spec.get("rate", "+6%")
    img_dir = spec.get("img_dir", os.path.dirname(spec_path))

    # 1) voce scena per scena
    mouth = spec.get("mouth", MOUTH)

    def voices(rate):
        scenes = []
        t = mouth[0] if spec["scenes"] and spec["scenes"][0]["img"] == "intro" else LEAD
        for i, sc in enumerate(spec["scenes"]):
            # La frase dell'intro la faccio dire a pezzi (frase per frase) con una pausa breve:
            # così la voce resta attaccata alla bocca che si muove.
            parts = ([p for p in re.split(r"(?<=[.!?])\s+", sc["say"].strip()) if p]
                     if sc["img"] == "intro" else [sc["say"]])
            pcms, words, off = [], [], 0.0
            for j, ptxt in enumerate(parts):
                mp3 = os.path.join(work, f"v{i:02d}_{j}.mp3")
                wj = tts(ptxt, voice, rate, mp3)
                pj, wj = trim_silence(decode_audio(mp3), wj)   # niente silenzio prima e dopo la frase
                words += [[w[0] + off, w[1], w[2]] for w in wj]
                pcms.append(pj)
                off += len(pj) / SR
                if j < len(parts) - 1:
                    pcms.append(np.zeros(int(INTRO_PAUSE * SR), dtype=np.float32))
                    off += INTRO_PAUSE
            pcm = np.concatenate(pcms)
            dur = len(pcm) / SR
            words = align_punct(words, sc["say"])
            words = apply_show(words, sc.get("show") or {})
            scenes.append({"start": t, "dur": dur, "pcm": pcm, "words": words, "img": sc["img"], "i": i,
                           "cap": bool(sc.get("caption")), "after": sc.get("after")})
            t += dur + GAP
        return scenes, t - GAP + TAIL

    scenes, total = voices(rate)
    # Video troppo lungo (es. massimo 35 s per i reel): la voce va un po' più veloce, solo quanto serve.
    maxs = spec.get("max_seconds")
    if maxs and total > maxs:
        base = int(str(rate).strip().rstrip("%") or 0)
        for extra in (4, 8, 12, 16):
            r2 = f"{base + extra:+d}%"
            print(f"video di {total:.1f}s (massimo {maxs}s): voce un po' più veloce ({r2})", flush=True)
            scenes, total = voices(r2)
            if total <= maxs:
                break

    # 2) traccia audio: voce + musica
    n = int(total * SR) + SR
    voice_tr = np.zeros(n, dtype=np.float32)
    for s in scenes:
        a = int(s["start"] * SR)
        voice_tr[a: a + len(s["pcm"])] += s["pcm"]
    mus = music_bed(n / SR) * 0.055
    mus = np.pad(mus, (0, max(0, n - len(mus))))[:n]     # stessa lunghezza della voce
    mix = voice_tr + mus
    mix /= max(1.0, np.abs(mix).max() / 0.97)
    wav = os.path.join(work, "mix.wav")
    import wave
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix * 32767).astype(np.int16).tobytes())

    # 3) segmenti visivi
    intro_frames = read_intro_frames(spec["intro"])
    intro_len = len(intro_frames) / FPS
    segs = []   # (start, end, kind, payload)
    cursor = 0.0
    for k, s in enumerate(scenes):
        imgs = s["img"] if isinstance(s["img"], list) else [s["img"]]
        nxt = scenes[k + 1]["start"] if k + 1 < len(scenes) else total
        if imgs == ["intro"]:
            end = max(min(intro_len, mouth[1] + 0.05), 0.1)     # finisce quando la bocca si chiude
            segs.append([0.0, end, "intro", None])
            cursor = end
            if s.get("after") and nxt > end + 0.3:               # il gancio dura di più: la sua immagine
                segs.append([end, nxt, "img", s["after"]])
                cursor = nxt
            continue
        st = max(s["start"], cursor)
        if st >= nxt:
            continue
        step = (nxt - st) / len(imgs)
        for j, im in enumerate(imgs):
            segs.append([st + j * step, st + (j + 1) * step, "img", im])
        cursor = nxt
    segs[-1][1] = total
    kb = {}
    for idx, sg in enumerate(segs):
        if sg[2] == "img":
            kb[idx] = KenBurns(os.path.join(img_dir, sg[3]), idx)

    # 4) sottotitoli (blocchi con tempi assoluti)
    caps = []
    for s in scenes:
        if s["img"] == "intro" and not s.get("cap"):
            continue
        for ch in chunk_words(s["words"]):
            words = [w[2].upper().strip(",.") for w in ch]
            st = s["start"] + ch[0][0]
            times = [s["start"] + w[0] for w in ch]
            end = s["start"] + ch[-1][0] + ch[-1][1] + 0.15
            caps.append({"st": st, "end": end, "words": words, "times": times})
    for a, b in zip(caps, caps[1:]):
        a["end"] = min(max(a["end"], b["st"] - 0.02), b["st"])
    cap_cache = {}

    # 5) rendering fotogrammi -> ffmpeg
    nframes = int(total * FPS)
    tmp_video = os.path.join(work, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-maxrate", "3500k", "-bufsize", "7M",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-movflags", "+faststart", "-shortest", tmp_video],
                          stdin=subprocess.PIPE)
    series, part = spec.get("series", "HOW TO INVEST IN CRYPTO"), spec.get("part", 1)

    def seg_frame(idx, t):
        st, en, kind, _ = segs[idx]
        if kind == "intro":
            fi = min(len(intro_frames) - 1, int(t * FPS))
            return intro_frame(intro_frames[fi], series, part, t, spec.get("part_label", "PART"), spec.get("badge"))
        p = (t - st) / max(0.01, en - st)
        return kb[idx].frame(p).convert("RGBA")

    for fno in range(nframes):
        t = fno / FPS
        idx = next(i for i, sg in enumerate(segs) if sg[0] <= t < sg[1] or i == len(segs) - 1)
        frame = seg_frame(idx, t)
        # dissolvenza dal segmento precedente
        if idx > 0 and t - segs[idx][0] < XFADE:
            prev = seg_frame(idx - 1, t)
            a = (t - segs[idx][0]) / XFADE
            frame = Image.blend(prev, frame, a * a * (3 - 2 * a))
        # sottotitolo
        cap = next((c for c in caps if c["st"] <= t < c["end"]), None)
        if cap:
            active = max(i for i, tt in enumerate(cap["times"]) if tt <= t + 0.02) if cap["times"][0] <= t + 0.02 else 0
            key = (id(cap), active)
            if key not in cap_cache:
                cap_cache[key] = caption_layer(cap["words"], active)
            lay = cap_cache[key]
            # piccolo "pop" quando compare il blocco
            age = t - cap["st"]
            if age < 0.12:
                s = 0.86 + 0.14 * (age / 0.12)
                lw, lh = int(W * s), int(260 * s)
                lay2 = lay.resize((lw, lh), Image.BILINEAR)
                frame.alpha_composite(lay2, ((W - lw) // 2, CAP_Y - lh // 2))
            else:
                frame.alpha_composite(lay, (0, CAP_Y - 130))
        ff.stdin.write(frame.convert("RGB").tobytes())
        if fno % 150 == 0:
            print(f"frame {fno}/{nframes}", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg fallito")
    os.replace(tmp_video, out_path)
    meta = {"duration": total, "scenes": [{"start": s["start"], "dur": s["dur"], "say": spec["scenes"][s["i"]]["say"]}
                                          for s in scenes]}
    json.dump(meta, open(os.path.join(work, "timeline.json"), "w"), indent=1)
    print("OK", out_path, f"{total:.1f}s")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
