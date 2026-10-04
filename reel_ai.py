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
import os, tempfile
import genscene
import reel3d


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
