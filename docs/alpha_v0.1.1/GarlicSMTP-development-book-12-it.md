# GARLICSMTP — DEVELOPMENT BOOK 12
## Storia dello sviluppo, architettura, protocollo operativo e ripartenza riproducibile

**Edizione:** 12 · 25 ottobre 2026  
**Obiettivo di sviluppo:** candidata `v0.1.1-alpha` · distribuzione Python `0.1.1a0`  
**Ultimo checkpoint di sviluppo riferito:** `8faf1c6` su `main`, pubblicato su `origin/main`  
**Ultima suite completa di sviluppo riferita:** `1.974 passed` (`python -m pytest -q`, circa 135,21 s)  
**Stato:** documento di continuità e onboarding di terzi; **non** annuncio di release, nuovo audit del codice o certificazione di sicurezza.

> **Gerarchia delle fonti.** Il checkout effettivamente selezionato, i sorgenti, il manifest delle dipendenze, i test e le osservazioni runtime riproducibili prevalgono sul presente libro. I risultati storici non sono test rieseguiti ora. Prima di qualsiasi correzione occorre leggere il codice esistente e i test pertinenti. Le discrepanze vanno registrate, non corrette silenziosamente.

## 0. Come usare il libro

Leggere le sezioni 1–4 per comprendere obiettivo e stato; 5–9 prima di intervenire sul codice; 10–13 per riprendere o creare un branch. **La sezione 14 contiene il messaggio dichiarativo completo da incollare in una nuova chat insieme a questo documento e ai file sorgente pertinenti.** L'Appendice A conserva integralmente il Book 11 originale in italiano, comprensivo dei materiali storici precedenti. L'appendice è archivistica: i checkpoint successivi aggiornano lo stato, senza riscrivere la storia.

**Etichette delle evidenze:** `IMPLEMENTATO` = presente secondo sorgenti esaminati o documentazione storica; `TESTATO` = accompagnato da un checkpoint di test; `VERIFICATO MANUALMENTE` = prova runtime riferita dall'utente; `DECISO` = comportamento richiesto, non necessariamente provato in ogni percorso; `APERTO` = questione non chiusa; `NON ATTESTATO` = non dedurre il supporto. Le categorie non sono intercambiabili.

## 1. Missione, confini e identità del progetto

GarlicSMTP è un'applicazione Python di messaggistica orientata alla privacy con componenti SMTP e IMAP, mailbox e coda di consegna persistenti, trasporto Tor Onion e identità Onion Service propria. Non è un semplice client per provider di posta pubblici. La GUI attuale è **Tkinter**, non PySide6. Il software è source-available con **PolyForm Noncommercial License 1.0.0**, non una licenza open source riconosciuta dall'OSI. È possibile richiedere una licenza commerciale separata; fa fede il `LICENSE` del repository. Copyright © 2026 Giuliano Signorelli. Contatto licenze: `giulisign@gmail.com`. Le licenze delle dipendenze restano autonome.

L'architettura distingue: (a) trasporto Tor e raggiungibilità Onion; (b) cifratura end-to-end e firme; (c) protezione dei dati applicativi salvati; (d) sicurezza operativa di sistema, endpoint e persone. Nessun livello da solo garantisce anonimato, fiducia, disponibilità, cifratura integrale del disco o consegna.

## 2. Provenienza e cronologia dei checkpoint

| Checkpoint | Evidenza e significato |
|---|---|
| 08 ottobre · Book 8 | Baseline narrativa di architettura e metodo; i limiti at-rest di allora sono storici. |
| 13 ottobre · Book 9 | Avanzamento SQLCipher/DEK/recovery; `1.797 passed` riferiti. |
| 18 ottobre · storia Book 10 | `1.830 passed`; recupero password provato in sviluppo. |
| 19 ottobre · Book 10 | `1.844 passed`; baseline applicativa `9bfc2f7`; scambi reali developer ↔ VM Ubuntu con allegati; osservazioni sugli archivi cifrati. |
| 19 ottobre · chiusura Book 11 | Release pubblica `v0.1.0-alpha.1` pre-release riferita, commit `212b9dd`, pacchetto `0.1.0a1`. Le precedenti sezioni del Book 11 che la dicevano in attesa sono superate dal suo aggiornamento di chiusura. |
| Sviluppo successivo `v0.1.1-alpha` | Checkpoint `main` riferito `8faf1c6`, pacchetto `0.1.1a0`, pagina HTML Onion personalizzabile e suite completa `1.974 passed`. **Solo candidata**; nuovo tag e pubblicazione GitHub non confermati. |

Non sommare i conteggi: sono esecuzioni differenti e le suite mirate possono sovrapporsi. La release del Book 11 e la candidata del Book 12 sono milestone distinte. Per `v0.1.1-alpha` non risultano attestati audit indipendente, installazione pulita certificata, upgrade o migrazione.

## 3. Repository, ambienti e igiene dei branch

**Remote canonico:** `https://github.com/giulsign/GarlicSMTP.git`; directory storica di sviluppo: `/mnt/c/garlicsmtp` in Ubuntu WSL, branch `main`. Un collaboratore può avere un checkout diverso: non presumere percorsi o HEAD senza verifica. Ubuntu 24.04 è il target documentato dell'installer e della precedente verifica VM; per il lavoro successivo sono riferite anche prove GUI su VM Ubuntu 22.04. Non significa supporto Windows/macOS nativo o di ogni distribuzione Linux. Requisito Python storico `>=3.12`: controllare `pyproject.toml` corrente.

Vincoli di dipendenza riferiti per `0.1.1a0`: `dnspython>=2.8,<3`, `cryptography>=46,<47`, `sqlcipher3==0.6.3`, build `setuptools>=77`. Verificare la risoluzione effettiva del checkout. `sqlcipher3` mantiene la propria licenza di terza parte, non è automaticamente rilicenziato da PolyForm.

**Comandi iniziali in sola lettura** (dal checkout corretto, non da directory con dati di produzione):

```bash
pwd
git status --short
git branch --show-current
git log -1 --oneline
git remote -v
git diff --check
python --version
python -m pytest -q
```

La suite completa è una verifica da eseguire se appropriata, non un risultato ottenuto durante la stesura. Registrare codice di uscita, numero esatto e durata. Vietati `git add .`, `git reset --hard`, `git clean`, checkout distruttivi e pulizie automatiche. I working tree storici contenevano modifiche non correlate, documenti rimossi, file non tracciati e backup: preservarli. Nessuno staging o commit senza autorizzazione. Non manipolare database reali, chiavi, credenziali di recovery, identità Onion o snapshot VM per verificare un'ipotesi.

**Per un branch di terzi:** registrare prima URL upstream, HEAD, `git status`, metadati del pacchetto e test di baseline; partire da un commit/tag immutabile scelto esplicitamente in un clone/worktree separato **solo dopo aver verificato che modifiche locali e dati privati non vengano toccati**. Definire nome branch, SHA di base e divergenze. Non copiare segreti o stato privato nel fork. Uso e distribuzione restano soggetti a `LICENSE`, avvisi di terze parti ed eventuali autorizzazioni separate: un repository GitHub pubblico non concede automaticamente diritti commerciali illimitati.

## 4. Mappa architetturale e responsabilità

```text
GUI Tkinter / entrypoint CLI supportati
    → autenticazione / setup / sblocco password o recovery
    → DEK di 32 byte disponibile per gli archivi protetti
    → ApplicationViewModel / ApplicationController
    → ApplicationBuilder (composition root)
       ├─ server SMTP → pipeline → Received locale / consegna remota
       ├─ server IMAP → mailbox con autenticazione configurata
       ├─ MailComposerService → firma / routing / preparazione E2EE
       ├─ QueueWorker → TransportManager → OnionTransport → Tor SOCKS5
       ├─ backend SQLCipher Received, Sent e Queue
       └─ AttachmentStore cifrato GSAT v1
```

È una mappa concettuale, non un call graph garantito. Controllare costruttori, call site e test nel checkout. Percorsi storici da ispezionare **solo se pertinenti**: `garlicsmtp/application/builder.py`, `garlicsmtp/gui/application.py`, `garlicsmtp/gui/tk_main_window.py`, `garlicsmtp/gui/tk_compose_section.py`, `garlicsmtp/core/pipeline/`, `garlicsmtp/security/auth/account_credentials.py`, `garlicsmtp/security/encrypted_sqlite.py`, `garlicsmtp/storage/sqlite/backend.py`, `garlicsmtp/queue/sqlite.py`, `garlicsmtp/storage/attachment_store.py`, `garlicsmtp/cli/mailbox.py`, moduli Tor/Onion e relativi `tests/`. Sono indicazioni storiche, non sostituti dell'inventario reale.

**Invio:** composizione → firma Ed25519 → destinazione locale/remota → discovery delle capability e della chiave X25519 con verifica del pin TOFU → cifratura HKDF/ChaCha20-Poly1305 **prima** dell'accodamento persistente → QueueWorker e OnionTransport via Tor → SMTP destinatario. **Ricezione:** accettazione SMTP → decifratura E2EE quando presente → verifica firma → classificazione/store → GUI/IMAP. Retry ed errori non devono alterare l'integrità. Un messaggio in **Sent** è accettato/salvato dall'applicazione locale, **non** una ricevuta di consegna remota. `Retry pending` anticipa l'idoneità al nuovo tentativo, non invia direttamente né certifica la consegna.

**Identità distinte:** Onion Service, firma Ed25519, cifratura X25519. Una firma valida non prova automaticamente la fiducia sociale nel mittente. Un cambio inatteso della chiave pinnata non deve sostituire silenziosamente quella accettata. Il TOFU al primo contatto ha limiti di fiducia intrinseci.

## 5. Protezione at-rest, autenticazione e invarianti di recovery

`IMPLEMENTATO/TESTATO` nei percorsi documentati: Received `data/mailboxes.db`, Sent `data/sent.db` e Queue `state/queue.db` usano SQLCipher con **DEK obbligatoria di 32 byte**; i percorsi standard osservati falliscono chiusi senza fallback SQLite in chiaro. `garlicsmtp/security/encrypted_sqlite.py` storicamente centralizza connessione e chiave SQLCipher. `AttachmentStore` usa GSAT v1 (`GSAT` + byte di versione), nonce di 12 byte e ChaCha20-Poly1305; HKDF-SHA256 deriva una sottochiave allegati dalla DEK e AEAD lega il contesto identificativo. Contenuto e metadati sono protetti nel blob applicativo. Il lettore documentato rifiuta i vecchi formati allegato plaintext.

La password è verificata tramite Scrypt con salt; una KEK derivata dalla password protegge la DEK, mentre il segreto offline di recovery consente di recuperare la **stessa** DEK in modo indipendente. Reset password e sostituzione recovery non devono rigenerare DEK, identità Onion o Ed25519/X25519. Conferma della recovery e comportamento fail-closed della GUI sono invarianti. Le credenziali erano storicamente in `state/account-credentials.json`, con permessi restrittivi e aggiornamenti atomici: verificare codice e semantica del filesystem correnti.

`NON ATTESTATI` come universalmente cifrati: file delle identità private, log, backup, allegati esportati, residui SQLite journal/WAL/temp, cache, tutti i percorsi CLI, integrazioni terze e file arbitrari del sistema. Un header database non-plaintext è solo evidenza corroborante. Gli allegati esportati sono leggibili nella destinazione scelta. Non esiste una procedura certificata di backup/restore o migrazione da archivi legacy plaintext. **Non cancellare database né reinstallare per una password dimenticata: usare il recupero supportato e preservare i dati originali.**

L'audit mirato del Book 11 non trovò bypass della DEK nei percorsi standard esaminati di GUI, builder, Bootstrap e mailbox CLI; **non** copriva ogni backend iniettato. Il Book 11 registra anche una **possibile anomalia funzionale**: la CLI server senza sottocomando potrebbe creare Bootstrap senza DEK. Non esisteva un test riproduttivo dedicato; potrebbe essere legacy/intenzionale e **non** dimostra un bypass della cifratura. Ispezionare e riprodurre prima di trattarla come difetto.

## 6. GUI, ciclo di vita e Tor

La GUI deve restare nascosta finché setup/login e sblocco DEK non riescono. I fallimenti di build devono distruggere la root Tk; la ricezione non deve partire prima dell'autenticazione. Chiudere la GUI deve fermare la ricezione applicativa, mentre Tor di sistema può restare attivo. L'invio asincrono usa un worker thread e polling dei risultati sul thread Tk; deve mostrare gli errori e svuotare i campi soltanto dopo l'accettazione applicativa. Modifiche ai thread richiedono test mirati su race e lifecycle.

Tor è prerequisito di sistema nel profilo validato; endpoint storico Tor Control locale `127.0.0.1:9051` con SAFECOOKIE. L'applicazione gestisce dinamicamente l'Onion Service persistente. La disponibilità locale di Tor **non** garantisce la raggiungibilità di un peer `.onion`. Non rendere il cookie Tor world-readable, non avviare come root, non rigenerare identità Onion per un timeout temporaneo. Dopo modifiche al gruppo `debian-tor` può servire logout/login grafico.

## 7. Novità `v0.1.1-alpha`: pagina HTML Onion facoltativa

L'ultimo checkpoint riferito aggiunge una **pagina HTML di presenza Onion personalizzabile** tramite preferenze GUI. Se attiva, la preferenza deve specificare un percorso non vuoto; la configurazione valida richiede un percorso HTML significativo. Le modifiche richiedono il riavvio dei servizi pertinenti: non presumere hot reload. La pagina non sostituisce SMTP/IMAP né l'identità crittografica Onion. Prima di modificarla esaminare implementazione e test di validazione percorso, abilitazione/disabilitazione, accesso al file, errori e lifecycle. Non pubblicare involontariamente segreti, identificativi personali o risorse esterne. Non è documentato un audit indipendente dell'HTML arbitrario.

La funzione è associata al commit di sviluppo `8faf1c6` e alla suite riferita `1.974 passed`. Non certifica installazione pulita Ubuntu 24.04, upgrade o pubblicazione release. Il file `docs/personalized_html/personalized_html.html` è stato esplicitamente escluso dalla produzione documentale: non copiarlo nell'output e non trattarlo come evidenza esaminata.

## 8. Matrice di validazione e incognite

| Ambito | Evidenza | Limite |
|---|---|---|
| SMTP/IMAP, consegna locale/Onion | test storici e invio/ricezione reale developer/VM | non garantisce ogni rete/peer |
| E2EE, firme e pinning | percorsi implementati e testati riferiti | nessun audit indipendente |
| SQLCipher Received/Sent/Queue | test e osservazioni read-only degli header su developer e VM | non prova cifratura dell'intero disco |
| Allegati GSAT v1 | test sintetici e scambi reali di allegati | export e backup fuori dallo store cifrato |
| Recovery offline | test automatici e prove manuali storiche developer/VM/macchine fisiche | nessun disaster restore certificato |
| GUI Tkinter | test storici login, lifecycle, invio, recovery | packaging e varianti GUI non tutti ricertificati |
| HTML Onion facoltativo | implementazione successiva e suite completa riferita | niente nuova certificazione clean install/upgrade |
| Suite completa di sviluppo | `1.974 passed` nell'ultimo checkpoint riferito | non dichiarare riesecuzione durante Book 12 |
| Windows/macOS nativi | non attestati | vietato dichiararne il supporto |

**Gate release APERTI salvo nuove prove:** tag/release `v0.1.1-alpha` realmente pubblicati, installazione pulita Ubuntu 24.04 con manifest corrente, upgrade/migrazione, backup/restore completo, packaging delle dipendenze su tutti gli host target, audit indipendente e, dove necessario, prova runtime aggiornata della nuova preferenza HTML. Non presentare verifiche storiche come gate della nuova release.

## 9. Metodo rigoroso di sviluppo e revisione

1. **Definire un micro-obiettivo osservabile**, classificandolo come bug, feature, caratterizzazione o documentazione; scrivere criteri di accettazione e limiti.
2. **Leggere prima sorgenti, test e fixture esistenti.** Richiedere solo i file/output pertinenti. Non inventare API o proporre patch basate soltanto sul libro.
3. **Fissare la baseline:** branch/HEAD/status, ambiente, test mirati. Se il comportamento esiste, usare un test GREEN di caratterizzazione, non creare un RED artificiale.
4. **RED quando giustificato:** un test focalizzato che riproduca il comportamento mancante; confermare il fallimento atteso, separando errori ambientali.
5. **GREEN:** modifica minima e localizzata, invarianti di sicurezza/persistenza/consegna intatti. Niente riscritture opportunistiche del core o refactoring estetici.
6. **Verifica:** test mirati → regressioni correlate → suite `python -m pytest -q` al gate pertinente → VM Ubuntu reale solo se cambia il confine interessato. Fermarsi al primo fallimento inatteso.
7. **Revisione:** `git diff --check`, elenco file modificati, comportamento prima/dopo, documentazione e rischi; commit solo con approvazione.
8. **Handoff:** registrare SHA, comandi ed esiti test, questioni aperte, singolo prossimo passo e dichiarazione per la nuova chat.

**Regola di collaborazione dei libri storici:** l'utente applica manualmente modifiche a sorgenti/test e approva esplicitamente le operazioni Git. Fornire diff piccoli e verificabili e comandi copiabili; non eseguire script che riscrivano il repository. Gli artefatti documentali possono essere prodotti separatamente. Un manutentore terzo può scegliere un workflow diverso sul proprio branch autorizzato, ma deve dichiarare la differenza e rispettare licenze, invarianti e standard di prova.

## 10. Lavori aperti e registro decisioni per il prossimo branch

**Stato riferito:** pacchetto `0.1.1a0`, checkpoint codice `8faf1c6`, pagina HTML facoltativa, `1.974 passed`. **Non attestati:** nuova release `v0.1.1-alpha` pubblicata o certificazione completa. Non riaprire automaticamente attività storicamente concluse e non considerare ancora presente un vecchio difetto senza nuova ispezione.

**Primo pacchetto di lavoro consigliato:** inventario read-only del checkout; confronto tra `pyproject.toml`, `garlicsmtp/__init__.py`, manifest installer, preferenze GUI HTML, percorso runtime di serving e test relativi; acquisire baseline mirata; decidere se il prossimo obiettivo è un gate release, un bug riprodotto o una feature separata. Per un branch nuovo concordare prima commit base, nome branch, permessi di licenza, responsabile review e target di test.

**Decisioni da prendere:** (a) pubblicare `v0.1.1-alpha` e su quale SHA esatto? (b) quali versioni Ubuntu supportare dopo i test installer correnti? (c) la CLI server senza sottocomando è supportata o legacy? (d) quale politica backup/restore e migrazione accettare? (e) quale threat model e review di sicurezza richiedere? (f) quale esposizione HTML e quali validazioni sono parte del contratto pubblico? Sono domande, non approvazioni implicite.

## 11. Mappa sorgenti per collaboratori terzi

Partire da `README`, `CONTRIBUTING`, `SECURITY`, `LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES`, `CHANGELOG`, documentazione d'installazione e `pyproject.toml` corrente; leggere i file effettivi, non solo le copie di revisione tradotte. Poi esaminare il sottosistema pertinente. Gruppi tipici: GUI (`garlicsmtp/gui/`, `tests/test_gui_*`), account/DEK (`garlicsmtp/security/auth/`, `garlicsmtp/security/encrypted_sqlite.py`), archivi (`garlicsmtp/storage/`, `garlicsmtp/queue/`), consegna (`garlicsmtp/core/pipeline/`, `garlicsmtp/application/`, moduli trasporto/Tor), installer (`install.sh`, test manifest). Verificare i nomi con `git ls-files`.

Fixture e dati di test devono essere sintetici. Non caricare segreti, messaggi reali, identità `.onion` o database SQLCipher in issue, pull request o chat AI. Distinguere copyright delle dipendenze e licenza del progetto. Documentare esplicitamente modifiche architetturali e impatti di compatibilità.

## 12. Pacchetto di continuità per una nuova chat

**Minimo:** questo Book 12, HEAD e branch esatti, `git status --short`, versione dai file reali, output dell'ultima suite completa e mirata, descrizione del prossimo micro-obiettivo e sorgenti/test pertinenti. **Se necessari:** ultimo diff, log ambiente/installer ripuliti dai segreti, traceback e passi riproducibili. Non allegare indiscriminatamente l'intero repository o dati/credenziali private. Specificare se la nuova sessione può solo consigliare oppure modificare file.

**Prima risposta attesa dall'assistente:** riconoscere la gerarchia delle evidenze; sintetizzare baseline nota e incertezze; richiedere i soli sorgenti/test mirati mancanti prima di suggerire modifiche; scegliere un solo passo. Non presumere accesso alla chat precedente, al checkout locale o al runtime.

## 13. Checklist di passaggio

- [ ] Verificare percorso checkout, branch, HEAD, remote e file modificati/non tracciati.
- [ ] Verificare versioni pacchetto e installer rispetto al commit scelto.
- [ ] Distinguere `v0.1.0-alpha.1` pubblicata da `v0.1.1-alpha` candidata.
- [ ] Registrare quando/dove è stato ottenuto `1.974 passed`; rieseguire solo se opportuno.
- [ ] Definire singolo task, criteri di accettazione e test da leggere.
- [ ] Preservare credenziali, DEK, recovery, identità Onion e chiavi di firma/cifratura.
- [ ] Verificare licenze progetto e terze parti prima di fork/distribuzione.
- [ ] Ottenere consenso esplicito prima di modifiche, commit, tag, release o operazioni distruttive.
- [ ] Aggiornare il libro dopo cambiamenti sostanziali, senza cancellare la storia.

## 14. MESSAGGIO DICHIARATIVO COMPLETO PER UNA NUOVA SESSIONE

> **Copiare il testo seguente in una nuova chat allegando questo Development Book 12. Sostituire i campi tra parentesi quadre con osservazioni reali; non indovinare.**

```text
INIZIO NUOVA SESSIONE DI SVILUPPO GARLICSMTP — DICHIARAZIONE

Sto riprendendo lo sviluppo di GarlicSMTP (https://github.com/giulsign/GarlicSMTP.git).
Allego GarlicSMTP Development Book 12 come riferimento di continuità, non come sostituto della lettura del codice attuale.

CONTESTO STORICO E CORRENTE
- Milestone storica pubblicata secondo Book 11: v0.1.0-alpha.1, commit release 212b9dd, pacchetto 0.1.0a1; baseline applicativa 9bfc2f7.
- Obiettivo successivo: candidata v0.1.1-alpha, pacchetto 0.1.1a0; ultimo commit main/origin/main riferito 8faf1c6.
- Ultima suite completa di sviluppo riferita: 1.974 passed. Resta evidenza storica finché non viene rieseguita in questa sessione.
- La nuova fase include pagina HTML Onion personalizzabile nelle preferenze Tkinter, con validazione del percorso se abilitata e necessità di riavvio.
- Questo libro non attesta tag/release v0.1.1-alpha pubblicati, audit indipendente, clean install, upgrade o migrazione certificati.

ARCHITETTURA E INVARIANTI
- Applicazione Python SMTP/IMAP; trasporto Tor Onion; identità Onion, Ed25519 e X25519 distinte; E2EE prima dell'enqueue remoto; coda persistente e retry.
- SQLCipher per Received/Sent/Queue e GSAT v1 per allegati con DEK applicativa entro i confini documentati.
- Password e recovery offline proteggono la stessa DEK. Recupero/reset devono preservare chiavi, identità e dati. Fallire chiusi senza DEK valida.
- GUI Tkinter. Setup/login prima della ricezione; Sent non prova la consegna remota; Retry pending non è ricevuta di consegna.
- Non dichiarare anonimato assoluto, cifratura di ogni file, sicurezza certificata o supporto Windows/macOS nativo.

REGOLE DI LAVORO
- PRIMA ispezionare sorgenti e test esistenti pertinenti; nessuna patch speculativa.
- Un micro-obiettivo osservabile per volta: RED mirato se difetto dimostrato, GREEN minimo, regressioni e suite completa al gate pertinente.
- L'utente applica manualmente le modifiche ai sorgenti e approva le operazioni Git; vietate riscritture automatiche, git add ., reset, clean o operazioni distruttive.
- Preservare modifiche non correlate del working tree, dati reali, recovery e identità Onion. Non richiedere segreti.
- Distinguere i test dei checkpoint storici da quelli realmente eseguiti in questa sessione.

CHECKOUT ATTUALE — COMPILARE CON COMANDI REALI
Percorso checkout: [DA VERIFICARE]
Branch / HEAD / remote: [DA VERIFICARE]
Git status compresi file non tracciati: [DA VERIFICARE]
Versioni Python e pacchetto: [DA VERIFICARE]
Ultimi comandi/esiti test mirati e completi: [DA VERIFICARE]
Prossimo singolo obiettivo e criteri di accettazione: [DA DECIDERE]
Permessi per modifiche e operazioni Git: [DA CONFERMARE]

TUA PRIMA AZIONE
Conferma contesto e lacune delle evidenze. Chiedi il minimo insieme di sorgenti, test e output read-only necessari a valutare l'obiettivo scelto. Non modificare, rifattorizzare, fare staging, commit, tag o pubblicare prima di aver letto l'implementazione e ottenuto autorizzazione esplicita.

FINE DICHIARAZIONE NUOVA SESSIONE
```

## Appendice A — Book 11, testo originale italiano di archivio

Segue il testo integrale originale, conservato senza alterazioni come fonte storica. Include le appendici precedenti. Le dichiarazioni legate ai checkpoint, incluso l'aggiornamento di chiusura, mantengono la loro data e non prevalgono sullo stato successivo del Book 12.

---

```text
AGGIORNAMENTO DI CHIUSURA — RELEASE PUBBLICATA (19 OTTOBRE 2026)
==============================================================================
STATO CORRENTE VERIFICATO: MILESTONE v0.1.0-alpha.1 CONCLUSA.
La pagina pubblica GitHub conferma la release
"GarlicSMTP v0.1.0-alpha.1 — First Official Alpha" marcata "Pre-release".
URL: https://github.com/giulsign/GarlicSMTP/releases/tag/v0.1.0-alpha.1
Tag: v0.1.0-alpha.1; commit di release: 212b9dd;
versione Python: 0.1.0a1; baseline applicativa: 9bfc2f7.
La pagina elenca funzionalità, validazioni, limiti Alpha e documentazione.
Non risulta attestata una nuova validazione installer o una certificazione
indipendente della sicurezza. Gli asset visualizzati da GitHub sono quelli
della pagina pubblica; non attestiamo build binarie o pacchetti aggiuntivi.
Il README e il CHANGELOG congelati nel tag dichiaravano correttamente,
all'epoca della loro stesura, la pubblicazione non ancora confermata:
sono affermazioni storiche ora superate, non errori da riscrivere nel tag.
Le sezioni del Book 11 che indicano la release come non confermata o da
decidere descrivono il checkpoint PRECEDENTE a questa verifica.
Nessun nuovo commit, tag, test o cambiamento al codice è stato effettuato
per questo aggiornamento documentale esterno al repository.
Prossima decisione: eventuale milestone successiva, distinta dalla alpha.

GARLICSMTP
DEVELOPMENT BOOK 11 — EDIZIONE ITALIANA
Storia dello sviluppo, stato verificato, decisioni e guida alla continuità
Checkpoint: 19 ottobre 2026
Versione di riferimento: v0.1.0-alpha.1
Stato: documento di continuità, NON attestazione di release pubblicata

NOTA EDITORIALE
Questa edizione aggiorna il Development Book 10 senza riscrivere retroattivamente
le attestazioni storiche. La nuova parte iniziale prevale per lo stato corrente;
il Book 10 integrale è conservato in appendice, inclusi i Book 9 e 8 che esso
già incorpora. Codice e test reali prevalgono sempre sui documenti.

INDICE
1. Sintesi esecutiva
2. Baseline e stato Git
3. Funzionalità e prove reali
4. Protezione dei dati a riposo
5. Recovery e autenticazione
6. Audit mirato dei percorsi alternativi
7. Evidenze di test e limiti
8. Anomalia CLI da registrare
9. Roadmap aggiornata
10. Metodo operativo e vincoli
11. Messaggio di ripresa
Appendice A: Development Book 10 integrale (con appendici storiche)

==============================================================================
1. SINTESI ESECUTIVA
==============================================================================
GarlicSMTP ha una baseline alpha funzionante. L'utente ha confermato scambi
reali di messaggi e allegati fra ambiente developer, macchine virtuali e
macchine reali; prove di recovery nei medesimi ambienti; connessione,
disconnessione e invii verso indirizzi errati. Queste prove non devono essere
ripetute senza un cambiamento pertinente o un difetto osservabile.

L'audit mirato dei percorsi standard che ricevono e propagano la DEK è stato
concluso con esito positivo entro il perimetro effettivamente ispezionato.
Nessun bypass della DEK è stato individuato. Non è un audit crittografico
indipendente né una certificazione di ogni file sensibile su disco.

==============================================================================
2. BASELINE E STATO GIT
==============================================================================
Versione concordata: v0.1.0-alpha.1.
HEAD e origin/main riportati nell'ultima verifica di questa conversazione:
212b9dd — docs: prepare v0.1.0-alpha.1 release documentation.
Il tag Git v0.1.0-alpha.1 risulta creato. Non è stata confermata una
GitHub Release pubblicata; non confondere tag e pubblicazione.

La baseline di codice applicativo precedentemente verificata sulla VM era
9bfc2f7; il commit 212b9dd è documentale. Non attribuire nuove prove runtime
al commit documentale senza evidenza specifica.

Working tree non pulito, con modifiche non correlate: test
tests/test_install_manifest.py modificato, vecchi documenti rimossi,
documenti non tracciati, file 'None' e backup di attachment_store.
Conservare tutto. Vietati reset/clean/checkout distruttivi, git add . e
qualsiasi operazione Git non espressamente autorizzata.

==============================================================================
3. FUNZIONALITÀ E PROVE REALI
==============================================================================
Conferme dirette dell'utente:
- invio e ricezione fra VM e macchine reali;
- messaggi con allegati;
- recovery su developer, VM e macchine reali;
- connessione e disconnessione;
- invio verso indirizzi errati.
Le prove di invio/ricezione developer ↔ Ubuntu VM, self-send e allegati
erano già documentate nel Book 10. Non inventare conteggi di messaggi,
sistemi operativi aggiuntivi o protocolli non dichiarati.
Il core SMTP/IMAP/Tor/E2EE, la pipeline e la semantica di consegna
rimangono congelati salvo difetto concreto e riproducibile.

==============================================================================
4. PROTEZIONE DEI DATI A RIPOSO
==============================================================================
I tre database persistenti applicativi Received, Sent e Queue usano SQLCipher
con DEK obbligatoria di 32 byte nei percorsi standard esaminati.
AttachmentStore usa il formato cifrato GSAT v1 con AEAD e metadati protetti,
come documentato nel Book 10.
Non dichiarare che identità private, cache, backup, log, file temporanei
e ogni artefatto secondario siano tutti cifrati: il perimetro di prova
è più stretto. La verifica degli header dei database è corroborante,
non una dimostrazione crittografica autonoma.

==============================================================================
5. RECOVERY E AUTENTICAZIONE
==============================================================================
La password e la recovery key offline proteggono tramite wrapping separati
la stessa DEK; il recupero non deve rigenerare DEK o identità.
L'utente ha confermato prove pratiche di recovery su developer, VM e macchine
reali. Il codice GUI ispezionato esegue login/setup prima di costruire il
ViewModel; rifiuta valori diversi da bytes di 32 byte, distrugge il root
in caso di annullamento/fallimento e rende visibile la finestra solo
dopo il build riuscito.

==============================================================================
6. AUDIT MIRATO DEI PERCORSI ALTERNATIVI
==============================================================================
CLI mailbox:
- sblocco con credenziali tramite unlock_dek_with_password;
- DEK passata allo store SQLite;
- senza DEK il percorso termina senza aprire lo store.

Bootstrap:
- build_context rifiuta DEK mancante o non valida prima del build.

ApplicationBuilder:
- build rifiuta DEK mancante/non valida;
- backend Received e Queue standard ricevono dek=self.dek;
- AttachmentStore riceve dek=self.dek;
- la pipeline SMTP è collegata a store e queue costruiti dal builder.

GUI:
- run_gui parte con finestra nascosta;
- il login o setup precede build_view_model;
- build_view_model verifica la DEK e la passa al builder e al database Sent;
- ApplicationViewModel.start delega a ApplicationController.start,
  che avvia context.runtime e il relativo thread;
- non è emerso un avvio SMTP pre-login nel percorso ordinario ispezionato.

Il parametro opzionale authenticate di run_gui compare nei test e permette
di fornire un autenticatore alternativo; la DEK restituita è comunque
validata. I backend iniettati sono punti di estensione/test: non è stato
dimostrato un bypass, ma neppure eseguito un audit esaustivo di integrazioni
esterne arbitrarie. Non creare patch preventive.

Conclusione limitata e precisa: nessun bypass della DEK riscontrato nei
percorsi standard esaminati; audit mirato chiuso, audit generale non implicato.

==============================================================================
7. EVIDENZE DI TEST E LIMITI
==============================================================================
- Suite completa developer del checkpoint Book 10: 1844 passed
  (storica, non rieseguita in questa conversazione).
- Test CLI/Bootstrap focalizzati eseguiti in questa conversazione:
  23 passed.
- Test GUI/ApplicationBuilder/Bootstrap eseguiti successivamente:
  120 passed, comunicati dall'utente.
I gruppi possono sovrapporsi: NON sommare 23 + 120 come numero di test
unici e NON presentare 1844 come una suite rieseguita oggi.
L'esame del codice è stato statico e mirato, con riscontri dai test.
Le prove reali sono conferme dell'utente, distinte dall'esecuzione pytest.

==============================================================================
8. ANOMALIA CLI DA REGISTRARE
==============================================================================
L'entrypoint CLI senza sottocomando richiama run_server(), che costruisce
Bootstrap() senza DEK. Poiché Bootstrap.build_context() rifiuta DEK assente,
questo percorso appare incapace di avviare il server: possibile difetto
funzionale fail-closed, NON bypass della cifratura.
Non è stato eseguito un test riproduttivo dedicato di questo specifico
percorso né verificato se sia legacy/intenzionale. Nessuna correzione
approvata; valutare solo se il percorso è un requisito di prodotto.

==============================================================================
9. ROADMAP AGGIORNATA
==============================================================================
1) Ubuntu VM e scambi reali E2E: CONCLUSI nei confini documentati.
2) Cifratura at-rest dei tre DB e allegati: VERIFICATA nei confini dichiarati.
3) Audit accessi alternativi DEK: CHIUSO per i percorsi standard esaminati.
4) Continuità documentale: Book 11 italiano e inglese preparati.
5) Nuova funzionalità: NON DEFINITA, separata dalla baseline congelata.
6) Pubblicazione finale/GitHub Release: DECISIONE ESPLICITA ANCORA NECESSARIA.
7) Anomalia CLI server senza DEK: ANNOTATA, non priorità di sicurezza.
Migrazione di dati preesistenti e nuova validazione dell'installer non sono
riaperte automaticamente: erano escluse dalla roadmap concordata.
Nessuna attività di modifica del codice è necessaria per chiudere il Book 11.

==============================================================================
10. METODO OPERATIVO E VINCOLI
==============================================================================
Prima di qualsiasi modifica leggere sorgente, test e fixture reali.
Un solo difetto riproducibile alla volta; RED solo se appropriato e
osservato, GREEN minimo, test mirati, regressioni e full pytest ai gate
rilevanti. Characterization GREEN se il comportamento esiste già.
L'utente esegue manualmente ogni modifica al sorgente e decide i commit.
Non generare script di riscrittura automatica del repository.
Non toccare database, credenziali, recovery key, identità, backup o VM.
Non richiedere nuovi E2E reali senza una modifica pertinente.
Preservare il working tree e le modifiche non correlate.

==============================================================================
11. MESSAGGIO DI RIPRESA PER UNA NUOVA CHAT
==============================================================================
«Sto proseguendo GarlicSMTP dalla milestone v0.1.0-alpha.1.
L'ultimo HEAD confermato in chat è 212b9dd su main/origin/main e il tag
v0.1.0-alpha.1 è stato creato; GitHub Release non confermata.
La baseline applicativa collaudata era 9bfc2f7.
L'utente ha confermato invio/ricezione e allegati fra VM e macchine reali,
recovery su developer/VM/reali, connessione/disconnessione e invii a
indirizzi errati. Non ripetere queste prove senza necessità tecnica.
Suite completa storica: 1844 passed; nella chat dell'audit: 23 passed
e poi 120 passed in gruppi focalizzati, non necessariamente disgiunti.
L'audit mirato DEK dei percorsi standard CLI mailbox, Bootstrap, builder
e GUI non ha individuato bypass; resta annotato un possibile difetto
funzionale CLI server senza DEK, non corretto.
Non dichiarare cifrati tutti i dati su disco né certificare backend
esterni arbitrari. Il working tree contiene modifiche non correlate da
preservare. Prima di proporre codice leggere sorgenti e test REALI.
Nessuna modifica automatica. La prossima decisione è pubblicare la
release alpha o definire una nuova milestone, senza riaprire il core
già collaudato.»


==============================================================================
APPENDICE A — DEVELOPMENT BOOK 10 INTEGRALE, DOCUMENTO STORICO
==============================================================================

GARLICSMTP
STORIA DELLO SVILUPPO, METODO DI LAVORO E GUIDA ALLA CONTINUITÀ
Development Book — edizione 10, 19/10/2026
VERSIONE DI RIFERIMENTO: v0.1.0-alpha.1
BASELINE CODICE: 9bfc2f7 — main / origin/main

NOTA DI CONTINUITÀ
Questa edizione segue il Development Book 9 (13/10), che a sua volta incorpora integralmente l'8 (08/10). Il testo storico viene conservato in appendice senza riscrivere retroattivamente date, limiti o conteggi. I checkpoint 1797, 1830 e 1844 rappresentano momenti diversi. Le attestazioni più recenti prevalgono sullo stato di implementazione, ma non trasformano test locali in audit di sicurezza indipendente.

INDICE DELL'EDIZIONE 10
1. Dalla ripresa 9 al checkpoint 19 ottobre
2. Il completamento della protezione at-rest nei perimetri implementati
3. Recupero password e continuità della DEK
4. Invio GUI asincrono e diagnostica della pipeline
5. Verifica reale bidirezionale developer / VM
6. Inventario della protezione read-only
7. Ingressi alternativi e audit non concluso
8. Baseline Git, freeze e integrità dei dati
9. Roadmap approvata e attività escluse
10. Metodologia TDD e regole operative
11. Istruzioni di ripresa per nuova chat
APPENDICE: Development Book 9 integrale (stato 13/10/2026)

==============================================================================
1. DALLA RIPRESA 9 AL CHECKPOINT 19 OTTOBRE
==============================================================================

Il Book 9 fotografava 1797 test superati e l'implementazione di DEK/SQLCipher/recovery, ma lasciava da verificare gli allegati e la VM. Un checkpoint intermedio al 18/10 registra 1830 test superati e il recupero password verificato manualmente nell'ambiente di sviluppo. Nel ramo successivo è stato completato il percorso degli allegati cifrati e corretto un difetto reale nell'invio dalla GUI. L'ultima suite completa developer riportata è `1844 passed` in circa 124,45 secondi. Non affermare che questa suite sia stata eseguita nuovamente durante la redazione del Book 10.

La baseline del codice applicativo consolidata è `9bfc2f7` (`fix: improve GUI sending and pipeline diagnostics`), successiva a `5aa5f8c` (`feat: complete encrypted storage and account recovery milestone`). Il commit 9bfc2f7 è stato pubblicato su origin/main e usato nella verifica della VM. La denominazione di release approvata è v0.1.0-alpha.1; non risulta ancora una conferma di creazione del tag Git, della GitHub Release o dell'allineamento di tutti i metadati di distribuzione.

==============================================================================
2. PROTEZIONE AT-REST: CONFINI REALMENTE IMPLEMENTATI
==============================================================================

Tre database persistenti applicativi:
- `~/.local/share/garlicsmtp/data/mailboxes.db` — Received;
- `~/.local/share/garlicsmtp/data/sent.db` — Sent;
- `~/.local/share/garlicsmtp/state/queue.db` — Queue.

`garlicsmtp/security/encrypted_sqlite.py` centralizza la connessione SQLCipher: DEK obbligatoria di 32 byte, `PRAGMA cipher_version` verificato, chiave applicata tramite `PRAGMA key`, `temp_store=MEMORY` e interrogazione di `sqlite_master` per fallire chiuso in caso di DB non apribile. `garlicsmtp/storage/sqlite/backend.py` e `garlicsmtp/queue/sqlite.py` usano questa connessione. Non sono emerse chiamate `sqlite3.connect` nel package durante l'ispezione dichiarata.

Il composition root `ApplicationBuilder` passa la DEK a Received, Queue e AttachmentStore; `garlicsmtp/gui/application.py` la passa al backend Sent e agli allegati. Non confondere questa verifica statica con un audit esaustivo di tutti i percorsi runtime.

L'archivio allegati `garlicsmtp/storage/attachment_store.py` usa `GSAT` + versione `01`, nonce di 12 byte e ChaCha20-Poly1305. Una sottochiave di 32 byte è derivata dalla DEK tramite HKDF-SHA256 con info `GarlicSMTP attachment storage v1`. Il JSON di metadata (`filename`, `declared_mime`, `content_length`) e il contenuto sono cifrati insieme. L'AAD lega `message_id`, `attachment_id` e header. I file sono identificati da UUID opachi con estensione `.gsat`; il lettore rifiuta i vecchi `.bin/.json` in chiaro. Test correlati: contenuto/metadati cifrati, DEK errata, spostamento di ciphertext, legacy rifiutato e riapertura persistente.

==============================================================================
3. RECOVERY E CONTINUITÀ DELLA DEK
==============================================================================

La DEK non dipende direttamente dalla password. Password e recovery key offline permettono di sbloccare la stessa chiave dati attraverso wrapping distinti. Il recupero della password e la rotazione della recovery key devono preservare database, allegati, chiavi Ed25519/X25519 e Onion identity. L'implementazione documentata in Book 9 prevede conferma esplicita della recovery, scritture atomiche, lock e fsync; gli errori prima/dopo `os.replace` sono coperti da test che preservano la semantica corretta del commit.

La GUI Tkinter mantiene la finestra ritirata durante setup/login e prima del build del view model. Se lo sblocco fallisce, il root viene distrutto e non parte la ricezione. Il recupero password è stato verificato manualmente in development; non dichiarare una prova di disaster recovery o una nuova installazione pulita con ripristino su VM.

==============================================================================
4. INVIO GUI ASINCRONO E DIAGNOSTICA DELLA PIPELINE
==============================================================================

Un difetto reale impediva o rendeva inaffidabile il percorso di invio dalla GUI pur in presenza di test positivi del backend. Il fix usa un worker thread per la spedizione, una coda di risultati e polling Tk per aggiornare la GUI sul thread corretto; durante l'operazione i controlli pertinenti sono disabilitati e la chiusura è gestita per evitare corse. Gli errori sono presentati all'utente; i campi della composizione vengono svuotati soltanto se l'invio è stato accettato. La pipeline e il logger espongono meglio inizio lavorazione, rifiuti ed errori senza alterare la semantica di consegna.

Il commit 9bfc2f7 contiene esattamente: `garlicsmtp/core/pipeline/logger.py`, `garlicsmtp/core/pipeline/pipeline.py`, `garlicsmtp/gui/application.py`, `garlicsmtp/gui/tk_compose_section.py`, `garlicsmtp/gui/tk_main_window.py`, `tests/test_gui_application.py`, `tests/test_gui_tk_compose_section.py`, `tests/test_gui_tk_main_window.py`, `tests/test_mail_composer.py`, `tests/test_pipeline.py`.

==============================================================================
5. VERIFICA REALE BIDIREZIONALE DEVELOPER / VM
==============================================================================

Con codice allineato al commit 9bfc2f7 l'utente ha confermato: self-send developer riuscito; self-send Ubuntu VM riuscito; invio developer → VM riuscito; invio VM → developer riuscito; allegati spediti correttamente. Queste sono verifiche runtime reali riferite dall'utente, distinte dai test pytest. La VM è Ubuntu 24.04 in VirtualBox, con dati e identità reali da preservare. Non richiedere di ripetere invii già validati senza un cambiamento pertinente.

==============================================================================
6. INVENTARIO READ-ONLY DEI DATI CIFRATI
==============================================================================

Developer: Received 45056 byte, Sent 45056 byte, Queue 12288 byte; intestazione SQLite plaintext `SQLite format 3\x00` assente in tutti e tre. La VM ha restituito `NO` per la stessa firma su tutti e tre i DB. Il solo header non prova da sé la robustezza crittografica, ma corrobora l'uso SQLCipher e i test.

Su entrambi gli ambienti la directory allegati contiene un file osservato di 327 byte con prefisso e versione `GSAT v1` corretti. Non è stata eseguita decrittazione dei file reali per non accedere inutilmente ai contenuti privati. I test sintetici attestano le proprietà del formato. Nessuna operazione distruttiva o migrazione è stata compiuta.

==============================================================================
7. ACCESSI ALTERNATIVI: AUDIT AVVIATO, NON CHIUSO
==============================================================================

L'ispezione del package ha individuato `SQLiteMessageStoreBackend` in GUI, Bootstrap, CLI e ApplicationBuilder, `SQLiteQueueBackend` nel builder e `AttachmentStore` in GUI/builder. Tutti i call site osservati passano `dek=`. `Bootstrap.build_context()` rifiuta DEK mancante/non valida; `garlicsmtp/cli/mailbox.py` richiede DEK come parametro per costruire lo store. `connect_encrypted_sqlite` è l'unico punto SQLCipher osservato; nessun accesso plaintext SQLite emerso dalla ricerca effettuata.

Restava da verificare in modo mirato il cablaggio degli entrypoint reali, la modalità con cui la CLI ottiene la DEK, la gestione di backend iniettati, l'autenticazione GUI e la ricezione SMTP. Il checkpoint non contiene la chiusura formale di questo audit. Non creare test o modifiche preventive senza un percorso di bypass riproducibile.

==============================================================================
8. FREEZE DELLA BASELINE E IGIENE GIT
==============================================================================

Il freeze concordato usa `v0.1.0-alpha.1` e il commit `9bfc2f7`. Lo stato pubblicato di `main` è noto dal checkpoint; NON sono attestati il tag `v0.1.0-alpha.1` né una release GitHub. Non attribuire al freeze documentale un effetto sul repository che non sia stato eseguito.

Working tree di sviluppo con modifiche non correlate da conservare: cancellazioni di vecchi file docs, file `None`, nuovi documenti e un backup `garlicsmtp/storage/attachment_store - Copia.py.backup`. Non usare `git add .`, cleanup automatici, reset, checkout distruttivi o comandi che tocchino dati reali. Un futuro tag/release richiede consenso esplicito, controllo di `git status` e verifica della versione dichiarata nei metadati.

==============================================================================
9. ROADMAP APPROVATA ED ESCLUSIONI
==============================================================================

1) Validazione Ubuntu VM e invio/ricezione E2E: CONCLUSA.
2) Verifica cifratura a riposo sui due ambienti: CONCLUSA entro i confini read-only e testati.
3) Chiusura audit degli accessi alternativi: AVVIATA, non attestata conclusa.
4) Snapshot/documentazione di continuità per nuova chat: presente edizione 10.
5) Nuova idea funzionale: da definire in una fase separata dalla baseline congelata.
6) Release finale: successiva alle decisioni esplicite dell'utente.

Esclusi dal lavoro concordato: migrazione dei dati preesistenti e nuova validazione di installer/dipendenze/disinstallazione, già trattati in milestone storiche. L'esclusione non equivale a una garanzia che quei confini siano stati collaudati nuovamente con ogni build.

==============================================================================
10. METODOLOGIA TDD E REGOLE OPERATIVE
==============================================================================

Prima di proporre modifiche: leggere sorgenti E test reali. Un solo problema osservabile alla volta; RED focalizzato e fallimento confermato; GREEN minimo; test mirati; regressioni; full pytest; validazione Ubuntu VM quando il confine cambia. Se il comportamento esiste già, characterization test GREEN senza inventare un RED. Fermarsi al primo fallimento inatteso. Nessun refactoring cosmetico e nessuna riscrittura del core SMTP/IMAP/Tor/E2EE senza prova di difetto.

L'utente applica manualmente ogni modifica al sorgente. Non proporre script o comandi che modificano automaticamente file sorgente/test. Consentiti comandi read-only, test e operazioni Git esplicitamente autorizzate. Non toccare database, credenziali, recovery key, identità, backup o VM senza permesso. La documentazione può essere redatta come artefatto separato, senza modificare il repository.

==============================================================================
11. ISTRUZIONI DI RIPRESA PER UNA NUOVA CHAT
==============================================================================

«Riprendiamo GarlicSMTP dalla baseline v0.1.0-alpha.1, commit 9bfc2f7 su main/origin/main. Suite developer: 1844 passed. Scambi reali developer ↔ Ubuntu VM e allegati: riusciti. Database Received, Sent, Queue SQLCipher e allegati GSAT v1 verificati nei confini documentati. Audit CLI/bootstrap/GUI/ricezione iniziato ma non dichiarato concluso. Tag Git/release non ancora creati. Mantieni TDD stretto: prima leggi sorgente e test reali; niente patch speculative né modifiche automatiche dei file. Preserva tutti i dati reali e le modifiche Git non correlate. La prossima idea funzionale va progettata separatamente, senza alterare la baseline congelata.»

==============================================================================
APPENDICE STORICA — DEVELOPMENT BOOK 9, EDIZIONE 13/10/2026
(Testo integrale preservato. Le affermazioni superate sono storicamente datate.)
==============================================================================

GARLICSMTP
STORIA DELLO SVILUPPO, METODO DI LAVORO E GUIDA ALLA CONTINUITÀ
Development Book — edizione 9, aggiornamento al 13 ottobre 2026

NOTA DI VERSIONE
Questa edizione conserva integralmente la revisione narrativa 8 come testimonianza storica e aggiunge il nuovo checkpoint 13/10/2026. Ogni affermazione «at-rest/recovery non implementata» nella versione 8 è valida per il suo checkpoint (08/10), NON per il ramo successivo. La versione 9 distingue SQLCipher/DEK/recovery implementati e testati localmente dalla cifratura integrale ancora da validare. Fonte di verità: working tree e test reali, non questo libro.

INDICE DELL'AGGIORNAMENTO
- Sezioni di aggiornamento: cifratura at-rest, DEK e SQLCipher; recovery offline; hardening Tk; checkpoint 1797 passed; roadmap
- Messaggio iniziale aggiornato al 13/10/2026
- Appendice: testo integrale della versione 8 preservato


6. OBIETTIVO AT-REST E DISTINZIONE DEI PERIMETRI

Obiettivo approvato: cifrare realmente i dati persistenti senza confondere cifratura E2EE del wire e protezione del disco. DEK casuale indipendente da password e recovery; password-derived KEK e recovery-derived KEK proteggono la stessa DEK. Reset della password non deve rigenerare DEK o perdere messaggi/identità. La recovery key offline è un mezzo di recupero, non un login alternativo ordinario.
Al checkpoint dell’08/10, mailboxes.db, sent.db, queue.db e allegati erano descritti come plaintext. Nel ramo successivo risultano implementati gli accessi SQLCipher obbligatori per message store e queue e la gestione DEK/recovery; questo NON dimostra che AttachmentStore, file .bin/.json, chiavi private, backup, WAL/SHM/journal/temp, cache o vecchi archivi plaintext siano stati migrati/protetti integralmente. Non dichiarare S1–S7 completati senza prova per ogni perimetro. In particolare, la persistenza delle chiavi Onion/Ed25519/X25519 e l’esportazione degli allegati richiedono un’analisi separata.

7. API E PERCORSI EFFETTIVAMENTE DISCUSSI NEL RAMO CORRENTE

garlicsmtp/security/auth/account_credentials.py: AccountCredentialStore.create(username,password), authenticate, enable_recovery(username,password,recovery_key), confirm_recovery(username), unlock_dek_with_password, unlock_dek_with_recovery, reset_password_with_recovery, replace_unconfirmed_recovery(username,password,new_recovery_key). La recovery è registrata inizialmente come recovery_confirmed=False; la conferma viene resa persistente con aggiornamento atomico. La sostituzione di recovery non confermata preserva la DEK. La sostituzione credenziali usa lock di thread, flock, replace atomico e fsync di file/directory. AtRestKeyManager.generate_recovery_key() produce 64 caratteri esadecimali (32 byte rappresentati in hex).
garlicsmtp/storage/sqlite/backend.py: SQLiteMessageStoreBackend(path, *, dek:bytes); garlicsmtp/queue/sqlite.py: SQLiteQueueBackend(path, *, dek:bytes); ApplicationBuilder(..., dek=...), Bootstrap(..., dek=...). La DEK richiesta è di 32 byte; nessun fallback intenzionale a SQLite plaintext. Non dedurre da queste firme che tutte le chiamate CLI/installer siano state collaudate in produzione.
garlicsmtp/gui/application.py: build_view_model(*, paths=None, dek:bytes); setup_application_dek(*,paths,username,password,show_recovery) crea account e recovery, confermando solo se la callback restituisce True. unlock_application_dek(*,paths,prompt,invalid_credentials=None,show_recovery=None) sblocca via password; se la recovery non è confermata, può sostituirla e richiederne la conferma; in assenza di callback valida fallisce chiuso. run_gui usa Tkinter e collega show_recovery_key(..., master=root). garlicsmtp/gui/tk_authentication.py: RecoveryDialog modale con conferma esplicita. I dettagli sono quelli letti nel ramo precedente, da verificare di nuovo nel checkout prima di scrivere codice.

8. HARDENING TDD ESEGUITO IN QUESTO RAMO

I test aggiunti/confermati comprendono: test_gui_resume_recovery_dialog_error_preserves_dek (errore callback: recovery non confermata, DEK invariata); test_gui_resume_recovery_confirmation_failure_preserves_dek (errore prima di os.replace: stato non confermato, DEK invariata); test_confirm_recovery_directory_fsync_failure_keeps_new_state (errore fsync directory dopo os.replace: stato confermato visibile, DEK invariata); test_gui_resume_recovery_directory_fsync_failure_blocks_unlock (GUI non ignora errore fsync, DEK invariata). Questi test distinguono la fase prima/dopo il punto di commit atomico e impediscono false assunzioni sulla rollback semantics.
Successivi RED/GREEN: test_run_gui_destroys_root_when_dek_unlock_raises (pulizia root sul login fallito); test_run_gui_destroys_root_when_first_setup_raises_oserror (pulizia su errore I/O setup); test_run_gui_destroys_root_when_first_setup_raises_runtime_error (pulizia su eccezione generica setup). Patch minime: try/except Exception, root.destroy(), raise nei rami di autenticazione/setup. Checkpoint di tre moduli 128 passed, riferito dall’utente.
Ultimo RED: test_run_gui_destroys_root_when_view_model_build_fails; il fallimento reale mostrava events=[withdraw,deiconify,build] anziché destroy. GREEN minimo nel run_gui: try/except Exception attorno a build_view_model con root.destroy() e raise, spostando root.deiconify() dopo il build riuscito. Il test mirato è passato (1 passed). La regressione iniziale ha mostrato 127 passed e 2 failure nei test che aspettavano il vecchio ordine: test_run_gui_default_login_unlocks_dek_before_build e test_run_gui_first_setup_creates_dek_and_confirms_recovery. Le asserzioni di ordine sono state aggiornate per aspettarsi build prima di deiconify. L’utente ha confermato 129 passed nelle tre suite; poi ha eseguito pytest -q --tb=short sull’intero progetto, riferendo 1797 passed. Nessuna prova di test falliti residui è stata comunicata.
Non trasformare questi conteggi in una attestazione di installazione reale: tutti i 1797 test sono un checkpoint della suite locale comunicato dall’utente.

9. COMPORTAMENTO GUI E CICLO DI VITA

run_gui inizializza Tk root, la ritira con withdraw e carica l’icona; se le credenziali esistono sblocca la DEK tramite login e callback di recovery, altrimenti avvia setup con controllo della conferma password. Cancel o autenticazione senza DEK valida chiudono root. Errori inattesi di login/setup distruggono root e vengono rilanciati. Una DEK mancante o diversa da bytes di lunghezza 32 produce errore senza avviare la finestra. Solo dopo il successo di build_view_model viene chiamato deiconify, quindi si costruisce MainWindow e si entra in mainloop. Il test RED dell’ultimo ciclo garantisce che, se build fallisce, la finestra non venga mostrata e root venga distrutta.
La GUI deve continuare a richiedere login/setup prima dell’avvio ricezione; la chiusura deve fermare la ricezione, mentre Tor di sistema può restare attivo. Non introdurre un daemon unattended o accesso diretto agli archivi senza sblocco. Per la recovery, la chiave va mostrata con conferma esplicita; la sua disponibilità in codice non è di per sé prova di un collaudo UX manuale completo.

10. EVIDENZE, LIMITI E DOMANDE APERTE

CONFERMATO DAL RAMO: suite completa 1797 passed; tre suite correlate 129 passed; codice SQLCipher/DEK/recovery riferito e testato in WSL; cleanup root e ordine GUI verificati con test. NON CONFERMATO: nuovo HEAD/commit, git status pulito, collaudo SQLCipher end-to-end su installazione Ubuntu 24.04, migrazione di archivi plaintext esistenti, protezione completa allegati e residui, backup/ripristino, recovery offline su VM, packaging nativo SQLCipher su VM, funzionalità Windows/macOS, audit indipendente. Non dichiarare «cifratura integrale a riposo completata» o «prodotto pronto per rilascio».
Il file project-tree.txt deriva da tree -J dell’08/10 ed è una fotografia storica: può non elencare nuovi moduli o test del 13/10. I documenti Handbook, quicklaunch e installation-architecture erano fermi all’08/10 e contenevano correttamente, a quella data, affermazioni ora superate sulla recovery/SQLCipher; le edizioni aggiornate allegate chiariscono il delta, senza attribuire validazioni non eseguite.

11. ROADMAP PROPOSTA E PREVENTIVO NON VINCOLANTE

Fase 1 (4–7 ore): inspect e collaudo end-to-end SQLCipher su mailbox Received, Sent e queue; verifica apertura/scrittura/riapertura, chiave errata, assenza fallback plaintext, confini GUI/CLI/bootstrap. Fase 2 (5–9 ore): flussi SMTP/IMAP/queue con persistenza cifrata, retry, riavvio e continuità della consegna; evitare modifiche preventive al core. Fase 3 (4–7 ore): analisi/chiusura dei perimetri rimasti scoperti, soprattutto AttachmentStore, metadata, WAL/SHM/journal/temp, backup, file corrotti e identità; la stima può aumentare se occorre migrazione dati preesistenti. Fase 4 (3–5 ore): prova manuale GUI su Ubuntu 24.04 VM, primo setup, login, recovery, chiusura, riavvio e visualizzazione. Fase 5 (4–8 ore): dipendenze SQLCipher, installazione pulita, documentazione e release checklist. Totale tecnico orientativo 20–36 ore, con margine 25–45 ore; non comprende porting Windows/macOS, migrazioni complesse né audit esterno. Stima formulata prima di una nuova ispezione del repository; non è un preventivo contrattuale né un elenco di feature garantite.
Prossimo passo raccomandato: fase 1, un solo rischio reale per volta, nessuna patch finché non sono disponibili sorgente e test reali. Prima di partire chiedere git status --short, git log -1 --oneline e sorgenti/test pertinenti; non richiedere tutto il repository indiscriminatamente.

12. COMANDI, FILE E CHECKPOINT UTILI

Sviluppo: cd /mnt/c/garlicsmtp; source .venv/bin/activate; python -m garlicsmtp.gui. Suite mirata confermata: pytest tests/test_account_credentials.py tests/test_gui_application.py tests/test_gui_tk_authentication.py -q --tb=short (129 passed). Suite completa confermata dall’utente: pytest -q --tb=short (1797 passed). Per un nuovo controllo: git status --short; git log -1 --oneline; git diff --check. La shell WSL e il filesystem Windows possono avere differenze di permessi rispetto alla VM Ubuntu: non usarli come prova sostitutiva.
Sorgenti da ispezionare all’inizio della fase 1, se pertinenti al micro-obiettivo: garlicsmtp/storage/sqlite/backend.py, garlicsmtp/queue/sqlite.py, garlicsmtp/security/auth/account_credentials.py, garlicsmtp/gui/application.py, garlicsmtp/application/builder.py, garlicsmtp/core/engine/bootstrap.py, garlicsmtp/configuration/paths.py, garlicsmtp/storage/attachment_store.py. Test da individuare e leggere realmente: tests/test_account_credentials.py, tests/test_gui_application.py, tests/test_gui_tk_authentication.py, tests/test_message_store_sqlite.py, tests/test_application_builder.py, test relativi alla queue, CLI e installer. Non assumere nomi dei nuovi test at-rest non verificati.

13. REGOLE DI COLLABORAZIONE DA TRASFERIRE

PRIMA DI GENERARE CODICE DEVI VEDERE SORGENTE E TEST REALI. L’utente approva il micro-obiettivo, esegue i comandi e riferisce i risultati; l’assistente ispeziona, propone un solo RED focalizzato, aspetta l’esito, poi suggerisce GREEN minimo e regressioni. Se il comportamento è già presente, characterization test GREEN anziché RED artificiale. Non sovraingegnerizzare; tutte le regole di sicurezza si applicano, ma non richiedono nuove astrazioni prive di un difetto. Niente refactoring cosmetico, niente batch di patch speculative, niente sudo/apt/systemctl reali nei test, niente git add . automatico, niente dati sensibili nei log o nel testo. Un failure inatteso impone stop e nuovo inspect. Ogni aggiornamento del Development Book deve distinguere fatti, test, decisioni, aperti e stime.

==============================================================================
CAPITOLO 32 — MESSAGGIO DI RIPRESA, STATO AL 13/10/2026
==============================================================================

Sto proseguendo lo sviluppo e la validazione alpha di GarlicSMTP. Considera il documento allegato «GarlicSMTP_Ripresa_8_Snapshot_Tecnico_Ripresa_Completa_13_10_26» e il Development Book 9 come cronologia e baseline, ma NON come sostituti del repository reale.

REGOLA OBBLIGATORIA E PRIORITARIA: PRIMA DI GENERARE CODICE DEVI VEDERE SORGENTE E TEST REALI. Non generare patch, test o script da memoria, per analogia o soltanto sulla base dell’handoff. Prima di OGNI modifica chiedi/leggi il file sorgente reale, i test pertinenti, le fixture e l’eventuale output del failure. Se il contesto è incompleto, chiedi soltanto i file o gli estratti necessari. Il repository e la working tree attuali prevalgono sui documenti.

AMBIENTE E STATO AL 13/10/2026: Python 3.12, WSL Ubuntu 24.04, checkout /mnt/c/garlicsmtp, .venv. GUI Tkinter; installazione di prodotto storicamente validata su VM Ubuntu 24.04. L’utente ha confermato pytest -q --tb=short: 1797 passed; regressione mirata account credentials + GUI application + GUI Tk authentication: 129 passed. Questi sono risultati locali comunicati dall’utente, NON una nuova validazione su VM. Non inventare HEAD, commit, git status o test ulteriori.

CORE CONGELATO: SMTP, IMAP, store/queue, crypto E2EE, Tor, semantiche pipeline/delivery non vanno riaperti preventivamente. Interventi solo con failure concreto e riproducibile e previa mia approvazione. Mantieni encrypt-before-queue, TOFU/pinning, separazione Onion/Ed25519/X25519, Sent leggibile ma accepted non equivale a consegnato, Retry pending senza reset di attempts/last_error, TorStatus.ready non uguale a peer raggiungibile.

NOVITÀ DEL RAMO: sono stati implementati e testati i percorsi DEK di 32 byte, SQLCipher per SQLiteMessageStoreBackend e SQLiteQueueBackend senza fallback intenzionale plaintext, wrapping indipendente via password/recovery, recovery key offline e conferma, recupero/reset password, GUI di recovery, fail-closed e cleanup root Tk. L’ultimo test RED/GREEN ha portato build_view_model prima di root.deiconify; sul fallimento del build root.destroy e rilancio. Non confondere queste implementazioni con la cifratura integrale già validata di allegati, chiavi, backup, WAL/temp o archivi preesistenti: quei perimetri e il collaudo end-to-end su Ubuntu 24.04 restano da verificare.

METODO OBBLIGATORIO: inspect → una proprietà e un solo RED focalizzato → mia conferma del RED → GREEN minimo → test mirato → regressione correlata → full pytest ai gate rilevanti → Ubuntu 24.04 VM per i confini di sistema → revisione del diff e commit esplicito. Se il comportamento esiste già, preferisci characterization GREEN; non creare RED artificiale. Fermati al primo failure inatteso. Niente overengineering, refactoring cosmetico, bypass developer o subprocess privilegiati reali nei test. Non usare git add . come automatismo.

OBIETTIVO PRIORITARIO: riprendere dalla fase 1 della roadmap, verificando in modo reale e circoscritto SQLCipher end-to-end e l’assenza di accessi plaintext nei percorsi storage/queue, senza toccare il core se non strettamente necessario. Successivamente: flussi SMTP/IMAP/queue cifrati, allegati e residui, recovery e migrazione crash-safe, VM Ubuntu 24.04, packaging e documentazione. Le stime 20–36 ore (25–45 con margine) sono preliminari, non risultati garantiti.

RUOLI: io eseguo i comandi, fornisco sorgenti e test, approvo ogni micro-intervento e decido i commit; tu mi guidi passo per passo, in italiano, con file e comandi esatti. Non attribuirti test o commit non confermati. Non eseguire modifiche autonome. Per iniziare, dammi soltanto (a) stato realizzato e aperto in poche righe, (b) confini intoccabili, (c) i primi file reali e test da ispezionare per un solo micro-obiettivo SQLCipher. Attendi il mio riscontro prima di generare codice. A fine chat aiutami ad aggiornare il Development Book con i soli delta confermati.

==============================================================================
APPENDICE STORICA — EDIZIONE 8 INTEGRALE (STATO AL SUO CHECKPOINT)
==============================================================================

GARLICSMTP
STORIA DELLO SVILUPPO, METODO DI LAVORO E GUIDA ALLA CONTINUITÀ
Development Book — edizione 8, revisione narrativa

Documento per il lettore umano e per il passaggio operativo a una nuova chat
Repository ufficiale: https://github.com/giulsign/GarlicSMTP.git

===============================================================================
NOTA EDITORIALE — COME LEGGERE QUESTO LIBRO
===============================================================================

Questo non è un diario scandito da date. È la storia ragionata di come GarlicSMTP
è stato costruito, nell'ordine in cui sono maturate le sue funzioni e le sue
decisioni. Ogni capitolo racconta quale problema si intendeva risolvere, che cosa
è stato realizzato, quali scostamenti dal piano iniziale si sono resi necessari e
quali prove hanno consentito di proseguire.

Il testo distingue rigorosamente quattro categorie:
  REALIZZATO: comportamento descritto dalle fonti di sviluppo e, ove indicato,
              riscontrato anche nel codice del repository ufficiale.
  VALIDATO: comportamento accompagnato da un esito di test o prova reale
            documentato; la prova resta riferita a quel checkpoint.
  DECISO:   regola o requisito approvato, non necessariamente implementato.
  APERTO:   lavoro non concluso, proposta tecnica o rischio da verificare.

Le stime di lavoro nella parte finale sono PREVISIONI, non impegni, e dipendono
dalle decisioni architetturali, dall'ambiente e dagli esiti del TDD. Il lettore
non deve confondere una verifica storica con una prova eseguita oggi.

La narrazione usa i documenti di sviluppo forniti dall'autore: recap iniziale,
architetture, metodologie, snapshot, handoff, validazione alpha e riprese
successive. Per la verifica statica sono stati letti anche file di codice,
configurazione e installazione del repository ufficiale, ESCLUDENDO la cartella
GitHub docs/ come richiesto. I documenti storici forniti direttamente
dall'autore rimangono invece fonti legittime di questa ricostruzione.

INDICE
  Parte I    — Nascita, architettura e percorso di sviluppo (capitoli 1–12)
  Parte II   — Metodo di ingegneria e collaborazione uomo–AI (13–18)
  Parte III  — Trasferimento della continuità fra chat (19–21)
  Parte IV   — Obiettivi aperti e piano di realizzazione (22–25)
  Parte V    — Messaggio completo da consegnare alla prossima chat (26)
  Appendice — Riferimenti, invarianti e glossario

===============================================================================
PARTE I — STORIA DELLO SVILUPPO
===============================================================================

1. L'IDEA ORIGINARIA: POSTA ELETTRONICA ORIENTATA ALLA PRIVACY

GarlicSMTP nasce come progetto Python di messaggistica SMTP in cui il trasporto
fra nodi passa attraverso Tor Onion Services. L'obiettivo non è semplicemente
nascondere un normale client di posta dietro un proxy: il programma deve
possedere la propria catena di ricezione, composizione, consegna, accodamento,
memorizzazione e consultazione dei messaggi. In prospettiva deve poter essere
installato e utilizzato da una persona senza dover assemblare manualmente ogni
componente.

Gli obiettivi iniziali sono distinguibili in più livelli: un nucleo SMTP
funzionante; consegna locale e remota con code e retry; consultazione IMAP;
indirizzamento .onion tramite Tor; persistenza dei messaggi; identità
crittografiche per firma e cifratura; interfaccia utente; installazione
riproducibile e compatibile con l'uso quotidiano. Non tutte queste ambizioni
sono state soddisfatte contemporaneamente. La scelta metodologica determinante
è stata trasformarle in traguardi successivi verificabili.

Fin dall'inizio è stato necessario tenere separati tre concetti spesso
confusi: protezione del trasporto Tor, cifratura end-to-end del contenuto e
protezione dei dati quando sono salvati sul disco. Sono livelli differenti e
nessuno può essere presentato come sostituto automatico degli altri.

2. IL PRIMO NUCLEO: PROTOCOLLI, MESSAGGI E PERSISTENZA

La prima fase documentata mostra già una base tecnica sostanziosa: componenti
SMTP client/server, modelli di messaggio, pipeline di elaborazione, backend
SQLite e in memoria, mailbox, funzioni IMAP, coda persistente e gestione dei
tentativi di consegna. Sono presenti anche i primi elementi del trasporto
Onion e SOCKS5. L'obiettivo operativo è rendere il percorso di un messaggio
osservabile e testabile, prima di curare il prodotto destinato all'utente.

La pipeline consente di assegnare responsabilità distinte ai vari stadi. La
persistenza locale non deve decidere come connettersi al destinatario; il
trasporto non deve interpretare arbitrariamente il significato del messaggio;
la coda non deve trasformarsi in un secondo motore SMTP. Questa divisione ha
reso possibili modifiche successive senza riscrivere ogni volta il nucleo.

Scostamento rispetto all'immagine iniziale di un semplice programma di posta:
il progetto si è configurato come un piccolo sistema di messaggistica completo,
con propri protocolli, storage e orchestrazione. Ciò ha aumentato il numero
dei confini da testare, ma ha anche permesso di esercitare controllo sulle
proprietà di privacy desiderate.

Alcune affermazioni dei primi riepiloghi, specialmente sulle capacità IMAP,
sono state precisate successivamente. Per esempio HIGHESTMODSEQ non va
presentato come capacità supportata nella versione V1: il suo mancato annuncio
è una scelta esplicita, non una funzione da dedurre dal nome di altri moduli.

3. UNA ARCHITETTURA COMPOSTA, NON UN INSIEME DI SCRIPT

Con il consolidamento del nucleo emerge ApplicationBuilder come composition
root: il punto nel quale le dipendenze vengono assemblate e rese coerenti.
Intorno a esso si riconoscono MailComposerService, DeliveryStage,
MessageStore, QueueWorker, TransportManager, server SMTP e IMAP e i servizi
Tor. L'architettura vuole evitare che ogni interfaccia costruisca un proprio
insieme incoerente di componenti.

La consegna locale salva il messaggio nella mailbox; la consegna remota usa
il trasporto appropriato e la coda quando necessario. Il codice applicativo
ha il compito di esprimere intenzioni e stati; il protocollo e il trasporto
hanno responsabilità più ristrette. Questo schema ha consentito di mantenere
separati i test unitari, quelli d'integrazione e le prove end-to-end.

Le identità vengono divise in tre famiglie: identità dell'Onion Service,
identità di firma Ed25519 e identità di cifratura X25519. Una chiave non deve
essere riutilizzata soltanto perché è già disponibile. La verifica di una
firma non equivale inoltre alla fiducia nell'identità che l'ha prodotta:
validità crittografica e trust sono due giudizi distinti.

4. LA PRIMA CIFRATURA END-TO-END E I SUOI LIMITI

In una prima iterazione vengono predisposte le primitive crittografiche e
l'integrazione della firma, ma il ciclo completo di scoperta e fiducia nelle
chiavi del destinatario non è ancora concluso. Questo è un punto importante
per comprendere la storia: disporre di X25519 e ChaCha20-Poly1305 non
significa ancora possedere un sistema E2EE completo e sicuro da usare.

L'obiettivo iniziale — proteggere il contenuto fra nodi — richiede almeno:
identificare la chiave pubblica del destinatario, ricordare quale chiave è
stata accettata, rifiutare sostituzioni inattese e garantire che un messaggio
non venga accodato in chiaro prima della cifratura. La fase successiva nasce
proprio da questa analisi delle lacune.

5. DALLA PRIMITIVA CRITTOGRAFICA ALLA CONSEGNA E2EE FRA NODI

Il progetto introduce discovery della capacità GARLICSMTP-E2EE, parsing
rigoroso, memorizzazione della chiave pubblica X25519 del peer e politica
TOFU/pinning. Al primo incontro una chiave può essere associata all'endpoint
secondo la policy; un cambio successivo non deve sovrascrivere silenziosamente
il pin. La differenza viene trattata come condizione da segnalare e gestire,
non come un normale aggiornamento invisibile.

Qui compare uno degli scostamenti architetturali più istruttivi. Sarebbe
sembrato comodo cifrare dentro OnionTransport al momento della connessione.
Ma un messaggio già entrato in coda potrebbe così essere salvato in chiaro.
La soluzione scelta sposta discovery e cifratura PRIMA dell'enqueue: la coda
contiene già ciphertext; il trasporto si occupa di consegnarlo, non di
inventare la semantica E2EE. Sul lato ricevente si applica la sequenza
coerente di decifratura e verifica della firma.

La costruzione crittografica documentata usa X25519, HKDF-SHA256 e
ChaCha20-Poly1305, con chiave effimera e nonce. La sua presenza nel codice
non costituisce da sola un audit di sicurezza.

Le prove node-to-node attraversano SMTP e componenti applicativi reali; per
rendere i test ripetibili, il tratto SOCKS/Tor può essere sostituito da un
redirect locale. Si tratta di una validazione del flusso applicativo, non di
una dimostrazione che la rete Tor reale sia stata esercitata in quel test.

6. L'INTEGRAZIONE IMAP E LA LEZIONE DEL COMPOSITION ROOT

Nel preparare il gate SMTP → Store → IMAP emerge un difetto di wiring:
ApplicationBuilder non propagava l'Authenticator al server IMAP. Il default
RejectingAuthenticator impediva l'accesso. La soluzione non è stata aggirare
il builder impostando la dipendenza a mano dopo la costruzione, ma descrivere
con un test il comportamento richiesto e aggiungere un'iniezione opzionale
nel punto architetturale giusto.

Questa esperienza rafforza un principio generale: se un test d'integrazione
non riesce a esercitare una funzionalità senza bypassare il composition root,
è spesso l'assemblaggio delle dipendenze a richiedere attenzione. Il gate
SMTP → Store → IMAP, inizialmente aperto, risulta concluso nelle fasi
successive; la sua progressione va letta nell'ordine e non cristallizzata
allo stato dei primi documenti.

7. LA SVOLTA VERSO UN PRODOTTO INSTALLABILE

Dopo il nucleo protocollare il problema cambia: il software deve funzionare
anche su una macchina che non è quella dello sviluppatore. Si definisce
un'architettura di installazione fondata sui principi P1–P46, successivamente
affiancati da requisiti S non retroattivi nel documento di architettura
approvato. I punti P non sono un ornamento documentale: stabiliscono
separazione fra codice e stato, virtual environment isolato, installazione
come utente normale, manifest verificabile, detect-before-modify,
idempotenza, configurazione minima e primo avvio reale.

Una questione cruciale è il rapporto con Tor. Il programma non deve
modificare indiscriminatamente una configurazione di sistema esistente.
Prima deve riconoscere se Tor è assente, già compatibile, da configurare o
in uno stato ambiguo. Un sistema incompatibile o ambiguo richiede una
decisione esplicita, non un overwrite cieco. Questo percorso porta al
completamento del requisito P45 e prepara la verifica end-to-end P46.

Si consolidano anche i principi sulle identità: l'hostname .onion reale
proviene dall'Onion Service effettivo, non da un segnaposto test.onion;
l'identità deve persistere e non essere rigenerata a ogni avvio; la GUI
non deve inventare un mittente differente da quello determinato dal backend.

8. FIRST-RUN, CREDENZIALI IMAP E CONFIGURAZIONE RIPRODUCIBILE

L'installazione prende forma attraverso manifest, validator, generator,
install.sh, creazione del venv, installazione delle dipendenze e procedure
first-run. I dati dell'utente sono collocati sotto
~/.local/share/garlicsmtp/, distinti dal checkout sorgente. Il runtime
configura la propria identità Onion e le credenziali IMAP persistenti.

L'autenticazione Tor Control usa SAFECOOKIE e deve ottenere l'accesso al
cookie della corretta istanza Tor senza eseguire l'applicazione come root.
Le credenziali IMAP non devono comparire in chiaro in settings.toml e non
vanno rigenerate quando la configurazione esiste già. Il first-run deve
essere riprendibile: creazione iniziale e recupero da un avvio interrotto
sono scenari differenti.

Il profilo di installazione che emerge è volutamente limitato: Ubuntu 24.04.
È una scelta di qualità delle prove, non un'affermazione che Python non possa
funzionare su altri sistemi. Windows con WSL resta soprattutto ambiente di
sviluppo; supporto Windows nativo e macOS non sono stati validati come
installazioni di prodotto.

9. LA PROVA SULLA MACCHINA VERGINE

La validazione su una VM Ubuntu Desktop pulita trasforma le ipotesi
installative in problemi osservabili. Vengono esercitati install.sh, first-run,
GUI, CLI, Tor e scambio reale di messaggi. Il lavoro rivela difetti che i
test unitari non potevano dimostrare da soli: disponibilità di ensurepip,
configurazione del ControlPort Tor, librerie Qt/XCB richieste dalla GUI di
quella fase, appartenenza al gruppo debian-tor non ancora attiva nella
sessione grafica e differenza fra percorsi di sviluppo e percorsi utente.

La correzione sul gruppo Tor non consiste nell'indebolire l'accesso ai
segreti, ma nel richiedere logout/login per aggiornare i gruppi effettivi
della sessione. La separazione dei percorsi distingue la GUI installata,
che usa ApplicationPaths.for_user(), dall'avvio tramite
python -m garlicsmtp.gui, destinato allo sviluppo.

Il risultato documentato è una baseline alpha validata con una prova reale
sulla VM e suite completa verde nel relativo checkpoint. È una tappa di
maturazione importante: da codice che passa i test a programma installabile.
Non implica però che ogni funzione aggiunta in seguito abbia già superato
la medesima prova su macchina vergine.

10. LA GUI CAMBIA TECNOLOGIA: DA PYSIDE6 A TKINTER

L'interfaccia iniziale utilizzava PySide6. Nel percorso verso una release
alpha più semplice da distribuire si passa a Tkinter. Le dipendenze Qt/XCB,
prima rilevanti e realmente incontrate in VM, diventano così un episodio
storico, non una necessità dell'interfaccia attuale. Anche i test sintetici
che citano Qt non vanno interpretati automaticamente come prova di una
dipendenza runtime rimasta in uso.

Si completa il launcher Desktop per GNOME, con icona e gestione del flag di
fiducia del file .desktop. Il tag storico v0.0.1-alpha marca una baseline,
non il contenuto di tutte le modifiche successive. L'interfaccia continua
a evolvere oltre il tag: è quindi scorretto attribuire automaticamente
alla release taggata ogni funzione successiva.

11. LA POSTA DIVENTA LEGGIBILE: RECEIVED, SENT E ALLEGATI

Il passo successivo affronta l'esperienza dell'utente. La GUI non deve
mostrare soltanto un motore di consegna: deve consentire di distinguere i
messaggi ricevuti da quelli inviati, esplorarli e visualizzarli. Si creano
due store separati: data/mailboxes.db per Received e data/sent.db per Sent.

Qui emerge un secondo scostamento fondamentale. Dopo la cifratura E2EE, la
rappresentazione destinata al trasporto non è più leggibile come il testo
scritto dall'utente. Salvare in Sent il payload wire avrebbe compromesso
l'utilità della cartella. MailComposerService conserva perciò la versione
applicativa leggibile prima della trasformazione crittografica e la salva
in Sent quando il risultato è accepted.

«Accepted» significa accettazione nel percorso applicativo, NON prova di
consegna remota al destinatario. Nel self-send possono comparire due record:
uno in Sent e uno in Received. I vecchi elementi Sent già memorizzati in
forma cifrata non vengono migrati retroattivamente senza un progetto
esplicito. Un refresh del ViewModel, la cui rimozione aveva causato una
regressione, viene mantenuto: anche questa è una decisione motivata dai test.

La gestione degli allegati amplia il modello: memorizzazione, elenco,
visualizzazione/materializzazione e controlli sui nomi e sui percorsi. Le
prove storiche comprendono anche un self-send manuale con allegato. Gli
allegati non sono però automaticamente protetti a riposo: la loro
rappresentazione locale costituisce una questione distinta dall'E2EE wire.

12. RETRY MANUALE, ACCESSO GUI E NUOVA FRONTIERA DELLA SICUREZZA

Per i messaggi in attesa viene introdotto «Retry pending». Il pulsante
segue la catena GUI → ViewModel → Controller → QueueManager → backend
Memory/SQLite. La sua responsabilità è rendere nuovamente eleggibili gli
elementi con next_retry impostato, senza azzerare attempts o last_error.
La consegna rimane affidata al QueueWorker: il pulsante non diventa un
secondo percorso di spedizione.

Non si attiva automaticamente il retry quando TorStatus diventa ready.
Tor locale pronto non equivale a destinatario Onion raggiungibile; una
ripetizione cieca potrebbe peggiorare il comportamento. I test e una prova
manuale documentano il funzionamento del retry pending.

Successivamente viene aggiunto l'account di accesso alla GUI: creazione
iniziale, richiesta di username e password, memorizzazione di un hash scrypt
e controllo dei permessi del file credenziali. La finestra principale non
viene mostrata prima dell'autenticazione. Questa password è distinta dalla
password IMAP impostata dall'installer. Il repository conferma la presenza
di AccountCredentialStore e del flusso di login Tkinter.

A questo punto il progetto scopre il suo limite di sicurezza più rilevante
per il lavoro futuro. L'hash della password protegge la verifica del login,
non cifra automaticamente i file salvati. Il codice usa SQLite standard per
mailboxes, Sent e queue; AttachmentStore scrive contenuto .bin e metadati
.json senza cifratura at-rest. Anche le identità crittografiche e i dati
temporanei devono essere inclusi nell'analisi del rischio. Il fatto che un
messaggio abbia viaggiato cifrato non significa che resti cifrato sul disco.

L'ultima fase documentata è dunque un'analisi architetturale, non una
implementazione: si studiano password-derived KEK, DEK casuale, recovery key
offline, protezione integrale dei database, migrazione e accessi multipli
allo storage. Non vengono aggiunti codice né nuovi test in questa fase.
Questa distinzione chiude la storia documentata e apre il programma di lavoro.

===============================================================================
PARTE II — LA METODOLOGIA DI LAVORO
===============================================================================

13. IL PRINCIPIO CHE GOVERNA OGNI INTERVENTO

La regola formulata dall'autore è testuale e non negoziabile:

    «PRIMA DI GENERARE CODICE DEVI VEDERE SORGENTE E TEST REALI.»

Il suo significato è operativo. L'assistente AI non può proporre una patch
sulla base di memoria, snapshot, supposizioni sui nomi di funzione o soli
risultati grep. Deve prima leggere il sorgente effettivo del checkout, i
test pertinenti, le fixture e le interfacce chiamate. Quando l'utente
condivide solo un estratto, l'assistente deve dichiarare che la visione è
parziale e chiedere le parti necessarie.

La stessa regola vale per OGNI creazione o modifica di file, compresi test,
configurazioni, script installer, componenti GUI, migrazioni e documentazione
che cambia un contratto tecnico. Una nuova funzionalità non autorizza una
serie di modifiche speculative in moduli adiacenti. Prima si stabilisce
quale comportamento osservabile deve cambiare e quali file lo governano.

14. IL CICLO TDD COMPLETO, SENZA SCORCIATOIE

INSPECT — L'umano comunica l'obiettivo e mette a disposizione sorgente,
test e output reali. L'AI legge implementazione, firme, dipendenze,
fixture, invarianti e casi limite. Verifica se il comportamento esista già.
Se esiste, si preferisce un characterization test GREEN, senza fabbricare
un fallimento artificiale.

SPECIFY — Si formula UNA proprietà misurabile: input, azione, risultato
atteso e risultato vietato. Si definiscono i confini che NON devono
cambiare. L'AI propone il test più piccolo capace di falsificare la
proprietà; l'umano ne approva direzione e portata.

RED — Si introduce un test focalizzato, generalmente uno per iterazione.
L'utente lo esegue e comunica l'output. Il RED è valido soltanto se fallisce
per il motivo previsto. Un errore di import, una fixture errata o un typo
non dimostrano che la nuova funzione manchi: vanno diagnosticati prima.

GREEN MINIMO — Solo dopo il RED confermato si interviene sulla produzione.
La modifica deve essere la più piccola sufficiente a soddisfare il test.
Non si aggiungono refactoring cosmetici, classi speculative, nuove cache,
servizi generalizzati o cambiamenti non richiesti.

TARGET — Si riesegue il test nuovo. Se fallisce per una causa diversa,
ci si ferma e si studia il nuovo output, invece di accumulare patch.

REGRESSION — Si eseguono i test del componente, delle integrazioni vicine
e, ai gate importanti, l'intera suite (tipicamente pytest -q). La suite
completa non sostituisce il test mirato: i due livelli rispondono a domande
differenti. I numeri passati non si riciclano come esiti attuali.

SYSTEM GATE — Se si tocca installazione, Tor, permessi, GUI, launcher,
first-run o integrazione reale, si valida su Ubuntu 24.04 in VM o in un
ambiente controllato equivalente. Il successo di mock e fake runner non
prova che il sistema operativo si comporti allo stesso modo.

REVIEW & COMMIT — L'umano controlla il diff, decide se la modifica
risponde all'obiettivo, esegue i comandi e autorizza il commit. L'AI può
proporre un commit mirato, ma non deve dare per avvenuto ciò che l'umano
non ha confermato. Evitare git add .: elencare i file intenzionali.

DECIDE — Solo dopo il checkpoint verde si sceglie il passo successivo.
L'avanzamento è fatto di piccoli comportamenti verificati, non di grandi
blocchi di codice scritti in anticipo.

15. COME L'UMANO DIRIGE L'AI

La direzione del progetto resta umana. L'autore stabilisce le priorità,
accetta o respinge i compromessi, decide quando congelare un sottosistema,
fornisce i file reali, verifica i comandi proposti, corregge o implementa il codice,
chiede validazione del codice e analisi delle criticità, valuta il risultato
sull'ambiente effettivo. L'AI opera come collaboratore di analisi,
progettazione controllata, revisione e stesura di modifiche piccole.

Una richiesta efficace descrive: obiettivo; comportamento osservato;
comportamento desiderato; vincoli da preservare; file/test disponibili;
comandi già eseguiti e relativo output. Se manca il sorgente necessario,
la risposta corretta è chiedere evidenze, non inventare il codice.

Per ogni intervento l'AI dovrebbe restituire: diagnosi ancorata ai file
letti; proposta di un unico RED; posizione precisa del test; comando per
eseguirlo; previsione del tipo di fallimento; elenco dei file che non vanno
toccati. Dopo la conferma del RED, deve proporre il GREEN minimo con diff
o istruzioni di sostituzione inequivocabili e poi i comandi di regressione.

L'umano deve poter interrompere o correggere il percorso in qualunque
momento. Una soluzione che passa i test ma viola un principio architetturale
non è automaticamente accettata. Allo stesso modo, una modifica suggerita
dall'AI non è una decisione del progetto finché l'autore non la approva.

16. PERCHÉ I TEST NON POSSONO ESSERE TUTTI UGUALI

I test unitari verificano contratti locali e casi negativi. I test
d'integrazione esercitano dipendenze reali o fake controllati. I test di
protocollo usano, dove utile, client SMTP/IMAP reali come oracolo di
interoperabilità. I test node-to-node possono sostituire il solo segmento
Tor con un redirect locale senza perdere il valore del percorso SMTP.
Le prove VM verificano infine installazione, gruppi, servizi, Desktop,
filesystem e rete reale.

I test non devono modificare il sistema ospite: sudo, apt-get, systemctl,
modifiche torrc, gio e accessi privilegiati si simulano tramite runner,
filesystem temporanei o dipendenze iniettate. Le prove reali si fanno
separatamente e con autorizzazione dell'utente, non dentro pytest.

Le proprietà di sicurezza richiedono anche test NEGATIVI: chiave peer
cambiata, symlink non autorizzati, permessi insicuri, fallimento di un
passaggio di migrazione, password errata, file corrotti, rollback, retry
senza perdita dello stato, impossibilità di leggere dati senza chiave.

17. GESTIONE DELLE REGRESSIONI E CONGELAMENTO DEL CORE

Il core SMTP, IMAP, storage, queue, crittografia E2EE, Tor e delivery è
considerato congelato nei punti già validati, salvo un difetto reale
riproducibile o una necessità dimostrata dal nuovo requisito. Congelare
non significa proibire qualunque modifica futura: significa imporre un
onere di prova più alto a chi propone di attraversare quel confine.

Se un test fallisce inatteso, il flusso si arresta. Si raccolgono output,
traceback, sorgenti e fixture; si verifica se il fallimento è stato
introdotto dalla patch o era preesistente; si interviene solo sulla causa
mostrata. Non si corregge una presunta fragilità sulla base di intuizioni.

Il lavoro sui messaggi Sent, sulla propagazione dell'Authenticator IMAP e
sul retry manuale mostra l'efficacia di questo criterio: ogni volta la
modifica è stata collocata nel layer appropriato, preservando i contratti
esistenti invece di introdurre percorsi paralleli.

18. IGIENE DI SICUREZZA, VERSIONAMENTO E COMUNICAZIONE

Non condividere nei prompt chiavi private Onion, cookie Tor, password,
chiavi di firma/cifratura, database reali con messaggi privati o log non
ripuliti. Preferire estratti minimi e dati sintetici. Non eseguire
comandi distruttivi per «riparare» un ambiente. La disinstallazione
richiede DELETE e distrugge dati, credenziali e identità: non è un reset.

Ambiente storico: sviluppo Windows con WSL Ubuntu, sorgenti spesso in
/mnt/c/garlicsmtp, Python 3.12+, Git gestito secondo il workflow
concordato con l'autore. L'installer di prodotto supporta il profilo
Ubuntu 24.04. Distinguere sempre shell, checkout, venv di sviluppo e
venv installato; non assumere che una GUI avviata da sviluppo usi gli
stessi percorsi dell'entrypoint di produzione.

Versioni, commit e test sono evidenze da riportare con provenienza.
Esiste una baseline taggata v0.0.1-alpha, ma il checkout attuale può essere
più avanti. pyproject.toml sul repository verificato dichiara 0.0.1-alpha.
I conteggi di suite storici attraversano checkpoint differenti (fra cui
1273, 1396, 1616, 1622 e 1712 test superati); non sono cumulativi né
attestano un'esecuzione nel presente. L'ultima analisi non ha prodotto
un nuovo run pytest.

===============================================================================
PARTE III — TRASFERIRE LO SVILUPPO FRA CHAT SENZA PERDERE CONTESTO
===============================================================================

19. IL PROBLEMA DELLA CONTINUITÀ

Una chat lunga contiene decisioni, correzioni, file letti e output che
possono diventare difficili da ritrovare. Aprire una nuova conversazione
senza un handoff costringe a ricostruire l'architettura e può indurre
l'assistente a ripetere errori già risolti. Lo scopo di questo Development
Book è trasferire il contesto in forma verificabile, non sostituire il
repository o simulare una memoria perfetta.

Un handoff efficace distingue: storia e motivazioni; stato realizzato;
ultima evidenza verificata; decisioni irreversibili o invarianti; obiettivo
aperto; informazioni ancora mancanti; istruzioni per il prossimo primo
passo. I dettagli già superati sono utili per capire il percorso, ma
non devono essere presentati come problemi ancora aperti.

20. IL PACCHETTO MINIMO DI CONSEGNA

Consegnare alla nuova chat, in quest'ordine:
  A. Questo Development Book completo, da leggere come contesto storico.
  B. installation-architecture.md approvato, per P1–P46 e requisiti S
     non retroattivi; non reinterpretarne il testo senza richiesta.
  C. project-tree.txt approvato, come orientamento, NON prova che i file
     del checkout corrente siano rimasti identici.
  D. quicklaunch.md e GarlicSMTP-Handbook.txt approvati, quando servono
     per installazione o comportamento utente.
  E. Il nuovo obiettivo in una frase verificabile, con priorità e vincoli.
  F. Stato Git effettivo: git status --short, git log -1 --oneline,
     branch, eventuali modifiche non committate e diff pertinente.
  G. Sorgenti e test REALI coinvolti nel primo intervento, con file
     completi quando necessari; output RED/GREEN e traceback disponibili.
  H. Ultima suite realmente eseguita, ambiente e comando, distinguendo
     risultati attuali da numeri storici.
  I. Decisioni appena prese, rischi aperti, blocchi e domanda immediata.

Il solo Development Book è sufficiente per riallineare la storia; NON è
sufficiente per autorizzare una patch. La lettura di file reali è un
passaggio obbligatorio per ogni modifica.

21. PROCEDURA DI RIPRESA E DI CHIUSURA DI UNA CHAT

All'apertura, l'assistente deve: leggere il libro; riassumere in poche
righe lo stato compreso; separare fatti, decisioni e proposte; verificare
HEAD e working tree; identificare il primo confine da studiare; chiedere
solo i sorgenti/test che mancano. Non deve produrre codice in risposta
al solo handoff, né tentare un refactoring preventivo.

Durante la chat, mantenere un registro operativo leggero: obiettivo,
file letti, RED, GREEN, test mirati, regressioni, decisioni umane,
commit confermati, problemi aperti. Evitare di ricostruire la storia a
ogni messaggio: bastano delta e riferimenti precisi.

Alla chiusura, produrre l'edizione successiva del libro aggiornando
nell'ordine la narrazione, le decisioni, lo stato delle prove, la roadmap
e il messaggio di handoff. Non cancellare la storia degli scostamenti;
marcare ciò che è stato superato. Non inserire test, commit, feature o
validazioni non realmente documentati. Un documento professionale deve
consentire a un nuovo collaboratore di distinguere immediatamente
«cosa sappiamo» da «cosa dobbiamo ancora verificare».

===============================================================================
PARTE IV — GLI OBIETTIVI ANCORA DA RAGGIUNGERE
===============================================================================

22. IL TRAGUARDO PRINCIPALE: CIFRATURA COMPLETA DEI DATI A RIPOSO

La priorità aperta documentata è proteggere i dati locali anche quando
un attaccante possa leggere i file sul disco, senza compromettere la
cifratura end-to-end, la consegna o la continuità delle identità.

Perimetro da inventariare prima di scegliere la tecnologia:
  • data/mailboxes.db: messaggi Received e metadati;
  • data/sent.db: copia leggibile dei messaggi Sent;
  • state/queue.db: payload, retry, destinatari e metadati;
  • data/attachments/: file .bin e metadati .json;
  • file di identità Onion, Ed25519 e X25519;
  • file di trust e chiavi pubbliche peer, configurazioni sensibili;
  • file temporanei, SQLite WAL/SHM/journal, backup e file di migrazione;
  • cache di allegati materializzati, log e ogni percorso secondario.

L'obiettivo non è nascondere una stringa in un test, ma evitare che i
contenuti e i metadati sensibili restino recuperabili dai file previsti
dal modello di minaccia. La copertura esatta richiede una threat-model
review: per esempio un sistema già compromesso mentre l'app è sbloccata
non è risolto semplicemente dalla cifratura at-rest.

23. ARCHITETTURA DELLE CHIAVI, RECOVERY E MIGRAZIONE

Proposta da progettare e testare, NON ancora implementata:
  • generare una DEK casuale, indipendente dalla password dell'utente;
  • derivare una KEK dalla password con KDF adeguata, sale e parametri
    versionati; proteggere la DEK con wrapping autenticato;
  • generare una recovery key offline indipendente, con proprio dominio
    KDF e proprio wrapping della stessa DEK;
  • mostrare la recovery key una sola volta, richiedendo conferma
    esplicita di avvenuto salvataggio, senza scriverla nei log;
  • consentire cambio password senza ricifrare ogni messaggio, tramite
    nuovo wrapping, preservando DEK e identità;
  • consentire recupero con recovery key senza conoscere la password
    precedente; prevedere rotazione e revoca della recovery key;
  • definire comportamento sicuro per recovery key persa, password
    dimenticata, file corrotto e tentativi di sblocco falliti.

La scelta del motore di cifratura dei DB resta aperta. SQLCipher è un
candidato da valutare per disponibilità, packaging Ubuntu, compatibilità
sqlite3 e gestione WAL/journal. Una cifratura per-record può lasciare
in chiaro schema, indici, metadata e file ausiliari: non va dichiarata
«cifratura completa del database» senza analisi della copertura.

La migrazione deve trattare l'installazione esistente come un patrimonio
da conservare: inventario, backup sicuro, prova di integrità, trasformazione
atomica o riprendibile, gestione crash/power loss, verifica post-migrazione
e rollback definito. Non rigenerare chiavi Onion o identità di firma/E2EE.
Non eliminare i file in chiaro prima che una verifica reale dimostri che
la migrazione è corretta e recuperabile.

24. ROADMAP ORDINATA CON STIME DI REALIZZAZIONE

Le stime sono espresse in giornate di lavoro tecnico effettivo, con
sorgenti e test disponibili, un solo sviluppatore umano che revisiona
passi piccoli e supporto AI. NON includono attese esterne, ricerca di
bug imprevedibili o certificazione di sicurezza. I blocchi possono
sovrapporsi solo quando non violano il TDD sequenziale.

FASE A — Baseline e modello di minaccia                     2–4 giornate
  A1. Verificare HEAD, stato Git, versione e full pytest attuale.
  A2. Mappare ogni percorso di scrittura e lettura sensibile.
  A3. Elencare entrypoint che bypassano ApplicationBuilder (es. CLI,
      bootstrap) e file transitori.
  A4. Stabilire quali dati devono essere protetti e quando l'app si
      considera sbloccata.
  Gate: inventario approvato dall'umano, nessun percorso non classificato.

FASE B — Scelta del motore e proof of concept                3–6 giornate
  B1. Confrontare SQLCipher e alternative rispetto al requisito completo.
  B2. Verificare installazione, dipendenze e distribuzione su Ubuntu 24.04.
  B3. Produrre test RED su creazione/apertura DB cifrato e password errata.
  B4. Verificare journal/WAL/SHM, temp, crash e assenza di fallback in chiaro.
  Gate: tecnologia motivata, test riproducibili e decisione umana.

FASE C — DEK, KEK e formato delle credenziali                4–7 giornate
  C1. Specificare formati versionati, sali, KDF e wrapping autenticato.
  C2. Implementare generazione DEK e sblocco via password con TDD.
  C3. Introdurre recovery key indipendente e conferma di custodia.
  C4. Testare errori, corruzione, permessi, symlink e gestione chiavi RAM.
  Gate: stessi dati sbloccabili con password o recovery key.

FASE D — Storage protetto e copertura dei percorsi           6–12 giornate
  D1. Integrare Received, Sent e queue senza alterare le semantiche.
  D2. Proteggere allegati, metadati e cache/materializzazioni.
  D3. Proteggere o giustificare separatamente identità e trust store.
  D4. Centralizzare il wiring nei diversi entrypoint.
  D5. Eseguire regressioni SMTP, IMAP, E2EE, queue, GUI e retry.
  Gate: nessun percorso previsto scrive dati sensibili in chiaro.

FASE E — Migrazione crash-safe dell'installato               5–9 giornate
  E1. Definire preflight, backup e rollback.
  E2. Implementare migrazione incrementale con test di interruzione.
  E3. Verificare integrità e conservazione delle identità.
  E4. Provare ripartenza dopo crash e rimozione sicura dei residui.
  Gate: installazione storica migrata e recuperabile senza perdita dati.

FASE F — Interfaccia, recupero e lifecycle                   4–8 giornate
  F1. Setup password e recovery key con messaggi chiari.
  F2. Login che sblocca i dati, non solo verifica un hash.
  F3. Reset password con recovery key, cambio password e rotazione key.
  F4. Gestire blocco, riavvio, errori, chiusura e stati parziali.
  Gate: flussi utente completi, test GUI e nessuna perdita di identità.

FASE G — Hardening, test E2E e validazione VM                 4–8 giornate
  G1. Testare DB copiati a programma chiuso, file temporanei e backup.
  G2. Ricevere messaggio e allegato reali, chiudere, riaprire, recuperare.
  G3. Verificare Onion identity, firma e chiave E2EE invariate.
  G4. Eseguire full pytest e installazione/upgrade su Ubuntu 24.04.
  G5. Aggiornare manuale, installer, recovery guidance e threat model.
  Gate: accettazione esplicita dell'umano su VM e documentazione.

STIMA AGGREGATA: 28–54 giornate tecniche, circa 6–11 settimane a cinque
 giornate effettive per settimana, prima di buffer e revisioni esterne.
RISERVA CONSIGLIATA: +25–40% per integrazione, packaging e failure
imprevisti; ordine di grandezza pianificabile 7–16 settimane. Sono stime
ragionate, non deducibili dai documenti storici né una promessa di consegna.

25. CRITERI DI ACCETTAZIONE E LAVORI SUCCESSIVI

Un gate finale significativo deve dimostrare, con implementazione reale:
  1. creazione o ricezione di un messaggio con allegato;
  2. persistenza, chiusura completa dell'applicazione e copia offline dei DB;
  3. impossibilità di leggere i dati sensibili dalla copia senza chiave,
     con verifica più forte di una semplice ricerca di stringhe;
  4. riapertura corretta con password e recupero con recovery key senza
     la vecchia password;
  5. lettura degli stessi messaggi e allegati dopo il recupero;
  6. identità Onion, Ed25519 e X25519 immutate;
  7. queue, retry, SMTP/IMAP e E2EE ancora funzionanti;
  8. nessun residuo sensibile in temp, cache, WAL/journal o backup non
     esplicitamente protetti;
  9. installazione e migrazione riuscite su Ubuntu 24.04;
 10. risultati test e commit registrati con output reali.

Restano inoltre lavori da pianificare dopo questo traguardo, ma le fonti
non consentono di attribuire loro una priorità o stima vincolante:
valutazione indipendente della sicurezza, ulteriore hardening e test del
modello di minaccia, miglioramento UX, gestione errori e compatibilità
con ulteriori sistemi operativi. Nessuno di essi va dichiarato supportato
prima di una verifica specifica.

===============================================================================
PARTE V — MESSAGGIO COMPLETO PER LA NUOVA CHAT
===============================================================================

26. TESTO DA COPIARE E INCOLLARE INSIEME AL DOCUMENTO

INIZIO MESSAGGIO

Sto riprendendo lo sviluppo di GarlicSMTP. Ti allego il documento
«GarlicSMTP-development-book-8.txt» nella sua revisione narrativa: leggilo
integralmente come storia, metodologia e stato dei lavori. Allego, quando
necessario, anche «installation-architecture.md» approvato (principi
P1–P46 e requisiti S non retroattivi), «project-tree.txt» approvato,
«quicklaunch.md» e «GarlicSMTP-Handbook.txt» approvati. I documenti sono
contesto, non sostituti del codice corrente.

Repository ufficiale: https://github.com/giulsign/GarlicSMTP.git.
Branch predefinito pubblicato: main. Se consulti il repository GitHub per
confronti documentali, ESCLUDI il contenuto della cartella docs/; puoi
usare i documenti che ti allego direttamente come fonti storiche.
La working tree locale e i test reali prevalgono sempre su qualsiasi
snapshot o resoconto.

IDENTITÀ E OBIETTIVO
GarlicSMTP è un sistema Python 3.12+ di messaggistica SMTP/IMAP con
trasporto Tor Onion Services, queue persistente, firme Ed25519 e E2EE
X25519/HKDF/ChaCha20-Poly1305. L'installer validato è per Ubuntu 24.04.
La GUI attuale è Tkinter; Received e Sent hanno store separati; esistono
allegati, Retry pending e login GUI con password hash scrypt.
Il software è alpha, source-available con PolyForm Noncommercial 1.0.0 e
licenza commerciale separata; non è auditato professionalmente. Non
promettere anonimato o protezione assoluti.

REGOLA ASSOLUTA
«PRIMA DI GENERARE CODICE DEVI VEDERE SORGENTE E TEST REALI.»
Non generare patch, test, script o refactoring da memoria, da questo libro,
da soli nomi di file o da grep. Prima di OGNI creazione o modifica leggi
il sorgente completo pertinente, i test reali e le fixture necessarie.
Se non hai accesso, chiedimi di incollarli o allegarli. Non inventare
API, nomi, path, esiti, commit o versioni. Se una fonte è parziale,
dichiaralo e chiedi il minimo contesto aggiuntivo necessario.

RUOLI E CONTROLLO
Io, autore umano, definisco priorità, approvo architettura e modifiche,
eseguo i comandi, verifico output e decido commit. Tu mi aiuti con
analisi rigorosa, proposte minime, test focalizzati e revisione.
Non procedere automaticamente con più modifiche; attendi il mio
riscontro dopo ciascun RED e dopo i gate significativi.

METODO OBBLIGATORIO
1. Inspect: leggi file reali, test, fixture e contratti.
2. Specifica una sola proprietà osservabile e i confini invarianti.
3. RED: proponi un solo test focalizzato; dimmi file, punto esatto,
   comando e fallimento atteso; attendi il mio output effettivo.
4. Se il comportamento esiste già, usa characterization GREEN:
   non costruire un RED artificiale.
5. GREEN: dopo RED confermato, proponi la minima modifica di produzione.
6. TARGET: rieseguo il test e ti comunico il risultato.
7. REGRESSION: test correlati, poi pytest -q ai checkpoint rilevanti.
8. SYSTEM: se necessario, validazione reale su VM Ubuntu 24.04.
9. REVIEW: controllo umano del diff e commit esplicito, file per file.
10. STOP al primo failure inatteso: non accumulare correzioni speculative.

VINCOLI ARCHITETTURALI
Non modificare core SMTP, IMAP, storage, queue, E2EE, Tor o delivery
senza necessità riproducibile. Non bypassare ApplicationBuilder,
Controller, ViewModel o QueueWorker per ottenere scorciatoie.
La queue remota conserva ciphertext E2EE: discovery e cifratura
precedono enqueue. Il pin X25519 non si sovrascrive silenziosamente.
Sent conserva la rappresentazione applicativa leggibile prima della
cifratura wire, e accepted NON significa consegna remota.
TorStatus.ready NON dimostra raggiungibilità del peer Onion.
Retry pending risveglia elementi eleggibili senza azzerare attempts
o last_error; il QueueWorker resta responsabile della consegna.
Non introdurre subprocess privilegiati reali nei test: usare fake runner.
Non usare git add . come automatismo. Non rigenerare identità Onion,
Ed25519 o X25519 come effetto di installazione, reset o migrazione.

STATO E PROVE
Il tag storico v0.0.1-alpha non rappresenta tutte le feature
successive. Il repository pubblicato dichiara 0.0.1-alpha.
I checkpoint di pytest riportati nei documenti sono storici;
l'ultimo conteggio storico citato è 1712 passed, NON una suite eseguita
oggi. L'ultima fase descritta nel libro è stata analisi senza nuovo
codice o nuovi test. Prima di qualsiasi affermazione sul checkout attuale,
chiedimi git status --short, git log -1 --oneline, branch e test recenti.

OBIETTIVO APERTO PRIORITARIO
Progettare e implementare, solo dopo mia conferma, la cifratura completa
at-rest dei database Received/Sent/queue, degli allegati, dei metadati,
dei file temporanei e delle identità sensibili. Distinguere E2EE wire
dalla cifratura su disco. Valutare tecnologia database (SQLCipher è
soltanto un candidato), DEK casuale, KEK da password, recovery key
offline indipendente, reset password e migrazione crash-safe. Preservare
messaggi, allegati e identità Onion/Ed25519/X25519. Considerare CLI,
bootstrap, installer, WAL/journal/cache e tutti gli accessi allo storage.
Non affermare che recovery o cifratura at-rest siano già implementate.

COME INIZIARE QUESTA CHAT
Prima di proporre codice, restituiscimi un riepilogo BREVE e preciso:
(a) ciò che consideri realizzato, (b) ciò che è aperto, (c) i confini
che non vanno modificati, (d) i primi file sorgente e test reali che
ti occorrono. Attendi che io definisca il micro-obiettivo e fornisca
quei file. Non iniziare da solo una modifica o una suite di test.

COME CHIUDERE QUESTA CHAT
Aiutami a produrre la prossima edizione del Development Book,
aggiungendo solo i delta confermati: obiettivo, motivazione, file
realmente modificati, test RED/GREEN, regressioni, esiti VM, commit
confermati, decisioni, problemi aperti e prossimo messaggio di handoff.
Mantieni la storia in ordine di sviluppo, senza date puntuali nel
racconto, e separa fatti da ipotesi e stime.

FINE MESSAGGIO

===============================================================================
APPENDICE A — MAPPA DEI COMPONENTI E DELLE INVARIANTI
===============================================================================

ApplicationBuilder       composition root e assemblaggio dipendenze
MailComposerService      composizione e copia leggibile in Sent
DeliveryStage            confine della consegna locale/remota
MessageStore             accesso applicativo alla persistenza
SQLiteMessageStoreBackend  database delle mailbox
QueueManager/QueueWorker  pianificazione e tentativi di consegna
SMTP/IMAP                protocolli e consultazione messaggi
Tor Onion Services       raggiungibilità pseudonima e identità Onion
SAFECOOKIE               autenticazione locale al Tor ControlPort
Ed25519                  firma e verifica, distinte dal trust
X25519 + HKDF + AEAD     cifratura E2EE del messaggio in transito
AccountCredentialStore   verifica dell'accesso GUI, NON cifratura disco
ApplicationPaths         distinzione dei percorsi user/development
AttachmentStore          persistenza allegati; attualmente non at-rest

Percorsi applicativi verificati nel codice:
  ~/.local/share/garlicsmtp/config/
  ~/.local/share/garlicsmtp/data/mailboxes.db
  ~/.local/share/garlicsmtp/data/sent.db
  ~/.local/share/garlicsmtp/data/attachments/
  ~/.local/share/garlicsmtp/state/queue.db
  ~/.local/share/garlicsmtp/state/account-credentials.json
  ~/.local/share/garlicsmtp/state/imap-credentials.json
  ~/.local/share/garlicsmtp/state/onion-service.key
  ~/.local/share/garlicsmtp/state/logs/
  ~/.local/share/garlicsmtp/cache/
  ~/.local/share/garlicsmtp/venv/

Invarianti principali:
  • l'identità Onion è distinta da firma e cifratura;
  • l'hostname .onion deriva dal servizio reale, non da test.onion;
  • il cambio chiave peer non aggiorna silenziosamente il pin;
  • la coda E2EE non conserva un plaintext destinato al wire;
  • accepted non è prova di recapito remoto;
  • Tor pronto localmente non implica destinatario raggiungibile;
  • credenziali IMAP e credenziali GUI non sono equivalenti;
  • password hash non significa cifratura dei dati a riposo;
  • test fake e validazione su VM sono complementari;
  • P1–P46 e requisiti S vanno letti nella versione approvata di
    installation-architecture.md, senza ricostruirli per approssimazione.

===============================================================================
APPENDICE B — PROVENIENZA E LIMITI
===============================================================================

Fonti storiche dell'autore, lette e riconciliate per ordine di sviluppo:
  - recap fondativo del progetto;
  - Architettura e Funzionamento e relativa versione evoluta;
  - Metodologia Ingegneristica e relativa versione evoluta;
  - Riepilogo Tecnico e relativa versione evoluta;
  - Punto di Aggiornamento Sviluppo e snapshot di ripresa;
  - handoff tecnico intermedio e snapshot successivi;
  - Validazione Alpha su Ubuntu Desktop;
  - handoff tecnico completo dopo l'evoluzione della GUI;
  - snapshot dedicato ad allegati e retry;
  - snapshot dell'analisi at-rest e recovery;
  - precedente Development Book 8, oggetto della presente revisione.

Riscontro statico sul repository ufficiale, esclusa la directory docs/:
README.md, SECURITY.md, pyproject.toml, requirements.txt, install.sh,
install/manifest.toml, install/installer.py, install/uninstaller.py,
install/platform.py, install/environment.py, garlicsmtp/gui/application.py,
garlicsmtp/gui/__main__.py, garlicsmtp/configuration/paths.py,
garlicsmtp/security/auth/account_credentials.py,
garlicsmtp/storage/sqlite/backend.py,
garlicsmtp/storage/attachment_store.py.

La ricostruzione risolve gli apparenti conflitti rispettando l'ordine delle
implementazioni: E2EE prima incompleta poi integrata; IMAP auth inizialmente
non propagata poi corretta; P45 prima aperto poi concluso; GUI PySide6 poi
Tkinter; Sent prima assente poi distinto; retry manuale introdotto dopo;
login GUI successivo; cifratura at-rest tuttora aperta. Nessuna nuova
esecuzione pytest, installazione VM o verifica dell'HEAD locale è stata
compiuta per questa revisione documentale.

===============================================================================
APPENDICE C — GLOSSARIO MINIMO
===============================================================================

Alpha         software in sviluppo, non garanzia di sicurezza o stabilità
At-rest       protezione dei dati mentre sono memorizzati sul dispositivo
DEK           Data Encryption Key: chiave che cifra i dati
KEK           Key Encryption Key: chiave che protegge una DEK
E2EE          cifratura end-to-end del messaggio fra i nodi
GREEN         test che passa per il comportamento atteso
RED           test che fallisce per la ragione attesa prima della modifica
Regression    verifica che la modifica non rompa funzioni esistenti
SAFECOOKIE    autenticazione challenge/response verso Tor Control
TOFU          Trust On First Use: primo pin di una chiave peer
VM            macchina virtuale di validazione
WAL/SHM       file ausiliari SQLite da includere nel modello di rischio

FINE DEL DEVELOPMENT BOOK — EDIZIONE 8, REVISIONE NARRATIVA


==============================================================================
MESSAGGIO FINALE ATTUALE DA INCOLLARE COME PRIMO MESSAGGIO (13/10/2026)
==============================================================================

Sto proseguendo lo sviluppo e la validazione alpha di GarlicSMTP. Considera il documento allegato «GarlicSMTP_Ripresa_8_Snapshot_Tecnico_Ripresa_Completa_13_10_26» e il Development Book 9 come cronologia e baseline, ma NON come sostituti del repository reale.

REGOLA OBBLIGATORIA E PRIORITARIA: PRIMA DI GENERARE CODICE DEVI VEDERE SORGENTE E TEST REALI. Non generare patch, test o script da memoria, per analogia o soltanto sulla base dell’handoff. Prima di OGNI modifica chiedi/leggi il file sorgente reale, i test pertinenti, le fixture e l’eventuale output del failure. Se il contesto è incompleto, chiedi soltanto i file o gli estratti necessari. Il repository e la working tree attuali prevalgono sui documenti.

AMBIENTE E STATO AL 13/10/2026: Python 3.12, WSL Ubuntu 24.04, checkout /mnt/c/garlicsmtp, .venv. GUI Tkinter; installazione di prodotto storicamente validata su VM Ubuntu 24.04. L’utente ha confermato pytest -q --tb=short: 1797 passed; regressione mirata account credentials + GUI application + GUI Tk authentication: 129 passed. Questi sono risultati locali comunicati dall’utente, NON una nuova validazione su VM. Non inventare HEAD, commit, git status o test ulteriori.

CORE CONGELATO: SMTP, IMAP, store/queue, crypto E2EE, Tor, semantiche pipeline/delivery non vanno riaperti preventivamente. Interventi solo con failure concreto e riproducibile e previa mia approvazione. Mantieni encrypt-before-queue, TOFU/pinning, separazione Onion/Ed25519/X25519, Sent leggibile ma accepted non equivale a consegnato, Retry pending senza reset di attempts/last_error, TorStatus.ready non uguale a peer raggiungibile.

NOVITÀ DEL RAMO: sono stati implementati e testati i percorsi DEK di 32 byte, SQLCipher per SQLiteMessageStoreBackend e SQLiteQueueBackend senza fallback intenzionale plaintext, wrapping indipendente via password/recovery, recovery key offline e conferma, recupero/reset password, GUI di recovery, fail-closed e cleanup root Tk. L’ultimo test RED/GREEN ha portato build_view_model prima di root.deiconify; sul fallimento del build root.destroy e rilancio. Non confondere queste implementazioni con la cifratura integrale già validata di allegati, chiavi, backup, WAL/temp o archivi preesistenti: quei perimetri e il collaudo end-to-end su Ubuntu 24.04 restano da verificare.

METODO OBBLIGATORIO: inspect → una proprietà e un solo RED focalizzato → mia conferma del RED → GREEN minimo → test mirato → regressione correlata → full pytest ai gate rilevanti → Ubuntu 24.04 VM per i confini di sistema → revisione del diff e commit esplicito. Se il comportamento esiste già, preferisci characterization GREEN; non creare RED artificiale. Fermati al primo failure inatteso. Niente overengineering, refactoring cosmetico, bypass developer o subprocess privilegiati reali nei test. Non usare git add . come automatismo.

OBIETTIVO PRIORITARIO: riprendere dalla fase 1 della roadmap, verificando in modo reale e circoscritto SQLCipher end-to-end e l’assenza di accessi plaintext nei percorsi storage/queue, senza toccare il core se non strettamente necessario. Successivamente: flussi SMTP/IMAP/queue cifrati, allegati e residui, recovery e migrazione crash-safe, VM Ubuntu 24.04, packaging e documentazione. Le stime 20–36 ore (25–45 con margine) sono preliminari, non risultati garantiti.

RUOLI: io eseguo i comandi, fornisco sorgenti e test, approvo ogni micro-intervento e decido i commit; tu mi guidi passo per passo, in italiano, con file e comandi esatti. Non attribuirti test o commit non confermati. Non eseguire modifiche autonome. Per iniziare, dammi soltanto (a) stato realizzato e aperto in poche righe, (b) confini intoccabili, (c) i primi file reali e test da ispezionare per un solo micro-obiettivo SQLCipher. Attendi il mio riscontro prima di generare codice. A fine chat aiutami ad aggiornare il Development Book con i soli delta confermati.
```
