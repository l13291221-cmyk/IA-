# 🧬 AgentColony — sciame di trading evolutivo con sito di gestione (24/7)

Un'IA che fa trading da sola. Una **palestra** evolutiva (soldi finti) fa nascere,
morire e migliorare di continuo tante strategie; la **strategia campione** che
sopravvive opera su **un** conto, che tu tieni in **DEMO** (soldi finti su prezzi
reali) oppure in **SOLDI VERI** su Kraken con le tue chiavi. Tutto si gestisce da un
**sito** con tre pagine, ed è pensato per girare **24 ore su 24**.

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
        PALESTRA (demo, veloce)                 BANCO OPERATIVO (tempo reale)
   ┌───────────────────────────┐            ┌────────────────────────────────┐
   │ sciame di agenti che       │  campione │ la strategia campione opera su  │
   │ nascono / muoiono /        │ ─────────▶│ UN conto, con limiti di rischio │
   │ si clonano ed evolvono     │           │  • DEMO  → soldi finti          │
   │ (soldi FINTI: può sbagliare│           │  • LIVE  → ordini veri Kraken   │
   │  e morire senza danni)     │           │  + stop-perdita + tasto STOP    │
   └───────────────────────────┘            └────────────────────────────────┘
```

**Scelta di sicurezza chiave:** lo sciame che si autoelimina gira **solo in demo**
(così può "morire" gratis). Sui **soldi veri** opera **una sola** strategia, quella
campione, con: limite di capitale, limite per-ordine, **stop-perdita giornaliero
automatico** e **tasto di emergenza**. Far perdere soldi veri a decine di bot sarebbe
da irresponsabili — così invece è sensato.

---

## Il sito (3 pagine)

1. **Panoramica** — come sta andando: valore del conto, posizione aperta/chiusa, P&L
   di oggi, grafico, ultime operazioni, diario, stato della palestra.
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
3. → **Soldi veri**: imposta i **limiti** (capitale massimo, importo per ordine,
   stop-perdita giornaliero) e premi **SOLDI VERI**.
4. Inizia con **pochi euro** che puoi permetterti di perdere del tutto.

**Sicurezza delle chiavi**
- Restano **solo sul tuo computer** in `data/config.json` (permessi `600`, e la
  cartella `data/` è nel `.gitignore` → **non finisce mai su GitHub**).
- Meglio ancora su un server: passale come **variabili d'ambiente**
  `KRAKEN_API_KEY` / `KRAKEN_API_SECRET` (hanno priorità e non vengono scritte su file).
- Il sito non mostra mai le chiavi in chiaro (le maschera) e non le manda a nessuno
  tranne che a Kraken.

**Protezioni sui soldi veri**
- **Limite capitale** e **limite per-ordine**: il bot non può impiegare più di così.
- **Stop-perdita giornaliero**: se in un giorno perde oltre la soglia, **vende e si
  ferma da solo**.
- **🛑 Tasto di emergenza**: chiude la posizione e disattiva il trading reale subito.

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
  engine.py               motore 24/7: palestra + banco + rischio + salvataggio
  colony.py               lo sciame: riproduzione, morte, selezione, memoria
  agent.py, genome.py     agenti e "DNA" delle strategie
  strategy.py             logica di decisione condivisa (demo = reale)
  broker.py               PaperBroker (demo) · LiveBroker (Kraken, soldi veri)
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
