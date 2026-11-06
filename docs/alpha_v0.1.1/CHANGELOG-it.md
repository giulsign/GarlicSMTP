# Registro delle modifiche (Changelog)

Questo registro distingue le verifiche storiche dal lavoro di preparazione della prossima release Alpha. Le voci descrivono modifiche e controlli documentati, non un audit di sicurezza indipendente.

## [Non pubblicata] — candidata v0.1.1-alpha (`0.1.1a0`)

**Stato:** preparazione della release; il tag Git `v0.1.1-alpha`, il commit finale di release, gli artefatti di distribuzione e la pubblicazione su GitHub non sono stati confermati. Il commit di sviluppo `8faf1c6` è un riferimento esaminato, **non** un tag di release.

### Modifiche e correzioni

- Aggiunto il supporto alla configurazione di una pagina HTML personalizzata opzionale per la pagina di presenza di un Onion Service, comprese le relative preferenze GUI e impostazioni di configurazione.
- Migliorata la validazione delle preferenze GUI: quando la pagina Onion personalizzata è abilitata, il percorso HTML deve essere non vuoto e indicare un file, non una directory. Le impostazioni selezionate hanno effetto dopo il riavvio pertinente.
- Aggiornati i testi in inglese delle preferenze GUI associate alla pagina Onion personalizzata.
- Aggiornate le dichiarazioni di versione del pacchetto a `0.1.1a0` in `pyproject.toml`, `garlicsmtp/__init__.py` e nei relativi test del manifesto di installazione, in preparazione della release.

### Verifiche riportate durante la preparazione

- **1.974 test superati** con `python -m pytest -q` nell'ambiente di sviluppo WSL (135,21 secondi); superato anche `git diff --check`.
- La GUI sulla VM Ubuntu 22.04 è stata verificata durante lo sviluppo. Il profilo di installazione dichiarato rimane Ubuntu 24.04; questo non certifica l'installazione su nessuna delle due versioni a partire dagli artefatti finali della release.
- Il modulo `sqlcipher3==0.6.3` installato ha riportato SQLCipher `4.12.0 community` e SQLite `3.51.1`. Si tratta di un'osservazione dell'ambiente, non di un audit completo dei binari o della sicurezza.

### Verifiche di release ancora aperte

- Creare e verificare il tag Git finale, il commit di release, gli artefatti e la pubblicazione GitHub.
- Rivalidare un'installazione pulita e gli eventuali percorsi di aggiornamento o migrazione che si intende supportare; qui non si dichiara alcuna certificazione in tal senso.
- Esaminare i componenti di terze parti effettivamente distribuiti, gli avvisi, le licenze e le librerie native.
- Confermare lo stato attuale della limitazione storica del bootstrap CLI `start` mediante esame del codice e dei test.
- Non è stato eseguito un audit professionale indipendente della sicurezza.

## v0.1.0-alpha.1 — Prima baseline Alpha ufficiale (preparazione della release, 19 ottobre 2026)

Commit sorgente della baseline: `9bfc2f7`. Quando fu scritta questa voce storica, la creazione del tag Git e la pubblicazione della release GitHub non erano state confermate. Questa affermazione registra lo stato **di allora**, non una nuova verifica di GitHub effettuata oggi.

### Funzionalità aggiunte e consolidate

- GUI desktop Tkinter con autenticazione, configurazione dell'account, composizione dei messaggi e viste Ricevuti e Inviati.
- Messaggistica SMTP bidirezionale su Tor Onion con cifratura end-to-end, verifica dell'autenticità Ed25519 e gestione della fiducia/pinning X25519.
- Cifratura SQLCipher dei database Ricevuti, Inviati e Coda, mediante DEK sbloccata con password.
- Archiviazione cifrata e autenticata degli allegati GSAT v1, compresi i metadati.
- Recupero offline della password applicativa e flussi di riavvolgimento della DEK/rotazione delle chiavi.
- Gestione dell'invio in background dalla GUI e miglioramento della diagnostica della pipeline.

### Verifiche registrate per quella baseline

- **1.844 test di sviluppo superati** nella suite completa allora confermata.
- Sviluppatore e VM Ubuntu: verificati auto-invio e consegna bidirezionale, compresi gli allegati.
- Su entrambi i sistemi: i database Ricevuti, Inviati e Coda esaminati non presentavano intestazioni SQLite in chiaro; formato GSAT v1 di alcuni allegati controllato in sola lettura.

### Limitazioni note registrate per quella baseline

- Nessun audit professionale indipendente della sicurezza; utilizzo soltanto come Alpha.
- Il bootstrap CLI `start` senza DEK falliva in modo sicuro; era una limitazione funzionale, non una prova di accesso ai dati in chiaro. Lo stato attuale richiede una nuova verifica.
- Installer, dipendenze e pacchettizzazione per un'installazione pulita di quella precisa baseline non erano stati nuovamente validati nella milestone documentata.
- Non veniva dichiarata alcuna certificazione della migrazione dei dati esistenti o del percorso di aggiornamento.

## v0.0.1-alpha — Baseline storica di sviluppo

- Struttura iniziale del progetto e definizione del pacchetto Python.
- Prima milestone di sviluppo (tag storico, distinto da `v0.1.0-alpha.1`).
