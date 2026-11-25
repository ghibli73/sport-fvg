# Agente "GitHub Sport FVG" — manuale operativo

Ruolo: custode del repository `sport-fvg` su GitHub (sito su GitHub Pages + aggiornamenti automatici con GitHub Actions).
Non raccoglie dati sportivi: pubblica quelli prodotti dagli script e dagli agenti per sport, controlla che gli automatismi funzionino e li ripara.

## Prerequisiti
- Repository collegato alla sessione con `add_repo` (owner/sport-fvg, access "push"). Senza collegamento: guidare l'utente con GUIDA.md e fermarsi.
- Per leggere le esecuzioni delle Actions: `gh run list` / `gh run view --log-failed` (gh è già configurato quando il repo è collegato).

## Compiti
1. **Prima pubblicazione**: accompagnare l'utente nei passi di GUIDA.md; verificare che Pages risponda e che il primo "Diagnosi pallavolo" sia verde.
2. **Validare lo scraper pallavolo** (`scripts/volley.py`): alla prima esecuzione scaricare l'artifact `pagine-portali` della Diagnosi, controllare che `parse_classifica` e `parse_gare` leggano le tabelle reali; se no, correggere i parser sulle pagine salvate e riprovare con `--solo <slug>`.
3. **Sorveglianza**: se "Aggiorna pallavolo" fallisce o i gironi hanno `aggiornato` vecchio di più di 7 giorni in stagione → leggere il log, correggere, aprire un commit con spiegazione.
4. **Pubblicare i risultati degli agenti** (basket, calcio, gironi giovanili): il coordinatore produce `risultati.json`; prima di ogni commit eseguire
   `python scripts/risultati_tools.py check <vecchio> <nuovo>` e committare solo se non segnala perdite.
5. **Nuovi gironi pallavolo**: aggiungerli a `data/risultati.json` o a mano in `config/pallavolo.json` (host, cid, pid, comitato_id, alias), poi `python scripts/genera_config.py`.
6. **Aggiornare l'app**: le modifiche a `index.html` (stesso codice dell'artifact, ma con `fetch('data/...')`) vanno provate in locale a 390 px senza errori prima del commit. Dopo modifiche a index.html incrementare `SHELL` in `sw.js` (`sportfvg-shell-vN`) così i telefoni scaricano la nuova versione, e aggiornare `VERSIONE` e `VERSIONE_DATA` in index.html (mostrate in piccolo nella pagina Info: 1.x.0 per novità, 1.1.x per correzioni).

## Regole
- Mai cancellare dati esistenti per sostituirli con dati peggiori (meno squadre, date più vecchie).
- Mai forzare push (`--force`) né riscrivere la storia di `main`.
- Messaggi di commit in italiano, chiari ("Pallavolo: corretto parser classifiche CT Udine").
- Ritmo di lettura dei portali: lasciare la pausa di `PAUSA` in volley.py, non aumentare la frequenza dei cron oltre quella attuale.
- Dati personali: nessun nome di atleti; solo società, squadre, risultati.

## Funzioni
- **Calendario (.ics)** — dalla 1.4.0.
  - In app: "Aggiungi al calendario" (pagina girone: tutte le partite future del girone; scheda società: le partite future di ciascuna squadra) genera il file nel browser. "Abbonati al calendario" apre `webcal://ghibli73.github.io/sport-fvg/data/ics/<id_società>.ics`.
  - `scripts/ics.py` scrive `data/ics/<id_società>.ics` per ogni società che compare in `data/risultati.json` (partite giocate negli ultimi 30 giorni con il risultato nel titolo + tutte quelle future; durata 2 ore, fuso Europe/Rome, senza ora = evento di giornata intera). UID stabili e identici a quelli generati dall'app; i file delle società senza più partite vengono tolti. Non fa mai fallire il workflow.
  - Workflow: passo "Calendari delle società (data/ics)" in `aggiorna-calcio/basket/pallavolo.yml`, prima del commit; il commit ora usa `git status --porcelain` per vedere anche i file nuovi.
- **Condividi** — dalla 1.4.0, solo nel browser: immagine 1080×1350 (classifica prime 8, risultati di una giornata, singola partita) con logo, "Zuìn · Sport in FVG" e indirizzo del sito; Web Share API con file se disponibile, altrimenti download del PNG.
- **Avvisi dei preferiti (ntfy.sh)** — dalla 1.5.0, gratuiti e senza account.
  - Argomento pubblico per società: `zuin-fvg-<id società>` (caratteri non alfanumerici → `-`), es. `zuin-fvg-030001-1`. In app: "Ricevi avvisi" nella scheda società (solo se ha partite) e nei Preferiti, con link a `https://ntfy.sh/<argomento>` e alle app ntfy per Android e iPhone.
  - `scripts/avvisi.py [prima] [dopo] [--prova]`: confronta `/tmp/risultati_prima.json` con `data/risultati.json`; per ogni partita che ha appena ricevuto il risultato (prima senza risultato, oppure nuova con data negli ultimi 3 giorni) pubblica su ntfy per le due società: titolo "Casa 3-1 Ospite", testo = girone, Click → `#g-<gid>`, Tags trophy. Massimo 200 avvisi, pausa 0,3 s, su 429 attende e riprova, al massimo 8 minuti. Esce sempre con 0. `--prova` stampa soltanto.
  - Workflow: passo "Avvisi dei risultati (ntfy.sh)" dopo i controlli e prima di ics/commit in `aggiorna-*.yml`; il lancio manuale ha l'input `silenzioso` (casella) che li disattiva (variabile SILENZIOSO).
  - Privacy: argomenti pubblici, nessun dato personale (spiegato in Info e in note-legali.html).
- **Mappa** — dalla 1.6.0.
  - `scripts/geocodifica.py [--max-minuti N] [--solo-cache]`: cerca con Nominatim (OpenStreetMap) il centro di ogni comune e l'indirizzo di ogni società (dalla prima parte che sembra una via: Via, Piazza, Loc., ...; poi la stessa via senza numero), 1 richiesta ogni 1,1 s, User-Agent `Zuin-SportFVG/1.0`. Scarta i punti fuori regione o a più di 20 km dal centro del comune; se l'indirizzo non si trova usa il centro del comune. Scrive `data/luoghi.json` `{id: [lat, lon, "indirizzo"|"comune"]}`; cache in `config/geocodifica_cache.json` (committata: i giri successivi chiedono solo gli indirizzi nuovi; gli errori di rete non vanno in cache).
  - Workflow manuale `.github/workflows/geocodifica.yml` (workflow_dispatch, input `max_minuti`): esegue lo script e committa luoghi + cache nel branch da cui è lanciato. Rilanciarlo dopo aver aggiunto società o corretto indirizzi. Gruppo di concorrenza proprio (`geocodifica`), non blocca gli aggiornamenti dei risultati.
  - In app: vista `#mappa` (pulsante "Mappa" in Comuni, "Vedi sulla mappa" nella scheda comune). Leaflet 1.9.4 da unpkg (con SRI) caricato solo all'apertura, tessere OpenStreetMap con attribuzione, segnaposti per sport raggruppati a griglia, filtro per sport, "Vicino a me" (geolocalizzazione chiesta solo al tocco, mai salvata) con le partite di sabato e domenica delle squadre di casa entro 15 km. Il service worker non mette in cache unpkg né le tessere (ignora tutte le richieste verso altri siti).

- **Abbinamenti squadre → società / comune** — dalla 1.8.1. Manuale: `pipeline/agenti/abbinamenti.md`.
  - Prove in `config/abbinamenti_prove.json`; id negli alias degli script (`config/pallavolo.json` alias, `config/basket/*.json` ids, `config/calcio_alias.json`); squadre agganciate solo al comune in `config/squadre_comune.json` (ISTAT).
  - `scripts/abbinamenti.py` (`applica_comuni`) è chiamato da volley/basket/calcio.py prima di scrivere `data/risultati.json`: righe di classifica senza id → `comune`, partite → `comune_casa`/`comune_ospite`. `scripts/applica_abbinamenti.py` applica subito id e comuni al file attuale (rilanciarlo dopo un conflitto su data/risultati.json).
  - In app il nome di una squadra senza id ma con comune porta a `#c-<ISTAT>` con "gioca a <Comune>".
  - Sonda fonti: nuovi modi `opzioni=<url>` (valori dei menu, es. SId società FIPAV) e `loghi=<url classifica>` (ID società dei loghi). Non mettere `&` nudi negli URL passati alla sonda (la shell del workflow li interpreta): usare URL senza `&` o metterli per ultimi.

## Registro
(una riga per intervento: data — cosa — esito)
- 2026-11-25 — Repository ghibli73/sport-fvg creato dall'utente e caricato; volley.py validato sui portali reali: la pagina risultati è divisa in sezioni con link classifica.aspx?CId (le Coppe non hanno link) e ha la colonna "G" = giornata. Prima esecuzione: 60/60 gironi, partite 1184 → 1398, classifiche e partite coerenti in tutti i gironi. Restano 4 doppioni di giornata ereditati (U13 F UD gir. D, U12 F UD gir. C). Limiti del collegamento: niente API Pages/impostazioni Actions né download degli artifact (proxy); i log dei job si leggono con gh api .../actions/jobs/<id>/logs.
- 2026-11-25 — Abbinamenti (1.8.1 beta): squadre FVG senza id da 105 a 24 righe-girone (81 agganciate a società con prova, 19 solo comune, 5 senza nulla); Colli Volley risulta di Volley Team 87 (FIPAV SId 2560), non di CSI Tarcento — branch dati/abbinamenti.
