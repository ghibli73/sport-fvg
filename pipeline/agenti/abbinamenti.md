# Agente ABBINAMENTI — squadre dei gironi ↔ società di data/data.json

Scopo: ogni squadra del FVG che compare nei gironi di `data/risultati.json` (classifica[].id, partite[].id_casa / id_ospite) deve essere agganciata a una società di `data/data.json`; se la società non è certa, almeno al COMUNE in cui gioca. Le squadre di altre regioni restano senza id (è corretto).
Molte squadre giocano col nome dello sponsor ("Colli Volley", "Fly Solartech Icarus", "Nautilus Allestimenti") o con un nome diverso da quello della società: l'abbinamento per nome non basta.

## Regola d'oro
- Abbinare alla SOCIETÀ solo con una prova certa, scritta in `config/abbinamenti_prove.json`.
- Con un solo indizio (es. stesso impianto) si assegna solo il COMUNE del campo di casa (`config/squadre_comune.json`), con la spiegazione.
- Mai cambiare un id già presente; mai inventare. Nessun nome di atleti.

## Prove, in ordine di forza
1. **Pallavolo — ID società FIPAV.** Il logo nelle classifiche (`classifica.aspx?CId=`) ha il percorso `mngArea/Societa/img/<ID>/...` e lo stesso numero è il valore `SId` del menu "Società" delle pagine risultati. Due modi di usarlo:
   - **Filtro per società (il più forte, funziona anche per le squadre SENZA logo):**
     `https://udine.federvolley.it/risultati-classifiche.aspx?DataDa=<lunedì gg%2fmm%2faaaa>&StatoGara=&CId=&SId=<ID>&PId=15544&btFiltro=CERCA`
     (stessa forma per Pordenone PId=7581, Trieste-Gorizia PId=7285, regionale `ComitatoId=28&...&PId=7274`). Elenca SOLO le gare delle squadre iscritte da quella società nella settimana: se la squadra compare, è sua. Si legge con WebFetch (prompt: "Elenca tutte le gare: campionato, casa, ospite, impianto; indica quale voce del menu Società è selezionata"). Scegliere una settimana in cui la squadra ha giocato.
   - **Tabella SId → nome società:** workflow "Sonda fonti" con `opzioni=<url pagina risultati>` (stampa i `<option value>` di tutti i menu). Al 25/11/2026 è riportata in fondo a questo file. Con `loghi=<url classifica>` stampa l'ID logo di ogni riga di classifica.
   - Elenco ID logo → società già noti: `pipeline/agenti/pallavolo.md`; classifiche con ID logo: `pipeline/patch/volley-squadre/_gironi.tsv`.
2. **Basket — FIP.** I calendari definitivi FIP danno la palestra (non il codice società); le omologazioni neanche. Prove valide: sponsor già abbinato con certezza in un altro campionato (`pipeline/agenti/basket.md`) + stessa palestra della società; oppure palestra della società + campionato dichiarato in `data.json` ("attuale") senza altre squadre della società nel girone.
3. **Calcio — LND.** Nome nei Comunicati = nome della società a meno di sigle (ASD, SSD, G.S., ...) o del troncamento a 25 caratteri ("CENTRO ATLETICO RICREATIV"), E la società in `data.json` ha squadre negli stessi campionati/gironi (campo "squadre"). I gironi calcio non hanno il campo di gioco.
4. **Impianto** (campo "campo" delle partite) confrontato con "indirizzo" delle società: stesso impianto o stessa via = indizio forte, ma serve una seconda prova.
5. **Siti/profili/notizie ufficiali** della società che citano la squadra (WebSearch/WebFetch; curl verso l'esterno è bloccato). Nel giro del 25/11/2026 le ricerche web non hanno dato prove utili per le squadre di basket.

## Dove si salva
| Sport | Abbinamento a società | Lettura nello script |
|---|---|---|
| pallavolo | `config/pallavolo.json` → `gironi[].alias` {"NOME SQUADRA": "id"} del girone | `scripts/volley.py` |
| basket | `config/basket/<slug>.json` → `ids` {"Nome squadra": "id"} | `scripts/basket.py` |
| calcio, calcio a 5 | `config/calcio_alias.json` {"NOME LND": "id"} (vale per tutti i gironi) | `scripts/calcio.py` |
| sport "agente" (baseball, bocce, rugby, ...) | direttamente in `data/risultati.json` | — |
Sempre anche: una voce in `config/abbinamenti_prove.json` `[{"nome","sport","id","prova","fonte","gironi"?}]` ("gironi" limita l'abbinamento a quei gid).
Solo comune: `config/squadre_comune.json` `{"<nome squadra come nel girone>": {"comune": "<ISTAT>", "prova": "..."}}`. Il nome si confronta senza maiuscole/spazi/punteggiatura, in tutti i gironi; il comune si scrive solo dove manca l'id.

## Codice
- `scripts/abbinamenti.py`: `applica_comuni(gironi)` scrive `classifica[].comune` e `partite[].comune_casa` / `comune_ospite` (ISTAT) alle squadre senza id e li toglie a quelle con id; `applica_id(gironi)` mette gli id di `abbinamenti_prove.json` dove mancano.
- `volley.py`, `basket.py`, `calcio.py` chiamano `applica_comuni` subito prima di scrivere `data/risultati.json` (gli id arrivano dai loro alias).
- `scripts/applica_abbinamenti.py [--prova]`: applica subito id e comuni al `data/risultati.json` attuale. Dopo: `python scripts/risultati_tools.py check <copia prima> data/risultati.json`.
- App (`index.html`, dalla 1.8.1): in classifica e partite il nome con id apre la scheda (`#s-<id>`); senza id ma con comune è un link alla pagina del comune (`#c-<ISTAT>`) con la scritta piccola "gioca a <Comune>". La scheda società mostra i risultati di tutte le squadre con il suo id, quindi anche quelle appena abbinate.

## Procedura per i nuovi gironi
1. Elenco delle squadre senza id per girone, con le partite in casa e il campo (script di esempio: confronto classifica/partite, ultimo campo di casa).
2. Escludere le squadre di altre regioni (Portogruaro, Concordia, Annone, Fossalta, ...: restano senza id). Attenzione: una squadra che gioca fuori regione può essere iscritta da una società FVG (es. APC Lifetime Center Cinto = A.P.D. Comunale Chions, ID FIPAV 2459).
3. Cercare la prova (ordine sopra); scriverla in `abbinamenti_prove.json` e nell'alias dello sport; oppure il comune in `squadre_comune.json`.
4. `python scripts/applica_abbinamenti.py`, `risultati_tools.py check`, `python scripts/test_dati.py` (la voce "id_mancante" deve scendere), prova dell'app a 390 px.
5. Se la società non esiste in `data.json` (es. ASD Le Volpi, A.S.D. Torriana) si mette il comune e si segnala all'agente delle società.

## Stato al 25/11/2026
Prima: 105 righe-girone di squadre FVG senza id (calcio 74, basket 16, pallavolo 8, calcio a 5 3, baseball 2, bocce 2). Dopo: 81 agganciate a società, 19 solo al comune, 5 senza nulla (COMETAZZURRA ×3: società non in data.json e nessun campo nei dati calcio; COLLEDANI SRL U15 UD: sponsor senza palestra nei dati; ASD Bocciofila Pasch (PN): località non individuata).
Da verificare in seguito: BIN Tigrotte, Monritz Team Sport, Nautilus Allestimenti, WIS 1963 Woman Spilimbergo, Basket Fiume, Pallacanestro Feletto, MB Paper's, Ronchi Basket Club, Trieste (A2 F) — solo comune.
Nota: l'utente indicava Colli Volley come squadra di CSI Tarcento, ma il portale FIPAV la elenca sotto VOLLEY TEAM 87 (SId 2560, Tricesimo) e non sotto CSI Tarcento (SId 2556).

## Stato al 26/11/2026
- Nuova prova per il BASKET (la più forte): le pagine giornata del portale `https://fip.it/risultati/?group=campionati-regionali&regione_codice=RFR&comitato_codice=RFR&sesso=<M|F>&codice_campionato=<...>&codice_fase=1&codice_girone=<...>&codice_ar=1&giornata=1` elencano, per ogni squadra, il CODICE SOCIETÀ FIP e la ragione sociale (codici girone in `config/basket_fip.json`; U13 UD A = U13S/M 86367, U15 reg. UD = U15S/M 85879, U15 reg. GO-TS = 85877). Si legge con WebFetch (curl è bloccato dal proxy).
- Agganciate: MB Paper's e Colledani srl = Centro Sedia Basket (006955); Ronchi Basket Club, Gereon Engineering e Nautilus Allestimenti = Ronchi Basket Club 054710 = "Fidema Group Ronchi" (031016-3, rinominata); WIS 1963 Woman Spilimbergo = Vis Spilimbergo (000794); BIN Tigrotte = Libertas Gym e Basket (054257); "Trieste" A2 femminile = Futurosa (051844); COMETAZZURRA = A.S.D. Cometazzura (030114-4).
- Società nuove (patch/correzioni): A.S.D. Pallacanestro Feletto (030118-14, FIP 005261, distinta da Feletto Basketball Academy 055339), A.S.D. Basket Fiume (093021-10, FIP 040527), Monritz Team Sport A.S.D. (032006-139, FIP 052094), A.S.D. Torriana (031008-7, FIPAV 2443), A.S. Dil. Le Volpi (032006-140, FIPAV 3632), A.S.D. Bocciofila Codroipese (030027-11), ASD Azzanese Softball (093005-15), Castionese softball (030020-2).
- Ancora aperte: Basket Maniago-Pol. Montereale (squadra congiunta, solo comune; girone FIP non trovato), ASD Bocciofila Pasch (PN) (località non trovata), San Lorenzo Bears e 3 B Italia Ponte Baseball (sede non indicata da FIBS), ECOPROJECT TECHNOLOGIES (B Interregionale, probabilmente fuori regione, non verificata).

### SId FIPAV → società (menu Società dei 4 portali, 25/11/2026)
2437 A.S.D. Olympia · 2438 PSD CCS Naš Prapor · 2439 A.S. O.K. Val · 2440 A.S.D. U.S. Azzurra · 2443 A.S.D. Torriana · 2444 A.S.D. Pallavolo Grado · 2445 A.R. Fincantieri · 2447 G.S. Pallavolo Mossa · 2449 U.S.D. Pallavolo ACLI Ronchi · 2450 A.S.D. Pallavolo Pieris · 2451 ASD Soča · 2452 A.S.D. Pallavolo Staranzano · 2453 ASD Pol. Libertas Turriaco · 2455 G.S. Pall. Arzene Valvasone · 2457 Pallavolo Brugnera 96 · 2458 A.S.D. Volley del Sanvitese · 2459 A.P.D. Comunale Chions · 2460 ASD U.S. Cordenons · 2461 A.S.D. Futura (Cordenons) · 2462 A.S.D. Insieme per Pordenone · 2465 A.S.D. Libertas Fiume Veneto · 2467 ASD Virtus Volley Fontanafredda · 2468 Polisportiva Montereale · 2470 A.S.D. Pol. S.Giorgio Domovip Porcia · 2471 A.S.D. Blu Volley Pordenone · 2473 Centro Sp. Prata di Pordenone · 2475 APD Roveredana Vis et Virtus · 2476 GIS Volley Sacile · 2477 Volley San Quirino · 2479 G.S. Favria · 2481 Pol. Aquila Spilimberghese · 2482 Ass. Polisportiva Travesio · 2483 A.S.D. Pol. Polisigma · 2484 C.S.D. Sokol · 2485 ASD Breg · 2486 ASD Centro Gioco Sport Coselli · 2496 U.S.D. Sloga · 2498 S.D. Kontovel · 2499 A.S.D. C.U.S. Trieste · 2500 Volley Club Trieste · 2503 Pallavolo Altura · 2507 A.P.S. Triestina Volley · 2510 ASD OFP Azzurra RDR · 2511 A.S.D. Aiello Volley · 2513 ASPA Pallavolo Artegna · 2514 Pallavolo Buia · 2517 PAV Bressa · 2518 A.P.D. Cassacco · 2519 ASD Sporting Club Cervignano · 2521 Volley Cividale · 2522 Volley Codroipo · 2523 Pallavolo Faedis · 2524 C.S.R. Chei de Vile · 2526 A.S.D. Volley Ball Gemona · 2527 Pol. Libertas Gonars · 2528 ASD Low West V.R. M. Gaspari · 2529 Pol. Com. Lestizza · 2531 A.S. Majanese · 2532 Pol. Libertas Martignacco · 2534 A.S.D. Muzzana · 2536 Futura Palmanova · 2537 A.S.D. Pallavolo Paluzza · 2538 A.S.D. Pasian di Prato Volley · 2539 A.S.D. Blu Team · 2540 A.S.D. Olimpia · 2544 C.C.R. Il Pozzo · 2546 A.S.D. Rojalese · 2548 Stella Volley · 2550 S.D. Pallavolo Sangiorgina · 2552 PAV Natisonia · 2553 APD San Leonardo · 2555 SSD Volley Talmassons · 2556 Centro Sport. Italiano Tarcento · 2557 Kennedy Adegliacco · 2559 Volley Ball Carnia · 2560 Volley Team 87 · 2562 Dopolavoro Ferroviario Udine · 2563 A.P.D. Rizzi Udine · 2566 Volleybas · 2568 Aurora Volley Udine · 2569 A.S.D. Vivil · 2666 Eurovolleyschool · 2973 ASD Moraro Volley · 3168 A.S.D. Intrepida Mariano · 3462 Arcobaleno Mavrica · 3625 Farravolo · 3632 A.S. Dil. Le Volpi · 3762 Chions Fiume Volley · 3792 A.S.D. Olympia Trieste Muggia · 3814 Maniago Volley · 3843 ASD Alta Resa · 4435 Fox Volley · 5182 Cordovado Volley · 5183 Aviano Dragonflies · 5295 S.C.S.D. Rojalkennedy · 5795 Sporting Porcia ASD.
