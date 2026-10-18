# GarlicSMTP — QUICKLAUNCH

> **Versione di riferimento: v0.1.0-alpha.1 — 19/10/2026.**
> Baseline applicativa: commit `9bfc2f7` su `main`, già pubblicato su `origin/main` secondo il checkpoint di sviluppo.
> **Il tag Git/release non risulta ancora creato:** un clone generico di `main` non garantisce una build immutabile.
> Validati invio/ricezione bidirezionali developer ↔ Ubuntu VM e allegati; suite developer: **1844 passed**.
> Database Received, Sent e Queue verificati senza intestazione SQLite plaintext su entrambe le macchine; allegato GSAT v1 verificato su entrambe.
> Non equivalgono ad audit indipendente, backup sicuro o migrazione di archivi legacy.

**Guida rapida per chi vuole installare e avviare GarlicSMTP senza conoscere Python.**
Aggiornata: 19/10/2026 · Release documentale: `v0.1.0-alpha.1`. I test e le prove operative sono checkpoint riferiti dall’utente; nessuna nuova installazione da zero eseguita durante questa redazione.

## Prima di iniziare

Questa procedura è **validata documentalmente per Ubuntu 24.04 Desktop**. Serve una connessione Internet, un account utente normale con possibilità di autorizzare l'installazione dei prerequisiti e il repository pubblico ufficiale `https://github.com/giulsign/GarlicSMTP.git`.

**Windows:** è documentato come macchina di sviluppo tramite WSL Ubuntu, **non** come sistema per installare direttamente la versione desktop Linux. **macOS e altre distribuzioni Linux:** nessuna installazione ufficialmente validata negli snapshot.

## A. Installazione su Ubuntu 24.04 — copia un blocco alla volta

### 1. Apri il Terminale

Su Ubuntu premi `Ctrl` + `Alt` + `T`.

### 2. Controlla Git

```bash
git --version
```

Se appare «command not found», installa Git:

```bash
sudo apt-get update
sudo apt-get install git
```

### 3. Clona il repository

Copia questo blocco **intero**. Alla richiesta incolla l'URL Git reale ricevuto dal progetto e premi Invio:

```bash
cd ~
git clone https://github.com/giulsign/GarlicSMTP.git GarlicSMTP
cd ~/GarlicSMTP
```

Il repository è pubblico e il clone normalmente non richiede credenziali.

### 4. Avvia l'installer

```bash
./install.sh
```

**Importante:** NON usare `sudo ./install.sh`. L'installer gestisce da sé le richieste di autorizzazione necessarie per i pacchetti di sistema. Non usare `sudo pip` o `pip install` globale. Alla richiesta `IMAP password:` inserisci la password del servizio IMAP, distinta da quella GUI. Attendi il completamento e leggi eventuali errori.

### 5. Se richiesto, esci dalla sessione Ubuntu e rientra

L'installer può predisporre l'accesso al cookie Tor tramite il gruppo di sistema `debian-tor`. Se la GUI non riesce ad avviare Tor dopo l'installazione, fai un **vero logout dalla sessione grafica e un nuovo login**; aprire soltanto un terminale nuovo non è sempre sufficiente.

### 6. Avvia GarlicSMTP

Usa l'icona **GarlicSMTP** sul Desktop, se presente, oppure esegui:

```bash
~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui
```

Questo percorso usa automaticamente la home dell'utente corrente: non devi sostituire `ubuntu` con il tuo nome.

### 7. Primo accesso e uso essenziale

Segui la schermata di configurazione dell'account, scegli credenziali personali e conserva la password in un luogo sicuro. Non esiste una password predefinita. Le credenziali GUI sono diverse dall'indirizzo Onion. La **recovery key offline è implementata**: al primo setup annotala e custodiscila fuori dal dispositivo, seguendo la richiesta di conferma della GUI. Non condividerla né conservarla accanto alla password.

Dopo il login avvia i servizi dall'interfaccia e verifica lo stato Tor e il runtime. Per inviare usa la sezione di composizione, inserisci il destinatario e invia; per leggere usa **Received** e per vedere i messaggi accettati per l'invio usa **Sent**. Un messaggio in Sent non è necessariamente già consegnato al destinatario remoto.

## B. Se un messaggio non parte

1. Controlla che i servizi e Tor siano operativi. Se necessario usa il refresh dei servizi Tor dal pannello GarlicSMTP.
2. Verifica se ci sono elementi in attesa nella coda. Il pulsante **Retry pending** rende subito riprovabili i messaggi sospesi: **non invia direttamente** e non certifica la consegna; il QueueWorker riproverà al tick successivo.
3. Se Tor è congestionato, attendi e riprova; se persiste, prova un'altra connessione Internet. `Tor ready` significa che Tor locale è disponibile, non che il destinatario `.onion` sia raggiungibile.
4. Non eliminare database o identità Onion per «riparare» un errore temporaneo.

## C. Avvio sviluppo in WSL Ubuntu (non è l'installazione utente)

Per lo sviluppatore, da repository **già presente e con `.venv` già creata**:

```bash
cd /mnt/c/garlicsmtp
source .venv/bin/activate
python -m garlicsmtp.gui
```

CLI di sviluppo, quando necessaria:

```bash
python -m garlicsmtp.cli
```

Non sostituire `python -m garlicsmtp.gui` con `garlicsmtp-gui` in sviluppo: i due entrypoint usano scelte di path differenti.

## D. Aggiornamenti, riparazioni e disinstallazione

- Non cancellare `~/.local/share/garlicsmtp/` e non rigenerare identità o chiavi per tentare un aggiornamento.
- La reinstallazione idempotente tramite `./install.sh` è stata validata storicamente; **non è un comando di reset password**.
- Il codice sorgente `~/GarlicSMTP` deve essere preservato dalla disinstallazione. La disinstallazione può invece rimuovere lo stato persistente di proprietà dell'applicazione, inclusa l'identità Onion: prima di qualsiasi disinstallazione esamina le opzioni e la documentazione del comando reale nel repository. Il comando reale è `python3 -m install.uninstaller` dalla radice del repository: richiede `DELETE` e cancella irreversibilmente tutti i dati dell’app, incluse chiavi e identità Onion. Il sorgente `~/GarlicSMTP` non viene eliminato.
- Per aggiornare il codice via Git servono branch, remote e stato del repository verificati; non eseguire alla cieca `git pull` su modifiche locali.

## E. Controlli rapidi (senza modificare nulla)

```bash
lsb_release -a
python3 --version
git --version
ls -l ~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui
```

Se un passaggio fallisce, **fermati lì** e conserva il messaggio di errore completo. Non eseguire comandi trovati casualmente online e non condividere password, chiavi private o il contenuto del cookie Tor.

**Nota sulla privacy:** E2EE in transito e cifratura a riposo sono due livelli distinti. In questa baseline i tre database usano SQLCipher con DEK e gli allegati usano GSAT v1 con ChaCha20-Poly1305. I file esportati restano leggibili, e non è attestata la protezione completa di backup, file temporanei o chiavi private.

## Versione, sblocco e verifiche (v0.1.0-alpha.1)

- **Setup GUI:** scegli una password robusta; quando viene mostrata la recovery key offline, conservala e conferma la presa visione. La chiave serve a recuperare l'accesso e a impostare una nuova password senza sostituire la DEK.
- **Login:** lo sblocco con password è necessario prima della costruzione della GUI e dell'avvio della ricezione. Se lo sblocco fallisce, l'applicazione deve restare chiusa (fail-closed).
- **Password dimenticata:** usa la procedura di recupero nella GUI con la recovery key. Non reinstallare né cancellare lo stato persistente per recuperare l'account.
- **Allegati:** cifrati a riposo nell'archivio applicativo; un allegato salvato/esportato in una cartella esterna è un nuovo file leggibile da chi vi ha accesso.
- **Verifiche reali:** self-send developer e VM; developer → VM; VM → developer; allegati inviati correttamente. Tre database con intestazione non-plaintext su entrambi gli ambienti; archivio GSAT v1 osservato. **1844 passed** nella suite completa developer.
- **Limiti:** accessi alternativi CLI/bootstrap/ricezione in audit, backup e residui temporanei non attestati integralmente, nessuna migrazione legacy eseguita, nessun audit crittografico indipendente.

## Fonti e rilascio

Repository: https://github.com/giulsign/GarlicSMTP.git. Baseline di riferimento: commit `9bfc2f7`, denominazione documentale `v0.1.0-alpha.1`. Non affermare che `pyproject.toml`, il tag Git o gli artefatti di distribuzione siano già stati allineati a questa denominazione senza verifica. I passaggi `git clone` e `./install.sh` descrivono il percorso di installazione noto; per installare *esattamente* la baseline congelata è necessario prima formalizzare il tag/release e verificarne i metadati. Non eseguire aggiornamenti o reinstallazioni su dati reali senza una procedura concordata.

**Disinstallazione distruttiva, solo se realmente voluta:** dalla radice del checkout `python3 -m install.uninstaller`, con conferma `DELETE`; rimuove i dati applicativi e l'identità Onion, preservando il checkout sorgente. Non usare questo comando come reset della password.
