# Contribuire a GarlicSMTP

Grazie per l'interesse a contribuire a GarlicSMTP.

GarlicSMTP è un progetto a **codice sorgente disponibile (source-available)** mantenuto da Giuliano Signorelli. Il codice originale di GarlicSMTP è reso disponibile con la **PolyForm Noncommercial License 1.0.0**; il titolare del copyright può concedere licenze commerciali separate. La disponibilità del sorgente non implica che il progetto utilizzi una licenza open source approvata dall'OSI. Consultare `LICENSE`, `NOTICE`, `COMMERCIAL-LICENSE.md` e `THIRD_PARTY_LICENSES.md`.

## Accordo di licenza per i contributori (CLA)

I contributi al codice possono essere accettati soltanto da persone che aderiscono al Contributor License Agreement di GarlicSMTP contenuto in `CLA.md`. Ogni pull request che contiene un contributo deve includere esplicitamente la seguente dichiarazione, riportata in inglese per mantenerla identica a quella ufficiale:

> I have read and agree to the GarlicSMTP Contributor License Agreement (CLA.md), and I have the right to submit this contribution under those terms.

I contributi privi di tale conferma non devono essere integrati. Leggere il testo effettivo di `CLA.md` prima di aderire: questa guida non ne sostituisce le condizioni.

## Copyright e diritti sui contributi

I contributori mantengono il copyright sui propri contributi originali. Come descritto in `CLA.md`, l'accordo concede al manutentore i diritti necessari per utilizzare, modificare, distribuire, concedere in sublicenza e rilasciare con licenze differenti i contributi accettati, anche in versioni commerciali con licenza separata. Fanno fede le condizioni del CLA stesso.

Inviare esclusivamente materiale creato personalmente e che si ha diritto di concedere in licenza, materiale che si è legalmente autorizzati a contribuire, oppure materiale di terze parti chiaramente identificato con provenienza, copyright e licenza applicabile. Non copiare codice da altri progetti senza identificarne origine e licenza. Non inviare codice generato o derivato se non è possibile accertarne la provenienza o i permessi di licenza.

## Baseline di sviluppo e stato della release

La versione del progetto in preparazione per la prossima release è **`0.1.1a0`**, con **`v0.1.1-alpha`** come etichetta prevista. Si tratta di una candidata in preparazione, **non di una dichiarazione che il tag Git o la release GitHub siano già stati pubblicati**. La precedente baseline `v0.1.0-alpha.1` e il commit `9bfc2f7` sono riferimenti storici, non la baseline di sviluppo attuale. L'ultimo commit di sviluppo segnalato prima degli aggiornamenti di versione e documentazione era `8faf1c6`.

Sviluppare le modifiche su un ramo separato o su un fork, basandosi sul codice effettivamente presente nel checkout e non su supposizioni tratte da documentazione precedente. Non riscrivere release storiche né dichiarare esistenti tag non ancora creati.

## Prima di modificare il codice: esaminare, testare, poi intervenire

1. Leggere l'implementazione esistente, la configurazione pertinente, i manifest di installazione e i test correlati **prima** di proporre correzioni o refactoring.
2. Individuare il comportamento atteso e, quando possibile, riprodurre il problema con un test mirato inizialmente fallito (**RED**).
3. Applicare la modifica minima che soddisfa il test (**GREEN**), quindi eseguire i test di regressione pertinenti.
4. Eseguire l'intera suite prima di proporre l'integrazione; l'ultima esecuzione comunicata durante la preparazione di `0.1.1a0` ha superato **1.974 test**, ma questo risultato storico non convalida modifiche future.
5. Per modifiche che coinvolgono sistema operativo, packaging, Tor, crittografia, database o GUI, verificare nell'ambiente di destinazione pertinente e descrivere esattamente quanto testato. Il manifest dell'installer dichiara attualmente **Ubuntu 24.04**; per alcune verifiche della GUI è stata utilizzata separatamente una VM Ubuntu 22.04. Non presentare nessuno dei due ambienti come prova di supporto universale.

Per l'ambiente virtuale Python esistente, il comando dei test è:

```bash
python -m pytest -q
```

Non eseguire pulizie estranee alla modifica né sovrascrivere cambiamenti non correlati presenti nella working tree. Aggiungere allo staging soltanto i file previsti, evitando per impostazione predefinita `git add .`. Nella pull request descrivere sinteticamente comportamento, test, piattaforma ed eventuali limitazioni residue.

## Dipendenze e licenze

Prima di aggiungere, sostituire, incorporare o aggiornare software di terze parti, identificarne sorgente upstream, versione esatta o intervallo di versioni, licenza e avvisi obbligatori, oltre alla classificazione come dipendenza runtime, di sistema, di build, di sviluppo o di test. Controllare anche le dipendenze transitive e i componenti nativi inclusi nelle wheel binarie o negli artefatti di release.

Le dipendenze Python runtime attualmente dichiarate sono `dnspython>=2.8,<3`, `cryptography>=46,<47` e `sqlcipher3==0.6.3`. Il manifest di installazione Linux dichiara inoltre Tor e i prerequisiti Python Tkinter/Tcl/Tk. **PySide6 non è utilizzato dall'applicazione attuale**, anche se può essere ancora installato nell'ambiente di un singolo sviluppatore. Non dedurre le dipendenze distribuite dal solo output di `pip freeze`.

Le licenze con obblighi di copyleft, divulgazione del sorgente, uso non commerciale, licenze commerciali o altre restrizioni richiedono una revisione prima dell'accettazione. Conservare gli avvisi di terze parti richiesti e aggiornare `THIRD_PARTY_LICENSES.md` quando opportuno. Non presumere che la licenza di GarlicSMTP sostituisca quella del codice di terze parti.

## Sicurezza, privacy e dati di test

Trattare GarlicSMTP come software Alpha sensibile alla sicurezza. Non inserire mai in commit o allegati database reali delle caselle, messaggi, chiavi private degli Onion Service, cookie di autenticazione Tor, password, chiavi di cifratura dei dati (DEK), materiale di recupero, credenziali o log contenenti segreti. Usare dati di test sintetici e oscurare le informazioni sensibili nella diagnostica. Evitare modifiche distruttive ai dati degli utenti o alle identità Onion.

Le potenziali vulnerabilità devono essere segnalate privatamente secondo `SECURITY.md`, senza pubblicarle inizialmente in issue pubbliche. Non presentare i test o il corretto funzionamento delle comunicazioni Tor come audit di sicurezza indipendente o garanzia di anonimato.

## Pull request e revisione

I contributi dovrebbero normalmente essere sviluppati su un ramo separato o su un fork e proposti mediante pull request. Includere la dichiarazione CLA obbligatoria, un riepilogo della modifica, la motivazione, i test effettuati e i risultati, nonché eventuali implicazioni di compatibilità, sicurezza, migrazione o licenza. La documentazione deve restare coerente con il comportamento effettivamente implementato.

L'accettazione è a discrezione del manutentore; l'invio di un contributo non ne garantisce l'integrazione. Non è garantito alcun tempo specifico di revisione o integrazione.

## Domande sulle licenze

Per domande sulle licenze commerciali, contattare **giulisign@gmail.com** oppure utilizzare il repository ufficiale di GarlicSMTP, quando appropriato.
