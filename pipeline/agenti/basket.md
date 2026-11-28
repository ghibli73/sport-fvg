# Agente BASKET FVG (FIP Comitato Regionale FVG + leghe nazionali)

Ambito: tutte le categorie da Under 12 in su (Esordienti U12, U13, U14, U15, U16, U17, U19 Eccellenza/Gold/Regionale), DR3, DR2, DR1, Serie C, B Interregionale, B Nazionale, A2, Serie A; femminile (U13–U19 F, Serie C F, B F, A2, A1).
Nel campo "categoria" usa: Under 12 … Under 19, Prima squadra, Seconda squadra; nel "campionato" la denominazione ufficiale con girone.
Più squadre della stessa società nella stessa categoria+genere (es. Gold + Regionale, squadre 'B'/'C') vanno in UNA voce, campionati separati da "; " (il merge sostituisce per categoria+genere).

## Accesso tecnico
- curl/Bash verso friuliveneziagiulia.fip.it è BLOCCATO dal proxy (403): usare solo WebFetch.
- WebFetch sui PDF FIP funziona bene con prompt "elenca ogni squadra distinta (nome esatto) e palestra di casa (comune), girone e campionato".

## Fonti verificate (2026/27)
- Archivio file FIP FVG (WordPress media API, via WebFetch):
  https://friuliveneziagiulia.fip.it/wp-json/wp/v2/media?search=<testo>&per_page=100&_fields=date,source_url
  Testi utili: "Calendario Definitivo", "Allegato", "Omologazione", "U15M", "Femminile". Risposta lunga: usare offset 100000.
- I CALENDARI DEFINITIVI (CU-xxx-GARE-yyy-Calendario-Definitivo-...pdf) contengono squadre, gare (numero, data, ora) e palestre: sono la fonte per "squadre".
- Gli "Allegato al Campionato" NON elencano le squadre (solo formula e numero squadre per girone): inutili per gli elenchi.
- Calendari 2026/27 usati (prefisso https://friuliveneziagiulia.fip.it/wp-content/uploads/):
  - Serie C gir. D: 2026/09/CU-008-GARE-004-Serie-C-Girone-D-Calendario-Definitivo-Prima-Fase.pdf
  - DR1 Est/Ovest: 2026/09/CU-012-GARE-007-DR1-Calendario-Definitivo-Girone-EST.pdf, 2026/09/CU-013-GARE-008-DR1-Calendario-Definitivo-Girone-OVEST.pdf
  - DR2 GO/TS, PN, UD: 2026/10/CU-064-GARE-051-...-DR2-Girone-GO-TS.pdf, 2026/10/CU-065-GARE-052-...-DR2-Girone-pn-1.pdf, 2026/10/CU-066-GARE-053-...-DR2-Girone-UD.pdf
  - DR3 UD, PN, GO/TS: 2026/10/CU-067-GARE-054-...-DR3-Girone-UD.pdf, CU-088-GARE-068-...-DR3-Girone-PN.pdf, CU-089-GARE-069-...-DR3-Girone-GO-TS.pdf
  - Serie C femminile: 2026/10/CU-048-GARE-041-Calendario-Definitivo-Prima-Fase-CF.pdf
  - U19 Eccellenza (girone 5 interregionale con Veneto): 2026/09/CU-016-GARE-011-Calendario-Definitivo-U19E-Girone-5.pdf
  - U19 Gold A/B: 2026/09/CU-024-GARE-019-...-U19GM-Girone-A.pdf, CU-025-GARE-020-...-U19GM-Girone-B.pdf
  - U19 Regionale: 2026/10/CU-068 (GO/TS/UD), CU-069 (UD), CU-091 (PN A), CU-092 (PN B)
  - U17 Eccellenza: 2026/09/CU-018-GARE-013-Calendario-Definitivo-U17E.pdf
  - U17 Gold: 2026/10/CU-040 (GO/TS), CU-041 (PN), CU-042 (UD); U17 Regionale: 2026/10/CU-071 (GO/TS), CU-072 (PN), CU-073 (UD)
  - U15 Eccellenza: 2026/09/CU-021-GARE-016-Calendario-Definitivo-U15E.pdf; U15 Gold: 2026/10/CU-045-GARE-038-Calendario-Definitivo-U15GM.pdf
  - U15 Regionale: calendario definitivo non pubblicato in archivio; squadre ricavate da omologazione 2026/11/CU-165-GIUDICE-061-Omologazione-gare-U15M-N.3.pdf (gironi GO/TS, PN, UD)
  - U14 Gold A/B/C: 2026/10/CU-056, CU-057, CU-058; U14 Regionale: 2026/10/CU-098 (GO/TS/UD), CU-099 (PN/UD)
  - U13 maschile: 2026/10/CU-101 (GO/TS A), CU-102 (GO/TS B), CU-103 (PN A), CU-104 (PN B), CU-105 (UD A), CU-106 (UD B)
  - Femminili: U19F 2026/10/CU-037; U17F 2026/09/CU-028; U15F 2026/09/CU-031; U14F A 2026/10/CU-107 (riemesso, sostituisce CU-060), B CU-061, C CU-062; U13F 2026/10/CU-082 (GO/TS), CU-083 (PN/UD)
  (nomi file completi: vedi gli "id_fonte" in /home/claude/fvg/patch/basket-squadre/*.json; elenchi grezzi in patch/basket-squadre/_lavoro/raw.txt)
- Serie B Interregionale: le squadre FVG (Dinamica Gorizia, VI Sistema Bk Pordenone, Falconstar, Motomarine Jadran Trieste) sono nel girone B gestito dal CR VENETO.
  Archivio: https://veneto.fip.it/wp-json/wp/v2/media?search=Interregionale&per_page=40&_fields=date,source_url
  (omologazioni settimanali "CU-xxx-del-gg_mm_aa-Omologazione-Gare-B-Interregionale.pdf", es. 2026/11/CU-161-del-18_11_26-...).
- Serie nazionali: en.wikipedia "20xx–yy LBA season" funziona (usata dall'agente nazionali).

## Fonti che NON funzionano
- it.wikipedia: le pagine stagione 2025-26/2026-27 di A2 e B Interregionale non esistono (url_not_found); esiste solo fino a "Serie B Interregionale 2024-2025 (pallacanestro maschile)". Anche l'API opensearch non risponde via WebFetch.
- en.wikipedia "2025–26 Serie A2 Basket": non esiste.
- eurobasket.com (client_error), lasicilia.it (robots), playbasket.it (blocca i robot); legabasket.it e legapallacanestro.com caricano i dati via JavaScript.
- Nessun archivio FIP FVG per Serie B femminile / A2 femminile (campionati nazionali): Women APU, Futurosa, Ginnastica Triestina restano da verificare (provare fip.it nazionale o siti delle società).

## Limiti noti / abbinamenti
Nei calendari le squadre hanno spesso il nome dello sponsor: abbina tramite palestra e scrivilo in "note". Abbinamenti usati:
Goriziana Caffè = Dinamo Gorizia; Tecnogiemme = Venezia Giulia Basketball; Pizzeria Amalfi = Virtus PN;
C.T.S. / Montgomery Hamburger House / GP Engineering / Gas Più Energie (Codroipo, Circonvallazione Sud 23) = Pallacanestro Codroipese;
Credifriuli / Chiurlo Cervignano = Basket Cervignanese; Intermek / Autoscuola Cordenonese / Economy Rent / 3 S Basket Cordenons = Intermek 3S Cordenons;
Errebi Majano = Majanese; Tecno 2 Commerciale Tricesimo = Pol. Tricesimo; Insureteach / O.F.P. Azzurra R.D.R. = Azzurra Trieste; Metamorfosi Gradisca = Basket Gradisca;
Nordcaravan = Roraigrande; A.P.C. Chions = Villotta Ice; BCC Pordenonese Monsile (giovanili) = Sistema Basket Pordenone; MEP Cividale / UEB Cividale B = UEB Gesteco Cividale;
SBaMM (Uattzy, Sonvilla, WEB, Farmacia del Sole) = Scuola Basket Miky Mian (da confermare); ZKB / Motomarine Jadran = U.S.D. Jadran; DINAMICA - Gorizia = Dinamo Gorizia (da confermare).
NON abbinate (lasciate fuori, da chiarire): MB Paper's (U19 reg., Corno di Rosazzo: Centro Sedia o Banca 360?), Fly Solartech Icarus (U19 Gold, San Daniele: in Serie C è lo sponsor di Pol. Libertas Acli San Daniele, quindi probabile stessa società, da confermare per U19), Ronchi Basket Club (U19 Gold, gioca a Fogliano), Nautilus Allestimenti (U15/U14, Ronchi-Vermegliano: forse Fidema Group Ronchi), Colledani srl (U15 UD), Pallacanestro Feletto (U13, Feletto Umberto), BIN Tigrotte (U14F/U13F, Trieste), Basket Fiume (U14F, Fiume Veneto), Monritz Team Sport (U19F, Trieste San Giovanni), WIS 1963 Woman Spilimbergo (Serie C F, U13F: forse Vis Spilimbergo), BCC Pordenonese e Monsile in DR1 Ovest (gioca ad Azzano: Azzano Basket o Sistema?).
Squadre venete nei gironi FVG (ignorate): Pall. Portogruaro, Polisportiva Concordia, Julia Concordia, BVO Annone, Pallacanestro Fossaltese.
Under 12/Esordienti (dal 27/11/2026, automatici in scripts/basket.py, passo 7): nessun calendario PDF in archivio; calendario e punteggi dal portale fip.it/risultati (campionati ES = Trofeo Esordienti, TFE = Esordienti Femminile; codici girone vicini: ES 87019-87023, 87025, 87026 fase 2; TFE 87015, 87027 fase 1). Config config/basket/esordienti-*.json con "minibasket": true, "portale" (parametri del girone), "ris_portale" (punteggi non ancora omologati: in app "da omologare"). Omologazioni "Esordienti" (nel 2025/26 uscite solo a gennaio, CU-260/261) confermano i punteggi; il pareggio esiste (punteggio per periodi: 3 punti al periodo vinto, 2 pari, 1 perso, es. 12-4, 8-8). Nessuna classifica (il Comitato non ne pubblica; il portale ne mostra una automatica a 2 punti per vittoria, non usata). Gironi nuovi cercati una volta alla settimana (stato minibasket_scoperta in config/basket_stato.json, o --scopri-minibasket). Al 27/11 nessun girone Esordienti maschile di Trieste sul portale. Squadre senza società in app: venete (Annone, Portogruaro, Concordia, Gaia) e Roveredo in Piano, Fiume Veneto Blu/Bianco, Baby Falcons, Leoncino M/F, Ronchi Basket Club, APD Principe, Feletto, ORA Basket, Tigrotte.

## Per i risultati in tempo reale
Stato al 24/11/2026: 49 gironi caricati in /home/claude/fvg/risultati/basket/ (tutti i campionati regionali senior e giovanili + B Interregionale gir. B), dati fino alle omologazioni del 18-20/11/2026.

### URL (solo WebFetch; curl bloccato)
- Elenco omologazioni per campionato, solo le nuove dall'ultima lettura:
  https://friuliveneziagiulia.fip.it/wp-json/wp/v2/media?search=Omologazione-gare-<SIGLA>&per_page=30&after=<AAAA-MM-GG>T00:00:00&_fields=date,source_url
  SIGLE: CM (Serie C maschile), DR1, DR2, DR3, CF, U19E, U19GM, U19M, U17E, U17GM, U17M, U15E, U15GM, U15M, U14GM, U14M, U13M, U19F, U17F, U15F, U14F, U13F.
  (search=Omologazione-gare-U19 / -U17 / -U15 / -U14 / -U13 / -DR restituisce tutte le varianti; senza &after compare anche la stagione 2025/26.)
  Ultima lettura: CM N.8, DR1 N.7, DR2 N.3, DR3 (CU-155 "N.2" del 18/11), CF N.2, U19E N.8, U19GM N.6, U19M N.1, U17E N.4, U17GM N.4, U17M N.2, U15E N.4, U15GM N.2, U15M N.3, U14GM N.3, U14M N.1, U13M N.2, U19F N.1, U17F N.2, U15F N.1, U14F N.1, U13F N.1.
  Prossima lettura: &after=2026-11-21T00:00:00.
- B Interregionale gir. B (CR Veneto): https://veneto.fip.it/wp-json/wp/v2/media?search=Omologazione%20B%20Interregionale&per_page=40&after=<data>&_fields=date,source_url (letti CU 056 del 30/09 - CU 161 del 18/11, giornate 1-8, gare 1-56). Calendario Veneto non ancora cercato (manca ora/campo e giornata successiva).
- Classifiche ufficiali: search=Classifica&after=2026-09-01 -> nessun file al 24/11/2026: classifiche sempre ricalcolate.

### Lettura dei PDF
- Omologazione, prompt breve: "For every game: girone | game number | score as printed | note (sospesa, 0-20, rinviata). No other text." Il punteggio è casa-ospite.
- Il testo non separa i nomi delle squadre: casa/ospite si prendono dal calendario definitivo tramite il NUMERO GARA (calendari già trascritti in risultati/basket/_lavoro/cal_*.txt, formato num|giornata|data|ora|casa|ospite|campo; per le giornate oltre il 25/11 vanno aggiunte righe dal PDF in id_fonte, prompt "List the games up to <data>, one compact line each, pipe-separated: game number|giornata|date|time|home|away|venue").
- Attenzione: il lettore a volte sbaglia il numero di giornata o salta righe del calendario: ricostruire la giornata dalla sequenza dei numeri gara (n. squadre/2 gare per giornata).
- Casi speciali: "sospesa"/"accertamenti"/"disposizione G.S." = omologazione sospesa -> esclusa dal calcolo finché non ricompare omologata; "ripetizione" -> esclusa; 0-20 (o 0-30 nel minibasket) = perdita gara, conteggiata come vittoria/sconfitta con quel punteggio (eventuali punti di penalizzazione NON applicati); punteggio ambiguo -> escluso e annotato.
- U15 Regionale: calendario definitivo non pubblicato, partite ricavate solo dalle omologazioni (prima squadra nominata = casa; niente ora/campo; nessuna giornata successiva).

### Calcolo e scrittura (script in risultati/basket/_lavoro)
- Per ogni girone c'è <slug>.meta.json: slug, girone, categoria, livello, genere, fonte, id_fonte, aggiornato, cal (file calendario), ultima_giornata (facoltativo), ris {numero gara: "casa-ospite"}, ids {nome nel calendario: id data.json}, note.
  Serie C gir. D usa ancora mk_seriec.py (stesso schema, dict ris interno).
- Aggiornamento settimanale: aggiungere le nuove gare a "ris" (e righe di calendario se servono), aggiornare fonte/aggiornato/ultima_giornata/note, poi:
  cd /home/claude/fvg/risultati/basket/_lavoro && for m in *.meta.json; do s=${m%.meta.json}; python3 mk_generic.py $m && python3 build.py $s.spec.json; done; python3 mk_seriec.py && python3 build.py serie-c-girone-d.spec.json
- build.py: 2 punti a vittoria; ordine punti, differenza canestri, punti fatti (non applica scontri diretti); "partite" = tutte le gare con risultato + l'intera giornata ultima_giornata+1 (risultato ""); classifica_calcolata: true.
- ultima_giornata va impostata a mano dove le gare sono infrasettimanali/sparse (DR3, giovanili): è l'ultima giornata quasi completa.

### Abbinamenti emersi dalle omologazioni/calendari (oltre a quelli sopra)
Calligaris = Centro Sedia Basket (Serie C); Neonis Basket GS = G.S. Vallenoncello; Fly Solartech Icarus = Pol. Libertas Acli San Daniele (Serie C, certo per numero gara; in U19 Gold lasciata senza id); PrimaCassa Cividale B = UEB Cividale B; Tecnovalore Venezia Giulia = Venezia Giulia Basketball; UsableNet SBaMM / Uattzy / Sonvilla / WEB / Farmacia del Sole SBaMM = Scuola Basket Miky Mian; ZKB Jadran = Jadran; DINAMICA - Gorizia = Dinamo Gorizia (B Interregionale); Basket Maniago-Pol. Montereale (U19 reg. PN B) squadra congiunta, senza id.
Abbinate il 25/11/2026 (pipeline/agenti/abbinamenti.md): Fly Solartech Icarus U19 Gold = Pol. Libertas Acli San Daniele; BCC Pordenonese e Monsile DR1 Ovest = Azzano Basket. Le altre hanno solo il comune (config/squadre_comune.json).
Ancora non abbinate: MB Paper's, Ronchi Basket Club, Nautilus Allestimenti, Colledani srl, Pallacanestro Feletto, BIN Tigrotte, Basket Fiume, Monritz Team Sport, WIS 1963 Woman Spilimbergo, BCC Pordenonese e Monsile (DR1 Ovest).

### Portale fip.it/risultati e provvisori "da omologare" (dal 28/11/2026)
- Le omologazioni arrivano 4–10 giorni dopo la gara (U13 anche di più); il portale ha quasi sempre già il punteggio (referto
  elettronico). Causa delle gare "in attesa" per giorni fino al 26/11: il giro rapido leggeva solo le gare degli ultimi 3 giorni
  e 6 gironi non erano abbinati al portale. Il lettore del portale era corretto (verificato con la Sonda `fipdiag=tutti`).
- `config/basket_fip.json`: 46 gironi. Aggiunti a mano il 28/11 (trovati con `fipscan=`): u13-ud-a U13S/M 86367, u13-ud-b 86368,
  dr3-ud 1DM 85891, u15-regionale-go-ts U15S/M 85877, -pn 85878, -ud 85879. La scoperta automatica ora prova i codici da 3 prima a
  3 dopo tutti i gironi già abbinati dello stesso campionato (prima solo ±3 dal girone mostrato) e salta i minibasket (TFE).
  NON trovati: u19-regionale-pn-a / pn-b (U19S/M mostra solo 85867 e 85869; provati 85860–85960, 86300–86362, fasi 1–3): da
  cercare quando il portale li pubblica. B Interregionale (CR Veneto) e nazionali: fuori dal portale regionale FVG.
- Giro rapido (`basket.py --rapido`): gare finite (inizio + 105 min) negli ultimi 21 giorni senza omologazione, per tutti i
  gironi abbinati e i minibasket (parametri "portale"). Giornate con gare degli ultimi 3 giorni lette a ogni giro; le più vecchie
  al massimo ogni 6 ore e 40 pagine per giro (`LIVE_RILETTURA`, `LIVE_MAX_VECCHIE`; ora dell'ultima lettura in
  `config/live.json` "letture"). Una gara già in live.json non viene riletta.
- Regole: mai sovrascritto un risultato omologato (tempo_reale.applica); pari/0-0 scartati (minibasket: solo 0-0); data 30 giugno
  (rinviata da definire) o data del portale nel futuro = nessun risultato; quando arriva l'omologazione il provvisorio sparisce
  (tempo_reale.pulisci, vale l'omologazione se diversa).
- Gare senza punteggio sul portale (al 26/11 circa 1 su 4 fra le U13): nessun referto elettronico, restano in attesa
  dell'omologazione. Gare con data cambiata sul portale (rinvii) sono aggiornate dall'esecuzione normale (variazioni_fip).
- U15 Regionale ("calendario_portale": true): senza calendario PDF; `calendario_portale()` aggiunge dal portale le gare mancanti
  (giornata, data, ora, campo) traducendo i nomi con le gare già note per numero; letto con --completo o quando il girone non ha
  più gare future.
- Sonda: `fipdiag=<slug,...|tutti>[@giorni]` confronta config e portale per le gare passate senza risultato.

### Da fare / limiti
- Serie A, A2, B Nazionale e femminili nazionali non coperte (siti JavaScript).
- Gare non ancora omologate o non trovate sono elencate nel campo "note" di ogni file: ricontrollarle alla lettura successiva.
- Frequenza: una volta a settimana (giovedì-venerdì, quando sono uscite tutte le omologazioni: senior il martedì-mercoledì, giovanili il giovedì-venerdì).
