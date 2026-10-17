# GarlicSMTP Installation Architecture — aggiornamento documentale

> **Aggiornamento milestone — 18/10/2026**
>
> Le osservazioni dell'08/10/2026 e la baseline P1–P46
> rimangono conservate come documentazione storica.
>
> **Implementazione in sviluppo:** gestione della DEK,
> wrapping mediante password e recovery key offline,
> integrazione SQLCipher nei backend SQLite interessati,
> cifratura degli allegati nelle componenti interessate,
> recupero della password applicativa e rotazione della
> recovery key senza rigenerazione della DEK.
>
> **Verifiche eseguite:** suite completa `python -m pytest -q`
> con 1830 test superati; recupero password verificato
> manualmente nell'ambiente di sviluppo.
>
> **Validazioni ancora aperte:** installazione e packaging
> della nuova build su Ubuntu 24.04 VM, migrazione sicura
> dei dati persistenti preesistenti e verifica end-to-end
> della protezione di database, allegati, metadati,
> residui temporanei e backup. Non dichiarare soddisfatti
> integralmente i requisiti S1–S7 sulla sola base dei test.
>

**Data aggiornamento:** 08/10/2026
**Stato:** requisiti architetturali P1–P46 preservati; stato di implementazione aggiornato dagli snapshot fino alla ripresa 8.
**Gerarchia delle fonti:** repository e test reali > evidenze di validazione successive > snapshot recenti > baseline storiche. Questa edizione BIS include una verifica statica dei file ufficiali pubblicati su GitHub, esclusa la cartella `docs/`. Non costituisce una nuova prova runtime.

## Guida alla lettura

Il testo originale del 06/09/2026 è conservato integralmente nella sezione «Baseline normativa P1–P46» per non perdere numerazione, vincoli o decisioni. Le sezioni che precedono e seguono la baseline ne aggiornano **lo stato**, non ne cancellano le prescrizioni. Dove la baseline dice «non ancora deciso», leggere anche gli aggiornamenti successivi: alcune scelte sono state nel frattempo implementate. Dove la baseline descrive una GUI Qt, il prodotto successivo utilizza Tkinter.

## Stato verificato documentalmente al 08/10/2026

| Area | Evidenza più recente | Stato |
|---|---|---|
| Sistema operativo | clean install e flusso SMTP/Tor su VM Ubuntu 24.04 | validato per Ubuntu 24.04; non estendere ad altre distro |
| Ambiente Python | Python >=3.12; venv isolato; metadata in pyproject.toml | realizzato |
| Installer | `./install.sh` generato da manifest/progetto, rootless, detect-before-modify, idempotente | validato su VM Ubuntu 24.04 |
| Tor | Control locale 127.0.0.1:9051, SAFECOOKIE, cookie della stessa istanza Tor, gestione Onion dinamica | validato su VM |
| GUI | launcher `garlicsmtp-gui` per produzione; `python -m garlicsmtp.gui` per development | Tkinter attuale; Qt/PySide6 è storia |
| Launcher Desktop | PNG, `.desktop`, trust GNOME | validato nella fase successiva al clean install |
| Account GUI | scrypt, `state/account-credentials.json`, creazione 0600 e controlli su symlink | implementato e testato in fase successiva |
| Dati persistenti | `data/mailboxes.db`, `data/sent.db`, `state/queue.db`, allegati bin/json | persistenza esistente; cifratura a riposo completa NON implementata |
| Recupero password | recovery key offline, DEK e doppia KEK | requisiti approvati, NON implementati |
| Disinstallazione | preservare `~/GarlicSMTP` sorgente; rimuovere solo risorse proprie secondo policy | test VM riportato nelle fasi successive |

**Non equiparare** la cifratura E2EE durante il trasporto alla cifratura dei database a riposo. L'account GUI non sblocca ancora una DEK. Le decisioni di SQLCipher, migrazione e recovery sono ancora aperte.

## Regole di installazione aggiornate

- Eseguire `./install.sh` come utente normale **dalla radice del repository**. Non usare `sudo ./install.sh`, `sudo pip`, `pip --user` o `--break-system-packages`.
- Per il primo avvio in produzione usare `~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui` o il launcher Desktop installato; per lo sviluppo usare `python -m garlicsmtp.gui` da repository e venv attiva. I due percorsi hanno configurazioni differenti.
- Il profilo realmente validato è Ubuntu 24.04 con `apt-get`, Tor di sistema e sessione grafica GNOME. La disponibilità su altre distribuzioni, macOS e Windows nativo **non è attestata**.
- Se l'utente viene aggiunto al gruppo `debian-tor`, può essere necessario **logout/login grafico completo** prima di avviare la GUI: la sessione esistente può avere gruppi supplementari obsoleti.
- L'installer deve conservare Onion identity, Ed25519, X25519, trust, pin remoti, archivi e credenziali nelle reinstallazioni idempotenti e negli upgrade.
- I test che simulano operazioni di sistema non devono eseguire realmente comandi privilegiati.

## Layout persistente attuale e responsabilità

`ApplicationPaths.for_user()` è autoritativo. Gli snapshot più recenti confermano la radice `~/.local/share/garlicsmtp/`, il venv sotto `venv/`, la configurazione in `config/settings.toml`, i messaggi ricevuti in `data/mailboxes.db`, gli inviati in `data/sent.db`, la coda in `state/queue.db` e le credenziali GUI in `state/account-credentials.json`. Esistono inoltre allegati e file di identità/chiavi gestiti dai rispettivi componenti; **non derivare automaticamente l'intero layout da questa lista**. Verificare sempre `garlicsmtp/configuration/paths.py`, `application/builder.py`, il manifest e il codice installer corrente prima di modificare i percorsi.

## Aggiornamenti cronologici che superano le osservazioni del 06/09

- **09/09:** milestone Tor P45 conclusa, commit storico `d86ce64`, full suite allora `1273 passed`. Il documento intermedio che riportava P45.4 RED è superato dal successivo snapshot che dichiara P45 chiuso.
- **15–17/09:** installer/first-run, runtime-config, packaging e validazione da Ubuntu 24.04 vergine. Correzioni documentate: probe venv/ensurepip; wiring Tor ControlPort; dipendenza `libxcb-cursor0` allora necessaria per GUI Qt; refresh gruppi; distinzione development/production paths. Il prerequisito Qt è **storico** dopo migrazione GUI a Tkinter.
- **18–27/09:** launcher Desktop PNG/trust GNOME; migrazione PySide6 → Tkinter; baseline alpha tag `v0.0.1-alpha` su `f249621a21afd75ca83571e62be7c8405c15705d`; archivi Received/Sent separati.
- **02/10:** allegati validati (precedente checkpoint `1616 passed`); pulsante manuale `Retry pending` validato (`1622 passed` full suite); non cambia l'algoritmo di retry né conferma la consegna remota.
- **Fasi successive riportate nella ripresa 8:** credenziali account GUI con scrypt e file 0600, test dedicati 18 passed, ultimo full pytest riferito `1712 passed`; disinstallazione testata su Ubuntu 24.04 preservando sorgenti. Questi numeri sono checkpoint storici, non test rieseguiti per questa redazione.
- **08/10:** audit dei percorsi persistenti e della crittografia; recovery offline e cifratura integrale a riposo restano solo in progettazione.

---

## Indice completo dei punti di sviluppo P e S (non retroattivi)

Questo indice riunisce tutti i punti in un unico elenco consultabile. I testi normativi **P1–P46** rimangono invariati nelle rispettive sezioni; i punti **S1–S7** sono requisiti successivi, **non retroattivi**, e non modificano né rinumerano i P. L’indice non attribuisce a nessun punto lo stato di implementazione.

### Principi P — baseline storica (P1–P46)

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

### Requisiti S — successivi e non retroattivi (S1–S7)

- **S1 — cifratura integrale:**: proteggere mailboxes.db, sent.db, queue.db, metadati, allegati e residui SQLite (WAL, SHM, journal, temp e backup) con una strategia verificata, anche dopo crash.
- **S2 — gerarchia chiavi:**: DEK indipendente da password e recovery key; due KEK indipendenti per proteggere la stessa DEK; nessun segreto salvato in chiaro.
- **S3 — recovery offline:**: generazione casuale, visualizzazione una sola volta, conferma di conservazione, reset password senza vecchia password, rotazione e invalidazione della vecchia chiave; non è login alternativo.
- **S4 — continuità:**: migrazione developer e nuove installazioni devono conservare messaggi, allegati, Ed25519, X25519 e identità Onion; niente bypass developer.
- **S5 — accesso e lifecycle:**: login prima di avvio ricezione; chiusura GUI ferma la ricezione; accessi diretti da CLI/bootstrap non devono aggirare lo sblocco degli archivi.
- **S6 — E2E di sicurezza:**: ricezione reale, chiusura, copia DB non leggibile, riavvio, recovery offline, lettura dello stesso messaggio, identità immutate.
- **S7 — packaging:**: prima di scegliere SQLCipher, verificare build, distribuzione, dipendenze e compatibilità Ubuntu 24.04. `cryptography>=46,<47` non cifra da sola un database SQLite.

---

## Baseline normativa P1–P46 (testo storico conservato)

> Nota editoriale: le affermazioni «currently», «not yet» e i dettagli Qt nel testo seguente sono riferiti **al 06/09/2026**; le sezioni di aggiornamento sopra e sotto hanno priorità temporale.

# GarlicSMTP Installation Architecture

**Status:** Design baseline  
**Project version at baseline:** 0.1.0-alpha  
**Baseline date:** 2026-09-06

## 1. Purpose

This document defines the approved architectural requirements for
GarlicSMTP installation, first-run configuration, repair, upgrade, and
release automation.

The existing GarlicSMTP application pipeline is considered functional
and protected. Installation work must not alter application behaviour
unless a concrete functional requirement is demonstrated and covered by
tests.

The installer is infrastructure around GarlicSMTP. It must not duplicate
or replace responsibilities already owned by tested application
components.

## 2. Installation principles

### P1 — Mandatory isolated virtual environment

A virgin Linux installation must:

- verify or install a compatible Python before creating the environment;
- create a dedicated virtual environment automatically;
- install Python dependencies only inside that environment.

There is no fallback to global Python installation.

The installer must not use `sudo pip`, `pip --user`, or
`--break-system-packages`.

Virtual-environment enforcement belongs to bootstrap/installation, not
to `ApplicationBuilder`, GUI startup, runtime, or the delivery pipeline.

### P2 — GarlicSMTP never runs as root

GarlicSMTP runtime processes run as a normal user.

Administrative privileges may be requested only by bootstrap operations
that genuinely require system modification.

Application state, databases, identities, private keys, credentials, and
the GarlicSMTP virtual environment must not be created as root.

### P3 — Detect before modifying

The installer detects compatible prerequisites before modifying the
system.

Existing compatible software should be reused.

The installer must not perform unnecessary upgrades, removals, system
Python modifications, or silent system changes.

### P4 — Bootstrap is idempotent

Re-running bootstrap must not destroy or regenerate a valid installation.

In particular, re-running bootstrap must not regenerate signing keys,
encryption keys, Onion identity, databases, or credentials merely
because bootstrap was executed again.

Install, update, repair, and credential reset are distinct operations.

### P5 — Installation is phased and verifiable

The conceptual installation sequence is:

    CHECK
      -> SYSTEM PREREQUISITES
      -> PYTHON
      -> CREATE VENV
      -> INSTALL DEPENDENCIES
      -> VERIFY ENVIRONMENT
      -> FIRST-RUN CONFIGURATION
      -> VERIFY GARLICSMTP
      -> COMPLETE

Installation is complete only after final verification succeeds.

Diagnostic output must not expose secrets or message content.

### P6 — Deterministic versions and dependencies

Installation must not depend on an unspecified "latest" version.

Compatible Python and dependency versions come from authoritative
project metadata.

Release facts must not be independently duplicated across installer
scripts.

### P7 — No implicit remote script execution

Installation must not use patterns such as `curl | sh`.

System packages and prerequisites must be obtained through supported
package managers or other explicitly declared and verified mechanisms.

### P8 — Installation manifest as a source of release truth

Variable installation and release facts must be represented by a
declarative, versioned installation/release description.

Installer scripts must not become independent stores of release facts.

### P9 — Detect project/installer divergence

Before release, automated or semi-automated validation must compare
project metadata with the installation manifest and fail when relevant
changes have not been classified.

Some information can be detected automatically, including Python
requirements, Python dependencies, project version, and entry points.

Other information requires explicit declaration or review, including
Linux packages, Tor requirements, ports, migrations, and new persistent
secrets.

### P10 — Installer is generated

The intended architecture has three layers:

    PROJECT
      pyproject.toml, source, configuration, tests

    RELEASE / INSTALL MANIFEST
      installation-specific declarations

    GENERATOR
      reads and validates project + manifest
      and emits installation artifacts

Generated installer artifacts are not the source of truth and must not
be maintained as independent monolithic scripts.

### P11 — Contemporaneous versioned documentation

Installation, first-run, upgrade, repair, packaging, and release
decisions are documented as they are developed.

Machine-readable version and dependency facts should not be duplicated
in prose documentation.

Stable requirement identifiers such as P1, P2, and so on are used so
tests and release validation can refer to architectural requirements.

### P12 — Upgrade is not reinstall

Upgrade must not, by default, regenerate, delete, or overwrite:

- Onion Service identity;
- Ed25519 signing keys;
- X25519 encryption keys;
- trust store;
- remote key pins;
- mailbox database;
- delivery queue;
- user configuration;
- persistent authentication credentials.

Replaceable software and persistent state are separate concerns.

## 3. Persistent state and filesystem

### P13 — Software and persistent state are separated

Replaceable application software and dependencies must be separable from
persistent user state.

Updating software must not imply replacing application state.

### P14 — Persistent state belongs to the runtime user

Persistent GarlicSMTP files are owned by the user that runs GarlicSMTP.

If bootstrap temporarily uses administrative privileges for system
prerequisites, it must return to the normal user before creating
GarlicSMTP configuration, keys, databases, credentials, or virtual
environment state.

### P15 — Restrictive secret permissions

Private keys, credentials, and other secrets use restrictive filesystem
permissions.

Unsafe permissions must result in safe failure or an explicit,
controlled correction.

They must not be silently ignored.

### P16 — ApplicationPaths.for_user() is authoritative for V1

For GarlicSMTP V1, `ApplicationPaths.for_user()` defines the persistent
filesystem layout.

Current layout:

    ~/.local/share/garlicsmtp/
    ├── config/
    │   └── settings.toml
    ├── data/
    │   └── mailboxes.db
    ├── state/
    │   ├── queue.db
    │   ├── onion-service.key
    │   └── logs/
    └── cache/

The installer must not independently reproduce or reinterpret these
paths.

Changing this layout in the future requires an explicit, versioned,
tested migration.

### P17 — No persistent writes outside declared layout

GarlicSMTP bootstrap and application components must not create
unrelated persistent files elsewhere in the repository, home directory,
or system filesystem.

System-level prerequisite configuration is treated separately from
GarlicSMTP persistent application state.

### P18 — Persistent layout changes are migrations

Future persistent path changes must be explicit and tested migrations.

Persistent data must never be silently relocated.

## 4. First-run state

### P19 — First-run is determined from real state

A completion marker may be used as supporting information but must not
be the sole authority for deciding whether first-run has completed.

Required artifacts and state must be validated.

### P20 — No default or shared secrets

There is no default GarlicSMTP password.

Passwords and other installation-specific secrets must not be embedded
in source code, installer artifacts, manifests, or documentation.

Each installation receives unique secret state.

### P21 — Cryptographic secrets are generated by their responsible components

First-run must not reimplement Onion, Ed25519, or X25519 private-key
generation in shell scripts.

Existing tested GarlicSMTP components remain responsible for their
cryptographic material and existing atomic-write, symlink, and
permission protections must remain effective.

### P22 — Creation is not regeneration

A valid existing key is reused.

A missing key may be generated only in the appropriate first-run path.

An invalid key or unsafe state must cause explicit failure or recovery;
it must not trigger silent deletion and regeneration.

### P23 — Generated configuration is minimal

First-run should persist only required or user-specific configuration
rather than copying every application default into `settings.toml`.

This allows future application defaults to evolve without unnecessary
configuration drift.

### P24 — Existing configuration is not silently overwritten

Valid existing configuration is reused.

Invalid configuration produces a diagnostic error.

Older configuration requiring structural changes uses an explicit
migration.

A parse failure must never be interpreted as permission to rewrite the
file with defaults.

### P25 — First-run is resumable

First-run is logically transactional and phase-aware.

If a later phase fails, already valid configuration, credentials,
identities, and keys are preserved.

A subsequent run resumes or repairs safely rather than destructively
starting over.

## 5. Local IMAP authentication

### P26 — Persistent local IMAP credentials

GarlicSMTP V1 has persistent local IMAP credentials established during
first-run.

There is no default password and no plaintext password persistence.

The password is chosen during first-run.

### P27 — Passwords use a dedicated password-hashing scheme

Persistent authentication must use an appropriate password-hashing
construction with algorithm information, parameters, random salt, and
derived value.

Direct SHA-256/SHA-512 password hashing and reversible password storage
are not acceptable.

The concrete algorithm remains an open implementation decision until
dependency and platform requirements are finalized.

### P28 — Credential state is separate from settings.toml

Authentication credential state is stored separately from general
application configuration.

Its final path must be represented by application path infrastructure
rather than hard-coded independently by the installer.

### P29 — Credentials are created once

Missing credentials during legitimate first-run may be created.

Valid existing credentials are reused.

Corrupt or permission-unsafe credential state causes explicit failure.

Authentication failure must never authorize automatic credential
replacement.

### P30 — Password reset is not reinstall

Password reset changes only local authentication credential state.

It must not alter Onion identity, signing or encryption keys, mailbox
data, queue data, trust/pinning state, or unrelated configuration.

### P31 — Authentication remains separate from IMAP protocol logic

The IMAP protocol continues to depend on the `Authenticator` interface.

Persistent authentication is introduced as an implementation behind
that interface, without reopening or redesigning the IMAP protocol
server.

### Approved V1 username decision

The V1 local IMAP username is:

    garlicsmtp

It is not a secret.

The Onion hostname is explicitly not used as the IMAP username.

The IMAP account identifies local access; it does not define GarlicSMTP
network identity.

## 6. Onion identity and mail identity

### P32 — Onion Service is the network-identity authority

The installer does not generate, calculate, or invent an Onion hostname.

The Onion Service established through the existing GarlicSMTP Tor
integration is authoritative.

### P33 — Canonical V1 mail address derives from the real Onion hostname

The canonical GarlicSMTP V1 sender identity is:

    garlicsmtp@<onion-hostname>

This preserves the existing application behaviour.

V1 does not introduce multiple local mail accounts or aliases as part of
installation work.

### P34 — test.onion is not an installed identity

The current `test.onion` application default must not be presented by
the installer as the user's real Onion mail identity.

A usable Onion identity exists only after the real Onion Service
hostname has been obtained.

### P35 — Onion identity is persistent

The Onion Service private identity is persistent state.

Initial creation occurs through the existing Onion Service component.

Subsequent application starts, repair operations, and upgrades reuse the
existing valid identity.

An invalid identity must not be silently deleted or regenerated.

### P36 — GUI sender remains backend-derived

The installer does not write or independently persist a GUI sender
address.

The existing Onion Service -> application ViewModel -> compose sender
flow remains authoritative.

### P37 — IMAP authentication identity and Onion identity are distinct

The local IMAP username and password authenticate local access.

They do not determine Onion identity, cryptographic keys, or the public
mail address.

### P38 — First-run verifies the real Onion identity

When Tor is enabled, successful first-run includes verification that
GarlicSMTP can establish its Onion Service and obtain a valid Onion
hostname.

This does not imply that every later upgrade operation must recreate or
republish the identity merely to manipulate replaceable software.

## 7. Tor integration

### P39 — Tor is a system prerequisite

Tor is infrastructure external to the Python virtual environment.

Bootstrap detects a compatible Tor installation before modifying the
system.

If installation is required, system privileges are limited to the
system-prerequisite phase.

### P40 — GarlicSMTP owns the Onion Service lifecycle

The installer must not configure a duplicate static Hidden Service in
`torrc`.

It prepares Tor infrastructure required by the existing
`OnionServiceManager`.

GarlicSMTP remains responsible for creating or restoring the Onion
Service through Tor Control.

### P41 — Tor Control remains local

V1 Tor Control access is local.

Installation must not expose the Tor Control endpoint on LAN or public
interfaces merely to simplify setup.

### P42 — SAFECOOKIE is mandatory

GarlicSMTP Tor Control authentication uses SAFECOOKIE.

Installation must not weaken this requirement by falling back to null
authentication, simple COOKIE authentication, or a Control password.

### P43 — Tor's advertised cookie is authoritative

The installer does not copy the Tor control cookie into GarlicSMTP
persistent state.

GarlicSMTP authenticates using the cookie belonging to the Tor instance
it contacted.

If an explicit cookie path is configured, it must match the path
advertised by Tor.

### P44 — SAFECOOKIE access without root runtime

The runtime user must have legitimate access to the Tor SAFECOOKIE.

If operating-system configuration or group membership is required, that
work occurs explicitly during the privileged bootstrap phase.

GarlicSMTP must not run as root.

The installer must not solve permission problems by making the cookie
world-readable.

### P45 — Detect Tor state before modifying it

Bootstrap distinguishes at least:

    Tor absent
      -> install prerequisite

    Tor present, compatible, correctly configured
      -> reuse without modification

    Tor present and compatible but Control/SAFECOOKIE unavailable
      -> minimal explicit configuration

    Tor present but incompatible or ambiguous
      -> diagnostic failure / explicit recovery

Existing Tor configuration must not be indiscriminately replaced.

### P46 — First-run performs end-to-end Tor verification

First-run is not complete merely because a Tor executable or service
exists.

The intended verification path is:

    Control endpoint reachable
      -> PROTOCOLINFO
      -> SAFECOOKIE available
      -> cookie readable
      -> SAFECOOKIE challenge verified
      -> authentication successful
      -> ADD_ONION successful
      -> valid .onion hostname obtained
      -> Onion identity persisted

Verification should exercise the normal GarlicSMTP integration rather
than reimplementing the Tor Control protocol in installer shell code.

## 8. Current project metadata observations

At this baseline the project declares:

    project version: 0.1.0-alpha
    Python requirement: >=3.12
    build backend: setuptools.build_meta

Runtime Python dependencies are declared in `pyproject.toml`.

The repository currently also contains `requirements.txt` with the same
runtime dependency declarations. This is a potential divergence point
and must eventually be covered by P6/P9 rather than silently maintained
as independent installer truth.

The project version is currently declared both in `pyproject.toml` and
in the Python package. This is another potential divergence point for
release validation.

The source tree contains a CLI `__main__.py` and GUI application module,
but the inspected `pyproject.toml` does not yet declare
`[project.scripts]` or `[project.gui-scripts]`.

These observations describe the current repository. They are not
authorization to refactor packaging as part of this documentation
change.

## 9. Open decisions

The following decisions are intentionally not finalized by this
baseline:

- concrete password-hashing algorithm and parameters;
- final persistent credential-store format and path;
- exact Linux distributions supported by V1 bootstrap;
- distribution-specific Tor package installation;
- distribution-specific Tor configuration file handling;
- mechanism for granting the runtime user SAFECOOKIE access;
- supported Tor version range;
- exact release/install manifest schema;
- installer generator implementation;
- generated installer artifact format;
- installed CLI/GUI entry-point declarations;
- update and migration implementation details.

Each decision must be resolved incrementally and, where applicable,
covered by focused tests before installer implementation relies on it.

## 10. Protected application boundary

The current GarlicSMTP backend, application/service layer, GUI
composition, SMTP -> Store -> IMAP path, Tor/E2EE integration, key
management, queue behaviour, and protocol implementations are considered
a protected functional pipeline.

Installer development must prefer composition around these components.

Existing application code is changed only when an installer requirement
demonstrates a real missing boundary or API, and such a change follows
the normal RED -> minimal implementation -> GREEN process.


---

## Requisiti nuovi da progettare — NON implementati

Questi requisiti sono registrati qui come backlog di sicurezza, **non** aggiunti retroattivamente ai principi P1–P46:

- **S1 / cifratura integrale:** proteggere mailboxes.db, sent.db, queue.db, metadati, allegati e residui SQLite (WAL, SHM, journal, temp e backup) con una strategia verificata, anche dopo crash.
- **S2 / gerarchia chiavi:** DEK indipendente da password e recovery key; due KEK indipendenti per proteggere la stessa DEK; nessun segreto salvato in chiaro.
- **S3 / recovery offline:** generazione casuale, visualizzazione una sola volta, conferma di conservazione, reset password senza vecchia password, rotazione e invalidazione della vecchia chiave; non è login alternativo.
- **S4 / continuità:** migrazione developer e nuove installazioni devono conservare messaggi, allegati, Ed25519, X25519 e identità Onion; niente bypass developer.
- **S5 / accesso e lifecycle:** login prima di avvio ricezione; chiusura GUI ferma la ricezione; accessi diretti da CLI/bootstrap non devono aggirare lo sblocco degli archivi.
- **S6 / E2E di sicurezza:** ricezione reale, chiusura, copia DB non leggibile, riavvio, recovery offline, lettura dello stesso messaggio, identità immutate.
- **S7 / packaging:** prima di scegliere SQLCipher, verificare build, distribuzione, dipendenze e compatibilità Ubuntu 24.04. `cryptography>=46,<47` non cifra da sola un database SQLite.

## Criterio per modificare architettura e installer

Ogni modifica segue: lettura sorgente reale + test pertinenti → RED singolo e confermato → GREEN minimo → test mirato → regressioni correlate → `pytest -q` → gate VM Ubuntu 24.04 se necessario. Core SMTP, IMAP, queue/store, E2EE e Tor congelato salvo failure concreto. Nessun commit o test va dichiarato senza output reale. Aggiornare questo documento soltanto dopo aver classificato evidenze e cambiamenti.

## Provenienza

Fonti: `installation-architecture(1).md` (baseline 06/09), documenti 03/09 e 06/09, snapshot 09/09 e 15/09, validazione alpha 17/09, handoff 27/09, ripresa 7 del 02/10, ripresa 8 del 08/10 e recap 31/07. La redazione non ha avuto accesso al repository Git corrente: le istruzioni operative sono derivate dagli snapshot.


## Addendum BIS — riscontro repository ufficiale (08/10/2026)

Repository `https://github.com/giulsign/GarlicSMTP.git`, branch predefinito `main`. Esclusa la cartella GitHub `docs/`; la baseline P1–P46 sopra proviene dai documenti forniti dall’utente.

- `pyproject.toml`: versione `0.0.1-alpha`, Python `>=3.12`, dipendenze `dnspython>=2.8,<3` e `cryptography>=46,<47`, entrypoint `garlicsmtp` e `garlicsmtp-gui`.
- `README.md` e `SECURITY.md`: alpha, nessun audit indipendente, nessuna garanzia di anonimato/sicurezza; PolyForm Noncommercial 1.0.0 e licenza commerciale separata.
- `install.sh`: invoca `/usr/bin/python3 -m install.installer`.
- `install/manifest.toml`: unico profilo Ubuntu 24.04; `apt-get`, Tor `127.0.0.1:9051` SAFECOOKIE, `python3-venv`, `python3-tk`.
- `install/installer.py`: chiede password **IMAP**, crea venv utente, installa package e configura runtime/launcher; richiede logout/login per gruppo Tor. Password IMAP distinta dall’account GUI.
- `install/uninstaller.py`: comando `python3 -m install.uninstaller`, conferma `DELETE`; elimina dati applicativi, chiavi e Onion identity, non il checkout Git. Non esiste `uninstall.sh` nella root esaminata.
- `garlicsmtp/gui/application.py`: setup/login prima dell’avvio runtime e della visualizzazione della finestra.
- `garlicsmtp/security/auth/account_credentials.py`: hash scrypt e permessi 0600.
- `garlicsmtp/storage/sqlite/backend.py` e `garlicsmtp/storage/attachment_store.py`: SQLite standard e allegati/metadati in chiaro. Cifratura integrale at-rest, DEK e recovery key ancora da implementare.

Confronto statico, senza nuove esecuzioni pytest o VM. Gli esiti storici restano tali.
