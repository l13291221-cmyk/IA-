"""
Costruttore reel "3D" in stile social (immagini ferme + inquadrature + movimento).

I video virali di questo tipo NON sono animati: sono IMMAGINI del personaggio 3D
riprese da angolazioni diverse (fronte, 3/4, dall'alto, dal basso, primo piano),
montate con zoom/pan e tagli, con voce sotto e scritte. L'unica parte animata è
l'intro (soldi che piovono). Questo modulo fa esattamente questo, partendo da una
libreria di immagini pre-renderizzate (reel3d_assets/) — così il render 3D pesante
si fa UNA VOLTA (offline) e il server monta i reel in modo leggero.

Il personaggio attuale e' PROVVISORIO: per cambiarlo basta sostituire le immagini
in reel3d_assets/ (shot_front.png, shot_tq.png, shot_top.png, shot_low.png,
shot_side.png, shot_close.png) con quelle del modello scelto.

build_reel(spec, assets_dir, out_mp4) -> durata in secondi (video MUTO).
La voce la aggiunge il motore come gia' fa per gli altri reel.
"""
import os, math, random
import numpy as np
import imageio.v2 as iio
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H, FPS = 720, 1280, 24           # STESSA risoluzione dei reel cartoon che IG pubblica senza problemi
                                     # (e stessa misura delle immagini Pollinations: niente upscale)
CAP = (255, 255, 255)               # scritte BIANCHE (niente giallo): leggibili su ogni sfondo
BILL_G = (55, 201, 138)             # verde brand #37c98a
SHOTS = ("front", "tq", "top", "low", "side", "close")


def _font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()


def _caption(draw, word, y, size, col=CAP):
    """Scritta bianca con bordo nero, rimpicciolita per stare nel frame."""
    sw = max(3, size // 9)
    sz = size
    while sz > 20:
        f = _font(sz); bb = draw.textbbox((0, 0), word, font=f, stroke_width=sw)
        if bb[2] - bb[0] <= W - 90:
            break
        sz -= 4
    f = _font(sz); bb = draw.textbbox((0, 0), word, font=f, stroke_width=sw)
    draw.text(((W - (bb[2] - bb[0])) // 2 - bb[0], y), word, font=f, fill=col,
              stroke_width=sw, stroke_fill=(18, 18, 18))


def _kenburns(base, u, idx, updown=False):
    z = 1.03 + 0.10 * u
    bw, bh = int(W * z), int(H * z)
    big = base.resize((bw, bh), Image.LANCZOS)
    dirx = (-1) ** idx
    diry = 1 if updown else 0
    l = int((bw - W) * (0.5 + 0.33 * dirx * (u - 0.5)))
    t = int((bh - H) * (0.5 + 0.33 * diry * (u - 0.5)))
    l = max(0, min(bw - W, l)); t = max(0, min(bh - H, t))
    return big.crop((l, t, l + W, t + H))


def _bill_img():
    b = Image.new("RGBA", (int(W * 0.12), int(W * 0.058)), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.rounded_rectangle([2, 2, b.width - 3, b.height - 3], 10, fill=(*BILL_G, 255),
                        outline=(20, 120, 85, 255), width=4)
    cx, cy = b.width // 2, b.height // 2
    d.ellipse([cx - 14, cy - 11, cx + 14, cy + 11], outline=(20, 120, 85, 255), width=4)
    return b


def _load(assets_dir, name):
    p = os.path.join(assets_dir, f"shot_{name}.png")
    if not os.path.exists(p):
        p = os.path.join(assets_dir, "shot_front.png")
    return ImageOps.fit(Image.open(p).convert("RGB"), (W, H), method=Image.LANCZOS)


def build_reel(spec, assets_dir, out_mp4, fps=FPS):
    """spec = {"title": "...", "scenes": [{"shot": "front", "caption": "...",
    "dur": 1.7}], "intro": True, "end": "FOLLOW"}. Ritorna la durata (s)."""
    bill = _bill_img()
    wr = iio.get_writer(out_mp4, fps=fps, codec="libx264", quality=7,
                        macro_block_size=1, ffmpeg_params=["-pix_fmt", "yuv420p"])
    total = 0.0
    # ---- INTRO con soldi ----
    if spec.get("intro", True):
        base = _load(assets_dir, "low")
        rnd = random.Random(7)
        bills = [(rnd.uniform(0, W), rnd.uniform(-H, 0), rnd.uniform(0.25, 0.6),
                  rnd.uniform(0, 6.28)) for _ in range(18)]
        n = int(3.0 * fps)
        for i in range(n):
            u = i / n
            fr = _kenburns(base, u, 0, updown=True).copy()
            for (bx, by, sp, ph) in bills:
                y = (by + u * sp * H * 3) % (H + 120) - 60
                b2 = bill.rotate(math.sin(u * 6 + ph) * 25, expand=True)
                fr.paste(b2, (int(bx + math.sin(u * 4 + ph) * 44), int(y)), b2)
            d = ImageDraw.Draw(fr)
            for k, line in enumerate(str(spec.get("title", "")).upper().split("\n")[:2]):
                _caption(d, line, int(H * 0.16) + k * int(W * 0.14), int(W * 0.14))
            wr.append_data(np.asarray(fr))
        total += 3.0
    # ---- CORPO: inquadrature + scritte ----
    for idx, sc in enumerate(spec.get("scenes", [])):
        base = _load(assets_dir, sc.get("shot", SHOTS[idx % len(SHOTS)]))
        dur = float(sc.get("dur", 1.7))
        ud = sc.get("shot") in ("top", "low")
        n = int(dur * fps)
        for i in range(n):
            u = i / max(1, n)
            fr = _kenburns(base, u, idx + 1, updown=ud).copy()
            d = ImageDraw.Draw(fr)
            if sc.get("caption"):
                _caption(d, sc["caption"], int(H * 0.76), int(W * 0.12))
            wr.append_data(np.asarray(fr))
        total += dur
    # ---- END CARD ----
    if spec.get("end"):
        base = _load(assets_dir, "front")
        n = int(1.4 * fps)
        for i in range(n):
            u = i / n
            fr = _kenburns(base, u, 9).copy()
            d = ImageDraw.Draw(fr)
            _caption(d, spec["end"], int(H * 0.44), int(W * 0.17))
            wr.append_data(np.asarray(fr))
        total += 1.4
    wr.close()
    return total


def build_from_images(scenes, out_mp4, fps=FPS):
    """Monta un reel da scene con immagini ESPLICITE (quelle generate dall'IA).
    scenes = [{"image": path, "caption": "...", "dur": 1.8, "bills": False}].
    La prima scena puo' avere "bills": True per l'intro coi soldi. Muto."""
    bill = _bill_img()
    wr = iio.get_writer(out_mp4, fps=fps, codec="libx264", quality=7,
                        macro_block_size=1, ffmpeg_params=["-pix_fmt", "yuv420p"])
    total = 0.0
    money = None
    for idx, sc in enumerate(scenes):
        p = sc.get("image")
        if not p or not os.path.exists(p):
            continue
        base = ImageOps.fit(Image.open(p).convert("RGB"), (W, H), method=Image.LANCZOS)
        dur = float(sc.get("dur", 1.8))
        n = int(dur * fps)
        rnd = random.Random(idx + 1)
        if sc.get("bills"):
            money = [(rnd.uniform(0, W), rnd.uniform(-H, 0), rnd.uniform(0.25, 0.6),
                      rnd.uniform(0, 6.28)) for _ in range(18)]
        for i in range(n):
            u = i / max(1, n)
            fr = _kenburns(base, u, idx).copy()
            if sc.get("bills") and money:
                for (bx, by, sp, ph) in money:
                    y = (by + u * sp * H * 3) % (H + 120) - 60
                    b2 = bill.rotate(math.sin(u * 6 + ph) * 25, expand=True)
                    fr.paste(b2, (int(bx + math.sin(u * 4 + ph) * 44), int(y)), b2)
            d = ImageDraw.Draw(fr)
            if sc.get("caption"):
                size = int(W * (0.15 if sc.get("title") else 0.12))
                y = int(H * (0.16 if sc.get("title") else 0.76))
                _caption(d, sc["caption"], y, size)
            wr.append_data(np.asarray(fr))
        total += dur
    wr.close()
    return total


if __name__ == "__main__":
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    demo = {
        "title": "CRYPTO MONEY\nMETHOD #1",
        "intro": True,
        "scenes": [
            {"shot": "front", "caption": "Most beginners"},
            {"shot": "tq", "caption": "panic and sell"},
            {"shot": "low", "caption": "when it drops"},
            {"shot": "top", "caption": "at the worst time"},
            {"shot": "side", "caption": "they sell all"},
            {"shot": "close", "caption": "then it recovers"},
        ],
        "end": "FOLLOW",
    }
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "reel3d_sample.mp4")
    d = build_reel(demo, os.path.join(here, "reel3d_assets"), out)
    print("reel3d OK", round(d, 1), "s ->", out)
