"""COPERTINE dei video (Instagram e YouTube): l'immagine della prima scena, l'ARGOMENTO
della puntata scritto grande e "PART N". Prima la copertina era un fotogramma a caso con
mezza frase dei sottotitoli ("THE REAL MARKET", "IT'S CONNECTED TO").

Il testo sta nella fascia centrale, così si legge anche nella griglia del profilo
(che taglia la copertina in 3:4).

Uso:  python studio/covers.py [nomi…]   → work/covers/<nome>.jpg  (senza nomi: tutti)"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

STUDIO = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(STUDIO, "library")


def key_img_name(k, i):                       # come batch_render (senza caricare la voce)
    return f"{k}_s{i}" if k.startswith("p") else f"{int(k):02d}_s{i}"


def lib_img(name_1jpg):
    base, _, flip = name_1jpg.partition(":")
    stem = base[:-6] if base.endswith("_1.jpg") else base.rsplit(".", 1)[0]
    if os.path.exists(os.path.join(LIB, stem + ".jpg")):
        return stem + ".jpg" + (":" + flip if flip else "")
    return None

W, H = 1080, 1920
OUT = os.path.join(STUDIO, "work", "covers")
FONT_BLACK = os.path.join(STUDIO, "fonts", "Inter-Black.otf")
FONT_BOLD = os.path.join(STUDIO, "fonts", "Inter-ExtraBold.otf")
YELLOW = (255, 212, 0)
SERIES = {"en": "HOW TO INVEST IN CRYPTO", "promo": "YOUR CRYPTO ASSISTANT"}


def first_image(name):
    """(percorso, capovolta) dell'immagine della prima scena del video `name`."""
    plan = json.load(open(os.path.join(STUDIO, "series", "plan.json")))
    key = None
    if name.endswith("a") and name[:-1].isdigit():
        key = f"p{int(name[:-1]):03d}"
    elif name.isdigit():
        key = str(int(name))
    img = None
    if key and key in plan:
        sc = plan[key]["scenes"][0]
        img = lib_img(sc["img"]) if sc.get("img") else lib_img(key_img_name(key, 0) + "_1.jpg")
    else:
        sp = os.path.join(STUDIO, "bot", "scripts", f"{name}.json")
        if os.path.exists(sp):
            en = json.load(open(sp)).get("en") or []
            for sc in en:
                cand = sc.get("after") if sc.get("img") == "intro" else sc.get("img")
                if isinstance(cand, list):
                    cand = cand[0]
                if cand and cand != "intro":
                    img = cand
                    break
    if not img:
        return None, False
    base, _, flip = img.partition(":")
    path = os.path.join(LIB, base)
    return (path if os.path.exists(path) else None), flip == "flip"


def _cover_crop(im):
    sc = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def _wrap(draw, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make(name, entry, out_dir=OUT):
    """Crea work/covers/<name>.jpg. Ritorna il percorso, o None se manca l'immagine."""
    path, flip = first_image(name)
    if not path:
        return None
    im = Image.open(path).convert("RGB")
    if flip:
        im = ImageOps.mirror(im)
    im = _cover_crop(im)
    # scurisco: più al centro (dove va il testo), meno in alto e in basso
    shade = Image.new("L", (W, H))
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        d = abs(y - 1060) / 900
        sd.line([(0, y), (W, y)], fill=int(175 * max(0.0, 1 - d * 1.1) + 40))
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, shade)
    dr = ImageDraw.Draw(im)

    promo = bool(entry.get("promo"))
    title = (entry.get("topic_en") or entry.get("hook_en") or "").upper().rstrip(".")
    # testo grande: il più grande che sta in 5 righe larghe 940 px
    for size in range(118, 58, -4):
        font = ImageFont.truetype(FONT_BLACK, size)
        lines = _wrap(dr, title, font, 940)
        if len(lines) <= (4 if size > 80 else 5):
            break
    lh = int(size * 1.12)
    block = lh * len(lines)
    top = 1060 - block // 2 + 30

    badge = "VCRIPTOV" if promo else f"PART {entry.get('part')}"
    bf = ImageFont.truetype(FONT_BLACK, 56)
    bw = dr.textlength(badge, font=bf)
    bx, by = (W - bw) / 2, top - 130
    dr.rounded_rectangle([bx - 34, by - 14, bx + bw + 34, by + 74], radius=22, fill=YELLOW)
    dr.text((bx, by), badge, font=bf, fill=(10, 10, 10))

    for i, ln in enumerate(lines):
        w = dr.textlength(ln, font=font)
        dr.text(((W - w) / 2, top + i * lh), ln, font=font, fill=(255, 255, 255),
                stroke_width=max(4, size // 14), stroke_fill=(0, 0, 0))

    sf = ImageFont.truetype(FONT_BOLD, 40)
    series = SERIES["promo" if promo else "en"]
    sw = dr.textlength(series, font=sf)
    dr.text(((W - sw) / 2, top + block + 34), series, font=sf, fill=YELLOW, stroke_width=3, stroke_fill=(0, 0, 0))
    ff = ImageFont.truetype(FONT_BOLD, 38)
    foot = "vcriptov.com"
    dr.text(((W - dr.textlength(foot, font=ff)) / 2, 1730), foot, font=ff, fill=(255, 255, 255),
            stroke_width=3, stroke_fill=(0, 0, 0))

    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{name}.jpg")
    im.save(out, "JPEG", quality=86, optimize=True, progressive=True)
    return out


def main(names=None):
    data = json.load(open(os.path.join(STUDIO, "series", "social.json")))
    names = names or list(data)
    ok, miss = 0, []
    for n in names:
        if n in data and make(n, data[n]):
            ok += 1
        else:
            miss.append(n)
    print(f"copertine: {ok} fatte" + (f", senza immagine: {', '.join(miss)}" if miss else ""))
    return miss


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--mancanti"]:
        # solo i video che non hanno ancora la copertina nella release (elenco in HAVE)
        have = {x.rsplit(".", 1)[0] for x in os.environ.get("HAVE", "").split()}
        todo = [n for n in json.load(open(os.path.join(STUDIO, "series", "social.json"))) if n not in have]
        print(f"da fare: {len(todo)}")
        main(todo) if todo else None
    else:
        main(args or None)
