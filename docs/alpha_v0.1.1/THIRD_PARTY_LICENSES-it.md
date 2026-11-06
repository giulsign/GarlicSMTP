# GarlicSMTP — Software di terze parti e verifica delle licenze

**Release candidata:** v0.1.1-alpha (versione del pacchetto Python `0.1.1a0`)  
**Stato:** Bozza per la revisione del manutentore — non è una certificazione di conformità  
**Data della verifica:** 24 ottobre 2026

Copyright © 2026 Giuliano Signorelli — GarlicSMTP Project.

## 1. Ambito e principio di licenza

Il codice originale di GarlicSMTP è offerto sotto **PolyForm Noncommercial License 1.0.0**, come dichiarato in `pyproject.toml` (`LicenseRef-PolyForm-Noncommercial-1.0.0`) e nel file `LICENSE` del progetto. Questa licenza **non modifica la licenza dei componenti di terze parti**. Ogni dipendenza mantiene i propri diritti d'autore, la propria licenza, le proprie condizioni e le proprie note legali. La licenza non commerciale di GarlicSMTP non rende automaticamente non commerciali i componenti di terze parti.

Questo inventario distingue le dipendenze applicative dichiarate, le loro dipendenze transitive, i prerequisiti di sistema e i pacchetti semplicemente presenti nell'ambiente virtuale dello sviluppatore. La sola presenza in `pip freeze` **non dimostra** che un pacchetto sia richiesto o ridistribuito da GarlicSMTP.

## 2. Fonti e versioni considerate

Fonti esaminate: il file `THIRD_PARTY_LICENSES.md` fornito; `pyproject.toml`; `requirements.txt`; `install/manifest.toml`; gli output di `pip show` e `pip freeze`; il testo LICENSE di `sqlcipher3` installato; le interrogazioni delle versioni SQLCipher/SQLite dall’ambiente di sviluppo WSL con Python 3.12. Quest'ultimo **non** costituisce l'inventario degli artefatti di release né quello di un'installazione Ubuntu.

Il pacchetto dichiara `dnspython>=2.8,<3`, `cryptography>=46,<47` e `sqlcipher3==0.6.3`. Nell'ambiente di sviluppo risultano `dnspython==2.8.0`, `cryptography==46.0.7`, `sqlcipher3==0.6.3`, `cffi==2.1.1` e `pycparser==3.0`. Tranne `sqlcipher3`, i vincoli dichiarati non bloccano le versioni esatte delle future installazioni.

## 3. Dipendenze runtime dichiarate

| Componente | Requisito dichiarato | Versione osservata | Licenza / valutazione |
|---|---|---|---|
| **dnspython** | `>=2.8,<3` | 2.8.0 | **ISC** (confermata dai metadati installati). Permissiva; conservare copyright e avviso di licenza in caso di ridistribuzione. |
| **cryptography** | `>=46,<47` | 46.0.7 | Il progetto upstream adotta **Apache-2.0 OR BSD-3-Clause**. Conservare gli avvisi applicabili all'artefatto esatto e agli eventuali componenti nativi inclusi. Il campo `License` vuoto in `pip show` non significa che il pacchetto sia privo di licenza. |
| **sqlcipher3** | `==0.6.3` | 0.6.3 | Binding Python per SQLCipher. La distribuzione installata contiene `sqlcipher3-0.6.3.dist-info/licenses/LICENSE`, con una licenza permissiva di tipo zlib e copyright © 2004–2007 Gerhard Häring. I campi `License` e `License-Expression` sono vuoti, ma il testo effettivo è stato letto. Gli avvisi relativi al codice nativo SQLCipher rimangono un obbligo distinto. |

### SQLCipher Community Edition

SQLCipher Community Edition è distribuito sotto una **licenza di tipo BSD**, generalmente compatibile con la licenza non commerciale di un'applicazione. Zetetic richiede la riproduzione del **copyright completo, delle condizioni di licenza e dell'esclusione di garanzia** applicabili in un luogo accessibile all'utente, insieme agli avvisi pertinenti per i componenti incorporati (come SQLite e librerie crittografiche). La semplice citazione di SQLCipher in questo documento **non** soddisfa tale obbligo. Il modulo installato è stato verificato: `PRAGMA cipher_version` restituisce `4.12.0 community` e `SELECT sqlite_version()` restituisce `3.51.1`. Ciò conferma l'uso di SQLCipher Community Edition nell'ambiente osservato, ma non identifica tutti i componenti nativi incorporati nell'artefatto. Occorre distribuire i testi legali completi corrispondenti. Non presumere che le build trial o commerciali concedano gli stessi diritti.

Riferimenti: https://pypi.org/project/sqlcipher3/0.6.3/ ; https://www.zetetic.net/sqlcipher/license/ ; https://www.zetetic.net/sqlcipher/community/

### Licenza del binding confermata localmente

Il file LICENSE di `sqlcipher3==0.6.3` installato attribuisce il copyright a **Gerhard Häring (2004–2007)** e consente utilizzo, modifica e ridistribuzione, anche commerciale, con tre condizioni: non attribuirsi falsamente la paternità del software; contrassegnare chiaramente le versioni sorgente modificate; non rimuovere o alterare l’avviso nelle distribuzioni sorgente. Il riconoscimento nella documentazione del prodotto è apprezzato ma **non obbligatorio** secondo questa licenza del binding. La licenza è distinta dagli avvisi BSD-style di SQLCipher Community Edition. Il testo completo della licenza del binding deve essere conservato quando applicabile.

## 4. Dipendenze Python runtime transitive

`cryptography==46.0.7` dichiara una dipendenza da **cffi** e nell'ambiente osservato sono presenti `cffi==2.1.1` e **pycparser==3.0** (dipendenza di cffi). Prima della ridistribuzione bisogna raccogliere i rispettivi testi di licenza e gli eventuali avvisi per componenti nativi inclusi dagli artefatti effettivi. Le licenze upstream comunemente indicate sono MIT per cffi e BSD-3-Clause per pycparser, da confermare sugli artefatti. Questi pacchetti **non sono dichiarati direttamente** nel `pyproject.toml` di GarlicSMTP.

## 5. Componenti di sistema, interfaccia grafica e Python

- **Tor:** prerequisito esterno di sistema installato tramite il sistema operativo (`tor`); si applicano la sua licenza e i suoi avvisi. Verificare se Tor venga installato separatamente oppure incluso in un'immagine o pacchetto distribuito. https://www.torproject.org/
- **Tkinter / Tcl / Tk:** l'interfaccia grafica attuale utilizza Tkinter; il manifest Ubuntu specifica il pacchetto di sistema `python3-tk`. Python, Tcl e Tk hanno avvisi di licenza distinti. Gli obblighi dipendono dalle modalità di fornitura o ridistribuzione. https://docs.python.org/3/license.html ; https://www.tcl-lang.org/software/tcltk/license.html
- **Python Standard Library / interprete:** soggetti alla licenza PSF e agli altri avvisi della specifica distribuzione Python; importare moduli della libreria standard non implica di per sé incorporare un interprete Python.

Il profilo installer in `install/manifest.toml` specifica **Ubuntu 24.04**; i test su Ubuntu 22.04 non modificano il profilo dichiarato.

## 6. I pacchetti nell'ambiente di sviluppo non sono automaticamente distribuiti

L'output `pip freeze` comprende anche `build`, `pytest`, `pluggy`, `iniconfig`, `packaging`, `Pygments`, `pyproject_hooks`, `PyYAML`, `PySocks`, strumenti di build collegati a `setuptools` e **PySide6 / PySide6_Addons / PySide6_Essentials / shiboken6 (6.11.1), che il manutentore conferma non essere più utilizzati da GarlicSMTP**. La loro presenza **non dimostra** che siano dipendenze runtime dell'applicazione o che siano inclusi nella release.

**Esclusione di Qt/PySide6:** Il manutentore conferma che PySide6 non è più utilizzato da GarlicSMTP e non compare nelle dipendenze runtime dichiarate. È pertanto **escluso dall’inventario delle dipendenze attuali dell’applicazione**. La sua presenza residua nella `.venv` di sviluppo non genera obblighi di ridistribuzione per GarlicSMTP, salvo che file Qt/PySide6 vengano effettivamente inclusi negli artefatti.

Requisito di build: **`setuptools>=77`** è specificato in `pyproject.toml` per la costruzione del pacchetto; essere un requisito di build non significa di per sé essere incorporato nell'applicazione installata.

## 7. Valutazione di compatibilità

**Risultato preliminare: non è stato individuato un conflitto intrinseco di licenza** fra PolyForm Noncommercial 1.0.0 di GarlicSMTP e lo stack runtime dichiarato, **a condizione** che i componenti selezionati siano utilizzati secondo i termini permissivi applicabili e che tutti gli avvisi siano conservati. L'applicazione può mantenere una licenza non commerciale senza modificare la licenza del codice di terze parti distribuito con licenze permissive.

Si tratta di una conclusione **condizionata, non di un'autorizzazione alla pubblicazione dei binari**. Sono stati verificati il testo di licenza del binding `sqlcipher3` installato e la versione runtime di SQLCipher Community Edition. Restano da controllare gli artefatti effettivi della release, gli avvisi completi SQLCipher e le eventuali librerie crittografiche native incorporate. PySide6 non è utilizzato dal progetto ed è escluso dall’inventario attuale.

## 8. Lista di controllo per la conformità della release — v0.1.1-alpha

- [ ] Congelare l'ambiente di release effettivo e registrare versioni esatte dei pacchetti, nomi e hash degli artefatti.
- [x] Leggere la licenza del binding `sqlcipher3==0.6.3` installato e verificare la versione runtime (`4.12.0 community`; SQLite `3.51.1`).
- [ ] Esaminare la wheel/build da sorgente esatta destinata alla release per identificare collegamento e librerie native incluse; conservare il testo di licenza del binding.
- [ ] Includere copyright, condizioni di licenza ed esclusione di garanzia completi di SQLCipher Community Edition per ogni copia distribuita, oltre agli avvisi applicabili per SQLite/OpenSSL e gli altri componenti inclusi.
- [ ] Ottenere e conservare testi di licenza e avvisi di copyright autorevoli per dnspython, cryptography, cffi, pycparser e gli altri componenti ridistribuiti.
- [ ] Verificare se la release includa Tor, Python, Tcl/Tk o altri componenti di sistema, anziché richiederne soltanto l’installazione separata; confermare l’assenza di PySide6/Qt dagli artefatti.
- [ ] Verificare separatamente installer, archivio sorgente, wheel ed eventuali futuri pacchetti completi, considerando le dipendenze transitive e di build effettivamente distribuite.
- [ ] Rendere disponibili agli utenti finali gli avvisi richiesti, nella distribuzione e/o in un luogo accessibile collegato dall'applicazione.
- [ ] Confermare che il pacchetto finale includa `LICENSE`, `NOTICE` e gli avvisi applicabili alle terze parti, aggiornando questa verifica agli artefatti finali.

## 9. Esclusione di responsabilità

Questo documento è un prospetto di attribuzione e una verifica tecnica preliminare delle licenze, **non** una distinta completa dei componenti software, un sostituto dei testi di licenza upstream o un parere legale. Fanno fede i termini forniti dai rispettivi titolari dei diritti. Prima di dichiarare la piena conformità della distribuzione è opportuna una revisione legale qualificata.
