# GarlicSMTP — QUICKLAUNCH

> **Versione di sviluppo:** `0.1.1a0` (release prevista `v0.1.1-alpha`, non ancora pubblicata né associata a un tag).
> **Baseline di codice documentata:** commit `8faf1c6` su `main`.
> **Regressione di sviluppo:** 1.974 test superati (`python -m pytest -q`); `git diff --check` superato.
> **Ambito:** non costituisce una nuova installazione pulita verificata su Ubuntu 24.04 né una validazione del pacchetto di rilascio. Le prove precedenti di invio/ricezione bidirezionale e allegati developer ↔ VM appartengono alla baseline precedente.
> **Sicurezza:** nessun audit indipendente, verifica esaustiva di backup/file temporanei o migrazione validata di archivi legacy plaintext.

**Guida rapida per chi vuole installare e avviare GarlicSMTP senza conoscere Python.**
Aggiornata: 25/10/2026 · Destinazione documentale: candidata di sviluppo `0.1.1a0`. La guida concilia le istruzioni storiche allegate con le ultime verifiche di sviluppo riferite; non certifica una nuova installazione pulita.

## Prima di iniziare

La procedura di installazione è **documentata storicamente per Ubuntu 24.04 Desktop**, ma non è stata ricollaudata da zero per `0.1.1a0`. Serve una connessione Internet, un account utente normale con possibilità di autorizzare l'installazione dei prerequisiti e il repository pubblico ufficiale `https://github.com/giulsign/GarlicSMTP.git`.

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

### 8. Pagina HTML Onion personalizzata (facoltativa)

Nelle preferenze della GUI, individua la configurazione della pagina di presenza Onion. Per abilitare una pagina personalizzata indica il percorso di un **file HTML esistente**: quando l'opzione è attiva, un percorso vuoto o una directory non sono validi. Salva le preferenze e **riavvia il servizio/l'applicazione interessata** affinché la modifica abbia effetto. Se la personalizzazione è disattivata, rimane disponibile la pagina predefinita. Non inserire password, chiavi private, recovery key o altri segreti in una pagina HTML accessibile pubblicamente. Il modello in `docs/personalized_html/` è un esempio del progetto, non un passaggio obbligatorio d'installazione.

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

## Versione, sblocco e verifiche (`0.1.1a0`)

- **Setup GUI:** scegli una password robusta; quando viene mostrata la recovery key offline, conservala e conferma la presa visione. La chiave serve a recuperare l'accesso e a impostare una nuova password senza sostituire la DEK.
- **Login:** lo sblocco con password è necessario prima della costruzione della GUI e dell'avvio della ricezione. Se lo sblocco fallisce, l'applicazione deve restare chiusa (fail-closed).
- **Password dimenticata:** usa la procedura di recupero nella GUI con la recovery key. Non reinstallare né cancellare lo stato persistente per recuperare l'account.
- **Allegati:** cifrati a riposo nell'archivio applicativo; un allegato salvato/esportato in una cartella esterna è un nuovo file leggibile da chi vi ha accesso.
- **Verifiche:** la baseline precedente comprendeva self-send developer/VM, developer → VM, VM → developer e prove sugli allegati, oltre a controlli limitati sulle intestazioni SQLCipher e sul formato GSAT v1. Per `0.1.1a0`, l’ultima suite completa di sviluppo riferita è di **1.974 test superati**; le prove di integrazione sulla VM non sono state rieseguite durante questa revisione.
- **Limiti:** accessi alternativi CLI/bootstrap/ricezione in audit, backup e residui temporanei non attestati integralmente, nessuna migrazione legacy eseguita, nessun audit crittografico indipendente.

## Fonti e rilascio

Repository: https://github.com/giulsign/GarlicSMTP.git. Baseline di sviluppo documentata: `8faf1c6`; `pyproject.toml` e `garlicsmtp/__init__.py` dichiarano `0.1.1a0`. Dipendenze runtime dichiarate: `dnspython>=2.8,<3`, `cryptography>=46,<47`, `sqlcipher3==0.6.3`; il manifest di installazione Ubuntu richiede anche Tor e Python Tkinter. PySide6 non è una dipendenza runtime attuale. La pubblicazione del tag e degli artefatti di release non è stata verificata. Un semplice `git clone` segue il `main` corrente al momento del clone, non necessariamente questa precisa baseline. Non aggiornare o reinstallare su dati reali senza una procedura concordata.

**Disinstallazione distruttiva, solo se realmente voluta:** dalla radice del checkout `python3 -m install.uninstaller`, con conferma `DELETE`; rimuove i dati applicativi e l'identità Onion, preservando il checkout sorgente. Non usare questo comando come reset della password.
