# Agente AGENDA EVENTI — Zuìn (Sport in FVG)

Ruolo: tiene aggiornata l'agenda delle gare e manifestazioni degli sport individuali (quelli che non si giocano a campionato) in `data/agenda.json`, mostrata nell'app nella vista `#agenda` (dalla 1.12.0 beta).

## Dati
- `data/agenda.json`: lista di eventi dal giorno corrente ai 6 mesi successivi (183 giorni), che si svolgono in FVG o sono organizzati da una società del FVG. La rigenera `scripts/agenda.py`.
- Formato: `id` (fnv1a di data|titolo|luogo, con prefisso `ag-`), `data`, `data_fine`?, `ora`?, `titolo`, `sport` (chiave di data.json: le arti marziali, il pugilato e la kickboxing stanno sotto `judo`; triathlon e orienteering sotto `altro`), `disciplina`?, `livello` (internazionale|nazionale|regionale|provinciale|promozionale), `luogo`, `comune`? (ISTAT), `prov`? (solo se la fonte dà la provincia e non il comune), `organizzatore`? (id di data.json se l'abbinamento è certo, altrimenti il nome come scritto nella fonte; assente se la fonte non lo indica), `societa`? (altri id di società indicate, solo negli eventi manuali), `categorie`?, `link`, `fonte`, `aggiornato`, `pos`? ([lat, lon] del centro del comune da `config/geocodifica_cache.json`, per "Vicino a me"), `origine` (modulo o `manuale`).
- `config/agenda_manuale.json`: `{"nota", "aggiornato", "eventi": [...]}` con lo stesso formato (l'`id` si può omettere). Lo script li conserva sempre; a parità di id vince il manuale.
- Regole: nessun dato inventato o dedotto (il comune non si ricava dalla sede della società; l'organizzatore non si indovina), nessun nome di atleti, ogni evento con la sua fonte.

## Fonti automatiche (scripts/agenda.py, un modulo per fonte)
| Sport | Modulo | Fonte | Come |
|---|---|---|---|
| Atletica, corsa su strada, trail, cross | `fidal` | https://www.fidal.it/calendario.php?anno=AAAA&mese=M&livello=REG&new_regione=FRIULIVENEZIAGIULIA&new_tipo=0&new_categoria=&submit=Invia (e `livello=COD` per le nazionali, filtrate su UD/PN/GO/TS) | tabella HTML; la "Pagina Regionale" doppia di una nazionale viene tolta |
| Sci alpino (e fondo quando esce) | `fisi` | https://comitati.fisi.org/friuli-venezia-giulia/wp-json/wp/v2/media?search=calendario | PDF "Calendario ... AAAA-AAAA" della stagione, tabelle lette con pdfplumber per intestazione (DATA, LOCALITÀ, ORGANIZZAZIONE, DENOMINAZIONE, SPEC.) |
| Ciclismo, MTB, ciclocross | `fci` | https://www.fcifriuli.com/calendario-gare-ciclistiche-friuli-venezia-giulia/ | tabella TablePress (data, settore, specialità, categoria, società, gara, località); il 25/11/2026 contiene solo il 2026, senza gare future |
| Vela | `fiv` | https://federvela.it/regate/ | righe `em-row` con attributi `data-*`, solo `data-zon="XIII"` |
| Pattinaggio | `fisr` | https://www.fisrfvg.it/core/base_calendario_zona.php?IDZona=1..4&anno=AAAA | tabella per provincia (1 TS, 2 UD, 3 GO, 4 PN); premiazioni e riunioni escluse |
| Judo, karate, lotta | `fijlkam` | https://www.fijlkam.it/fvg/gare-ed-eventi-friuli-venezia-giulia.html | blocchi `eventi-item`; si tengono solo quelli con sede in un comune FVG |
| Bocce | `fib` | https://www.federbocce.it/friuliveneziagiulia/gare.html | modulo POST `calendario=27` (stagione ottobre-settembre), poi `?start=100...`; la fonte dà solo la provincia |

Il workflow `.github/workflows/aggiorna-agenda.yml` gira ogni giorno alle 3:17 UTC (gruppo di concorrenza `aggiorna-dati`), committa `data/` come gli altri; lancio manuale con `opzioni` (`--prova`, `--debug`, `--solo fidal,fisi`). Nelle pull request che toccano lo script gira da solo in `--prova`. Se un modulo va in errore o non trova niente mentre prima aveva eventi, restano quelli già presenti (avviso nel log).

Prova dal proprio branch senza workflow sul main: `Sonda fonti` con `prove=agenda=--debug` (opzioni separate da virgola) oppure `prove=agendajson` (rigenera e stampa il JSON tra `@@INIZIO_AGENDA@@` e `@@FINE_AGENDA@@`). Altri modi della sonda per esplorare una pagina: `grezzo=<url>`, `cercah=<regex>@@<url>`, `da=<regex>@@<url>`; nell'URL `~` sta per `&`, nella regex `,,` per `|` e `LT` per `<`.

## Fonti manuali (config/agenda_manuale.json, controllo mensile)
Al 25/11/2026 il file è vuoto: il giro di ricerca si è fermato per il limite d'uso. Fonti da controllare ogni mese:
- Pugilato e kickboxing: comitato FPI FVG (nessun calendario pubblico trovato), federkombat.it (sezione FVG).
- Ciclocross: federciclismo.it, PDF "campionati regionali e top class regionali ciclocross 2026 2027" (download/5469/calendari-ciclocross) e comunicati FCI FVG (download/5797).
- Sci di fondo, scialpinismo: PDF "CALENDARIO-FONDO-FVG-AAAA-AA" sul sito FISI FVG (di solito a dicembre; il modulo `fisi` lo legge da solo se il nome contiene la stagione).
- Karate e judo regionali: calendario karate e PAR judo FIJLKAM FVG (`/fvg/comunicati-e-circolari/karate/...calendario-AAAA/file.html`, `/fvg/judo/comunicati-e-circolari-judo/par-AAAA.html`).
- Nuoto: FIN FVG (fonte non ancora trovata); Scherma: friuliveneziagiulia.federscherma.it; Tennistavolo: fvg.fitet.org (news); Tennis: fitp.it; Ginnastica: federginnastica.it (circolari); Triathlon: fitri.it (il calendario rispondeva 503); Orienteering: fiso.it (PDF in `_files/f_media/`); Canottaggio e canoa: canottaggio.org (`wp-content/uploads/<anno>/<mese>/`), federcanoa; Tiro: fitarco-italia.org, UITS, FITAV; Danza sportiva: FIDS.
- Grandi eventi: turismofvg.it/eventi (con il circolo o la società organizzatrice).

## Procedura mensile
1. Leggere il log dell'ultimo "Aggiorna agenda eventi": nessun modulo con `!`; se un modulo dà 0 eventi da più settimane in stagione, lanciarlo con `--debug --solo <modulo>` e correggere il parser.
2. A dicembre-gennaio controllare che escano i calendari 2027 (FIDAL regionale, FCI 2027, FISR 2027, FIV XIII Zona, fondo FISI): i moduli li prendono da soli; se cambia il nome o la pagina, aggiornare il modulo.
3. Fonti manuali: per ogni sport dell'elenco sopra cercare gli eventi dei prossimi 6 mesi e aggiungerli a `config/agenda_manuale.json` con `fonte` e `link`; togliere quelli annullati. `organizzatore` = id di data.json solo se il nome coincide senza dubbi.
4. Aprire una PR (il workflow gira in prova sulla PR); dopo il merge il giro notturno rigenera `data/agenda.json`.

## App (index.html)
- Vista `#agenda` (raggiungibile da Home "Tutta l'agenda" e da Sport "Agenda eventi"; nessuna voce nuova nella barra in basso): filtri sport, provincia, comune; "Vicino a me" (30 km dal centro del comune, posizione mai salvata); "Questo weekend" in evidenza; elenco per mese.
- Scheda evento `#e-<id>`: quando, Aggiungi al calendario (.ics nel browser, UID `<id>@zuin-fvg`), pagina ufficiale, mappa, luogo con link al comune, organizzatore (scheda società se c'è l'id), livello, categorie, fonte.
- Scheda società: "Prossimi eventi" (organizzati o con la società indicata in `societa`). Home: blocco "Prossimi eventi" (3 righe). Sport: elenco per gli sport senza girone in `data/risultati.json`; vista Società filtrata per uno di quegli sport: 3 prossimi eventi.
