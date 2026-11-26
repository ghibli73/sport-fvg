# Vista "Partite" a settimane — Zuìn 1.15.0 beta (prototipo)

Risultati e calendario uniti in una sola vista, una settimana alla volta (lunedì–domenica, ora italiana Europe/Rome).
Tutto è calcolato nel browser da `data/risultati.json`: nessun campo nuovo nei dati, nessuna modifica agli script.

## Dove compare
- **Pagina del girone** (`#g-<gid>`): schede **Partite** (predefinita) e **Classifica**. Le vecchie schede Risultati e Calendario non ci sono più.
- **Scheda società** (`#s-<id>`): blocco "Partite di tutte le squadre" in cima a "Partite e classifica"; ogni partita ha sopra il campionato (tocco → girone, sulla stessa settimana).
- **Preferiti** e sezione **Partite** (`#risultati`, ex "Risultati"): blocco "Le partite delle mie squadre" (società preferite + gironi preferiti). Lo stato della settimana è condiviso tra le due viste.
- La voce della barra in basso, della barra in alto (computer) e della ruota in Home si chiama ora **Partite** (stessa icona e stesso hash `#risultati`). Il nastro dei risultati resta invariato.

## Navigazione
- Si apre sulla settimana in corso. Frecce ‹ › (44×44) con l'intervallo ("23–29 nov") e la distanza ("Settimana scorsa", "Tra 2 settimane"); pulsante oro **Oggi** quando non si è sulla settimana in corso.
- Scorrimento orizzontale col dito sull'elenco (≥ 60 px, prevalentemente orizzontale) = stesse azioni delle frecce. Le frecce ci sono sempre.
- Limiti: dalla settimana della prima partita (o quella corrente) a una settimana dopo l'ultima (o quella corrente).
- Animazione di 0,22 s solo senza `prefers-reduced-motion`; un'area `aria-live` annuncia la nuova settimana; il fuoco resta sulla freccia premuta.

## Contenuto di una settimana
- **Risultati** sopra (partite con risultato, in corso, in attesa di risultato, rinviate), **In programma** sotto (ora, campo con link alla mappa). Raggruppate per giorno ("Oggi · sabato 28 novembre · 9ª giornata"), in ordine di data e ora reali.
- Risultati provvisori/da omologare: stessa etichetta di prima (`provTag`); partite spostate negli ultimi 7 giorni: etichetta "Spostata"/"Orario cambiato" come prima (`varTag`).
- Oggi, partita senza risultato con ora passata: "in corso" (fino a 2 h 30) poi "risultato in arrivo". Data passata da 1 a 7 giorni senza risultato: "risultato in arrivo".

## Anticipi, recuperi, rinvii (regole)
- **Settimana della giornata**: per ogni girone e giornata si prende la **mediana (inferiore) delle date originali** delle partite di quella giornata (`data_prec` se la partita è stata spostata, altrimenti `data`). La settimana lun–dom che la contiene è la settimana della giornata.
- **Anticipo / Recupero**:
  1. se la partita ha `data_prec` in un'altra settimana rispetto a `data` → anticipo se la nuova data è prima, recupero se è dopo;
  2. altrimenti, se la settimana reale è diversa da quella della giornata **e** la data dista almeno 5 giorni dalla mediana → "Anticipo · giornata N" (prima) o "Recupero · giornata N" (dopo).
  La soglia di 5 giorni evita falsi positivi nei campionati giovanili che giocano la stessa giornata tra domenica e mercoledì.
- **Rinviata**: partita senza risultato con `rinviata: true`, oppure `stato`/`note` che contengono "rinvi"/"sospes" (oggi nessuno script scrive questi campi; sono pronti per il futuro), **oppure** data passata da più di 7 giorni senza risultato e senza nuova data (rinvio probabile; il tooltip dice "rinviata o in attesa del comunicato"). Resta nella sua settimana, tratteggiata e barrata, con "Rinviata".
- **Da recuperare (n)**: in cima alla **settimana corrente**, riquadro richiudibile con le rinviate degli ultimi 120 giorni del contesto (girone, società, preferiti); aperto se sono al massimo 3, chiuso altrimenti; ogni riga porta alla settimana originale. Quando la federazione fissa la nuova data la partita (con `data_prec` da `scripts/variazioni.py`) passa nella settimana del recupero con l'etichetta "Recupero".

## Settimane vuote e calendari incompleti
- Girone senza partite: "Calendario non ancora pubblicato".
- Settimana dopo l'ultima partita nota: se le giornate presenti sono meno di 2×(n−1) (n squadre in classifica; n se dispari) → "Calendario non ancora pubblicato" con l'ultima data in programma; altrimenti "Campionato concluso". Pulsante per andare all'ultima settimana con partite.
- Prima dell'inizio: "Il campionato non è ancora iniziato" + pulsante per la prima giornata.
- Settimana vuota dentro la stagione: "Nessuna partita in questa settimana" (turno di riposo/sosta) + "Prossime partite: …".
- Società e preferiti: nota se per alcuni campionati il calendario non arriva fino alla settimana mostrata.

## Prestazioni e accessibilità (misurate il 26/11/2026 con data simulata 28/11/2026)
- 11.542 partite in `risultati.json`; i dati per girone (mediane, prima/ultima data) sono calcolati una volta per versione dei dati (WeakMap). Con CPU rallentata 4×: girone Serie A 10 ms, cambio settimana 3 ms; società con 12 gironi 99 ms all'apertura, 23 ms al cambio; preferiti (5 società + 1 girone) 86–93 ms.
- axe-core (wcag2a/aa, 2.1, 2.2 aa, best-practice): 0 violazioni a 320, 390 e 1280 px, chiaro e scuro, su girone (settimana corrente e precedente), girone senza calendario, anticipo, scheda società, Preferiti, Partite. Tutti i comandi della vista ≥ 44 px (i nomi delle squadre sono pulsanti alti 44 px).
- Prova: `design/screenshot/partite/` (schermate, `navigazione-settimane.gif`, `tavola-riepilogo.png`).
