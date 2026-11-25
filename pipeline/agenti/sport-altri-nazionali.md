# Agente RISULTATI ALTRI SPORT E SERIE NAZIONALI (rugby, baseball/softball, bocce, tennis, volley e basket nazionali)

Stato al 25/11/2026 (stagione 2026/27; baseball/softball stagione 2026 conclusa).
Formato file: /home/claude/fvg/risultati/FORMATO.md. Dopo ogni girone: `cd /home/claude/fvg && python3 build_risultati.py` (non deve stampare righe "!").
Script di lavoro (dati grezzi + generatori dei file): /home/claude/fvg/risultati/_lavoro_altri/ (mk.py = funzioni comuni: save, pa, volley_table, basket_table, parse_be, check_rounds). Per aggiornare un girone: aggiorna le righe grezze nello script corrispondente e rilancialo.

## Vincolo tecnico importante
curl/Bash verso l'esterno è bloccato. WebFetch accetta solo URL comparsi in un risultato di WebSearch o in una risposta di WebFetch precedente; URL "costruiti a mano" vengono spesso rifiutati (PROVENANCE_REQUIRED). Eccezioni osservate: su fibs.it, federugby.it, federbocce.it, betexplorer.com gli URL di sottopagine dello stesso sito, una volta "visti", funzionano. Partire sempre da una pagina indice (sotto) e farsi elencare i link.

## Fonti verificate

### Basket nazionale (betexplorer + Tuttosport)
- Indice competizioni Italia: https://www.betexplorer.com/basketball/italy/ (Lega A, Serie A2, A1 Women, A2 Women Gr. A/B 2026/27)
- LBA: https://www.betexplorer.com/basketball/italy/lega-a/results/ e /fixtures/ ; classifica ufficiale: https://www.tuttosport.com/basket/risultati/serie-a/classifica
- Serie A2: https://www.betexplorer.com/basketball/italy/serie-a2/results/ e https://www.betexplorer.com/it/basketball/italy/serie-a2/fixtures/ (nessuna classifica leggibile: si calcola)
- A2 femminile gir. A: https://www.betexplorer.com/basketball/italy/serie-a2-women-gr-a/results/ e /fixtures/ (fonte incompleta: manca la 7a giornata)
- Note betexplorer: date senza anno, "Yesterday" al posto della data recente, gare raggruppate per data (controllare che ogni squadra compaia una volta per giornata: funzione check_rounds). La classifica (standings ajax) è bloccata.
- NON funzionano: legabasket.it, legapallacanestro.com, it.wikipedia (URL non raggiungibili dallo strumento), eurosport.* (geobloccato), pagina "risultati" Tuttosport (ferma alla 6a giornata).

### Pallavolo nazionale
- SuperLega: articoli di giornata Tuttosport (indice https://www.tuttosport.com/pallavolo/superlega , con parziali, classifica e prossimo turno) + https://www.betexplorer.com/it/volleyball/italy/superlega/results/ e /fixtures/ ; set vinti/persi: https://www.365scores.com/it/volleyball/team/prata-54844/standings
- A1 femminile: https://www.betexplorer.com/it/volleyball/italy/serie-a1-women/results/ e https://www.betexplorer.com/volleyball/italy/serie-a1-women/fixtures/ ; parziali Talmassons: https://www.betexplorer.com/volleyball/team/talmassons/8tuPRJ3a/results/ (classifica calcolata: standings bloccati)
- Indice: https://www.betexplorer.com/volleyball/italy/ (solo SuperLega, A2, A1 W, A2 W: nessuna squadra FVG in A2 M/F 2026/27)
- NON funzionano: widget Tuttosport (iframe enetscores), eurosport (geoblocco), legavolley/legavolleyfemminile (non raggiunti). Serie B/B1/B2 nazionali: federvolley.it pubblica solo comunicati del Giudice Sportivo (senza risultati); nessuna fonte leggibile trovata. Il portale https://pordenone.portalefipav.net/risultati-classifiche.aspx?PId=7581 (sezione "CAMPIONATI NAZIONALI") mostra solo le gare in casa delle squadre PN: non basta per un girone completo.
- Squadre FVG in B/B1/B2 2026/27 (organici FIPAV https://guidapratica.federvolley.it/campionati-indoor/campionati/organici_26-27_con_classifche_dei_ripescaggi.pdf + data.json): B M Libertas (Fiume Veneto, "Libertas PN"); B1 F Blu Team; B2 F Pol. S. Giorgio (Sangiorgina), Pol. Aquila Spilimberghese, Insieme per Pordenone ("Pordenone Volley"), Chions Fiume Volley (CFV).

### Baseball / softball (FIBS, stagione 2026 conclusa)
- Classifiche: https://www.fibs.it/it/events/<evento>/standings ; partite: pagina squadra https://www.fibs.it/it/events/<evento>/teams/<id> (punteggio "ospiti : locali" — verificato confrontando V/P con la classifica). La pagina "schedule-and-results" e "calendars" non sono leggibili; l'elenco /teams dà gli ID (testo alternativo dei loghi).
- Eventi: 2026-serie-a-silver-baseball (girone B: Ronchi 39763, Buttrio 39739, Junior Alpina 39711); 2026-serie-b-baseball-2026 (girone B: Redipuglia 40050, Staranzano 39724, Cervignano 39814); 2026-serie-c-baseball-2026 (girone F: Europa 40713, Buttrio 40337, Porcia 40709, San Lorenzo 40388); 2026-serie-a2-softball-2026 (girone B: Stars Ronchi 39823).
- Non verificati: Serie A1 softball, Serie A Gold, giovanili (nessuna squadra FVG trovata nei gironi letti).

### Rugby (FIR + CR Veneto)
- Serie B (nazionale): elenco comunicati https://www.federugby.it/categorie/serie-b-stagione-sportiva-2026-27-giudice-sportivo/ -> pagina documento -> PDF (nome non sempre regolare: COMB01GS…, COMB02S2026.2027.pdf, COMB03GS…, COMB04GS2026.2027.pdf). Ogni PDF ha risultati della giornata + classifica di tutti i gironi. Calendario: https://www.federugby.it/wp-content/uploads/serie-b.pdf (girone 2 Fiumicello, girone 3 Rugby Udine).
- Serie C (Triveneto, CR Veneto): https://www.crvenetorugby.it/crv/omologazioni-gare-serie-c/ (PDF "COMUNICATO GST SERIE C N x"): girone Territoriale 1 con Rugby Udine (cadetta) e Pordenone Rugby n.2. Calendario della Serie C non trovato. I PDF contengono nomi di giocatori/arbitri: NON trascriverli.
- Venjulia Trieste: non trovata nei gironi senior letti. Giovanili U18/U16: non lette (omologazioni su https://www.crvenetorugby.it/crv/omologazione-gare-under-18/ e /omologazioni-gare-under-16/ — da provare).

### Bocce (FIB, specialità volo)
- Indice campionati: https://www.federbocce.it/attivit%C3%A0-sportiva/classifiche/fibcampionatiserie.html
- Pagina giornata (classifica + risultati della giornata g): https://www.federbocce.it/attivit%C3%A0-sportiva/classifiche/fibcampionato/2027%7C<id>%7CVolo%7C<g>.html ; ID 2026/27: Serie A 322520, A femminile 322521, A2 girone 2 Est 322523, B girone 5 Est 322534. Raffa A/A2 e petanque: nessuna squadra FVG. Serie C e regionali: non presenti sul sito nazionale.

### Tennis (FITP)
- Gironi Serie A1/A2 2026 (PDF linkati da https://www.fitp.it/Campionati-tornei-e-classifiche/Campionati-nazionali/campionati-affiliati): nessuna squadra FVG in A1/A2 maschile e femminile. Serie B/C/D e regionali (https://www.fitp.it/Siti-regionali/Friuli-Venezia-Giulia/Campionati/Campionati-a-squadre) sono caricati in JavaScript: illeggibili. Nessun file tennis creato.

## File caricati (25/11/2026)
- basket/naz-serie-a.json (LBA, 9 giornate + 10a), basket/naz-serie-a2.json (11 + 12a, classifica calcolata), basket/naz-a2-femminile-a.json (1-6 + 8a, parziale)
- pallavolo/naz-superlega.json (1-6 + recuperi + 7a), pallavolo/naz-a1-femminile.json (1-10 + 11a, classifica calcolata)
- baseball/serie-a-silver-girone-b.json, baseball/serie-b-girone-b.json, baseball/serie-c-girone-f.json, baseball/softball-serie-a2-girone-b.json (stagione 2026 finita; partite solo delle squadre FVG, salvo Serie C quasi completa)
- rugby/serie-b-girone-2.json, rugby/serie-b-girone-3.json (1-4 + 5a del 29/11), rugby/serie-c-territoriale-girone-1.json (1-4)
- bocce/volo-serie-a.json, volo-serie-a-femminile.json, volo-serie-a2-girone-2-est.json, volo-serie-b-girone-5-est.json

## Procedura di aggiornamento settimanale (lunedì/martedì)
1. Basket: rileggere betexplorer results/fixtures di lega-a, serie-a2, serie-a2-women-gr-a (prompt: "List ALL results … every row verbatim: round, date, home, away, score"); classifica LBA da Tuttosport. Aggiornare lba_be.txt / a2_be.txt / a2f.py, lanciare gli script.
2. SuperLega: dall'indice Tuttosport aprire l'articolo dell'ultima giornata (risultati con parziali, classifica, prossimo turno); controllare con betexplorer results. Aggiungere le righe in superlega.py.
3. A1 femminile: betexplorer results/fixtures; aggiungere le righe in a1f.py (assert su 14 squadre per giornata).
4. Rugby: nuovo comunicato Serie B/0x/GS (venerdì-mercoledì dopo la giornata) e GST Serie C n.x; aggiungere risultati e sostituire la classifica in rugby.py / rugbyc.py; prossima giornata dal calendario serie-b.pdf.
5. Bocce: pagina della giornata g e g+1 per i 4 ID; aggiornare bocce.py.
6. Baseball/softball: fermi fino alla stagione 2027 (eventi FIBS "2027-…").
7. `python3 build_risultati.py` dopo ogni file.

## Abbinamenti con app/data.json (solo certi)
- Basket: Udine/APU -> 030129-15; Pallacanestro Trieste -> 032006-21; Cividale -> 030026-1. "Trieste" A2 femminile: NON abbinata (società incerta).
- Pallavolo: Tinet Prata di Pordenone -> 093034-1; Talmassons -> 030114-1.
- Baseball: Gereon Engineering NBP Ronchi -> 031016-2 (New Black Panthers); Alfa Sistemi Buttrio e White Sox Buttrio (Serie C) -> 030014-5; IS Copy Junior Alpina -> 032006-31; Rangers Redipuglia -> 031006-3; Staranzano Ducks -> 031023-8; Sultan Allestimenti Navali Cervignano -> 030023-10; Europa Baseball Club -> 030008-3; Astros Porcia -> 093032-11; Stars Ronchi (softball) -> 031016-8. San Lorenzo Bears: non abbinata (sede non indicata).
- Rugby: Rugby Udine S.R.L. SSD (anche cadetta in Serie C) -> 030129-17 (Udine RFC, come da note di data.json); Rugby Fiumicello -> 030190-13.
- Bocce: Bocciofila Spilimberghese -> 093044-7; Osoppana -> 030066-2; Cussignacco (anche femminile) -> 030129-48.

## Società FVG trovate nelle fonti ma assenti in data.json
- Bocce: A.S.D. Quadrifoglio (UD, Serie A volo); A.S.D. Bocciofila Buttrio (UD, Serie A femminile volo); A.S.D. Bocciofila Codroipese (UD), Bocc. Villaraspa BCC (GO), ASD Bocciofila Pasch (PN) (A2 girone 2 Est); ASD Bocciofila Triestina (TS), ASD Tagliamento (UD), Nuova del Corno (UD), ASD Tre Stelle Ronchi dei Legionari (GO) (B girone 5 Est). Fonte: pagine federbocce.it sopra.
- Rugby: Pordenone Rugby ASD (Pordenone; Serie C Territoriale 1 con la squadra "n.2"). Fonte: comunicati GST Serie C CR Veneto.
