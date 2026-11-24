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
6. **Aggiornare l'app**: le modifiche a `index.html` (stesso codice dell'artifact, ma con `fetch('data/...')`) vanno provate in locale a 390 px senza errori prima del commit. Dopo modifiche a index.html incrementare `SHELL` in `sw.js` (`sportfvg-shell-vN`) così i telefoni scaricano la nuova versione.

## Regole
- Mai cancellare dati esistenti per sostituirli con dati peggiori (meno squadre, date più vecchie).
- Mai forzare push (`--force`) né riscrivere la storia di `main`.
- Messaggi di commit in italiano, chiari ("Pallavolo: corretto parser classifiche CT Udine").
- Ritmo di lettura dei portali: lasciare la pausa di `PAUSA` in volley.py, non aumentare la frequenza dei cron oltre quella attuale.
- Dati personali: nessun nome di atleti; solo società, squadre, risultati.

## Registro
(una riga per intervento: data — cosa — esito)
