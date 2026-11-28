# Calendario della squadra — Zuìn 1.20.0 beta

Richiesta dell'utente: «La squadra preferita deve avere un tasto agenda per far apparire tutto il calendario dalla prima
all'ultima partita». Tutta la vista è calcolata nel browser da `data/risultati.json` (nessun campo nuovo nei dati);
per l'iscrizione al calendario del telefono `scripts/ics.py` scrive un file `.ics` per squadra.
Codice in index.html: blocco «1.20.0 Calendario della squadra» (`vCalSq`, `calRiga`, `calSquadra`, `calChiave`, `calCl`).

## Dove c'è il pulsante «Calendario» (icona agenda A+1)
- **Preferiti › Squadre**: pulsante con testo «Calendario» sotto ogni squadra seguita; nelle squadre delle società seguite
  icona agenda sotto la stella.
- **Home**: accanto alla riga «Le tue squadre» (apre la prima squadra seguita; dalla vista si passa alle altre coi chip).
- **Scheda società**: «Calendario» sulla squadra principale (accanto a «Classifica e risultati del girone») e icona agenda
  accanto alla stella di ogni altra squadra.
- **Classifica del girone**: icona agenda accanto alla stella di ogni squadra, anche non seguita (aggiunta dopo il disegno
  della tabella da `calCl`, senza toccare la riga della classifica).
Tutti i pulsanti sono di almeno 44×44 px e hanno l'etichetta «Calendario di <squadra> <campionato>».

## La vista (`#cal-<gid>--<chiave>`)
- **Chiave** della squadra: id della società se in quel girone la società ha una sola squadra; altrimenti `n-` + nome
  normalizzato (minuscole, senza accenti, caratteri non alfanumerici → `-`, massimo 60 caratteri). Stessa regola in
  `calChiave()` (index.html, blocco `CALSQ-CHIAVI`) e `squadre()` (scripts/ics.py). Gli altri hash non cambiano; un link a
  una squadra che non c'è più mostra «Squadra non trovata».
- In alto i **chip** «Le tue squadre» (squadre con la stella e tutte le squadre delle società seguite; prima quelle della
  stessa società; c'è anche la squadra aperta se non è seguita). Il chip cambia squadra senza aggiungere passi alla
  cronologia; il fuoco resta sul chip.
- **Riepilogo**: giocate su totale, vinte, (pari: nel calcio o se ce ne sono), perse, posizione e punti, prossima partita
  con «Vai a oggi nel calendario», numero di rinviate da recuperare; pulsanti Segui/Seguita (stella della singola
  squadra, formato `{v:2,c,g,sq}`), **Classifica** (apre il girone sulla classifica), **Condividi** (link della vista);
  «Aggiungi al calendario del telefono».
- **Elenco**: tutte le partite con data, dalla prima all'ultima, per mese (intestazione agganciata sotto la barra blu con
  numero di partite e vinte/perse). Ogni riga: giorno, In casa/Trasferta, avversario (tocco → scheda società o comune),
  giornata, ora, campo con link alla mappa (solo per le partite da giocare), risultato con **Vinta/Persa/Pari scritto**
  (più la striscia colorata), stati come nella vista Partite: «da omologare»/«provvisorio» (`provTag`), «Rinviata»
  (`wkStato` = r, riga tratteggiata), «in corso»/«risultato in attesa», «Anticipo/Recupero · giornata N» (`wkSpost`),
  «Spostata · era il …» o «Orario cambiato» (`data_prec`/`ora_prec`).
- **Oggi**: riga gialla «Oggi · sabato 28 novembre · prossima tra N giorni» nel punto giusto dell'elenco (se il mese
  corrente non ha partite compare da sola). All'apertura la pagina scorre in modo che si vedano l'ultima partita giocata,
  la riga Oggi e la prossima partita (bordo oro, «Prossima partita»); il fuoco va al titolo per i lettori di schermo.
- In fondo: «Fine del calendario» oppure «Dopo il … il calendario ufficiale non è ancora pubblicato».
- Nessuna modifica alle righe partita della vista Partite (`wkRow`) né a Info: le righe del calendario sono `calRiga`.
  I campi della 1.19.0 (`stato_gara`, `esito`, `data_cal`) arrivano già attraverso `rinvEsplicita`, `wkSpost` e `provTag`.

## Calendario del telefono
- **Abbonati al calendario** (consigliato): `webcal://ghibli73.github.io/sport-fvg/data/ics/squadra/<gid>--<chiave>.ics`.
  Il telefono riscarica il file da solo (REFRESH-INTERVAL 6 ore): orari cambiati, rinvii e risultati si aggiornano.
  Su computer: Google Calendar › Altri calendari › Da URL con l'indirizzo https.
- **Scarica il file**: stesso contenuto generato nel browser (copia che non si aggiorna).
- File: tutte le partite della stagione della squadra in quel girone (giocate con il risultato nel titolo), stessi UID
  dei calendari delle società e dei download dell'app (nessun doppione se si usano insieme), durata 2 ore, fuso
  Europe/Rome, senza ora = giornata intera. Nome del calendario «Zuìn · <squadra> · <categoria> <girone>».
- `python scripts/ics.py` scrive `data/ics/<id_società>.ics` (come prima) e `data/ics/squadra/*.ics` per ogni squadra
  con partite (28/11/2026: 1.765 file, 25.689 eventi, circa 15 MB; ~1 s); toglie i file delle squadre che non ci sono
  più; un errore nei calendari delle squadre non blocca né gli altri file né il workflow.
- **Workflow**: nessuna modifica necessaria. `aggiorna-calcio/basket/pallavolo.yml`, `giro-rapido.yml` e
  `aggiorna-nazionali.yml` eseguono già `scripts/ics.py` quando i dati cambiano e salvano `data/` (che comprende
  `data/ics/squadra/`) con `scripts/salva_dati.sh`; in caso di conflitto `salva_dati.sh` rilancia `ics.py` dopo l'unione.
- Controllo: `node tests/calendario-squadra.test.js` (dopo `python scripts/ics.py`) confronta le chiavi dell'app con i file:
  esce con 1 se manca un file o ce n'è uno in più.

## Misure (28/11/2026, orologio simulato sabato 28/11 ore 12, dati di main del 28/11)
- axe-core (wcag2a/aa, 2.1, 2.2 aa, best-practice): **0 violazioni** a 320, 390 e 1280 px, chiaro e scuro, su Home,
  Preferiti, calendario (squadra seguita, società seguita, chip cambiato, pannello calendario aperto, squadra non seguita
  dalla classifica, squadra con due formazioni della stessa società), classifica, scheda società. Nessun errore JS,
  nessuno scorrimento orizzontale; tutti i comandi nuovi ≥ 44 px.
- Prestazioni con CPU 4× (telefono 390 px): apertura del calendario 35–81 ms la prima volta (Serie A, 38 partite: 44 ms),
  8–18 ms le successive.
- Schermate e tavola: `design/screenshot/calendario-squadra/` (`tavola-riepilogo.png`).
