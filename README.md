# Sport in FVG

App web (PWA) con le società sportive dei 215 comuni del Friuli Venezia Giulia, i loro campionati, classifiche e risultati.
Applicazione indipendente e non ufficiale: i dati provengono dalle pubblicazioni ufficiali delle federazioni (FIPAV, FIP, LND FVG e altre), sempre citate.

## Struttura
- `index.html` — l'app (un solo file, nessuna dipendenza da compilare).
- `manifest.webmanifest`, `sw.js`, `icons/` — installazione sul telefono e funzionamento offline.
- `data/data.json` — società (id, comune, sport, indirizzo, squadre 2026/27, storico, social).
- `data/comuni.json` — i 215 comuni ISTAT.
- `data/risultati.json` — gironi: classifica, tutte le partite, prossima giornata.
- `config/pallavolo.json` — gironi FIPAV seguiti dallo script, con la tabella nome squadra → id società.
- `scripts/volley.py` — aggiornamento automatico della pallavolo (nessuna AI).
- `scripts/genera_config.py` — rigenera `config/pallavolo.json` da `data/risultati.json`.
- `scripts/risultati_tools.py` — `split` / `build` / `check` dei gironi.
- `.github/workflows/` — aggiornamento pianificato e diagnosi.
- `note-legali.html` — note legali e privacy (da completare).

## Pubblicazione
Vedi [GUIDA.md](GUIDA.md).

## Principi sui dati
Nessun dato inventato; abbinamenti squadra → società solo se certi; classifiche ricalcolate dichiarate come tali;
letture lente e poco frequenti dei portali (una pausa tra le richieste, User-Agent riconoscibile); fonte sempre indicata.
