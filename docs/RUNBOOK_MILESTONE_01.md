GarlicSMTP – Manuale operativo

1\. Entrare nella directory del progetto

cd /mnt/c/GarlicSMTP



Verifica:



pwd



Output atteso:



/mnt/c/GarlicSMTP

2\. Attivare l'ambiente virtuale Python

source .venv/bin/activate



Il prompt deve diventare:



(.venv) giuliano@...

3\. Avviare GarlicSMTP (mittente)



In un primo terminale:



cd /mnt/c/GarlicSMTP

source .venv/bin/activate



python -m garlicsmtp.cli



Output atteso:



Runtime starting...

SMTP Server listening on 127.0.0.1:2525

QueueWorker started

Runtime ready



Lascia questo terminale aperto.



4\. Avviare il nodo ricevente



In un secondo terminale:



cd /mnt/c/GarlicSMTP

source .venv/bin/activate



Recupera l'hostname Onion del ricevente:



RECEIVER\_ONION=$(sudo cat /var/lib/tor/garlicsmtp\_receiver/hostname)



Avvia il receiver:



python -m tools.run\_onion\_receiver \\

&#x20;   --hostname "$RECEIVER\_ONION" \\

&#x20;   --port 2526 \\

&#x20;   --queue-db receiver-queue.db



Output atteso:



Runtime starting...

SMTP Server listening on 127.0.0.1:2526

Runtime ready



Lascia anche questo terminale aperto.



5\. Verificare che i due server siano in ascolto



In un terzo terminale:



ss -ltnp | grep -E '2525|2526'



Output atteso:



127.0.0.1:2525

127.0.0.1:2526

6\. Verificare il banner SMTP locale



Mittente:



printf 'QUIT\\r\\n' | nc 127.0.0.1 2525



Output:



220 garlicsmtp.local GarlicSMTP ready

221 Bye



Ricevente:



printf 'QUIT\\r\\n' | nc 127.0.0.1 2526



Output:



220 ...

221 Bye

7\. Verificare il servizio Onion del ricevente

RECEIVER\_ONION=$(sudo cat /var/lib/tor/garlicsmtp\_receiver/hostname)



python -m tools.check\_onion\_smtp \\

&#x20;   "$RECEIVER\_ONION"



Output atteso:



Connecting to Tor SOCKS5 proxy...

SOCKS5 tunnel established...

SMTP banner: 220 ...

8\. Caricare gli hostname Onion



Mittente:



SENDER\_ONION=$(sudo cat /var/lib/tor/garlicsmtp/hostname)



Ricevente:



RECEIVER\_ONION=$(sudo cat /var/lib/tor/garlicsmtp\_receiver/hostname)



Verifica:



echo "$SENDER\_ONION"

echo "$RECEIVER\_ONION"



Entrambi devono terminare con:



.onion

9\. Inviare una mail GarlicSMTP → GarlicSMTP

python -m tools.send\_onion\_mail \\

&#x20;   --from-address "alice@$SENDER\_ONION" \\

&#x20;   --to-address "bob@$RECEIVER\_ONION" \\

&#x20;   --hostname "$SENDER\_ONION" \\

&#x20;   --subject "Prima mail GarlicSMTP" \\

&#x20;   --body "GarlicSMTP to GarlicSMTP over Tor."



Output atteso:



Delivery accepted

10\. Verificare che la mail sia stata ricevuta



Aprire il database:



sqlite3 receiver-queue.db



Numero di messaggi:



SELECT COUNT(\*) FROM queue\_items;



Output atteso:



1



Visualizzare il contenuto:



SELECT payload FROM queue\_items;



Verificare che siano presenti:



mittente

destinatario

Subject

Body



Uscire da SQLite:



.quit

11\. Verificare gli hostname Onion



Mittente:



sudo cat /var/lib/tor/garlicsmtp/hostname



Ricevente:



sudo cat /var/lib/tor/garlicsmtp\_receiver/hostname

12\. Arrestare i server



Nei terminali del mittente e del ricevente:



Ctrl+C



Non usare Ctrl+Z, che sospende il processo lasciando aperte le connessioni.



13\. Controllare che non siano rimasti processi in ascolto

ss -ltnp | grep -E '2525|2526'



Non deve essere restituito alcun risultato.

