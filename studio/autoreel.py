"""BOT AUTOMATICO DEI REEL — crea UN nuovo reel usando solo la libreria di immagini.

Nessun costo Vadoo, nessun Claude: gira su GitHub Actions (vedi .github/workflows/autoreel.yml).

  1. argomento: il prossimo da bot/topics_backlog.txt (finiti quelli, lo inventa l'AI)
  2. copione in inglese scritto da un'AI GRATUITA SENZA CHIAVI: GitHub Models (inclusa in
     GitHub Actions) o, se non risponde, Pollinations; Gemini/Mistral solo se ci sono le chiavi
  3. immagini: dalla libreria (library/), con la REGOLA DEI 30 REEL: un'immagine già usata in
     uno dei 30 reel precedenti non può essere riusata
  4. voce gratuita (Edge TTS) + sottotitoli + montaggio (render_reel.py)
  5. carica il video NNN.mp4 nelle RELEASE del repository (tag bot-reels-1, bot-reels-2, ...):
     le release non contano nello spazio del repository (limite consigliato 5 GB), quindi il
     bot può andare avanti per anni. Il sito le legge insieme alla cartella reels/.
  6. aggiorna bot/state.json (numero del prossimo reel, immagini usate, argomenti fatti)

Variabili d'ambiente: GITHUB_TOKEN e GITHUB_REPOSITORY (li dà GitHub Actions da solo).
Facoltative: GEMINI_API_KEY / MISTRAL_API_KEY (segreti del repository), usate solo come riserva.
Senza GITHUB_TOKEN (prova sul computer) il video resta in ../reels/NNN.mp4.
"""
import json
import os
import random
import re
import sys
import time

import requests

STUDIO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, STUDIO)
import render_reel  # noqa: E402
import selector as S  # noqa: E402

REELS = os.path.normpath(os.path.join(STUDIO, "..", "reels"))
LIB_DIR = os.path.join(STUDIO, "library")
BOT_DIR = os.path.join(STUDIO, "bot")
STATE = os.path.join(BOT_DIR, "state.json")
BACKLOG = os.path.join(BOT_DIR, "topics_backlog.txt")
INTRO = os.path.join(STUDIO, "intro.mp4")
FIRST_BOT_PART = 391          # primo reel del bot (prima ci sono i 428 della serie in reels/)
# CICLO DI 14 MESI: 13 mesi con 1 reel al giorno, poi l'ultimo mese 2 al giorno (piccola scorta
# in più se qualche video non funziona o viene eliminato), poi ricomincia. Il secondo reel del
# giorno lo fa il giro serale del workflow (EXTRA_RUN=true) solo nel mese "doppio".
CYCLE_MONTHS = 14
DOUBLE_MONTHS = 1
CYCLE_START = "2026-10-07"    # inizio del primo ciclo (si può cambiare in bot/state.json: cycle_start)
# VIDEO SU VCRIPTOV: 1 a settimana (mercoledì), 2 nel mese "doppio" (mercoledì e domenica).
# Il sito li pubblica il SABATO. Nomi v001.mp4, v002.mp4, … nella release bot-reels-vcriptov.
PROMO_DAYS, PROMO_DAYS_DOUBLE = (2,), (2, 6)
PROMO_TAG = "bot-reels-vcriptov"
MAX_SECONDS = 35             # reel al massimo 35 s: se serve la voce va un po' più veloce
IT_TAG = "anteprima-it"       # copie in ITALIANO: solo anteprima per il titolare, il sito NON le pubblica
IT_SERIES = {"HOW TO INVEST IN CRYPTO": "COME INVESTIRE IN CRYPTO", "HOW TO INVEST": "COME INVESTIRE",
             "YOUR CRYPTO ASSISTANT": "IL TUO ASSISTENTE CRYPTO"}
PROMO_CTA = "Start free at VcriptoV dot com. Link in bio. Not financial advice."
PROMO_CTA_IT = "Inizia gratis su VcriptoV punto com. Link in bio. Non è un consiglio finanziario."
BANK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", "bank.json")
PER_RELEASE = 500             # video per release (GitHub ne accetta fino a 1000)
GH_API = "https://api.github.com"

# AI GRATUITE, SENZA CHIAVI: prima quella di GitHub (GitHub Models, inclusa in GitHub Actions
# con il token automatico), poi Pollinations (pubblica, senza registrazione). Gemini e Mistral
# solo se un giorno metti le loro chiavi nei segreti del repository.
GH_MODELS = "https://models.github.ai/inference/chat/completions"
GH_MODELS_LIST = []           # GitHub Models è stato chiuso da GitHub il 30/07/2026 (risponde "OK" e basta)
POLLINATIONS = "https://text.pollinations.ai/openai"
LLM7 = "https://api.llm7.io/v1/chat/completions"     # gratis, senza chiave (provata l'8/10/2026)
LLM7_MODELS = ["GLM-5.3-Flash", "gemma4:31b", "codestral-latest"]
GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]
MISTRAL = "https://api.mistral.ai/v1/chat/completions"

PROMPT = """You write the voice-over script for one short vertical video (Instagram Reels, TikTok,
YouTube Shorts) of an educational series called "{series}". Audience: complete beginners
worldwide. Language: simple, natural spoken English.

Topic of this episode: {topic}

Rules:
- Exactly 5 scenes. Each scene is 1 or 2 short sentences, at most 25 words.
- The whole script is 80 to 110 words.
- Scene 1 is a strong hook that makes people keep watching.
- Educational only: no price predictions, no promises of profit, no "buy this" advice, no hype.
- Only state facts you are completely sure about. Avoid exact numbers, dates and statistics
  unless they are very well known.
- No greetings, no "in this video", no emojis, no hashtags, no lists, no stage directions.
- For every scene add "visual": 3 to 8 simple English keywords for a matching cartoon image
  (for example "gold bars vault", "stock exchange crowd panic", "phone wallet security").

Return ONLY valid JSON, nothing else:
{{"scenes": [{{"say": "...", "visual": "..."}}, ...]}}"""

# Fatti VERI sul sito (gli stessi dei 38 video VcriptoV già controllati sulla homepage):
# l'AI può usare SOLO questi, niente funzioni inventate.
PROMO_FACTS = """- VcriptoV is software that analyzes the real crypto market 24/7 and sends automatic signals.
- Signals arrive on Telegram and on the VcriptoV dashboard. Signals cover cryptocurrencies and gold too.
- Every signal has a coin, an entry, a stop loss and a take profit.
- Every signal has two buttons: invest or don't invest. The user always decides.
- Signals are automatic analyses: not 100 percent accurate, not certainties, not financial advice.
- Your money stays on your own exchange (for example Kraken or Binance). VcriptoV never holds funds and the software can't withdraw them.
- You connect your exchange with API keys you create yourself: read-only for analysis, or trading for orders. Keys and Telegram tokens are stored encrypted. You can revoke keys anytime from your exchange.
- Real trading is off by default: without it everything is paper trading on real prices, with no real money.
- One-tap invest places the order on your own exchange account, with stop loss, take profit and a maximum amount per order that you set.
- You can start for free, no card needed: get an access code by email. Credits are used only for extras like the AI assistant and one-tap invest.
- The AI assistant answers questions about crypto, markets and investing in plain words, in many languages. It is not a financial advisor.
- The dashboard shows the equity curve, profit and loss, liquidity, open positions and trade history.
- Setup takes a few minutes, with a step-by-step guide to connect Telegram. No coding needed.
- The website and the assistant are available in many languages.
- There is a live prices page, daily articles (the VcriptoV journal) and a podcast in English (Spotify, Apple Podcasts, Amazon, and the website).
- The website can be installed on the phone home screen like an app, no app store needed.
- The website shows how past signals performed, wins and losses. Past results don't guarantee future ones.
- Real people answer support questions by email and WhatsApp. VcriptoV never asks for seed phrases or passwords.
- Creators can join the partner program ("Earn with us" page).
- VcriptoV is not affiliated with any exchange. You can cancel auto-renewal anytime from settings.
- The wolf in the videos is the VcriptoV mascot: calm, careful, never gambling."""

PROMO_ANGLES = [
    "what a VcriptoV signal looks like", "your money stays on your own exchange", "start for free",
    "the AI assistant", "gold signals too", "the dashboard", "paper trading before real money",
    "setup in a few minutes", "the podcast", "the daily articles", "honesty: signals are not always right",
    "install it like an app", "a plan before every trade: stop loss and take profit", "one-tap invest",
    "it speaks your language", "live prices", "the partner program for creators", "real people for support",
    "works with the exchange you already use", "who is the wolf", "software doesn't panic",
    "you are always in control", "made for beginners", "how your keys stay safe", "what VcriptoV is not",
    "crypto never sleeps, VcriptoV doesn't either", "the track record of past signals",
    "learning and tools together", "why we built VcriptoV",
]

PROMO_PROMPT = """You write the voice-over for one short vertical video (Instagram Reels, TikTok,
YouTube Shorts) that presents the website VcriptoV. Language: simple, natural spoken English.

Angle of this video: {angle}

Facts about VcriptoV. Use ONLY these facts, never invent features, numbers, prices or results:
{facts}

Rules:
- Exactly 4 scenes. Each scene is 1 or 2 short sentences, at most 22 words.
- The whole script is 45 to 75 words. Say the name "VcriptoV" at least once.
- Scene 1 is a hook. Honest and calm: no promises of profit, no "guaranteed", no hype, no emojis.
- Do not write the final call to action: it is added automatically.
- For every scene add "visual": 3 to 8 simple English keywords for a matching cartoon image.

Return ONLY valid JSON, nothing else:
{{"scenes": [{{"say": "...", "visual": "..."}}, ...]}}"""

TOPIC_PROMPT = """Suggest ONE new topic for an educational short video series about investing
(crypto, stocks, gold, silver, commodities, economy, personal finance, investor psychology).
It must be different from all of these: {done}
Return ONLY the topic as a short lowercase phrase (max 8 words), nothing else."""


# ------------------------------------------------------------------ AI
def _chat(url, model, prompt, temperature, headers=None, extra=None):
    body = {"model": model, "temperature": temperature, "messages": [{"role": "user", "content": prompt}]}
    body.update(extra or {})
    r = requests.post(url, timeout=120, headers=headers or {}, json=body, allow_redirects=False)
    if 300 <= r.status_code < 400:
        return None, f"{r.status_code} spostato a {r.headers.get('Location')}"
    if r.status_code == 200:
        try:
            text = r.json()["choices"][0]["message"].get("content") or ""
        except (ValueError, KeyError, IndexError, TypeError):
            return None, f"200 ma risposta non valida: {r.headers.get('content-type')} {r.text[:200]!r}"
        if text.strip():
            return text, None
        return None, "risposta vuota"
    return None, f"{r.status_code} {r.text[:200]}"


def ask_ai(prompt, temperature=0.7):
    errors = []
    tok = os.environ.get("GITHUB_TOKEN", "").strip()
    if tok:                                           # GitHub Models: gratis dentro GitHub Actions
        for m in GH_MODELS_LIST:
            try:
                text, err = _chat(GH_MODELS, m, prompt, temperature,
                                  {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
                if text:
                    print(f"copione scritto da GitHub Models ({m})", flush=True)
                    return text
                errors.append(f"github {m}: {err}")
            except Exception as exc:
                errors.append(f"github {m}: {exc}")
    ltok = os.environ.get("LLM7_API_KEY", "").strip()   # facoltativo: con la chiave gratuita più richieste
    for m in LLM7_MODELS:                             # llm7.io: gratis, senza chiave
        try:
            text, err = _chat(LLM7, m, prompt, temperature, {"Authorization": f"Bearer {ltok}"} if ltok else None)
            if text:
                print(f"copione scritto da llm7.io ({m})", flush=True)
                return text
            errors.append(f"llm7 {m}: {err}")
        except Exception as exc:
            errors.append(f"llm7 {m}: {exc}")
    for attempt in range(3):                          # Pollinations: gratis, senza chiave
        try:
            # seed casuale: senza, Pollinations ridà la risposta in cache per lo stesso testo
            text, err = _chat(POLLINATIONS, "openai", prompt, temperature,
                              extra={"seed": random.randint(1, 2_000_000_000), "private": True})
            if text:
                print("copione scritto da Pollinations" + (f" (prima: {' | '.join(errors)[:300]})" if errors else ""),
                      flush=True)
                return text
            errors.append(f"pollinations: {err}")
        except Exception as exc:
            errors.append(f"pollinations: {exc}")
        time.sleep(20 * (attempt + 1))                # il livello gratuito vuole pause tra le richieste
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        for m in GEMINI_MODELS:
            try:
                r = requests.post(GEMINI.format(m=m), params={"key": key}, timeout=120, json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": temperature}})
                if r.status_code == 200:
                    parts = r.json()["candidates"][0]["content"]["parts"]
                    return "".join(p.get("text", "") for p in parts)
                errors.append(f"gemini {m}: {r.status_code} {r.text[:200]}")
            except Exception as exc:
                errors.append(f"gemini {m}: {exc}")
    key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if key:
        try:
            r = requests.post(MISTRAL, timeout=120, headers={"Authorization": f"Bearer {key}"}, json={
                "model": os.environ.get("MISTRAL_MODEL", "mistral-small-latest"), "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]})
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            errors.append(f"mistral: {r.status_code} {r.text[:200]}")
        except Exception as exc:
            errors.append(f"mistral: {exc}")
    raise RuntimeError("nessuna AI ha risposto: " + " | ".join(errors))


def parse_json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("risposta senza JSON")
    return json.loads(m.group(0))


def valid(script):
    sc = script.get("scenes") or []
    if not (4 <= len(sc) <= 6):
        return False
    words = 0
    for s in sc:
        say = str(s.get("say", "")).strip()
        if not say or len(say) > 220 or re.search(r"[#*\[\]]|https?://", say):
            return False
        words += len(say.split())
    return 55 <= words <= 140


def valid_promo(script):
    sc = script.get("scenes") or []
    if len(sc) != 4 or not all(isinstance(x, dict) and (x.get("say") or "").strip() for x in sc):
        return False
    text = " ".join(x["say"] for x in sc)
    words = len(text.split())
    bad = re.search(r"guarantee|risk-free|get rich|100 ?%|\$\d|\d+ ?percent (profit|return)", text, re.I)
    return 35 <= words <= 90 and "vcriptov" in text.lower() and not bad


def bank_entry(kind, name):
    """Copione SCRITTO IN ANTICIPO (inglese + italiano) da studio/bot/bank.json, se c'è: così il
    bot non dipende dalle AI gratuite (che a volte chiudono o si rompono)."""
    try:
        return (json.load(open(BANK)).get(kind) or {}).get((name or "").lower().strip())
    except (OSError, ValueError):
        return None


def it_from_bank(spec, scenes, nxt=None):
    """Le frasi italiane del video se il copione viene dalla banca, se no None."""
    body = [sc.get("it") for sc in scenes[:-1]]          # l'ultima scena è la chiusura aggiunta dal bot
    if not all(body):
        return None
    m = re.match(r"How to invest( in crypto)?\. Part (\d+)\.", spec["scenes"][0]["say"])
    intro = f"Come investire{' in crypto' if m.group(1) else ''}. Parte {m.group(2)}." if m else "Ecco VcriptoV."
    if nxt is None:
        cta = PROMO_CTA_IT
    else:
        e = bank_entry("series", nxt) or {}
        cta = (f"Segui per la parte {spec['part'] + 1}: {e['topic_it']}. Non è un consiglio finanziario."
               if e.get("topic_it") else f"Segui per la parte {spec['part'] + 1}. Non è un consiglio finanziario.")
    return [intro] + body + [cta]


def write_promo(angle):
    e = bank_entry("promo", angle)
    if e and valid_promo(e):
        print("copione VcriptoV dalla banca (scritto in anticipo)", flush=True)
        return [dict(x) for x in e["scenes"]]
    last = None
    for attempt in range(4):
        try:
            data = parse_json(ask_ai(PROMO_PROMPT.format(angle=angle, facts=PROMO_FACTS)))
            if valid_promo(data):
                return data["scenes"]
            last = "copione non valido"
        except Exception as exc:
            last = str(exc)
        time.sleep(3)
    raise RuntimeError(f"copione VcriptoV non riuscito: {last}")


def write_script(topic, series):
    e = bank_entry("series", topic)
    if e and valid(e):
        print("copione dalla banca (scritto in anticipo)", flush=True)
        return [dict(x) for x in e["scenes"]]
    last = None
    for attempt in range(4):
        try:
            data = parse_json(ask_ai(PROMPT.format(topic=topic, series=series)))
            if valid(data):
                return data["scenes"]
            last = "copione non valido"
        except Exception as exc:
            last = str(exc)
        time.sleep(3)
    raise RuntimeError(f"copione non riuscito: {last}")


# ------------------------------------------------------------------ stato e argomenti
def load_state():
    return json.load(open(STATE))


def months_since(start, day):
    return (day.year - start.year) * 12 + (day.month - start.month) - (1 if day.day < start.day else 0)


def double_month(day, start):
    """True se `day` cade nell'ultimo mese del ciclo (quello con 2 reel al giorno)."""
    return months_since(start, day) % CYCLE_MONTHS >= CYCLE_MONTHS - DOUBLE_MONTHS


def backlog():
    out = []
    if os.path.exists(BACKLOG):
        for line in open(BACKLOG):
            line = line.strip()
            if line and "|" in line:
                cat, topic = line.split("|", 1)
                out.append((cat.strip().upper(), topic.strip()))
    return out


def next_topics(state, k=2):
    done = set(t.lower() for t in state.get("topics_done", []))
    todo = [x for x in backlog() if x[1].lower() not in done]
    while len(todo) < k:      # backlog finito: l'AI inventa un argomento nuovo
        recent = ", ".join(list(done)[-150:] + [t for _, t in todo])
        t = ask_ai(TOPIC_PROMPT.format(done=recent), temperature=1.0).strip().strip('."').lower()[:80]
        crypto = any(w in t for w in ("crypto", "bitcoin", "ethereum", "token", "coin", "blockchain", "defi", "wallet"))
        if t and t not in done:
            todo.append(("C" if crypto else "G", t))
            with open(BACKLOG, "a") as f:
                f.write(f"\n{'C' if crypto else 'G'}|{t}")
    return todo[:k]


# ------------------------------------------------------------------ immagini
def library():
    index = json.load(open(os.path.join(LIB_DIR, "index.json")))
    lib = S.Library()
    for k, d in index.items():
        if os.path.exists(os.path.join(LIB_DIR, f"{k}.jpg")):
            lib.add(k, d, 0)
    lib.build_index()
    return lib


def recent_keys(state, n=S.WINDOW):
    """Gli ultimi n video creati (serie e VcriptoV), in ordine: servono alla regola dei 30."""
    order = state.get("order")
    if order is None:      # stato vecchio: solo numeri di parte
        order = sorted((k for k in state.get("usage", {}) if k.isdigit()), key=int)
    return order[-n:]


def remember(state, key, used, topic):
    order = (state.get("order") or recent_keys(state, 10 ** 6)) + [key]
    state["order"] = order[-(S.WINDOW + 10):]
    state.setdefault("usage", {})[key] = used
    state["usage"] = {k: v for k, v in state["usage"].items() if k in state["order"]}
    state.setdefault("made", []).append({"part": key, "topic": topic, "date": time.strftime("%Y-%m-%d")})


def choose_images(scenes, key, state, lib, promo=False):
    window = set()
    for k in recent_keys(state):
        window |= set(state.get("usage", {}).get(k, []))
    bonus = (lambda k: 0.12 if k.startswith("p") else 0) if promo else None   # immagini del sito/app
    used, out = set(), []
    for i, sc in enumerate(scenes):
        cta = sc["say"].startswith("Follow for part") or sc["say"].startswith("Start free")
        allowed = [x for x in lib.desc if x not in window and x not in used]
        if cta:
            allowed = [x for x in allowed if S.is_pointing(lib.desc[x])] or allowed
        if not allowed:                          # libreria troppo piccola: allento la regola
            allowed = [x for x in lib.desc if x not in used]
        query = sc["say"] + (" " + sc.get("visual", "")) * 3
        best, _ = lib.similar(query, allowed, bonus)
        used.add(best)
        out.append(f"{best}.jpg" + (":flip" if random.random() < 0.35 else ""))
    return out, sorted(used)


# ------------------------------------------------------------------ release GitHub
def _gh(method, url, **kw):
    hdr = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
           "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    hdr.update(kw.pop("headers", {}))
    timeout = kw.pop("timeout", 60)
    fatal = kw.pop("fatal", True)
    for attempt in range(4):
        try:
            r = requests.request(method, url, headers=hdr, timeout=timeout, **kw)
        except requests.RequestException as e:
            print("GitHub non risponde:", e, flush=True)
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code < 500:
            return r
        time.sleep(5 * (attempt + 1))
    if not fatal:
        return None
    raise SystemExit(f"GitHub {method} {url}: errore del server")


def release_tag(part):
    return f"bot-reels-{(part - FIRST_BOT_PART) // PER_RELEASE + 1}"


def upload_release(path, part, tag=None):
    """Carica il video nella release giusta (la crea se manca). Se il video c'è già
    (giro precedente interrotto prima di salvare lo stato) lo sostituisce."""
    repo = os.environ["GITHUB_REPOSITORY"]
    tag, name = tag or release_tag(part), os.path.basename(path)
    r = _gh("GET", f"{GH_API}/repos/{repo}/releases/tags/{tag}")
    if r.status_code == 404:
        if tag.startswith(IT_TAG):
            title = "Anteprima in italiano (non pubblicata)"
        elif tag == PROMO_TAG:
            title = "Video su VcriptoV (bot)"
        else:
            first = FIRST_BOT_PART + (part - FIRST_BOT_PART) // PER_RELEASE * PER_RELEASE
            title = f"Reel automatici {first:03d}-{first + PER_RELEASE - 1:03d}"
        r = _gh("POST", f"{GH_API}/repos/{repo}/releases", json={
            "tag_name": tag, "name": title,
            "body": ("Copie in italiano dei reel, solo da guardare nell'anteprima del sito. Non vengono "
                     "pubblicate." if tag.startswith(IT_TAG) else
                     "Video creati ogni giorno dal bot (studio/autoreel.py). Il sito VcriptoV li "
                     "pubblica in ordine dopo quelli della cartella reels/. Non cancellare."),
            "make_latest": "false"})
    if r.status_code not in (200, 201):
        raise SystemExit(f"release {tag}: GitHub ha risposto {r.status_code} {r.text[:200]}")
    rel = r.json()
    page = 1
    while True:
        a = _gh("GET", f"{GH_API}/repos/{repo}/releases/{rel['id']}/assets",
                params={"per_page": 100, "page": page}).json()
        for asset in a:
            if asset.get("name") == name:
                d = _gh("DELETE", f"{GH_API}/repos/{repo}/releases/assets/{asset['id']}", fatal=False)
                if d is None or d.status_code not in (204, 404):
                    # GitHub non lo cancella: lo rinomino con un nome che il sito ignora
                    # (non .mp4), così il video nuovo può prendere il suo posto
                    old = f"old-{name[:-4]}-{int(time.time())}.bak"
                    _gh("PATCH", f"{GH_API}/repos/{repo}/releases/assets/{asset['id']}", json={"name": old})
                    print(f"vecchio {name} non cancellabile ora: rinominato {old}", flush=True)
        if len(a) < 100:
            break
        page += 1
    with open(path, "rb") as f:
        data = f.read()
    up = _gh("POST", f"https://uploads.github.com/repos/{repo}/releases/{rel['id']}/assets",
             params={"name": name}, data=data, timeout=300,
             headers={"Content-Type": "video/mp4"})
    if up.status_code != 201:
        raise SystemExit(f"caricamento {name}: GitHub ha risposto {up.status_code} {up.text[:200]}")
    return up.json()["browser_download_url"]


# ------------------------------------------------------------------ main
def render_and_store(spec, key, tag=None):
    os.makedirs(os.path.join(STUDIO, "work"), exist_ok=True)
    sp = os.path.join(STUDIO, "work", f"auto_{key}.json")
    json.dump(spec, open(sp, "w"), indent=1)
    online = bool(os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPOSITORY"))
    out = os.path.join(STUDIO, "work" if online else REELS, f"{key}.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    render_reel.build(sp, out)
    return upload_release(out, spec["part"], tag) if online else out


IT_PROMPT = """Translate these voice-over lines of a short crypto video from English to natural,
spoken Italian (as an Italian creator would say them on Instagram, informal "tu"). Same meaning,
about the same length, no additions. Keep "crypto" and the English finance words Italians use
(trader, long, short, stop loss, exchange, wallet, staking, futures, ETF, DCA, stablecoin...).
Write numbers as digits ("21 milioni", "99%", "50.000 dollari"), never "$". "Part N" -> "Parte N",
"Follow for part N: ..." -> "Segui per la parte N: ...", "Not financial advice" -> "Non è un
consiglio finanziario", "VcriptoV dot com" -> "VcriptoV punto com".
Reply with ONLY a JSON array of {n} strings, one per line, same order.

{lines}"""


def translate_it(lines):
    """Le frasi del video in italiano (lista della stessa lunghezza) o None."""
    for _ in range(2):
        try:
            text = ask_ai(IT_PROMPT.format(n=len(lines), lines=json.dumps(lines, ensure_ascii=False)), 0.3)
            m = re.search(r"\[.*\]", text or "", re.S)
            out = json.loads(m.group(0)) if m else None
            if isinstance(out, list) and len(out) == len(lines) and all(isinstance(x, str) and x.strip() for x in out):
                return [x.strip() for x in out]
        except Exception as exc:
            print("traduzione:", exc, flush=True)
    return None


def it_tag():
    """La release delle copie italiane con posto libero (GitHub: max 1000 file per release)."""
    repo = os.environ["GITHUB_REPOSITORY"]
    n = 1
    while True:
        tag = IT_TAG if n == 1 else f"{IT_TAG}-{n}"
        r = _gh("GET", f"{GH_API}/repos/{repo}/releases/tags/{tag}", fatal=False)
        if r is None or r.status_code != 200:
            return tag
        if len(_gh("GET", f"{GH_API}/repos/{repo}/releases/{r.json()['id']}/assets",
                   params={"per_page": 100, "page": 10}).json()) < 50:      # meno di ~950 file
            return tag
        n += 1


def make_italian(spec, key, it_lines=None):
    """COPIA IN ITALIANO del video appena fatto (stesse immagini, voce italiana): va solo nella
    release dell'anteprima, il sito NON la pubblica. Se qualcosa va storto, il video inglese
    resta comunque buono."""
    try:
        lines = [sc["say"] for sc in spec["scenes"]]
        it = it_lines if it_lines and len(it_lines) == len(lines) else translate_it(lines)
        if not it:
            print("copia italiana saltata: traduzione non riuscita", flush=True)
            return
        it_spec = dict(spec, series=IT_SERIES.get(spec["series"], spec["series"]), part_label="PARTE",
                       voice="it-IT-DiegoNeural", rate="+5%",
                       scenes=[dict({"say": t, "img": sc["img"]},
                                    **{f: sc[f] for f in ("caption", "after") if f in sc},
                                    **({"show": {"VcriptoV punto com": "VCRIPTOV.COM"}} if "VcriptoV punto com" in t else {}))
                               for t, sc in zip(it, spec["scenes"])])
        os.makedirs(os.path.join(BOT_DIR, "scripts"), exist_ok=True)
        json.dump({"en": spec["scenes"], "it": it}, open(os.path.join(BOT_DIR, "scripts", f"{key}.json"), "w"),
                  indent=1, ensure_ascii=False)
        if not (os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPOSITORY")):
            return
        work = os.path.join(STUDIO, "work", "it")
        os.makedirs(work, exist_ok=True)
        sp = os.path.join(work, f"{key}.json")
        json.dump(it_spec, open(sp, "w"), indent=1, ensure_ascii=False)
        out = os.path.join(work, f"{key}.mp4")
        render_reel.build(sp, out)
        print("copia italiana:", upload_release(out, spec["part"], it_tag()), flush=True)
    except BaseException as exc:          # anche SystemExit dei caricamenti: mai fermare il bot
        print(f"copia italiana non riuscita: {exc}", flush=True)


def hook_first(spec, it_lines=None):
    """NUOVO INIZIO (come tutti i video della serie): il titolo resta scritto in alto ma non si
    dice a voce; il lupo dice SUBITO la prima frase, con i sottotitoli e le labbra a tempo. Se la
    frase dura più dell'intro, dopo si vede la sua immagine. Toglie il titolo anche dall'italiano."""
    first = spec["scenes"][1]
    spec["scenes"] = [dict(first, img="intro", caption=True, after=first["img"])] + spec["scenes"][2:]
    return spec, (it_lines[1:] if it_lines else it_lines)


def save_state(state, last):
    json.dump(state, open(STATE, "w"), indent=1, ensure_ascii=False)
    with open(os.path.join(BOT_DIR, "last.txt"), "w") as f:
        f.write(last)


def make_series(state, lib):
    part = int(state["next_part"])
    (cat, topic), nxt = next_topics(state, 2)
    series = "HOW TO INVEST IN CRYPTO" if cat == "C" else "HOW TO INVEST"
    print(f"reel {part:03d}: {topic} ({series})", flush=True)
    scenes = write_script(topic, series)
    scenes.append({"say": f"Follow for part {part + 1}: {nxt[1]}. Not financial advice.",
                   "visual": "wolf points at the viewer"})
    key = f"{part:03d}"
    imgs, used = choose_images(scenes, key, state, lib)
    spec = {"part": part, "series": series, "voice": "en-US-AndrewNeural", "rate": "+6%", "intro": INTRO,
            "img_dir": LIB_DIR, "max_seconds": MAX_SECONDS,
            "scenes": [{"say": ("How to invest in crypto. " if cat == "C" else "How to invest. ") + f"Part {part}.",
                        "img": "intro"}] + [{"say": s["say"], "img": im} for s, im in zip(scenes, imgs)]}
    spec, it_lines = hook_first(spec, it_from_bank(spec, scenes, nxt[1]))
    out = render_and_store(spec, key)
    make_italian(spec, key, it_lines)
    state["next_part"] = part + 1
    remember(state, str(part), used, topic)
    state.setdefault("topics_done", []).append(topic)
    save_state(state, f"{key} - {topic}")
    print("OK", out)


def make_promo(state, lib):
    n = int(state.get("next_promo", 1))
    done = state.setdefault("promo_angles_done", [])
    todo = [a for a in PROMO_ANGLES if a not in done] or PROMO_ANGLES       # finiti: si ricomincia
    if len(todo) == len(PROMO_ANGLES):
        done.clear()
    angle = todo[0]
    key = f"v{n:03d}"
    print(f"video VcriptoV {key}: {angle}", flush=True)
    scenes = write_promo(angle)
    scenes.append({"say": PROMO_CTA, "visual": "wolf points at the viewer smartphone"})
    imgs, used = choose_images(scenes, key, state, lib, promo=True)
    spec = {"part": n, "badge": "VCRIPTOV", "series": "YOUR CRYPTO ASSISTANT", "voice": "en-US-AndrewNeural",
            "rate": "+6%", "intro": INTRO, "img_dir": LIB_DIR, "max_seconds": MAX_SECONDS,
            "scenes": [{"say": "Meet VcriptoV.", "img": "intro"}]
                      + [{"say": s["say"], "img": im} for s, im in zip(scenes, imgs)]}
    spec, it_lines = hook_first(spec, it_from_bank(spec, scenes))
    out = render_and_store(spec, key, PROMO_TAG)
    make_italian(spec, key, it_lines)
    state["next_promo"] = n + 1
    done.append(angle)
    remember(state, key, used, f"VcriptoV: {angle}")
    save_state(state, f"{key} - VcriptoV: {angle}")
    print("OK", out)


def remake(state, lib, key):
    """RIFA' un video del bot già fatto (es. dopo un miglioramento del montaggio), con lo STESSO
    argomento: nuovo copione, immagini, voce, copia italiana. Sostituisce il file nella release.
    Non tocca la numerazione né l'elenco degli argomenti."""
    made = {str(m.get("part")): m.get("topic") for m in state.get("made", []) if isinstance(m, dict)}
    topic = made.get(key)
    if not topic:
        print(f"{key}: non trovo l'argomento nello stato, salto", flush=True)
        return
    if key.startswith("v"):
        angle = topic.split(":", 1)[1].strip() if ":" in topic else topic
        n = int(key[1:])
        print(f"rifaccio {key}: {angle}", flush=True)
        scenes = write_promo(angle)
        scenes.append({"say": PROMO_CTA, "visual": "wolf points at the viewer smartphone"})
        imgs, used = choose_images(scenes, key, state, lib, promo=True)
        spec = {"part": n, "badge": "VCRIPTOV", "series": "YOUR CRYPTO ASSISTANT", "voice": "en-US-AndrewNeural",
                "rate": "+6%", "intro": INTRO, "img_dir": LIB_DIR, "max_seconds": MAX_SECONDS,
                "scenes": [{"say": "Meet VcriptoV.", "img": "intro"}]
                          + [{"say": s["say"], "img": im} for s, im in zip(scenes, imgs)]}
        tag, it_lines = PROMO_TAG, it_from_bank(spec, scenes)
    else:
        part = int(key)
        cat = next((c for c, t in backlog() if t.lower() == topic.lower()), "C")
        nxt = made.get(str(part + 1)) or next_topics(state, 1)[0][1]
        series = "HOW TO INVEST IN CRYPTO" if cat == "C" else "HOW TO INVEST"
        print(f"rifaccio {key}: {topic} (poi: {nxt})", flush=True)
        scenes = write_script(topic, series)
        scenes.append({"say": f"Follow for part {part + 1}: {nxt}. Not financial advice.",
                       "visual": "wolf points at the viewer"})
        imgs, used = choose_images(scenes, key, state, lib)
        spec = {"part": part, "series": series, "voice": "en-US-AndrewNeural", "rate": "+6%", "intro": INTRO,
                "img_dir": LIB_DIR, "max_seconds": MAX_SECONDS,
                "scenes": [{"say": ("How to invest in crypto. " if cat == "C" else "How to invest. ") + f"Part {part}.",
                            "img": "intro"}] + [{"say": s["say"], "img": im} for s, im in zip(scenes, imgs)]}
        tag, it_lines = None, it_from_bank(spec, scenes, nxt)
    spec, it_lines = hook_first(spec, it_lines)
    key = f"{int(key):03d}" if key.isdigit() else key
    out = render_and_store(spec, key, tag)
    make_italian(spec, key, it_lines)
    state.setdefault("usage", {})[key.lstrip("0") if key.isdigit() else key] = used
    save_state(state, f"{key} rifatto - {topic}")
    print("OK", out)


SITE_STATUS = os.environ.get("SITE_STATUS_URL", "https://www.vcriptov.com/api/reel-stato")
STALE_DAYS = 3        # se il sito non pubblica reel da più di 3 giorni, il bot si ferma


def site_publishing():
    """Il sito sta pubblicando? (True, motivo) / (False, motivo). Se la pubblicazione è in
    pausa, ferma da giorni (qualcosa rotto) o il sito non risponde, il bot NON crea video:
    così la scorta non cresce a vuoto. Riparte da solo quando il sito ripubblica."""
    try:
        r = requests.get(SITE_STATUS, timeout=30)
        st = r.json() if r.status_code == 200 else None
    except Exception as exc:
        return False, f"il sito non risponde ({type(exc).__name__})"
    if not st:
        return False, f"il sito ha risposto {r.status_code}"
    if st.get("paused"):
        return False, "pubblicazione social in PAUSA sul sito"
    last = int(st.get("last_reel_at") or 0)
    if not last:
        return False, "il sito non ha ancora pubblicato nessun reel"
    days = (int(st.get("now") or time.time()) - last) / 86400
    if days > STALE_DAYS:
        return False, f"nessun reel pubblicato da {days:.0f} giorni (pubblicazione ferma)"
    return True, f"il sito pubblica (ultimo reel {days * 24:.0f} ore fa, {st.get('published')} pubblicati)"


def main():
    if not (os.path.exists(os.path.join(LIB_DIR, "index.json")) and os.path.exists(STATE)):
        print("Bot fermo: manca la libreria (studio/library/index.json) o lo stato (studio/bot/state.json).")
        return
    state = load_state()
    if state.get("paused"):
        print("Bot in pausa (state.json: paused = true).")
        return
    import datetime as _dt
    start = _dt.date.fromisoformat(state.get("cycle_start") or CYCLE_START)
    today = _dt.date.today()
    double = double_month(today, start)
    kind = os.environ.get("KIND", "").lower()           # lancio a mano: "serie" o "vcriptov"
    extra = os.environ.get("EXTRA_RUN", "").lower() == "true"
    if kind == "controllo":
        print("Controllo:", site_publishing()[1])
        return
    if kind == "prova-ai":                              # le AI gratuite rispondono?
        try:
            print("Risposta:", ask_ai('Reply only with the word OK.', 0)[:80])
        except Exception as exc:
            print("Nessuna AI:", exc)
        return
    if not kind:                                        # giri automatici: solo se il sito pubblica
        ok, why = site_publishing()
        print(("Avanti: " if ok else "Oggi niente video: ") + why, flush=True)
        if not ok:
            return
    lib = library()
    if kind == "rifai":
        for key in [k.strip().lower() for k in os.environ.get("KEYS", "").split(",") if k.strip()]:
            remake(state, lib, str(int(key)) if key.isdigit() else key)
        return
    if kind == "vcriptov":
        make_promo(state, lib)
    elif kind == "serie" or not extra:
        make_series(state, lib)                           # mattina: il reel del giorno
    else:                                                 # sera: VcriptoV e/o secondo reel
        did = False
        if today.weekday() in (PROMO_DAYS_DOUBLE if double else PROMO_DAYS):
            make_promo(state, lib)
            did = True
        if double:
            make_series(state, lib)
            did = True
        if not did:
            print(f"Giro della sera: oggi niente (mese {months_since(start, today) % CYCLE_MONTHS + 1} "
                  f"del ciclo di {CYCLE_MONTHS}; video VcriptoV il mercoledì).")


if __name__ == "__main__":
    main()
