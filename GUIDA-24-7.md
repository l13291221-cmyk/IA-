# Guida — Far girare AgentColony 24 ore su 24

Per girare **24/7** serve un computer **sempre acceso e connesso a internet**. Hai tre
strade, dalla più semplice alla più solida. Per il vero 24/7 la scelta giusta è un
**VPS** (un piccolo computer nel cloud, ~4–6€/mese).

> ⚠️ **Prima di iniziare**
> - Parti **sempre in DEMO** e provalo per settimane prima dei soldi veri.
> - Per i soldi veri: chiavi Kraken con permesso **solo trading**, **NIENTE prelievi**.
> - Le chiavi restano sul server, **mai su GitHub** (la cartella `data/` è già ignorata).

---

## Quale strada scegliere

| Strada | Difficoltà | Sempre acceso? | Costo |
|---|---|---|---|
| **A) Il tuo PC acceso** | facilissima | solo se non spegni il PC | 0 € |
| **B) VPS + systemd** ✅ consigliata | media | sì, davvero 24/7 | ~4–6 €/mese |
| **C) Docker** | media (se lo conosci) | sì | dipende |

---

## Opzione A — Il tuo PC sempre acceso

Va bene per **provare**. Il limite: se spegni il PC o cade la linea, si ferma.

1. Installa **Python 3** da python.org.
2. Scarica il progetto (bottone verde *Code → Download ZIP* su GitHub, oppure `git clone`).
3. Apri il terminale nella cartella del progetto e (per i prezzi reali) installa ccxt:
   ```bash
   pip install ccxt
   ```
4. Avvia:
   ```bash
   python3 server.py
   ```
   Per lasciarlo attivo anche chiudendo il terminale (Mac/Linux):
   ```bash
   nohup python3 server.py &
   ```
5. Apri **http://localhost:8000**.

---

## Opzione B — Un VPS (consigliata per il vero 24/7)

Un **VPS** è un piccolo computer nel cloud, sempre acceso. Provider economici: Hetzner,
Contabo, DigitalOcean, OVH… Prendi il taglio più piccolo (**1 CPU / 1–2 GB RAM**: basta
e avanza) con **Ubuntu 22.04 o 24.04**.

### 1) Connettiti al server
Dal tuo PC (terminale su Mac/Linux, oppure *Windows Terminal* / PuTTY su Windows):
```bash
ssh root@INDIRIZZO_IP_DEL_SERVER
```

### 2) Installa gli strumenti
```bash
apt update && apt install -y python3 python3-pip git
pip3 install ccxt
```

### 3) Scarica il progetto
```bash
git clone https://github.com/l13291221-cmyk/IA-.git
cd IA-
git checkout claude/ai-site-generator-realtime-qgr9i1
```
*(usa `main` se hai già unito le modifiche al ramo principale).*

### 4) (Soldi veri) Metti le chiavi in un file protetto
```bash
nano /etc/agentcolony.env
```
Scrivi dentro (una password lunga a piacere per il token):
```
KRAKEN_API_KEY=la_tua_key
KRAKEN_API_SECRET=il_tuo_secret
AGENTCOLONY_TOKEN=una_password_lunga_a_caso
```
Salva con **Ctrl+O**, Invio, **Ctrl+X**. Poi blinda il file:
```bash
chmod 600 /etc/agentcolony.env
```
> Le chiavi via variabili d'ambiente hanno la priorità e **non vengono scritte** nel
> file di configurazione. In DEMO puoi saltare questo passo.

### 5) Installa il servizio (riparte da solo dopo crash e riavvii)
```bash
cp deploy/agentcolony.service /etc/systemd/system/
nano /etc/systemd/system/agentcolony.service
```
Assicurati che `User` e `WorkingDirectory` siano giusti. Per l'utente `root` e la
cartella `/root/IA-` il file è:
```ini
[Unit]
Description=AgentColony
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/IA-
EnvironmentFile=-/etc/agentcolony.env
ExecStart=/usr/bin/python3 server.py --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Attivalo:
```bash
systemctl daemon-reload
systemctl enable --now agentcolony
systemctl status agentcolony      # deve risultare "active (running)"
```
Fatto: ora gira **24/7** e **riparte da solo** dopo un crash o un riavvio del server.

### 6) Apri il sito in sicurezza
Il servizio ascolta solo in locale sul server (`127.0.0.1`), quindi **non è esposto a
internet**. Per vederlo, apri un **tunnel SSH** dal tuo PC:
```bash
ssh -L 8000:localhost:8000 root@INDIRIZZO_IP_DEL_SERVER
```
Lascia aperta questa finestra e apri sul tuo PC **http://localhost:8000**. È il modo
più sicuro: nessuno da fuori può raggiungere la pagina.

> **In alternativa**, se vuoi raggiungerlo da qualsiasi dispositivo senza tunnel:
> nell'`ExecStart` metti `--host 0.0.0.0 --port 8000`, tieni **obbligatoriamente** il
> `AGENTCOLONY_TOKEN`, e apri la porta 8000 nel firewall. Meno sicuro: la pagina è
> raggiungibile da internet (protetta dal token).

---

## Opzione C — Docker

Se conosci Docker, c'è già il `Dockerfile`:
```bash
docker build -t agentcolony .
docker run -d --name agentcolony --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  -v $PWD/data:/app/data \
  -e KRAKEN_API_KEY=... -e KRAKEN_API_SECRET=... \
  -e AGENTCOLONY_TOKEN=una_password \
  agentcolony
```
Il `--restart unless-stopped` lo fa ripartire da solo. Accedi via tunnel SSH come sopra.

---

## Opzione D — Render (deploy dal browser, senza terminale)

Render mette il progetto online partendo da GitHub, **senza usare SSH**. Nel repo c'è
già il file **`render.yaml`** che configura tutto (servizio a pagamento + disco
persistente + variabili). Segui i passi e occhio alle **3 trappole** qui sotto.

### Passi
1. Vai su **render.com**, crea un account e collega il tuo **GitHub**.
2. **New → Blueprint**, scegli il repository `IA-` e il ramo. Render legge `render.yaml`
   e propone il servizio già configurato.
3. Nelle **Environment Variables** del servizio imposta:
   - `AGENTCOLONY_TOKEN` = una password lunga → è la **password del sito** (obbligatoria).
   - (solo soldi veri) `KRAKEN_API_KEY` e `KRAKEN_API_SECRET` (chiavi **solo-trading**).
4. Avvia il deploy. Quando è **Live**, apri l'indirizzo `https://…onrender.com`, inserisci
   la password e usi il sito come in locale.

### ⚠️ Le 3 trappole (già gestite dal `render.yaml`)
- **Niente piano gratuito:** il *free* si spegne dopo ~15 min di inattività e **ferma il
  bot**. Il file usa `plan: starter` (a pagamento, ~7$/mese, non dorme).
- **Disco persistente:** senza, Render cancella `data/` ad ogni riavvio e **perdi lo
  stato dei bot**. Il file monta un disco su `/var/data` e ci punta il bot.
- **Sito pubblico → token obbligatorio:** su Render l'indirizzo è raggiungibile da
  internet. Senza `AGENTCOLONY_TOKEN` chiunque potrebbe aprire il pannello (che comanda
  **soldi veri**!). Impostalo **prima** di attivare i soldi veri.

> Tieni **una sola istanza** (già impostato): più istanze = più motori che tradano in
> parallelo sullo stesso conto.

---

## Comandi utili (VPS)

```bash
journalctl -u agentcolony -f          # guarda i log in tempo reale
systemctl restart agentcolony         # riavvia
systemctl stop agentcolony            # ferma
cd /root/IA- && git pull && systemctl restart agentcolony   # aggiorna il codice
```

---

## Sicurezza e backup

- **Chiavi solo-trading** (niente prelievi): anche nel peggiore dei casi nessuno può
  spostarti i fondi.
- **Non esporre il sito senza token.** Meglio ancora: usa il tunnel SSH.
- La cartella **`data/`** contiene chiavi e stato dei bot: resta sul server, **mai su
  GitHub**. Ogni tanto fanne una copia di backup (contiene lo storico dei bot).
- Tieni il server aggiornato: `apt update && apt upgrade -y`.

---

## Promemoria onesto

Nessun guadagno è garantito. Tieni tutto in **DEMO** finché non sei convinto, e quando
passi ai soldi veri **inizia con pochi euro** e prova prima un ordine reale piccolo per
confermare che tutto funzioni. Il massimo che puoi perdere è il **capitale** che imposti.
