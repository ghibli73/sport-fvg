# Agente PALLAVOLO FVG (FIPAV: Comitato Regionale + Territoriali Udine, Pordenone, Trieste-Gorizia)

Ambito: tutte le categorie da Under 12 in su, maschile e femminile: Under 12, 13, 14, 15, 16, 17, 18, 19; Prima, Seconda, Terza Divisione; Serie D, C; nazionali B2, B1, B, A3, A2, A1/SuperLega.
Nel campo "categoria" usa: Under 12 … Under 19, Prima squadra, Seconda squadra (poi Terza/Quarta squadra se la società ha più squadre senior dello stesso genere); nel "campionato" la denominazione ufficiale con girone; "id_fonte" = CId del girone.
ATTENZIONE merge (build.py): le voci "squadre" sono fuse per chiave categoria+genere, anche dentro la stessa patch. Due squadre della stessa categoria e genere vanno distinte: "Under 17", "Under 17 (2ª squadra)", …; senior: Prima/Seconda/Terza squadra in ordine di livello. Il campo "note" e "indirizzo" della patch SOSTITUISCONO quelli esistenti: se aggiungi una nota, riparti da quella già in app/data.json.

## Fonti verificate (aggiornato 24/11/2026, stagione 2026/27)
Tutti i portali sono la piattaforma PowerSPORT (stessa struttura). Si leggono con WebFetch (curl/Bash è bloccato dal proxy: 403 per udine.federvolley.it e *.portalefipav.net).

### Pagine risultati (gare della settimana corrente + link a classifiche e calendari di tutti i gironi)
- Regionale: https://friulivg.portalefipav.net/risultati-classifiche.aspx?ComitatoId=28&PId=7274
- Udine: https://udine.federvolley.it/risultati-classifiche.aspx?PId=15544 (pagina ~110k caratteri: serve una seconda lettura con offset 100000)
- Pordenone: https://pordenone.portalefipav.net/risultati-classifiche.aspx?PId=7581 (include la sezione "CAMPIONATI NAZIONALI" con le gare in casa delle squadre PN in B, B2, A1)
- Trieste-Gorizia: https://trieste.portalefipav.net/risultati-classifiche.aspx?PId=7285
Le pagine senza PId (es. pordenone.portalefipav.net/risultati-classifiche.aspx) caricano la stagione corrente e reindirizzano al PId sopra.

### Classifica di un girone
https://<portale>/classifica.aspx?CId=<CId>  (es. https://udine.federvolley.it/classifica.aspx?CId=92400). Il CId è nazionale: funziona su qualunque dei portali, ma usa quello del comitato.
Formato: titolo "Classifica <campionato>", tabella pos | squadra | punti | PG (anche V/P, set). Per ogni squadra c'è il logo con percorso mngArea/Societa/img/<ID SOCIETÀ>/Loghi/LogoS<ID>.png: l'ID è il codice interno della società che ha iscritto la squadra, uguale su tutti i portali FVG. È la chiave migliore per abbinare le squadre col nome dello sponsor (squadre con "no-image.png" = società senza logo: abbinare per nome/palestra).
Prompt WebFetch efficace: "Riporta il titolo del girone e, per ogni squadra in classifica, una riga nel formato: pos|NOME SQUADRA|punti|PG|numero nel percorso del logo".

### CId dei gironi 2026/27
Regionale (CR FVG): Serie C F girone unico 92843; Serie C M girone unico 92844; Serie D F girone unico 92845; Serie D M girone unico 92846. (Nel filtro compaiono anche Coppa Regionale F/M e Supercoppa B2 FVG, senza classifica.)
Udine: 1ª Div F 92400; 1ª Div M 92402; 2ª Div F gir. A 92405, gir. B 92406; U19 F 92410; U17 F gir. A 92414, B 92415, C 92416; U15 F gir. A 93676, B 93677, C 93678, D 93679; U14 F gir. A 92422, B 92423; U13 F gir. A 92432, B 92433, C 94276, D 94330; U12 F gir. A 94277, B 94278, C 94279; U12 Misto Udine 94465 (dal 27/11/2026; nelle pagine risultati la sezione non ha link classifica: config "sezione" = titolo della tabella).
Interterritoriali (stesse classifiche sui portali UD/PN/TS): U19 M PN-UD 94136; U17 M PN-UD 93940; U15 M PN-UD gir. A 93944, gir. B 93945; U14 M TSGO-UD-PN 93759.
Pordenone: 1ª Div M 93936; 1ª Div F 93614; 2ª Div F 93615; U19 F 93710; U17 F gir. A 93617, B 93618; U15 F gir. A 93619, B 93620; U14 F gir. A 93621, B 93622; Coppa Autunno U13 F gir. A 94207, B 94208; Coppa Autunno U12 Misto gir. A 94211, B 94212. "Campionati Nazionali": nessun CId (solo calendario c=3B0E3B26223422342A2632043E766B6F796C72).
Trieste-Gorizia (nessun Under 12 al 27/11/2026; nuovi U13 F 6vs6 gir. A 94888, B 94889 non configurati): 1ª Div M 93458; 1ª Div F 93451; 2ª Div F gir. A 93456, gir. B 93457; U19 M 93582; U19 F gir. A 93459, B 93460; U17 M 93583; U17 F gir. A 93462, B 93463, C 93464; U15 M 93584; U15 F gir. A 93466, B 93467; U14 F gir. A 93468, B 93469.
Nessuna Terza Divisione né Under 16/18 nei 4 comitati nel 2026/27 (al 24/11/2026). Udine e TS-GO non hanno sezione nazionali.

### ID società (logo) -> società (abbinamenti usati nella patch volley-squadre)
2437 ASD Olympia (Slovolley) · 2439 A.S. O.K. Val (Slovolley Val) · 2440 U.S. Azzurra GO · 2443 A.S.D. Torriana (comune non verificato) · 2445 A.R. Fincantieri · 2447 Pallavolo Mossa · 2449 ACLI Ronchi (Tigers) · 2450 Pallavolo Pieris (AL.MA., F.lli Tamburin) · 2451 Soča (Soca, Socaslovolley) · 2452 Pallavolo Staranzano (Tikitaka, Geko Gold, Mavi, Autoscuola EDI) · 2453 Libertas Turriaco (Cassa Rurale FVG Turriaco) · 2455 Arzene Valvasone (Tecneco, Trevisan Metalmeccanica) · 2457 Brugnera 96 · 2458 Volley del Sanvitese (Ur-Bun) · 2459 ? (APC Lifetime Center Cinto, non abbinata) · 2460 US Cordenons (De Bortoli, Bielectra, Farout, Economy Rent, Centro Gomme, Autofficina Cordenonese, PCA, Parpinelli, Snoopy Pub) · 2461 A.S.D. Futura Cordenons (Piera1899, Futura …) · 2462 Insieme per Pordenone (Pordenone Volley; per esclusione) · 2465 Libertas Fiume Veneto (anche "Fox Volley U15") · 2467 Virtus Volley Fontanafredda (Maeg, Eidos, The Gammon, Degusto, Farmacia di Nave; per palestra) · 2468 Pol. Montereale (Casamercato) · 2470 PSG Domovip Porcia · 2471 Blu Volley PN · 2473 Centro Sp. Prata = VPA · 2475 Roveredana Vis et Virtus (Gefion, Union Volley Academy PN in Serie C) · 2476 GIS Sacile · 2479 GSD Favria (Marcolin Arredamenti SV) · 2481 Aquila Spilimberghese · 2482 A.P. Travesio (Valli Pordenonesi Volley) · 2483 Pol. Polisigma Zoppola (per esclusione, da confermare) · 2484 Sokol (Zalet ZKB in Serie C F) · 2486 Coselli · 2496 Sloga (Zalet Sloga) · 2498 Kontovel · 2499 CUS Trieste · 2500 Volley Club Trieste (Rosso, Revolution, Filo…via, Vitalfrutta) · 2503 Pallavolo Altura (Climatrieste, TVA Academy) · 2507 Triestina Volley (Uniclima/Mamaca TSV, Tre Merli Volley, TNT Pub Ruggine) · 2510 OFP Azzurra RDR · 2513 ASPA Artegna (Art_Cento) · 2514 Pallavolo Buia (Maschio, Farmacia Da Re e Canova, Severoli) · 2518 APD Cassacco (Cjassa) · 2519 Sporting Club Cervignano · 2521 Volley Cividale (ASFJR 1971) · 2522 Volley Codroipo (Horizon …) · 2524 Chei de Vile · 2526 Volley Ball Gemona (Gemona La Perla) · 2529 Pol. Com. Lestizza · 2531 Majanese · 2532 Libertas Martignacco (Itas Ceccarelli Group in Serie C F) · 2534 Muzzana · 2536 Futura Palmanova (Futura-Libertas U15) · 2537 Paluzza (Legnolandia Val-But) · 2538 Pasian di Prato (Ingegni) · 2539 Blu Team (FVG Volley Academy) · 2544 Il Pozzo (Siel) · 2546 Rojalese (Credifriuli, RK Blu) · 2552 PAV Natisonia · 2553 APD San Leonardo · 2555 SSD Volley Talmassons (CDA Volley Lignano, Zaniboni Snack) · 2556 CSI Tarcento (Art_Cento) · 2557 Kennedy Adegliacco · 2559 Volley Ball Carnia · 2562 DLF Udine · 2563 Rizzi Udine (IMQ, FTV, Blanc) · 2566 Volleybas (Gaia, Gesteco) · 2568 Aurora Volley Udine (anche "Club Aurora") · 2569 Vivil (Villadies) · 2666 Eurovolleyschool (System Volley) · 3168 Intrepida Mariano (Cassa Rurale FVG in Serie D M) · 3462 Arcobaleno Mavrica (Glasmik) · 3625 Farravolo · 3632 ASD Le Volpi (comune non verificato) · 3762 Chions Fiume Volley (CFV) · 3792 Olympia Trieste Muggia · 3814 Maniago · 3843 ASD Alta Resa (Union Volley Academy PN U19) · 4435 Fox Volley · 5182 Cordovado · 5183 Aviano Dragonflies (Mida, Sol.E, Pandam, Rist. San Giorgio) · 5295 S.C.S.D. Rojalkennedy.
Senza logo: Stella Volley, Sangiorgina (Projectvolley), Libertas Gonars, Factory Volley Faedis, L.W.V. (Low West Latisana), Aiello, Pav Bressa, Olimpia Porpetto (Project Volley Olimpia), Moraro, Grado, Naš Prapor, San Quirino, Alta Resa (1ª Div M).
Attribuite il 25/11/2026 col filtro Società (SId) delle pagine risultati (vedi pipeline/agenti/abbinamenti.md): Colli Volley = Volley Team 87 (SId 2560, Tricesimo), Talmastella Pink = Stella Volley (2548), St. Dentistico Cian = PAV Bressa (2517), Futura-Libertas U14 F = Futura Palmanova (2536), APC Lifetime Center Cinto = A.P.D. Comunale Chions (2459). ASD Le Volpi (3632, Trieste) e A.S.D. Torriana (2443, Gradisca d'Isonzo) non sono in data.json: solo comune.

### Elenco società per comitato
Il filtro "Società" delle pagine risultati elenca le società con squadre in quel comitato (testo leggibile con WebFetch, i "value" no). Udine anche: https://udine.federvolley.it/societa-affiliate-fipav-udine (codici 07.032.xxxx).

### Nazionali
- Portale CT Pordenone, sezione "Campionati Nazionali" (solo gare della settimana, codice serie: "B A" = Serie B M girone A, B2 girone A, A1): Tinet Prata (A1/SuperLega M, in casa al PalaCrisafulli, Via F.lli Rosselli 4, Pordenone), A.S.D. Libertas PN (Serie B M gir. A, Fiume Veneto), Pordenone Volley (B2 F gir. A, Palestra Gallini), CFV - IZC Costruzioni (B2 F gir. A, Villotta di Chions).
- CDA Talmassons: Serie A1 F 2026/27 (Corriere dello Sport, 06/11/2026). Fonti di lega: legavolley.it, legavolleyfemminile.it (non lette in questo giro).
- Le Serie B/B1/B2 di squadre UD e TS-GO non compaiono nei portali territoriali: da cercare su federvolley.it (non trovato con 1 ricerca).

### Fonti che NON funzionano
- https://www.portalefipav.net/CalendarioGare.asp?c=… : bloccato a WebFetch (robots_disallowed). Usare le pagine risultati-classifiche.
- curl da Bash: proxy 403 su udine.federvolley.it e *.portalefipav.net.
- WebFetch non legge i "value" dei menu (StId/PId di altre stagioni, ID società nel filtro).
- Le gare non hanno link individuali (solo icone).

## Per i risultati in tempo reale
1. Risultati di giornata e calendario della settimana: aprire la pagina risultati del comitato (URL sopra). Mostra la settimana corrente (lun-dom, es. "dal 23/11/2026 al 29/11/2026") raggruppata per girone: numero gara, data/ora, casa, ospite, risultato in set ("-" se da disputare) e impianto con indirizzo. Le partite della settimana sono quindi tutte quelle elencate; stato "da disputare"/disputata. Prompt utile: "Elenca ogni gara: sezione | numero gara | data ora | casa | ospite | risultato | impianto".
   - Udine: pagina lunga, leggere anche con offset 100000.
   - Pordenone: in fondo la sezione "CAMPIONATI NAZIONALI" (gare interne delle squadre PN in A1, B, B2).
2. Classifica aggiornata: https://<portale>/classifica.aspx?CId=<CId> (CId sopra; id_fonte delle squadre in app = "CId=<n>"). Si aggiorna dopo ogni giornata; il menu "Classifica alla giornata n°" non ha URL leggibili.
   - SETTIMANE PRECEDENTI (verificato 24/11/2026 su tutti e 4 i portali): filtro via URL con il lunedì della settimana in DataDa (gg%2fmm%2faaaa), CId vuoto:
     Regionale: https://friulivg.portalefipav.net/risultati-classifiche.aspx?ComitatoId=28&DataDa=16%2f11%2f2026&StatoGara=&CId=&SId=&PId=7274&btFiltro=CERCA
     Udine: https://udine.federvolley.it/risultati-classifiche.aspx?DataDa=16%2f11%2f2026&StatoGara=&CId=&SId=&PId=15544&btFiltro=CERCA
     Pordenone: https://pordenone.portalefipav.net/risultati-classifiche.aspx?DataDa=16%2f11%2f2026&StatoGara=&CId=&SId=&PId=7581&btFiltro=CERCA
     Trieste-Gorizia: https://trieste.portalefipav.net/risultati-classifiche.aspx?DataDa=16%2f11%2f2026&StatoGara=&CId=&SId=&PId=7285&btFiltro=CERCA
     Per le gare disputate: risultato in set + parziali. Il parametro CId=<n> NON filtra (dà "Nessuna gara trovata"). Gare rinviate: compaiono nella settimana originale con "-" e poi nella settimana del recupero.
   - Stagione 2026/27: tutti i campionati sono partiti la settimana del 12/10/2026 (05/10: nessuna gara). U13/U12 Udine dal 09/11, U14 M interterritoriale dal 22/11, 1ª Div F TS-GO dal 26/10.
   - Prompt WebFetch che funziona: "Estrai dalla tabella le gare delle sezioni X, Y. Per ciascuna gara riporta su una riga, separati da barre verticali: sezione, numero gara, data e ora, squadra di casa, squadra ospite, risultato, parziali separati da spazi, impianto e comune. Copia i nomi delle squadre come sono scritti nella pagina." NON usare formati imperativi tipo "formato esatto ...|...": sulle pagine lunghe il modello li scambia per istruzioni nascoste nella pagina e rifiuta.
   - Udine (pagina ~110k caratteri): 2 letture per settimana (Divisioni+U19+U17 F; U15/U14/U13/U12 F + U14 M) più una con offset 85000-90000 per U17 M e U15 M (stanno in fondo). Regionale, Pordenone e Trieste: 1 lettura per settimana. Nelle settimane vecchie la pagina UD è più corta e basta 1 lettura con "tutte le sezioni".
   - A volte il modello unisce i parziali senza spazi ("11-2525-20..."): conv.py li separa da solo (ricostruzione con il risultato in set).
   - Numero di giornata: non è scritto, ma FIPAV numera le gare giornata per giornata (N/2 gare per giornata, con N squadre; se N dispari a volte (N+1)/2, es. U14 M). conv.py sceglie numero iniziale e gare/giornata che non mettono mai una squadra due volte nella stessa giornata. Gare con numerazione separata (es. U13 F UD gir. D, 13156-13158: squadra aggiunta dopo) restano senza giornata.
   - Controllo di qualità: per ogni girone, gare giocate lette = somma PG della classifica / 2. Al 24/11/2026 torna per tutti i 60 gironi.
   - Consegna: /home/claude/fvg/risultati/pallavolo/_lavoro/: raw/<comitato>-wGG.txt (righe grezze per settimana), spec-reg/ud/pn/ts.json (regex sezione → CId, slug, nomi), conv.py (raw → file lavoro con giornata), build.py (file lavoro → JSON finale, abbina gli id di app/data.json solo se il nome tra virgolette nel campo "squadre" dello stesso CId coincide), *.cls (classifiche complete lette a mano; senza .cls usa _gironi.tsv: pos, punti, PG). Comandi: for c in reg ud pn ts; do python3 conv.py spec-$c.json raw/$c-*.txt; done; poi python3 build.py <slug>.txt ...
   - ATTENZIONE _gironi.tsv: la classifica U14 F UD gir. A (92422) lì era vecchia/errata (PG 1-2 invece di 4-6); riletta il 24/11 (ud-u14a.cls). Se il controllo giocate/PG non torna, rileggere la classifica.
   - Giro settimanale (dal 30/11/2026): basta leggere la settimana appena chiusa e la nuova (DataDa = lunedì) per ogni comitato: ~2 letture REG, ~6 UD, 2 PN, 2 TS, salvare in raw/ e rilanciare conv+build; rileggere le classifiche (classifica.aspx?CId=) almeno per Serie C/D e dove il controllo non torna.
   - Aggiornamento dei portali: i risultati compaiono dopo la gara (domenica sera tutti presenti, a volte "ufficioso"); le classifiche si aggiornano dopo ogni giornata. Rileggere il lunedì.
   - Nazionali: la sezione "Campionati Nazionali" di Pordenone mostra solo le gare interne delle squadre PN, senza risultati né classifica: non usata. Le fonti di lega (legavolley, legavolleyfemminile, federvolley B/B2) non sono state lette.
3. Calendario completo del girone: solo via CalendarioGare.asp?c=<codice> (bloccato per WebFetch); in alternativa le pagine risultati settimana per settimana con DataDa (vedi sopra). Provato calendario.aspx?CId=…: non leggibile (binario).
4. Per una squadra dell'app: prendere id_fonte (CId) → classifica; per le gare, cercare il nome squadra (nome sponsor, nel campo "campionato" tra virgolette) nella pagina risultati del comitato giusto (dedotto dal campionato: "FVG" = regionale, "CT Udine/Pordenone/Trieste-Gorizia", "interterritoriale" = presente su più portali).
5. I CId cambiano ogni stagione e per le fasi successive (play-off, seconde fasi, finali U13/U12): ricontrollare la pagina risultati (elenco gironi con link "classifica" e "calendario").

## Limiti noti
I CId sono numerati a livello nazionale. Le squadre compaiono spesso col nome dello sponsor: abbinare tramite ID logo, palestra, elenco società; scriverlo in "note". Gli abbinamenti "per esclusione" (Insieme per Pordenone, Polisigma, Naš Prapor) vanno confermati.
Lavoro 2026/27 conservato in /home/claude/fvg/patch/volley-squadre/_gironi.tsv (tutte le classifiche al 24/11/2026 con ID logo).

## Dati della gara (dalla 1.19.0, automatici in scripts/volley.py)
Formato: pipeline/agenti/formato-risultati.md. Ogni riga gara delle pagine risultati ha `<img alt="statogara" src="/img/statogara/statoN.png" title="...">`:
stato0 "da disputare", statodesignata "da disputare<br/>Arbitro designato<br>1° arbitro: …", stato1 "risultato ufficioso", stato5 "gara omologata"
(verificato il 28/11/2026 con la Sonda `maschera=`). Il tooltip "info" ha l'impianto e, dove pubblicate, `<p class="designazione"><b>Designazioni</b>…`.
Lo script salva `stato_gara` (omologata/ufficioso, rinviata/sospesa) e `designata: true` (solo gare dei prossimi 7 giorni, mai Pordenone),
**senza mai leggere i nomi** (si controlla solo che dopo "arbitro:" ci sia un testo). Nessuna pagina in più: sono le pagine settimanali già lette
(giro normale ora da -2 a +1 settimane, per vedere arrivare le omologazioni). I CU dei comitati (`/download.ashx`) restano vietati da robots.txt.
