# 🧬 AgentColony — sciame di trading evolutivo con sito di gestione (24/7)

Un'IA che fa trading da sola. Prima **analizza il mercato** per un periodo (default
**30 giorni**), poi parte **un solo Bot** col capitale che imposti (es. **20€**).
Ogni Bot decide **da solo** (fa investimenti diversi dagli altri) e tiene la **sua
tabella** di operazioni (ogni segnale vinto/perso). Quando **raddoppia** (arriva a 40)
si **clona e dà metà** al figlio (Bot 2), e così via; se perde troppo si **autoelimina**
(finisce nel "cimitero", segnato morto). Ciò che i Bot imparano viene **condiviso** con
gli altri tramite una **palestra** evolutiva (il "cervello"). Tutto in **DEMO** (soldi
finti su prezzi reali) o in **SOLDI VERI** su Kraken, da un **sito** con tre pagine,
pensato per girare **24 ore su 24**.

> ⚠️ **Parti in DEMO.** I soldi veri sono spenti finché non inserisci le chiavi,
> accetti i rischi e attivi l'interruttore. **Nessun profitto è garantito: puoi
> perdere tutto.** Leggi la sezione "La verità onesta".

---

## La verità onesta (leggila davvero)

- **Nessuna IA raddoppia i soldi in modo affidabile.** Se esistesse varrebbe
  infinito. I fondi con PhD e miliardi festeggiano per un **10–30% *all'anno***.
- **Le commissioni** (~0,26% a operazione) e lo spread **mangiano** i piccoli conti.
- **"Tempo indeterminato" è vero**: può metterci mesi e **può anche non riuscirci
  mai**. Questo software non promette guadagni: ti dà gli strumenti per **provare in
  sicurezza** e vedere coi tuoi occhi come va, prima di rischiare un euro.

La cosa intelligente da fare: tienilo in **DEMO per settimane**. Se in demo, sui
prezzi reali e **dopo le commissioni**, non guadagna con costanza, non guadagnerà
nemmeno coi soldi veri — e l'avrai scoperto senza perdere niente.

---

## Come è fatto (e perché è sicuro)

```
   1) ANALISI          2) UN BOT           3) SI CLONA           4) SCIAME
   ┌──────────┐       ┌──────────┐        ┌──────────┐        ┌──────────────┐
   │ studia il│       │ Bot 1    │ 20→40  │ Bot 1 20 │        │ Bot1 Bot2 ...│
   │ mercato  │ ────▶ │ parte con│ ─────▶ │ Bot 2 20 │ ────▶  │ ognuno pensa │
   │ ~30 gg   │       │ 20€      │  metà  │ (metà)   │        │ per sé;      │
   └──────────┘       └──────────┘        └──────────┘        │ condividono  │
                             ▲  chi perde muore (cimitero)    │ ciò che      │
        PALESTRA (cervello) ─┘  i geni vincenti si condividono │ imparano     │
                                                               └──────────────┘
```

**Come resta sicuro anche con i soldi veri:** ogni Bot piazza i **propri** ordini reali
su Kraken (≥ ordine minimo). Non c'è leva: il massimo che puoi perdere è il **capitale
iniziale** che decidi tu. In più: **stop-perdita giornaliero automatico** e **tasto di
emergenza**. Le chiavi devono essere **solo-trading** (niente prelievi), quindi il resto
del tuo saldo non è a rischio. Così la tua idea funziona sul serio, entro un limite chiaro.

---

## Il sito (3 pagine)

1. **Panoramica** — come sta andando: barra della **fase di analisi** (con tasto
   "salta"), valore totale, P&L di oggi, **ogni Bot** con stato **vivo/morto**,
   **duplicazioni**, **soldi** e la **tabella delle sue operazioni** (vinto/perso),
   più il **cimitero** dei Bot morti e lo stato della palestra.
2. **Soldi veri** — l'interruttore **DEMO / SOLDI VERI**, i limiti di rischio e il
   **tasto di emergenza** (chiude tutto e vende).
3. **Impostazioni** — dove metti le **chiavi API**, la coppia (BTC/EUR…), e i
   parametri della palestra.

---

## Come si avvia

Serve **Python 3.8+**.

### Prova subito (DEMO, anche senza internet)
```bash
python3 server.py
# apri http://localhost:8000
```
Parte in DEMO. La palestra evolve, il campione opera su un conto finto. Zero rischi.

### Per prezzi reali e soldi veri
```bash
pip install ccxt
python3 server.py
```

---

## Passare ai SOLDI VERI (con attenzione)

1. Su **Kraken**: crea una coppia di **API key** con permesso **solo trading**
   (*Create & Modify Orders* / *Query*), **SENZA** permesso di **prelievo**
   (*Withdraw Funds* deve restare disattivato). Così, anche nel peggiore dei casi,
   nessuno può portarti via i fondi: si può solo comprare/vendere.
2. Nel sito → **Impostazioni**: incolla le chiavi, spunta il consenso ai rischi,
   salva.
3. → **Soldi veri**: nella tabella imposti **capitale iniziale**, **stop-loss** (quanto
   sei disposto a perdere) e il **numero massimo di bot** (lo decidi tu); il **resto lo
   decide l'IA** da sola. Poi premi **SOLDI VERI** e i bot operano in **autonomia**,
   senza chiederti il permesso a ogni operazione.
4. Inizia con **pochi euro** che puoi permetterti di perdere del tutto. Con poco
   capitale tieni **pochi bot** (es. 1–3): parte comunque da 1 Bot e si clona da solo
   crescendo. Ricorda la **fase di analisi**: per iniziare subito, premi "salta analisi".

**Sicurezza delle chiavi**
- Restano **solo sul tuo computer** in `data/config.json` (permessi `600`, e la
  cartella `data/` è nel `.gitignore` → **non finisce mai su GitHub**).
- Meglio ancora su un server: passale come **variabili d'ambiente**
  `KRAKEN_API_KEY` / `KRAKEN_API_SECRET` (hanno priorità e non vengono scritte su file).
- Il sito non mostra mai le chiavi in chiaro (le maschera) e non le manda a nessuno
  tranne che a Kraken.

**Protezioni sui soldi veri**
- **Nessuna leva**: il massimo che puoi perdere è il **capitale iniziale** che decidi
  tu; i bot non spendono più di quello che hanno. Il resto del saldo non è toccato.
- **Chiavi solo-trading**: nessun prelievo possibile, neanche in caso di bug.
- **Stop-loss**: appena la perdita rispetto al capitale iniziale raggiunge l'importo
  che hai impostato, **vende tutto e si ferma da solo**.
- **🛑 Tasto di emergenza**: chiude tutte le posizioni e disattiva il trading reale.

---

## Farlo girare 24/7

Il PC/server deve restare acceso. Lo stato è salvato su disco, quindi un riavvio
riprende da dove era.

- **PC sempre acceso (semplice):** lascia aperto `python3 server.py`.
  Su Linux/Mac per non tenere il terminale aperto: `nohup python3 server.py &`.
- **VPS + systemd (consigliato):** vedi `deploy/agentcolony.service` — riparte da
  solo dopo crash o reboot.
- **Docker:**
  ```bash
  docker build -t agentcolony .
  docker run -d --name agentcolony -p 8000:8000 \
    -v $PWD/data:/app/data \
    -e KRAKEN_API_KEY=... -e KRAKEN_API_SECRET=... \
    -e AGENTCOLONY_TOKEN=una_password \
    agentcolony
  ```

> Se esponi il sito in rete (`--host 0.0.0.0`), proteggilo **sempre** con un token:
> `python3 server.py --host 0.0.0.0 --token una_password` (o `AGENTCOLONY_TOKEN`).

---

## Struttura del progetto

```
server.py                 sito di gestione + API di controllo
agentcolony/
  engine.py               motore 24/7: palestra + sciame + rischio + salvataggio
  swarm.py                sciame operativo su un conto nettato (clona/autoelimina, ≤ tetto)
  colony.py               la palestra evolutiva (riproduzione, morte, selezione, memoria)
  agent.py, genome.py     agenti e "DNA" delle strategie
  strategy.py             logica di decisione condivisa (demo = reale)
  broker.py               LiveBroker (Kraken, soldi veri) · PaperBroker (demo)
  livefeed.py             prezzo reale in tempo reale (con fallback)
  market.py, indicators.py  mercato della palestra e indicatori
  config.py               config e chiavi (salvate in data/, mai su git)
  llm.py                  cervello Claude opzionale (spento di default)
dashboard/app.html        il sito (3 pagine)
run_sim.py                esperimenti da terminale (offline)
Dockerfile, deploy/       per il 24/7
```

Esperimenti veloci da terminale: `python3 run_sim.py --no-real --ticks 4000 --delay 0`

---

## Disclaimer

Software **educativo**. **Non è un consiglio finanziario né di investimento.** Le
prestazioni passate o simulate non predicono i risultati futuri. Il trading di
criptovalute comporta un **rischio elevato, fino alla perdita totale** del capitale.
Usalo con soldi che puoi permetterti di perdere e sotto la tua responsabilità.
