# studio/ — come nascono i reel del magazzino

Qui c'è il "laboratorio" che crea i video in `../reels/`. Il bot del sito VcriptoV legge
**solo** `reels/`: questa cartella non viene mai pubblicata.

Ogni reel = **intro Vadoo** (`intro.mp4`, uguale per tutti) + **immagini del lupo** generate su
Vadoo (modello Grok Imagine, 2 crediti l'una, con `wolf_ref.png` come riferimento) + **voce
inglese gratuita** (Microsoft Edge TTS) + sottotitoli + montaggio. Su Vadoo non si generano video.

## Cosa c'è nel magazzino

- `reels/001.mp4` … `reels/390.mp4`: la serie **How to invest** (crypto + investimenti in generale).
- `reels/010a.mp4`, `020a.mp4`, … `380a.mp4`: 38 video **su VcriptoV**, uno ogni 10 parti
  (in ordine alfabetico `010a` viene subito dopo `010`, quindi escono in mezzo alla serie).
- Nomi **sempre a 3 cifre**: il bot pubblica in ordine alfabetico del nome.
- Con 3 reel a settimana: circa **2 anni e 9 mesi** di pubblicazioni.

## Regola dei 30 reel (anti-ripetizione)

Un'immagine **non può ricomparire** se è già stata usata in uno dei **30 video precedenti**
(in ordine di pubblicazione, promo comprese), né due volte nello stesso video.
La applica `selector.py`: quando l'immagine scelta non è libera, prende la più simile tra quelle
libere della libreria (descrizioni + parole chiave). Controllo: `python selector.py ...` → "problemi: 0".

## Il bot automatico (dal reel 391 in poi)

`autoreel.py` + `.github/workflows/autoreel.yml`: **ogni giorno** GitHub Actions crea UN nuovo reel
(391, 392, …) senza Vadoo e senza Claude. **Ciclo di 14 mesi:** 13 mesi con 1 reel al giorno, poi
l'ultimo mese **2 al giorno** (scorta in più se qualche video non funziona o viene eliminato), poi
ricomincia. Primo ciclo dal 7/10/2026: mesi doppi dal 7/11 al 6/12/2027, dal 7/1 al 6/2/2029, dal
7/3 al 6/4/2030, … (inizio del ciclo: `cycle_start` in `bot/state.json`).
**Video su VcriptoV:** il bot ne crea anche **uno a settimana** (il mercoledì sera; nel mese doppio
due: mercoledì e domenica), `v001.mp4`, `v002.mp4`, … nella release `bot-reels-vcriptov`. Il copione
usa SOLO i fatti veri sul sito scritti in `PROMO_FACTS` (autoreel.py). Il sito pubblica un video su
VcriptoV ogni **sabato** (prima i 38 già pronti `010a`…`380a`, poi quelli del bot).
Per crearne uno subito: *Actions* → *Reel automatico* → *Run workflow* → `vcriptov`.

**Si ferma da solo se il sito non pubblica:** prima di ogni giro automatico il bot legge
`https://www.vcriptov.com/api/reel-stato`. Se la pubblicazione social è **in pausa**, se non esce un reel da
**più di 3 giorni** (qualcosa si è rotto) o se il sito non risponde, quel giorno **non crea video**: la
scorta non cresce a vuoto. Riparte da solo quando il sito ricomincia a pubblicare. (I lanci a mano da
*Run workflow* creano sempre; `controllo` mostra solo lo stato.)

Ogni reel:
1. argomento dalla lista `bot/topics_backlog.txt` (temi senza tempo + storie del passato);
   finita la lista, l'AI propone argomenti nuovi;
2. copione scritto da un'**AI gratuita senza chiavi**: GitHub Models (inclusa in GitHub Actions) o,
   se non risponde, **Pollinations**;
3. immagini dalla libreria `library/` con la regola dei 30 reel;
4. voce + montaggio → `NNN.mp4` caricato nelle **Release** del repository (`bot-reels-1` = reel
   391–890, `bot-reels-2` = 891–1390, …) e aggiorna `bot/state.json`.

**Perché nelle Release e non in `reels/`:** GitHub consiglia di tenere un repository sotto i 5 GB
(i 428 video di `reels/` sono già circa 3 GB). I file delle Release **non contano** in quello spazio
e non hanno un limite totale, quindi il bot può andare avanti per anni. Un altro *ramo* non
servirebbe: i rami condividono lo stesso spazio del repository.
Il sito VcriptoV legge `reels/` **e** le Release, e pubblica tutto in ordine di numero.

**Non servono chiavi:** il bot usa AI gratuite che non chiedono registrazione. Se un giorno
vuoi usare Gemini o Mistral come riserva: *Settings* → *Secrets and variables* → *Actions* →
segreti `GEMINI_API_KEY` / `MISTRAL_API_KEY` (facoltativo).

Per metterlo in pausa:
in `bot/state.json` metti `"paused": true`. Per provarlo subito: *Actions* → *Reel automatico* → *Run workflow*.

## File

| File | A cosa serve |
|---|---|
| `series/plan.json` | **il piano completo**: testi, immagini nuove e riusate di ogni video (è la fonte di verità) |
| `series/plan_*.py`, `build.py` | come sono stati scritti i copioni (`plan_02_13`, `plan_14_25`, `plan_26_37` sono storici: rilanciarli cancellerebbe i riusi) |
| `series/library_prompts.json` | la libreria generica (270 scene del lupo) |
| `selector.py` | regola dei 30 reel e scelta automatica delle immagini |
| `vadoo_web.py` | login al sito Vadoo (codice OTP via email) e generazione immagini |
| `produce.py` | `images A B` / `library` genera le immagini mancanti · `render A B` monta i video |
| `render_reel.py` | montaggio di un singolo reel 1080x1920 |
| `render_when_ready.py` | monta ogni video appena le sue immagini sono pronte |
| `upload.py` | copia i video finiti in `reels/` **in ordine e senza buchi**, commit e push |
| `autoreel.py` | il bot automatico (video nelle Release) |

## Generare altre immagini in futuro (serve Vadoo)

```bash
cd studio && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt playwright
.venv/bin/python vadoo_web.py send <EMAIL-ACCOUNT-VADOO>   # arriva un codice via email
.venv/bin/python vadoo_web.py verify <EMAIL-ACCOUNT-VADOO> <CODICE>
.venv/bin/python produce.py library        # oppure: produce.py images A B
```
`.vadoo_profile/` (sessione di login) e `work/` non vanno mai su git.
Titolo e descrizione dei post li scrive il bot del sito, non vanno messi qui.
