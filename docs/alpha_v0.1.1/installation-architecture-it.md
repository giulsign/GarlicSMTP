# GarlicSMTP — Architettura di installazione — 0.1.1a0

**Stato del documento:** architettura candidata al rilascio; 25 ottobre 2026. **Release prevista:** `v0.1.1-alpha` (tag non ancora creato).

## 1. Ambito, gerarchia delle fonti e stato della release

Questo documento è la **specifica architetturale corrente e di preparazione al rilascio**, non la prova di una nuova esecuzione dell'installer. Fonti: i quattro documenti allegati (baseline storica del 6 settembre; aggiornamenti dell'8, 13, 18 e 19 ottobre 2026) e i successivi checkpoint di sviluppo forniti per `0.1.1a0`. In caso di conflitto prevalgono le evidenze successive **solo per lo stato implementativo**, non per i requisiti originari.

- **Candidata:** versione pacchetto Python `0.1.1a0`; tag Git previsto `v0.1.1-alpha` (non confermato come creato o pubblicato).
- **Baseline di sviluppo:** commit `8faf1c6` indicato come pubblicato su `main`; suite completa **1.974 test superati**. Non sono test rieseguiti durante questa redazione.
- **Checkpoint storico:** commit `9bfc2f7`, 1.844 test superati e scambi SMTP/allegati developer ↔ VM Ubuntu. Non equivalgono a un nuovo collaudo dell'installer `0.1.1a0`.
- **Piattaforma:** Ubuntu 24.04 Desktop / GNOME come target del manifest; osservazioni GUI su VM Ubuntu 22.04 non sostituiscono il collaudo di installazione pulita su 24.04. Windows WSL è ambiente di sviluppo, non target Windows nativo.

## 2. Responsabilità e flusso di installazione

L'installer è infrastruttura: non deve duplicare responsabilità applicative né alterare il runtime già testato senza requisito e test. `install/manifest.toml`, `pyproject.toml`, componenti dell'installer generato e `ApplicationPaths.for_user()` vanno riconciliati prima del rilascio.

```text
CONTROLLO → PREREQUISITI SISTEMA → PYTHON → VENV ISOLATO
         → DIPENDENZE → VERIFICA AMBIENTE
         → PRIMO SETUP → VERIFICA GARLICSMTP → COMPLETATO
```

Eseguire `./install.sh` dalla radice del repository come **utente normale**. Non usare `sudo ./install.sh`, `sudo pip`, `pip install` globale, `pip --user` o `--break-system-packages`. L'installazione dei pacchetti di sistema può richiedere autorizzazione; runtime e stato persistente restano di proprietà dell'utente normale. Rilevare prima di modificare; preservare le installazioni compatibili. Vietata l'esecuzione remota implicita (`curl | sh`).

Entrypoint di produzione: `~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui` (oppure launcher Desktop). In sviluppo, da checkout esistente e `.venv` attiva: `python -m garlicsmtp.gui`. I due percorsi hanno contesti di configurazione differenti. La GUI attuale usa **Tkinter**, non PySide6/Qt. Dopo l'aggiunta al gruppo `debian-tor` può servire un logout/login grafico completo.

## 3. Confine runtime, versioni e dipendenze

Python **>=3.12** e ambiente virtuale dedicato. Requisiti runtime riportati da `pyproject.toml`: `dnspython>=2.8,<3`, `cryptography>=46,<47` e `sqlcipher3==0.6.3`; setuptools >=77 è dipendenza di build. PySide6 presente nella venv di sviluppo **non è** dipendenza runtime GarlicSMTP. La verifica dei metadati non sostituisce prove reali di packaging e installazione sulla VM target.

Tor è prerequisito di sistema. Il ControlPort è locale (`127.0.0.1:9051` nella configurazione documentata), con **SAFECOOKIE** e cookie pubblicizzato dall'istanza Tor attiva. GarlicSMTP gestisce il ciclo di vita dell'Onion Service, preserva l'identità Onion reale e deriva da questa l'identità email canonica. `test.onion` non è un'identità installata. Credenziali GUI, autenticazione IMAP e identità Onion sono concetti distinti.

## 4. Layout persistente e proprietà

`ApplicationPaths.for_user()` è autoritativo. Radice documentata: `~/.local/share/garlicsmtp/`:

| Percorso | Scopo / confine |
|---|---|
| `venv/` | Ambiente Python isolato installato |
| `config/settings.toml` | Configurazione runtime; preservare le preferenze |
| `state/account-credentials.json` | Credenziali GUI, recovery e stato delle chiavi protette secondo implementazione; permessi restrittivi |
| `data/mailboxes.db` | Archivio Received, SQLCipher |
| `data/sent.db` | Archivio Sent, SQLCipher |
| `state/queue.db` | Coda di consegna, SQLCipher |
| `data/attachments/` | Archivio allegati cifrati GSAT v1 |

La tabella **non è un inventario esaustivo**. Identità, chiavi private, pin di fiducia e stato Tor sono gestiti dai rispettivi componenti: verificare percorsi e sorgenti dell'installer prima di modificarli. Lo stato esistente non deve essere sovrascritto o rigenerato silenziosamente. Installazione, upgrade, riparazione, recupero password, migrazione e disinstallazione sono operazioni distinte.

## 5. Sblocco crittografico e archiviazione a riposo

Il progetto implementa una **DEK indipendente di 32 byte**, protetta tramite password e recovery key offline. La GUI deve sbloccare gli archivi prima di costruirli e avviare la ricezione; lo sblocco fallito termina in modo fail-closed. Il recupero offline cambia la password senza rigenerare la DEK. Conservare la recovery key fuori dal dispositivo: non è un login alternativo ordinario.

Il connettore documentato `connect_encrypted_sqlite(path, *, dek)` controlla la DEK a 32 byte, verifica SQLCipher con `PRAGMA cipher_version`, imposta la chiave e interroga `sqlite_master`. `SQLiteMessageStoreBackend` e `SQLiteQueueBackend` usano questo confine; Received, Sent e Queue richiedono la DEK. Il percorso CLI `start` senza DEK risulta fallire chiuso. Ciò **non** dimostra la copertura completa di ogni futuro punto d'ingresso.

L'archivio allegati GSAT v1 utilizza header `GSAT` versionato, nonce di 12 byte, sottochiave derivata con HKDF-SHA256 e cifratura autenticata ChaCha20-Poly1305 di contenuto e metadati JSON, con AAD contestuale. I file allegato legacy plaintext sono rifiutati dal lettore cifrato. L'esportazione esplicita produce plaintext nella destinazione. Header SQLCipher e marker GSAT osservati su developer/VM sono controlli utili, **non audit crittografici indipendenti**.

La cifratura descritta non attesta protezione universale di backup, temporanei, WAL/SHM/journal SQLite, allegati esportati, chiavi private o archivi legacy plaintext. Non dichiarare soddisfatti integralmente S1–S7 senza evidenze dedicate.

## 6. Pagina HTML Onion facoltativa

La candidata introduce una pagina HTTP di presenza Onion configurabile, con validazione delle preferenze GUI. La pagina HTTP è un servizio distinto da SMTP/IMAP Onion; le modifiche non devono rigenerare identità email/Onion. Validare tramite GUI e riavviare i servizi pertinenti quando richiesto dall'implementazione. Trattare l'HTML personalizzato come contenuto non fidato ed evitare la pubblicazione di dati privati. Prima di cambiare implementazione o dichiarare dettagli su bind e percorsi verificare modulo del servizio, preferenze e test correnti.

## 7. Verifiche, criteri di rilascio e operazioni sicure

| Controllo | Evidenza corrente | Ancora necessario |
|---|---|---|
| Test di sviluppo | 1.974 superati per `0.1.1a0` | Ripetere sulla candidata esatta dopo modifiche |
| Trasporto e allegati | Prove storiche developer ↔ VM | Ripetere se la candidata cambia comportamento pertinente |
| SQLCipher / GSAT | Header e allegati controllati storicamente | Copertura su target, recovery, crash e backup |
| Installer e dipendenze | Precedente validazione Ubuntu 24.04 | **Nuova installazione pulita e upgrade `0.1.1a0` non attestati** |
| Migrazione | Nessuna migrazione plaintext→cifrato validata | Piano sicuro, backup e test di rollback |
| Release | Metadati versione indicati `0.1.1a0` | Verificare manifest, tag, artefatti; pubblicare solo su decisione esplicita |

Non eseguire prove di migrazione o riparazione distruttiva su database e identità Onion reali. Non usare `git add .`, reset/clean del working tree né creare commit/tag implicitamente. Prima di modificare il codice esaminare sorgenti e test reali; poi regressioni mirate, suite completa e VM quando opportuno. Il disinstallatore documentato (`python3 -m install.uninstaller` dalla radice checkout) richiede `DELETE` e **cancella irreversibilmente dati applicativi e identità Onion**, preservando il checkout sorgente: non è un reset password.

## 8. Requisiti architetturali e continuità

I **P1–P46** sono i principi originari di installazione di settembre; i **S1–S7** sono successivi e non rinumerano né sostituiscono i P. L'indice seguente conserva identificatori e titoli originari. Per i paragrafi normativi integrali e i checkpoint storici conservare i documenti di architettura settembre–ottobre allegati come archivio storico immutabile: questa è la specifica corrente consolidata, **non una sostituzione letterale di quell'archivio**.

### P1–P46 — identificatori e titoli originali

- **P1 — Mandatory isolated virtual environment**
- **P2 — GarlicSMTP never runs as root**
- **P3 — Detect before modifying**
- **P4 — Bootstrap is idempotent**
- **P5 — Installation is phased and verifiable**
- **P6 — Deterministic versions and dependencies**
- **P7 — No implicit remote script execution**
- **P8 — Installation manifest as a source of release truth**
- **P9 — Detect project/installer divergence**
- **P10 — Installer is generated**
- **P11 — Contemporaneous versioned documentation**
- **P12 — Upgrade is not reinstall**
- **P13 — Software and persistent state are separated**
- **P14 — Persistent state belongs to the runtime user**
- **P15 — Restrictive secret permissions**
- **P16 — ApplicationPaths.for_user() is authoritative for V1**
- **P17 — No persistent writes outside declared layout**
- **P18 — Persistent layout changes are migrations**
- **P19 — First-run is determined from real state**
- **P20 — No default or shared secrets**
- **P21 — Cryptographic secrets are generated by their responsible components**
- **P22 — Creation is not regeneration**
- **P23 — Generated configuration is minimal**
- **P24 — Existing configuration is not silently overwritten**
- **P25 — First-run is resumable**
- **P26 — Persistent local IMAP credentials**
- **P27 — Passwords use a dedicated password-hashing scheme**
- **P28 — Credential state is separate from settings.toml**
- **P29 — Credentials are created once**
- **P30 — Password reset is not reinstall**
- **P31 — Authentication remains separate from IMAP protocol logic**
- **P32 — Onion Service is the network-identity authority**
- **P33 — Canonical V1 mail address derives from the real Onion hostname**
- **P34 — test.onion is not an installed identity**
- **P35 — Onion identity is persistent**
- **P36 — GUI sender remains backend-derived**
- **P37 — IMAP authentication identity and Onion identity are distinct**
- **P38 — First-run verifies the real Onion identity**
- **P39 — Tor is a system prerequisite**
- **P40 — GarlicSMTP owns the Onion Service lifecycle**
- **P41 — Tor Control remains local**
- **P42 — SAFECOOKIE is mandatory**
- **P43 — Tor's advertised cookie is authoritative**
- **P44 — SAFECOOKIE access without root runtime**
- **P45 — Detect Tor state before modifying it**
- **P46 — First-run performs end-to-end Tor verification**

### S1–S7 — requisiti successivi

- **S1 — Protezione integrale a riposo:** Proteggere database, metadati, file collaterali SQLite, temporanei e backup, anche dopo crash.
- **S2 — Gerarchia delle chiavi:** Una DEK indipendente di 32 byte è protetta da chiavi derivate da password e recovery; nessun segreto deve essere salvato in chiaro.
- **S3 — Recupero offline:** La recovery key è generata, confermata e conservata offline; il reset password conserva la DEK e la rotazione invalida la vecchia chiave.
- **S4 — Continuità e migrazione:** Preservare messaggi, allegati, chiavi, pin di fiducia e identità Onion durante le migrazioni; nessun bypass developer.
- **S5 — Sblocco e ciclo di vita:** Sblocco prima della ricezione; arresto servizi alla chiusura GUI; CLI e bootstrap non devono aggirare la DEK.
- **S6 — Verifica di sicurezza end-to-end:** Verificare ricezione reale, chiusura, copia database cifrato, riavvio, recupero offline e identità conservate.
- **S7 — Distribuzione:** Validare dipendenze, build e installazione SQLCipher su Ubuntu 24.04, incluse installazione pulita e upgrade.

## 9. Controllo documentale

I documenti sorgente storici restano invariati. Prima di promuovere la candidata, riconciliare questa specifica con i sorgenti reali, il manifest di installazione e gli artefatti della release. Durante questa redazione non sono stati eseguiti una nuova ispezione del repository né test su VM.
