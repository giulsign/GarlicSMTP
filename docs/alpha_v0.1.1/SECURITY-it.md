# Politica di sicurezza di GarlicSMTP

## Scopo e stato del progetto

GarlicSMTP è un software sensibile dal punto di vista della sicurezza, progettato per trasportare email attraverso i servizi Onion di Tor. Le segnalazioni relative a sicurezza e privacy sono benvenute.

Questa politica è in revisione per la **versione di sviluppo 0.1.1a0**, destinata a una futura release **v0.1.1-alpha**. Al momento della revisione, il tag Git e la pubblicazione di v0.1.1-alpha **non sono stati confermati**. La baseline v0.1.0-alpha.1 documentata in precedenza (commit sorgente `9bfc2f7`) è storica e non dimostra che v0.1.1-alpha sia stata pubblicata. Le modifiche di sviluppo più recenti discusse durante questa revisione sono associate al commit `8faf1c6`; tale commit non viene qui presentato come baseline di sicurezza certificata.

GarlicSMTP non è stato sottoposto a un audit di sicurezza professionale indipendente. La progettazione e i risultati dei test non garantiscono anonimato, riservatezza, integrità o resistenza alla compromissione degli endpoint. Prima di impiegarlo per comunicazioni sensibili, valutare l'ambiente di installazione e il modello di minaccia.

## Proprietà di sicurezza e relativi limiti

L'implementazione Alpha precedentemente verificata utilizza una chiave di cifratura dei dati (DEK) di 32 byte sbloccata mediante password e SQLCipher per i database Received, Sent e Queue. Il contenuto e i metadati degli allegati locali sono memorizzati in file autenticati GSAT v1. I flussi GUI e CLI della casella di posta sbloccano la DEK prima dell'accesso ai database; la ricezione SMTP utilizza un application builder dotato della DEK.

Controlli storici di sola lettura, eseguiti su una macchina di sviluppo e su una VM Ubuntu, non hanno rilevato intestazioni SQLite in chiaro nei database esaminati e hanno identificato il formato GSAT v1 nei file degli allegati controllati. Si è trattato di osservazioni limitate: **non** costituiscono un audit crittografico completo, un'analisi forense o una verifica di ogni file, elemento temporaneo, backup, chiave privata o configurazione di distribuzione. Non devono essere interpretati come prova che tutti i dati a riposo siano cifrati.

La precedente politica documentava una limitazione del bootstrap CLI `start`: in assenza della DEK terminava senza procedere. Prima della pubblicazione occorre verificare nel codice e nei test correnti se tale limitazione sia ancora presente nella release candidata. Questa politica non certifica alcuna migrazione di dati preesistenti in chiaro.

Nell'ambiente di sviluppo installato è stato osservato `sqlcipher3` 0.6.3 con SQLCipher `4.12.0 community` e SQLite `3.51.1`. Questo identifica le versioni osservate in tale ambiente, ma non verifica autonomamente tutti i binari distribuiti, le opzioni di compilazione o le proprietà crittografiche. Per dipendenze e licenze si rimanda a `THIRD_PARTY_LICENSES.md`.

Proteggere materiale di recupero, password, chiavi private, backup locali e sistema operativo host. La sicurezza dipende dalla loro gestione oltre che dal codice applicativo.

## Segnalazione di una vulnerabilità

Inviare le sospette vulnerabilità **in forma privata** a:

**giulisign@gmail.com**

Evitare la divulgazione pubblica prima che il manutentore abbia avuto un'opportunità ragionevole di indagare e coordinare una risposta appropriata. È una richiesta di divulgazione coordinata, non la promessa di un embargo o di un termine di risposta prestabilito.

Quando possibile, includere:

- versione o commit GarlicSMTP interessato e ambiente operativo;
- componente coinvolto e descrizione chiara del problema;
- passaggi minimi riproducibili o una dimostrazione di fattibilità sicura;
- comportamento atteso e osservato e potenziale impatto sulla sicurezza o sulla privacy;
- dettagli diagnostici pertinenti, privati di segreti e dati personali;
- eventuale mitigazione o correzione proposta.

**Non inviare** chiavi private dei servizi Onion, cookie di autenticazione Tor, password, segreti di recupero, chiavi crittografiche private, contenuti delle caselle di posta o altre credenziali. Se le prove contengono materiale sensibile, descriverlo senza allegarlo e richiedere prima una procedura sicura di gestione. Non presumere che la posta elettronica offra di per sé riservatezza end-to-end.

## Problemi inclusi nell'ambito

Esempi di segnalazioni rilevanti per la sicurezza:

- esposizione dell'indirizzo di rete di un utente o dell'identità di un servizio Onion;
- aggiramento dell'instradamento Tor previsto o connessioni clearnet inattese;
- aggiramento di autenticazione o autorizzazione e accesso non autorizzato alle caselle;
- esecuzione remota di codice, injection di comandi o protocolli e parsing non sicuro dei messaggi;
- esposizione di contenuti dei messaggi, allegati, metadati o materiale crittografico;
- errori nella cifratura, nell'autenticazione, nella verifica delle firme o nella gestione delle chiavi;
- log, file temporanei, backup o configurazioni non sicuri che espongono in modo significativo informazioni sensibili;
- vulnerabilità che indeboliscono in modo significativo le protezioni di privacy o anonimato previste.

I difetti funzionali senza un plausibile impatto sulla sicurezza possono essere gestiti tramite il normale processo di segnalazione. In caso di dubbio, segnalare privatamente.

## Vulnerabilità di terze parti

GarlicSMTP si appoggia a componenti di terze parti, inclusi pacchetti Python, SQLCipher e il demone Tor esterno. Le vulnerabilità originate in tali componenti dovrebbero in genere essere segnalate anche ai rispettivi canali di sicurezza upstream. Sono benvenute le segnalazioni quando l'integrazione in GarlicSMTP espone o amplifica l'impatto di un problema.

Un pacchetto installato nell'ambiente virtuale di uno sviluppatore non è necessariamente una dipendenza distribuita con GarlicSMTP. Sono il manifest runtime e gli artefatti effettivi della release, non il solo `pip freeze`, a determinare il contenuto della distribuzione.

## Tor e limiti dell'anonimato

I servizi Onion di Tor possono ridurre l'esposizione delle posizioni di rete degli endpoint comunicanti, ma **non forniscono anonimato assoluto**. Le minacce includono compromissione degli endpoint o del sistema operativo, dipendenze malevole, analisi o correlazione del traffico, metadati applicativi, identità persistenti dei servizi Onion, log non sicuri, errori di configurazione o crittografici ed esposizione di messaggi o chiavi memorizzati.

Tor non protegge le informazioni compromesse su un endpoint prima dell'ingresso o dopo l'uscita dal percorso di comunicazione protetto da Tor. Non presumere che contenuti applicativi, informazioni identificative o dati locali siano sicuri per il solo utilizzo di Tor.

## Informazioni sensibili e precauzioni operative

Un'installazione può contenere chiavi d'identità dei servizi Onion, materiale di autenticazione Tor, materiale di recupero, database delle caselle, messaggi in coda, allegati, identificativi di mittenti e destinatari, metadati e configurazioni. Non inserire tali materiali nel controllo versione, non allegarli a segnalazioni pubbliche e non condividerli in log non oscurati.

Limitare i permessi del filesystem, proteggere host e backup, esaminare log e file esportati e usare un ambiente controllato per i test di sicurezza. Sono precauzioni operative, non prove di una valutazione di sicurezza completata.

## Versioni supportate e manutenzione di sicurezza

La **candidata v0.1.1-alpha non è ancora una release pubblica confermata**. Questa politica non la designa come ramo con manutenzione di sicurezza garantita. La precedente baseline `v0.1.0-alpha.1` è storica e non è stato stabilito per essa alcun periodo di supporto garantito. Non presumere che commit precedenti, prerelease e snapshot di sviluppo ricevano correzioni di sicurezza.

Al momento della pubblicazione di una release, aggiornare questa sezione con il tag effettivamente pubblicato, il relativo commit sorgente e gli eventuali impegni di supporto. Fino ad allora, non dedurre garanzie di manutenzione di sicurezza da una stringa di versione o dal superamento dei test.

## Divulgazione coordinata e ricerca sulla sicurezza

Il manutentore intende compiere uno sforzo ragionevole per confermare la ricezione delle segnalazioni credibili, indagarne l'impatto, coordinare le correzioni quando appropriato, proteggere ove possibile le informazioni del segnalante e comunicare i risultati rilevanti quando ciò aiuta gli utenti. **Non è garantito alcun termine specifico per la presa in carico, la correzione o la pubblicazione.**

La ricerca in buona fede è benvenuta quando condotta legalmente e senza danneggiare intenzionalmente altre persone, sistemi o reti. Eseguire preferibilmente i test su sistemi e servizi Onion sotto il proprio controllo; evitare l'accesso a dati di terzi o l'interruzione di servizi.

## Revisione di sicurezza della release: verifiche ancora aperte

Prima di pubblicare v0.1.1-alpha, verificare rispetto al codice corrente e agli artefatti finali:

- versione effettiva, tag Git, commit sorgente e formulazione del supporto di sicurezza;
- eventuale persistenza della limitazione CLI `start` documentata;
- flussi correnti di sblocco della DEK, comportamento della cifratura dei database e gestione GSAT v1;
- gestione dei percorsi della pagina HTML Onion e di altre configurazioni influenzabili dall'esterno;
- log, file temporanei, backup, permessi delle chiavi e percorsi di errore;
- dipendenze runtime effettivamente distribuite e componenti nativi incorporati;
- risultati finali dei test ed eventuali limitazioni note rilevanti per la sicurezza.

Si tratta di **verifiche aperte**, non di dichiarazioni di test falliti o vulnerabilità scoperte. I 1.974 test precedentemente segnalati come superati rappresentano un risultato di test funzionali, non sostituiscono un audit di sicurezza.

## Nessuna garanzia di sicurezza

GarlicSMTP è fornito secondo le condizioni di garanzia e responsabilità della licenza applicabile al codice originale del progetto, PolyForm Noncommercial License 1.0.0. I componenti di terze parti mantengono le rispettive licenze.

Nulla in questa politica garantisce che GarlicSMTP sia sicuro, anonimo o adatto a uno specifico modello di minaccia.
