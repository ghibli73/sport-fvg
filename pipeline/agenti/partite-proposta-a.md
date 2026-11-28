# Sezione "Partite", proposta A: Zuìn 1.17.0 beta

L'utente ha approvato la proposta A dell'analisi di usabilità del 26/11/2026: prima si sceglie lo sport, poi il campionato. Tutto è calcolato nel browser da `data/risultati.json`. Non ci sono campi nuovi nei dati e nessuno script è stato toccato. Il codice è in index.html, nei blocchi che iniziano con "1.17.0".

## Un solo nome e un solo ordine
- La sezione si chiama **Partite** dappertutto: nastro della Home, barra in basso, barra in alto (computer), ruota e titolo della pagina. Hash invariato: `#risultati`.
- Gli sport seguono un solo ordine: **Calcio, Pallavolo, Basket**, poi gli altri per numero di società. Vale in Home (carosello), Partite, Sport, Comune, Mappa e Info. Il codice è in `SPPOP` / `spSort`.

## Ingresso di Partite (`#risultati` senza parametri)
1. **Questo weekend**: la settimana in corso, con le frecce di sempre.
   - Chi segue qualcosa vede solo le partite delle squadre, società e gironi che segue (contesto `f`).
   - Chi non segue nulla vede le partite **in evidenza** (contesto `e`, funzione `evidenza()`). Per calcio, pallavolo e basket si prendono i campionati più alti con squadre FVG in gioco nella settimana, finché ci sono almeno 2 partite per sport. Si mostrano solo le partite delle squadre FVG.
   - Restano in vista 3 partite. Le altre si aprono con "Mostra tutte le N partite" (`pweCompatta`).
2. **Cerca squadra o campionato** (`#rq`). Cerca nei nomi delle squadre (classifiche e partite) e dei campionati, con il nome breve del girone. Tutte le parole devono comparire, quindi "gonars 13" trova l'Under 13. L'indice si ricostruisce a ogni nuova versione dei dati.
   - Toccando una squadra si apre il suo girone con la squadra evidenziata. Invio apre il primo risultato, Esc cancella.
3. **Tessere degli sport**:
   - Calcio a tutta larghezza, poi Pallavolo e Basket.
   - Sotto, "Altri sport" con un pulsante per ogni altro sport con gironi. Sono tratteggiati quelli senza partite nei 30 giorni prima e dopo oggi.

## Dentro lo sport (`#risultati?sport=…`)
- Si sceglie tra **Prima squadra** e **Giovanili** (nuovo parametro `liv=p|g`; `livDi(g)` = giovanili se il campionato ha un'età). Il controllo compare solo se lo sport li ha entrambi.
- Sotto c'è la **barra dei campionati** di 1.16.0, filtrata per il livello scelto. Etichette per esteso: "Divisione Regionale 1", "Under 13", "Serie A2".
- **Zone come pulsanti**: Tutte le zone, Udine, Pordenone, Trieste e Gorizia, Regionale, Nazionale. Il genere resta com'era.
- I gironi sono raggruppati per **campionato e genere** (es. "Under 13 maschile", con `gGruppo`). Ogni riga ha un **nome breve e distinto** (`gBreve`/`gParti`), come "Udine B", "Gold · Girone A", "Provinciali · Trieste A" o "Tra comitati · Pordenone-Udine".
- Sotto il gruppo, le **sigle spiegate** (`SIGLE`): Eccellenza, Gold, Regionale, Provinciali/Regionali, Tra comitati, Area 3, Divisione Regionale.
- Sottotitolo su una riga: giornata · capolista (senza l'ente federale). A destra il pulsante **Classifica**, che apre il girone sulla scheda Classifica.
- Parametri compatibili: `sport`, `camp`, `genere`, `zona` come in 1.16.0. Se c'è `camp`, il livello si ricava dal campionato. Lo stato dello sport resta in `sfvg-ris` (`{s,l,c,g,z}`) e torna quando si ritocca la stessa tessera.

## Pagina del girone (`#g-<gid>`, hash invariato)
- Titolo breve: "Under 13 maschile · Udine B". Sottotitolo: sport · comitato (CT = Comitato territoriale, FVG) · stagione.
- Una riga di pulsanti: **Segui**, **Calendario**, **Avvisi** (pannello), **⋯** (pannello con "Metti sul tuo sito", "Condividi la classifica" e il nome ufficiale del girone).
- Se nella settimana in corso non si è giocato nulla (nessun risultato e nessuna partita con data fino a oggi), il girone si apre sull'**ultimo turno giocato** (`wkInizio`, etichetta "Ultimo turno giocato"). In fondo c'è il pulsante del turno successivo. Le frecce e "Oggi" funzionano come prima.
- In classifica c'è una stella per ogni squadra, per seguire **solo quella squadra**.
- **Indietro** torna da dove si veniva (`GBACK`, calcolato in `route()` con `origine()`): Home, Partite, sport, Preferiti, comune, Società o scheda della società. Con un link diretto torna allo sport e al campionato del girone.

## Dal nastro
Il pulsante del nastro porta l'indice della partita e la sua settimana. Nel girone la partita è **evidenziata** (bordo oro), portata al centro dello schermo e riceve il fuoco. Per i lettori di schermo è annunciata come "Partita che hai scelto". "‹ Home" torna alla Home.

## Preferiti: seguire una sola squadra
- Formato salvato in `sfvg-fav` (e nel cloud, se c'è): `{v:2, c:[società], g:[gironi], sq:["<gid>|<id società>" oppure "<gid>|n:<nome>"]}`.
- I preferiti 1.x (`{c,g}`) si leggono così come sono, con `sq` vuoto. Le versioni vecchie dell'app ignorano `sq`.
- Le stelle delle squadre sono in classifica e nella scheda della società (squadra principale e "Altre squadre"). Preferiti le elenca in "Squadre".
- Seguire una società vuol dire seguire tutte le sue squadre. Se di una società seguita si segue anche almeno una squadra, in Partite e nel nastro di quella società compaiono **solo le squadre con la stella**. In Preferiti lo dice una nota.
- Tolto il doppione: il blocco settimanale delle partite resta solo in Partite ("Questo weekend"). Preferiti ha il pulsante "Le loro partite: vai a Partite".

## Misure (28/11/2026, orologio simulato giovedì 26/11 alle 19, dati di main del 26/11)
- **Percorsi** (telefono 390×844, touch, DPR 2,5), prima → dopo:
  - **(a)** genitore Under 13: prima 5 tocchi, 5 passate, 1 schermata, e bisognava sapere il girone. Dopo 3 tocchi + "gonars 13" nella ricerca, oppure 5 tocchi e 1 passata dalle tessere con i gironi nominati "Udine A/B".
  - **(b)** classifica di Promozione: prima 3 tocchi e 2 passate, dopo 3 tocchi e 0 passate.
  - **(c)** apertura di Partite: prima 0 partite visibili, dopo 3 partite sopra la piega.
  - **(d)** 3 squadre di sport diversi: prima 15 partite a settimana, dopo 3.
  - **(e)** dal nastro: prima partita non evidenziata, dopo partita evidenziata e in vista, e "‹ Home" con 1 tocco.
- **axe-core** (wcag2a/aa, 2.1, 2.2 aa, best-practice): 0 violazioni a 320, 390 e 1280 px, chiaro e scuro. Viste controllate: Home, Partite, ricerca, basket giovanili, calcio, girone, pannelli, classifica, arrivo dal nastro, Preferiti, scheda società. Tutti i comandi nuovi sono almeno 44×44 px. Nessun errore JavaScript.
- **Prestazioni** con CPU 4×: ingresso Partite 84 ms alla prima apertura e poi 18–33 ms; liste degli sport 19–76 ms; girone 3–21 ms; primo tasto della ricerca (con l'indice) 36 ms, tasti successivi sotto i 10 ms.
- Prove: `design/screenshot/proposta-a/` (schermate dei percorsi, `percorso-genitore-under13.gif`, `percorso-dal-nastro.gif`, `tavola-prima-dopo.png`).
