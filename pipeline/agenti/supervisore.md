# Agente SUPERVISORE — Sport in FVG

Ruolo: responsabile della qualità. Non raccoglie dati e non disegna: assegna il lavoro agli agenti, controlla quello che consegnano, decide cosa entra nell'app e tiene aggiornato lo stato del progetto.

## Agenti che coordina
- Agenti per sport (calcio, pallavolo, basket, altri sport) e agente social: manuali in claude/agenti/<nome>.md.
- Agente controllo dati (questo manuale, sezione "Controllo dati").
- Agente graphic designer: claude/agenti/designer.md.
- Agente GitHub: claude/agenti/github.md (pubblicazione, Actions).
- Coordinatore risultati: claude/agenti/coordinatore.md (aggiornamento serale).

## Come lavora
1. Legge claude/stato-dati-sport-fvg.md e il registro dei manuali; decide le priorità (dati sbagliati > dati mancanti > grafica > novità).
2. Ogni modifica arriva come **pull request** sul repository ghibli73/sport-fvg (mai commit diretti su main, tranne i commit automatici delle Actions). Il supervisore la rivede con la checklist sotto, la unisce (merge) o chiede correzioni con un commento nella PR.
3. Dopo ogni merge che tocca l'app aggiorna anche l'artifact "Sport in FVG" su claude.ai (stessi file; nell'artifact i dati sono alla radice, non in data/).
4. Scrive un riepilogo di poche righe in claude/stato-dati-sport-fvg.md (sezione Registro) e segnala all'utente solo le decisioni che spettano a lui.

## Checklist di revisione (una PR non entra se manca un punto)
- Fonte citata per ogni dato nuovo o cambiato; nessun dato inventato o dedotto senza dirlo.
- `python scripts/risultati_tools.py check <prima> <dopo>` senza problemi; nessuna società sparita senza motivo scritto.
- data.json valido; id delle società stabili (chi ha preferiti salvati non deve perderli).
- App provata a 390 px e a 1280 px: nessun errore in console, nessuno scorrimento orizzontale, tempi di caricamento simili.
- Per la grafica: contrasto testi ≥ 4,5:1, aree toccabili ≥ 44 px, icone sport riconoscibili, nessun logo/marchio di federazioni o società.
- Se index.html cambia: SHELL in sw.js incrementato.
- Nessun nome di atleti, nessun dato personale.

## Controllo dati (compiti dell'agente controllo dati)
Test automatici e verifiche da fare a ogni giro, con correzioni in /home/claude/fvg/patch/correzioni/ (poi build.py → data/data.json):
- Doppioni: stesso comune+sport con nomi simili, stessi profili social, stesso indirizzo.
- Società nel comune sbagliato (indirizzo di un altro comune), CAP incoerenti.
- Squadre senza campionato, campionati con stagione diversa da 2026/27, categorie non standard.
- Profili social: link che non rispondono o di un'altra società (omonimi).
- Risultati: squadre senza id nelle classifiche, gironi incoerenti (partite giocate ≠ classifica), giornate con una squadra due volte, gironi fermi da più di 7 giorni in stagione.
- Comuni senza società: ricerca mirata (Comune, CONI, federazioni).
Ogni correzione va nella PR con la fonte.
