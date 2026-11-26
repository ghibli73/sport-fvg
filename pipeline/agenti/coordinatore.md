# Agente COORDINATORE RISULTATI — Sport in FVG

Scopo: aggiornare ogni settimana classifiche, risultati e calendari di tutti i campionati FVG (tutte le categorie, giovanili comprese) nell'app "Sport in FVG", coordinando gli agenti specializzati per sport.
App: artefatto slug `bcd5f4b7-0208-4f42-9b8a-48f566922058` (https://claude.ai/artifact/QKTaVE8W2PiMyZdcn8ieLX), file `risultati.json` (stato completo dei gironi), `data.json` (società, id), `index.html`.

## Materiale nel progetto "Sport FvG"
- claude/agenti/formato-risultati.md — formato di un girone (classifica, tutte le partite con giornata, prossima giornata).
- claude/strumenti/risultati_tools.py — `split` (risultati.json → un file per girone), `build` (cartella → risultati.json), `check` (confronto vecchio/nuovo prima di pubblicare).
- Manuali degli agenti: claude/agenti/pallavolo.md, basket.md, calcio.md (fonti, URL, codici dei gironi, abbinamenti sponsor → società, sezione "Per i risultati in tempo reale").

## Procedura (ogni esecuzione parte da zero)
1. Prepara la cartella di lavoro: scarica dal progetto risultati_tools.py, formato-risultati.md e i manuali; scarica dall'artefatto risultati.json e data.json (read_file / list_files sull'artefatto). `python3 risultati_tools.py split risultati.json gironi/`.
2. Decidi chi lavora oggi in base al calendario delle pubblicazioni:
   - Pallavolo (portali FIPAV regionale, Udine, Pordenone, Trieste-Gorizia: le stesse fonti dell'app Bale): risultati disponibili dal lunedì; pagina risultati con DataDa=<lunedì>.
   - Basket (FIP FVG): omologazioni del Giudice Sportivo tra martedì e venerdì; archivio media filtrato con &after=<ultima data>.
   - Calcio (LND FVG): CU regionale del giovedì; Delegazioni mercoledì (PN) e giovedì (UD, GO, TS).
3. Avvia in parallelo (al massimo 3 alla volta, per il limite d'uso dell'account) un agente per sport. A ciascuno dai: il suo manuale, il formato, la cartella gironi/<sport>/ già popolata e la regola "aggiungi solo le giornate nuove dopo il campo aggiornato di ogni girone; aggiorna classifica (ufficiale o calcolata), giornata, aggiornato; aggiungi l'intera giornata successiva; non toccare i gironi non aggiornabili; nessun dato inventato; abbina gli id solo se certi". Chiedi di coprire tutte le categorie: prima i campionati senior, poi le giovanili, e di aggiornare il proprio manuale se una fonte cambia.
4. Quando tornano: `build gironi/ data.json nuovo.json`, poi `check risultati.json nuovo.json`. Se il check segnala gironi spariti, squadre in meno, date o giornate tornate indietro, correggi o scarta quel girone (tieni la versione vecchia). Controlla a campione 2–3 classifiche contro la fonte.
5. Pubblica solo risultati.json sull'artefatto (publish_files, modalità patch, base_version dall'ultima get_artifact). Non toccare index.html né data.json salvo correzioni d'abbinamento.
6. Aggiorna nel progetto i manuali cambiati e il registro qui sotto (data, gironi aggiornati per sport, problemi).

## Controllo serale: gironi nazionali "agente"
I gironi nazionali automatici (`auto: "naz"`, Serie A e SuperLega) si aggiornano da soli con il workflow "Aggiorna nazionali".
Nel controllo serale (domenica e lunedì sera, e dopo i turni infrasettimanali) aggiornare i gironi nazionali `auto: "agente"`
secondo `pipeline/agenti/nazionali.md`: Serie D girone C (Sonda `testo2=Round@@...betexplorer.../results/` e `/fixtures/`, poi
`scripts/nazionali_manuale.py serie_d_c ...`), e secondo `pipeline/agenti/sport-altri-nazionali.md` basket LBA/A2/A2 femminile,
A1 femminile pallavolo, rugby, pallamano, hockey, bocce. Dopo ogni girone: `python scripts/risultati_tools.py check`, ics.py,
widget_dati.py. Controllare che nessuna squadra compaia due volte nella stessa giornata e che nessuna partita futura abbia un risultato
(`scripts/variazioni.py prima dopo --prova` stampa entrambi i controlli).

## Copertura attuale (24/11/2026)
- Pallavolo: 4 gironi regionali (C e D M/F) + gironi CT Udine e altri territoriali in caricamento; obiettivo 63 gironi.
- Basket: Serie C girone D; in corso DR1, DR2, DR3, C femminile, giovanili; B Interregionale dal CR Veneto.
- Calcio: Eccellenza, Promozione, Prima A e B (giornate 1–11, classifica calcolata); da fare Seconda/Terza delle Delegazioni e giovanili.

## Registro
- 24/11/2026: prima costruzione (agenti specializzati avviati dalla sessione principale).
