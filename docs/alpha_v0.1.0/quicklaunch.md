# GarlicSMTP — QUICKLAUNCH

> **Avvertenza milestone — 18/10/2026**
>
> Questa guida descrive una procedura storica di installazione.
> La build di sviluppo successiva integra DEK, SQLCipher,
> cifratura a riposo nelle componenti interessate e recupero
> offline della password applicativa.
>
> La suite locale ha superato 1830 test e il recupero password
> è stato verificato manualmente. **La nuova build non è ancora
> stata ricollaudata sulla VM Ubuntu 24.04.**
> Non considerare questa guida una validazione dell'installer
> aggiornato o della migrazione dei dati esistenti.
>

**Guida rapida per chi vuole installare e avviare GarlicSMTP senza conoscere Python.**
Aggiornata: 08/10/2026 · Basata sulla documentazione di progetto, non su una nuova installazione eseguita oggi.

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

Segui la schermata di configurazione dell'account, scegli credenziali personali e conserva la password in un luogo sicuro. Non esiste una password predefinita. Le credenziali GUI sono diverse dall'indirizzo Onion. La recovery key offline **non è ancora disponibile**.

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

**Nota sulla privacy:** l'E2EE dei messaggi esiste, ma i database locali e gli allegati non risultano ancora protetti da cifratura integrale a riposo. Non considerare il disco sicuro solo perché il trasporto usa Tor.

## Fonti ufficiali verificate (BIS)

Repository: https://github.com/giulsign/GarlicSMTP.git (`main`). Versione `0.0.1-alpha`; licenza PolyForm Noncommercial 1.0.0; nessun audit professionale indipendente. Fonti: `README.md`, `SECURITY.md`, `pyproject.toml`, `install/installer.py`, `install/uninstaller.py`, `install/manifest.toml`. Cartella GitHub `docs/` esclusa.

Per disinstallare **soltanto se vuoi cancellare tutti i dati**:

```bash
cd ~/GarlicSMTP
python3 -m install.uninstaller
```
