"""
Orchestratore reel in stile "MaialeDiWallStreet": genera le SCENE con l'IA
(stesso personaggio in luoghi/pose diversi) e le monta in un reel verticale.

build_ai_reel(script, out_mp4, character_path, api_key) -> durata (video MUTO;
la voce la aggiunge il motore come per gli altri reel).

script = {
  "scenes": [
     {"prompt": "...", "caption": "PAROLA", "character": True, "bills": True,
      "title": True, "dur": 3.0},
     ...
  ]
}
Se la generazione IA non e' disponibile (niente chiave / errore rete), ogni scena
ripiega sull'immagine del personaggio: il reel esce comunque (versione ridotta).
"""
import os, time, tempfile, subprocess, shutil
import genscene
import reel3d


def make_ai_reel(script, out_dir, api_key, character_path=None):
    """Pipeline COMPLETA per il worker: genera le scene con l'IA, monta il reel
    e aggiunge la VOCE (edge-tts). Ritorna il percorso dell'mp4 finale (con audio).
    Ogni scena puo' avere: prompt (per generare l'immagine), caption (scritta),
    narration (testo letto dalla voce), character (bool), bills/title (intro)."""
    import cartoon   # per _tts (edge-tts), _decode, _ffmpeg
    os.makedirs(out_dir, exist_ok=True)
    wd = tempfile.mkdtemp(prefix="aireel_")
    character_path = character_path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "reel3d_assets", "character.jpg")
    scenes = script.get("scenes", [])
    provider = script.get("provider") or "auto"
    # 1) immagini generate dall'IA. NIENTE immagine fissa di ripiego: se una scena
    #    non viene generata, la SALTO (scena intera: immagine+scritta+voce). Il lupo
    #    lo genero UNA volta e lo riuso in tutte le scene-personaggio (coerenza).
    kept = []          # scene effettivamente generate (sc, img)
    wolf_img = None
    first = True
    for i, sc in enumerate(scenes):
        img = os.path.join(wd, f"s{i}.png"); got = None
        if sc.get("prompt"):
            is_char = sc.get("character", True)
            if is_char and wolf_img:
                got = wolf_img                       # riuso il lupo gia' generato
            else:
                if not first:
                    time.sleep(3)                    # distanzio le chiamate
                if is_char:
                    got = genscene.generate_scene(sc["prompt"], character_path, api_key, img,
                                                  provider=provider, seed=genscene.WOLF_SEED)
                    if got:
                        wolf_img = got
                else:
                    got = genscene.generate_object(sc["prompt"], api_key, img,
                                                   provider=provider, seed=100 + i)
                first = False
        if got:
            kept.append((sc, got))                   # tengo solo le scene con immagine VERA
    if len(kept) < 2:
        # l'IA non ha generato abbastanza immagini: NON pubblico un video con
        # immagini fisse. Meglio niente che una schifezza.
        raise RuntimeError("immagini IA non generate (nessuna fonte disponibile): reel annullato")
    kept_scenes = [sc for sc, _ in kept]
    imgs = [im for _, im in kept]
    # 2) voce unica (solo le scene tenute) + durata
    narr = " ".join((sc.get("narration") or sc.get("caption") or "").strip()
                    for sc in kept_scenes).strip()
    mp3 = os.path.join(wd, "voice.mp3"); total = None
    if narr:
        try:
            cartoon._tts(narr, mp3)
            total = len(cartoon._decode(mp3)) / cartoon.SR
        except Exception:
            total = None
    # 3) durate scene proporzionali al testo (cosi' la voce copre il video)
    weights = [max(1, len((sc.get("narration") or sc.get("caption") or ""))) for sc in kept_scenes]
    if total and sum(weights) > 0:
        durs = [max(1.0, total * w / sum(weights)) for w in weights]
    else:
        durs = [float(sc.get("dur", 1.8)) for sc in kept_scenes]
    # durata MINIMA 9s: un reel troppo corto (e piu' corto della copertina a 5.8s)
    # fa fallire Instagram. Se e' corto, allungo le scene in proporzione.
    if sum(durs) < 9.0:
        f = 9.0 / max(0.1, sum(durs))
        durs = [d * f for d in durs]
    scenes_out = [{"image": imgs[i], "caption": sc.get("caption"), "dur": durs[i],
                   "bills": sc.get("bills", False), "title": sc.get("title", False)}
                  for i, sc in enumerate(kept_scenes)]
    silent = os.path.join(wd, "silent.mp4")
    reel3d.build_from_images(scenes_out, silent)
    out = os.path.join(out_dir, f"aireel_{int(time.time())}.mp4")
    ff = cartoon._ffmpeg()
    if total:
        # STESSO mux dei reel cartoon che IG pubblica: copio il video (niente re-encode)
        # + audio AAC con loudnorm + faststart (indice all'inizio).
        subprocess.run([ff, "-v", "error", "-y", "-i", silent, "-i", mp3, "-c:v", "copy",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ac", "2", "-c:a", "aac",
                        "-b:a", "128k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out], check=True)
    else:
        # niente voce: aggiungo comunque una traccia audio SILENZIOSA (un reel senza
        # audio Instagram lo rifiuta) + faststart.
        subprocess.run([ff, "-v", "error", "-y", "-i", silent,
                        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                        "-movflags", "+faststart", "-shortest", out], check=True)
    return out


def build_ai_reel(script, out_mp4, character_path, api_key, workdir=None, log=None):
    def _log(m):
        if log:
            try: log(m)
            except Exception: pass
    workdir = workdir or tempfile.mkdtemp(prefix="reelai_")
    os.makedirs(workdir, exist_ok=True)
    scenes_out, gen_ok = [], 0
    for i, sc in enumerate(script.get("scenes", [])):
        img = os.path.join(workdir, f"scene_{i:02d}.png")
        got = None
        prompt = sc.get("prompt", "")
        if prompt:
            if sc.get("character", True):
                got = genscene.generate_scene(prompt, character_path, api_key, img)
            else:
                got = genscene.generate_object(prompt, api_key, img)
        if got:
            gen_ok += 1
        else:
            got = character_path   # ripiego: immagine del personaggio
        scenes_out.append({"image": got, "caption": sc.get("caption"),
                           "dur": sc.get("dur", 1.8), "bills": sc.get("bills", False),
                           "title": sc.get("title", False)})
    _log(f"scene generate dall'IA: {gen_ok}/{len(scenes_out)}")
    dur = reel3d.build_from_images(scenes_out, out_mp4)
    return dur


# copione d'esempio (stile del riferimento)
SAMPLE = {
    "scenes": [
        {"prompt": "the character sitting on a huge pile of gold coins and cash, fanning banknotes, city skyline behind",
         "caption": "CRYPTO MONEY\nMETHOD #1", "bills": True, "title": True, "dur": 3.0},
        {"prompt": "the character standing confident in a modern trading office, big screens with green candlestick charts",
         "caption": "MOST PEOPLE", "dur": 1.8},
        {"prompt": "the character looking worried at a big red crashing chart",
         "caption": "PANIC AND SELL", "dur": 1.8},
        {"prompt": "a glowing red 'LIQUIDATION' stamp on a pile of documents on a desk",
         "caption": "AT THE BOTTOM", "character": False, "dur": 1.8},
        {"prompt": "the character walking calmly through a bank vault full of gold",
         "caption": "THE SMART ONES", "dur": 1.8},
        {"prompt": "the character with arms crossed, confident, in front of a night city skyline",
         "caption": "DO THE OPPOSITE", "dur": 1.8},
        {"prompt": "the character pointing at the viewer, friendly, office background",
         "caption": "FOLLOW", "dur": 1.6},
    ],
}


if __name__ == "__main__":
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "reel_ai_sample.mp4")
    key = os.environ.get("GEMINI_KEY", "")   # vuoto = ripiego sull'immagine
    ch = os.path.join(here, "reel3d_assets", "character.jpg")
    d = build_ai_reel(SAMPLE, out, ch, key, log=print)
    print("reel_ai OK", round(d, 1), "s ->", out)
