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

## Registro
(una riga per intervento: data — cosa — esito)
- 2026-11-25 — Repository ghibli73/sport-fvg creato dall'utente e caricato; volley.py validato sui portali reali: la pagina risultati è divisa in sezioni con link classifica.aspx?CId (le Coppe non hanno link) e ha la colonna "G" = giornata. Prima esecuzione: 60/60 gironi, partite 1184 → 1398, classifiche e partite coerenti in tutti i gironi. Restano 4 doppioni di giornata ereditati (U13 F UD gir. D, U12 F UD gir. C). Limiti del collegamento: niente API Pages/impostazioni Actions né download degli artifact (proxy); i log dei job si leggono con gh api .../actions/jobs/<id>/logs.
