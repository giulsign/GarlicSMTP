# GarlicSMTP

**Versione di sviluppo:** `0.1.1a0`  
**Release prevista:** `v0.1.1-alpha` — tag e pubblicazione non ancora effettuati  
**Ultimo commit di sviluppo considerato per questa documentazione:** `8faf1c6`  
**Stato:** Alpha sperimentale; questo README descrive una release candidata, non una release completata.

GarlicSMTP è un'applicazione di messaggistica SMTP orientata alla riservatezza che comunica tramite i servizi Onion di Tor. Comprende un'interfaccia desktop Linux realizzata con Tkinter, componenti SMTP/IMAP e operazioni da riga di comando sulle caselle di posta.

> **Avvertenza di sicurezza:** GarlicSMTP non è stato sottoposto a un audit di sicurezza professionale indipendente. Tor, la cifratura e il superamento dei test non garantiscono anonimato, riservatezza, integrità o protezione su un dispositivo compromesso. Consultare [SECURITY.md](SECURITY.md) prima di usarlo con dati sensibili.

## Funzionalità

- Messaggistica SMTP bidirezionale tra peer con servizi Onion di Tor; la comunicazione tra macchina di sviluppo e VM Ubuntu è stata esercitata in precedenti test d'integrazione.
- Cifratura dei messaggi con scoperta e pinning delle chiavi X25519, HKDF e ChaCha20-Poly1305, con firme Ed25519 e relativa verifica.
- Caselle Received e Sent e coda persistente di consegna basate su SQLCipher e su una chiave di cifratura dati (DEK) di 32 byte sbloccata tramite password.
- Contenuti e metadati degli allegati locali cifrati in file autenticati GSAT v1.
- Autenticazione applicativa e recupero offline della password mediante materiale di recupero; nessuna password GUI predefinita.
- Interfaccia desktop Tkinter per comporre, ricevere e leggere messaggi, con supporto ai nuovi tentativi di consegna.
- Pagina di presenza del servizio Onion configurabile, inclusa la convalida nelle preferenze GUI del percorso HTML personalizzato facoltativo. Per abilitare una pagina personalizzata è necessario un percorso non vuoto riferito a un file; le modifiche hanno effetto dopo il riavvio del servizio o dell'applicazione interessati.

Queste descrizioni riguardano funzionalità implementate, non una certificazione di sicurezza né una garanzia di funzionamento in ogni configurazione.

## Stato delle verifiche

L'ultima esecuzione di sviluppo comunicata per la preparazione di `0.1.1a0` ha registrato **1.974 test superati** (`python -m pytest -q`, 135,21 secondi), con esito positivo di `git diff --check`. I risultati provengono dall'ambiente di sviluppo WSL; non dimostrano un'installazione pulita, una build di release riproducibile o un audit indipendente.

Precedenti test d'integrazione tra macchina di sviluppo e VM Ubuntu hanno incluso messaggi bidirezionali e allegati. Precedenti controlli in sola lettura su alcuni database Received, Sent e Queue non hanno rilevato intestazioni SQLite in chiaro; alcuni allegati controllati presentavano il formato GSAT v1. Si è trattato di verifiche limitate, non della prova che ogni file, backup, elemento temporaneo o chiave sia cifrato.

L'ambiente di sviluppo esaminato utilizzava `sqlcipher3==0.6.3` e riportava SQLCipher `4.12.0 community` / SQLite `3.51.1`. È un'osservazione dell'ambiente di sviluppo, non una specifica valida per tutti i futuri artefatti di release.

## Ambiente supportato e installazione

Il profilo dell'installer dichiarato in `install/manifest.toml` è destinato a **Ubuntu 24.04**. Una VM Ubuntu 22.04 è stata utilizzata anche per verifiche della GUI e d'integrazione, ma ciò non amplia il profilo dell'installer dichiarato. WSL è un ambiente di sviluppo; non si dichiara disponibile una release desktop Windows nativa. Altri sistemi operativi e configurazioni non sono qui convalidati.

Per un nuovo checkout:

```bash
git clone https://github.com/giulsign/GarlicSMTP.git
cd GarlicSMTP
./install.sh
```

**Non eseguire `sudo ./install.sh`.** L'installer può richiedere privilegi elevati per specifici prerequisiti di sistema. Non risulta ancora documentata come completata una prova di installazione pulita dell'esatta futura release `v0.1.1-alpha`. Prima dell'installazione, consultare `docs/quicklaunch.md` e `docs/installation-architecture.md` e verificare che corrispondano alla release prevista. Non eliminare mai dati applicativi, materiale di recupero o chiavi d'identità Onion come generico tentativo di riparazione.

Per un ambiente di sviluppo WSL già configurato:

```bash
cd /mnt/c/garlicsmtp
source .venv/bin/activate
python -m garlicsmtp.gui
```

Questo percorso di sviluppo non è una procedura generale d'installazione. La limitazione storica del bootstrap CLI `start` (errore in assenza di una DEK sbloccata) deve essere ricontrollata nel codice corrente prima della pubblicazione; non si deve presumere che sia stata risolta o che aggiri la cifratura dei database.

## Dipendenze runtime

Le dipendenze Python runtime dichiarate in `pyproject.toml` e `requirements.txt` sono:

| Pacchetto | Requisito |
|---|---|
| dnspython | `>=2.8,<3` |
| cryptography | `>=46,<47` |
| sqlcipher3 | `==0.6.3` |

Il profilo dell'installer Ubuntu richiede inoltre Tor, `python3-venv` e `python3-tk` come prerequisiti di sistema. La GUI utilizza **Tkinter**, non PySide6. PySide6 è ancora installato in un precedente ambiente virtuale di sviluppo, ma **non è utilizzato dal progetto attuale** e non è una dipendenza runtime dichiarata. Possono essere presenti anche dipendenze transitive e librerie native; consultare [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Release e versioni

Il pacchetto Python dichiara attualmente `0.1.1a0`, destinato alla futura release `v0.1.1-alpha`. Il tag `v0.1.1-alpha`, il commit sorgente definitivo, gli artefatti distribuibili e la release GitHub **non risultano ancora confermati**. Il commit `8faf1c6` identifica uno stato di sviluppo esaminato, non una release congelata o sottoposta ad audit.

La precedente baseline `v0.1.0-alpha.1` / `9bfc2f7` è storica. Aggiornare questa sezione soltanto dopo l'effettiva creazione del tag e pubblicazione della release. La presenza del solo numero di versione non prova l'esistenza di una release.

## Sicurezza e segnalazione delle vulnerabilità

Consultare [SECURITY.md](SECURITY.md) per la politica di sicurezza, i limiti noti e le indicazioni per la divulgazione coordinata. Inviare privatamente le presunte vulnerabilità a **giulisign@gmail.com**. Non allegare alle segnalazioni password, DEK, chiavi di recupero, chiavi private dei servizi Onion, cookie di autenticazione Tor, contenuti delle caselle o database attivi.

## Licenze

GarlicSMTP è **source-available, non open source approvato dall'OSI**. Il codice originale del progetto è reso disponibile secondo la **PolyForm Noncommercial License 1.0.0**. Gli usi che esulano dai permessi di tale licenza, inclusi determinati usi commerciali, richiedono una licenza scritta separata. Il software di terze parti mantiene le proprie licenze; consultare `LICENSE`, `NOTICE`, `COMMERCIAL-LICENSE.md`, `THIRD_PARTY_LICENSES.md`, `CONTRIBUTING.md` e `CLA.md`.

Copyright © 2026 Giuliano Signorelli — GarlicSMTP Project.  
Richieste di licenza commerciale: **giulisign@gmail.com**.
