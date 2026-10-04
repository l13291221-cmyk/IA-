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
    provider = script.get("provider") or "pollinations"
    # 1) immagini (IA, con ripiego sul personaggio). Per il lupo uso lo STESSO seme
    #    in tutte le scene-personaggio: cosi' resta coerente tra una scena e l'altra.
    imgs = []
    for i, sc in enumerate(scenes):
        img = os.path.join(wd, f"s{i}.png"); got = None
        if sc.get("prompt"):
            if sc.get("character", True):
                got = genscene.generate_scene(sc["prompt"], character_path, api_key, img,
                                              provider=provider, seed=genscene.WOLF_SEED)
            else:
                got = genscene.generate_object(sc["prompt"], api_key, img,
                                               provider=provider, seed=100 + i)
        imgs.append(got or character_path)
    # 2) voce unica (tutta la narrazione) + durata
    narr = " ".join((sc.get("narration") or sc.get("caption") or "").strip()
                    for sc in scenes).strip()
    mp3 = os.path.join(wd, "voice.mp3"); total = None
    if narr:
        try:
            cartoon._tts(narr, mp3)
            total = len(cartoon._decode(mp3)) / cartoon.SR
        except Exception:
            total = None
    # 3) durate scene proporzionali al testo (cosi' la voce copre il video)
    weights = [max(1, len((sc.get("narration") or sc.get("caption") or ""))) for sc in scenes]
    if total and sum(weights) > 0:
        durs = [max(1.0, total * w / sum(weights)) for w in weights]
    else:
        durs = [float(sc.get("dur", 1.8)) for sc in scenes]
    scenes_out = [{"image": imgs[i], "caption": sc.get("caption"), "dur": durs[i],
                   "bills": sc.get("bills", False), "title": sc.get("title", False)}
                  for i, sc in enumerate(scenes)]
    silent = os.path.join(wd, "silent.mp4")
    reel3d.build_from_images(scenes_out, silent)
    out = os.path.join(out_dir, f"aireel_{int(time.time())}.mp4")
    ff = cartoon._ffmpeg()
    if total:
        # voce presente: re-encode video (H.264 yuv420p + faststart = indice all'inizio,
        # che Instagram pretende) + audio AAC con loudnorm.
        subprocess.run([ff, "-v", "error", "-y", "-i", silent, "-i", mp3,
                        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ac", "2", "-c:a", "aac",
                        "-b:a", "128k", "-movflags", "+faststart", "-shortest", out], check=True)
    else:
        # niente voce: aggiungo comunque una traccia audio SILENZIOSA (un reel senza
        # audio Instagram lo rifiuta) + faststart.
        subprocess.run([ff, "-v", "error", "-y", "-i", silent,
                        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                        "-shortest", out], check=True)
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
