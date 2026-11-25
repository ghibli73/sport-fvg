# Agente RISULTATI SPORT DI SQUADRA MINORI (pallamano, hockey, pallanuoto, tennistavolo)

Stagione 2026/27. File girone in /home/claude/fvg/risultati/<sport>/<slug>.json (formato: risultati/FORMATO.md).
Campo "sport" esattamente: pallamano, hockey, pallanuoto, tennistavolo. Per l'hockey la specialità va nel campo "girone" (es. "Hockey inline — Serie A …").
Dopo ogni modifica: `cd /home/claude/fvg && python3 build_risultati.py` (non deve stampare righe "!").

## Accesso tecnico
- curl/Bash verso siti esterni bloccato dal proxy: solo WebFetch.
- Alcune pagine federhandball.it possono richiedere un'autorizzazione all'utente (errore PROVENANCE_REQUIRED, es. home page e U14 femminile al 25/11/2026): non riprovare nella stessa sessione, passare oltre.

## Strumenti
- /home/claude/fvg/risultati/_strumenti_minori/mk.py — costruisce un file girone da una spec JSON:
  `cd /home/claude/fvg/risultati/<sport>/_lavoro && python3 ../../_strumenti_minori/mk.py <slug>.spec.json`
  La spec contiene: out, head (testata: girone, categoria, genere, comitato, fonte, id_fonte, aggiornato, note, eventuale giornata), ids {nome come nella fonte: id data.json}, classifica (file pipe `pos|squadra|punti|g|v|n|p|f|s`, colonne vuote ammesse) oppure null + "punti":[V,N,P] per classifica calcolata, partite (file pipe `giornata|data|ora|casa|ospite|risultato|campo`, date "gg/mm/aaaa" o "8 novembre 2026"), ultima_giornata (le giornate oltre ultima+1 sono scartate), solo_con_risultato_fino_a (scarta le gare passate senza punteggio).
- Dati grezzi e spec: risultati/pallamano/_lavoro/*.txt e *.spec.json, risultati/hockey/_lavoro/.

## PALLAMANO (FIGH) — fonte funzionante
Portale federale, HTML leggibile con WebFetch:
- Territoriali Area 3 (Veneto + FVG): https://www.federhandball.it/campionati-territoriali/area-3/girone/<girone>/classifica e …/<girone>/calendario-e-risultati
  Gironi: serie-b-maschile-area-3, under-18-maschile-area-3, under-16-maschile-area-3-girone-a|b|c, under-16-femminile-area-3, under-14-maschile-area-3-girone-a|b|c, under-14-femminile-area-3.
- Nazionali: https://www.federhandball.it/campionati-nazionali/serie-a-gold/classifica e …/serie-a-gold/calendario-e-risultati; altri: serie-a-silver/?girone=serie-a-silver-maschile-gir-a|b, serie-a1/, serie-a2/?girone=serie-a2-femminile-gir-a…e.
- Prompt calendario: "Elenca TUTTE le partite presenti, una per riga: giornata | data | ora | casa | ospite | risultato (se il punteggio è '-' scrivi vuoto) | città. Nessun altro testo." (pagina Serie A Gold lunga: oltre la 18ª giornata serve offset 100000, non necessario per le giornate fino a dicembre).
- Prompt classifica: "Riporta la classifica completa esattamente: pos | squadra | Pt | G | V | N | P | GF | GS". ATTENZIONE: nel testo il nome squadra è seguito dalla sigla attaccata (es. "PALLAMANO TRIESTE 1970 SSDTS", "JOLLY CAMPOFORMIDOJOL"): togliere la sigla.
- Classifiche: sempre ufficiali (classifica_calcolata false). Serie A/B e U16-U18: 2 punti vittoria, 1 pareggio. Under 14: punteggio diverso (fino a 5 punti a vittoria), usare la classifica pubblicata così com'è (può non essere aggiornata all'ultima gara).
- Limite: nei calendari U18 maschile e U16 maschile gir. C i punteggi delle gare giocate non sono pubblicati (solo "-"): file con sola classifica ufficiale + prossima giornata. Ricontrollare ogni settimana.

Gironi caricati (stato al 25/11/2026):
| slug | ultima giornata | squadre FVG |
|---|---|---|
| serie-a-gold-maschile | 11 (prossima 12, 28/11) | Trieste |
| serie-b-maschile-area-3 | 6 | Pallamano Trieste 1970 (squadra B), Jolly Campoformido |
| u18-maschile-area-3 | 6 (nessun punteggio pubblicato) | Pallamano Trieste 1970 |
| u16-maschile-area-3-girone-c | 6 (punteggi solo 1ª giornata) | Pallamano Trieste 1970, Immobiliare Macoratti Jolly Campoformido |
| u16-femminile-area-3 | 4 | U16 CUS Udine |
| u14-maschile-area-3-girone-c | 3 | Pallamano Trieste 1970, Banca di Udine Jolly Campoformido |
Senza squadre FVG (non caricati): U16 M gir. A e B, U14 M gir. A e B ("San Vito Marano" = Marano Vicentino, VI), Serie A Silver, A1 femminile, A2 femminile (gironi A/B senza FVG secondo la pagina e le note di data.json).
Non letto: under-14-femminile-area-3 (PROVENANCE_REQUIRED).

## HOCKEY
### Hockey inline (FISR)
- Portale risultati https://hockeyinline.fisr.it/ NON leggibile (robots.txt non raggiungibile).
- Fonte usata: comunicati settimanali FISR, elenco in https://www.fisr.it/hockey-inline/news-hockey-inline.html (titoli "… giornata di Serie A …"). Contengono risultati, classifica (solo punti) e spesso il programma della giornata successiva.
  Letti: news 21867 (1ª g.), 21887 (2ª), 21896 (programma 3ª), 21901 (risultati 3ª), 21907 (4ª + programma 5ª), 21910 (5ª + programma 6ª), 21922 (6ª, 24/11/2026). URL: https://www.fisr.it/news/<id>-<titolo>.html.
- Punteggio: 3 vittoria, 2 vittoria dopo overtime/rigori, 1 sconfitta dopo overtime/rigori. Classifica: punti ufficiali; G e gol ricalcolati dai risultati.
- Attenzione: nei comunicati dei risultati l'ordine casa/ospite a volte è invertito rispetto al programma: si tiene il programma e si annota.
- File: risultati/hockey/inline-serie-a.json (6 giornate; Edera Trieste). Programma 7ª giornata non ancora pubblicato al 25/11.
- Non trovati: Serie A2/B/giovanili inline (nessun comunicato FISR; portale illeggibile). Kwins Polet Trieste: campionato 2026/27 non verificato.
### Hockey su pista (FISR)
- https://www.fisr.it/hockey-pista.html: nessuna squadra FVG individuata nelle serie nazionali; non caricato.
### Hockey su ghiaccio (FISG)
- Portale ufficiale https://italia.hockey/championship/?level=633 (IHL Division I) e ?level=741: calendario leggibile, classifiche e risultati caricati via JavaScript (non leggibili); intestazione stagione incoerente ("24/25", "25/26").
- Nessuna squadra FVG in IHL Division I; nelle partite elencate di IHL Serie A/IHL non compaiono squadre FVG. "Zoldo U16" compare in Under 16 (club di Zoldo/Claut: appartenenza a U.S.G. Zoldo Valcellina 093015-1 non verificata). Non caricato.
- Hockey su prato (FIH, es. A.R. Fincantieri Monfalcone in A2) fuori ambito.

## PALLANUOTO (FIN) — non caricata
- Pagine ufficiali (struttura navigazione OK, dati via JavaScript, illeggibili):
  A1 M https://www.federnuoto.it/home/pallanuoto/campionato-a1-maschile/2026-2027-pn-m/regular-season-pn-m-2026-2027.html
  A1 F https://www.federnuoto.it/home/pallanuoto/campionato-a1-femminile/2026-2027-pn-f/regular-season-pn-f-2026-2027.html
  A2 M/F Nord, B M gironi 1-4: link dalla pagina https://www.federnuoto.it/home/pallanuoto.html
- it.wikipedia "Serie A1 2026-2027 (pallanuoto maschile)" ed en.wikipedia "2026–27 Serie A1 (men's water polo)": non esistono.
- finfvg.it: robots.txt non raggiungibile. Nessun PDF di comunicati FIN con risultati trovato.
- Unica fonte leggibile: articoli di stampa (oasport.it, 1x2pallanuoto.com) — NON usati perché non ufficiali. Se il coordinatore li autorizza: oasport pubblica per ogni giornata risultati e classifica (es. 6ª giornata A1 M del 7/11/2026).
- Da provare: pagine "pallanuoto-extra" del sito FIN (esisteva https://www.federnuoto.it/pallanuoto-extra/2023-2024/8914-serie-a1-maschile-2023-2024-classifica.html), sito FIN Veneto (finveneto.org) per eventuali campionati giovanili interregionali.

## TENNISTAVOLO (FITeT) — non caricato
- Portale risultati http://portale.fitet.org/ (regionale FVG: http://portale.fitet.org/risultati/regioni/default_reg.asp?REG=8): robots.txt non raggiungibile, illeggibile con WebFetch.
- Sito comitato FVG http://fvg.fitet.org/it/friuliveneziagiulia.html: leggibile ma senza calendari/classifiche 2026/27 (rimanda al portale).
- Nessuna news fitet.org con classifiche di serie nazionali con squadre FVG trovata.

## Abbinamenti squadra -> società (data.json)
- Pallamano Trieste 1970 (032006-25): "TRIESTE" (Serie A Gold), "Pallamano Trieste 1970" (Serie B, squadra B), "PALLAMANO TRIESTE 1970 SSD" / "Pallamano Trieste 1970 SSD" (giovanili).
- Jolly Handball Campoformido (030016-2): "Jolly Campoformido", "Immobiliare Macoratti Jolly Campoformido", "Banca di Udine Jolly Campoformido" (sponsor indicati nelle note di data.json).
- CUS Udine pallamano (030129-18): "U16 CUS UDINE".
- Edera Trieste (032006-29): "Edera Trieste" (hockey inline Serie A).
- Squadre venete e di altre regioni: senza id.

## Aggiornamento settimanale (lunedì-martedì)
1. Pallamano: rileggere classifica + calendario-e-risultati di ciascun girone sopra (13 fetch circa); aggiungere le nuove righe ai file _lavoro/<girone>.txt (e <girone>_cl.txt), aggiornare in <slug>.spec.json "aggiornato", "ultima_giornata", eventualmente "giornata" e "note"; per la prossima giornata copiare le righe del calendario; poi mk.py su ogni spec.
2. Hockey inline: leggere le nuove news su https://www.fisr.it/hockey-inline/news-hockey-inline.html, aggiungere i risultati a _lavoro/inline-a.txt, rigenerare inline-a_cl.txt con i punti ufficiali, aggiungere il programma della giornata successiva (risultato vuoto).
3. Riprovare le fonti non funzionanti (portale.fitet.org, hockeyinline.fisr.it, FIN) e U14 femminile pallamano.
4. `cd /home/claude/fvg && python3 build_risultati.py`.
