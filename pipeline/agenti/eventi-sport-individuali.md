# Eventi e piazzamenti – sport individuali

## Gruppo A: atletica, ciclismo, sci, vela, canottaggio, nuoto (aggiornato 25/11/2026)

Patch: `patch/eventi-gruppo-a/<ISTAT>.json`. Dati solo a livello di società, mai nomi di atleti.
Raccolta: script di lavoro con una lista di eventi per (codice, nome esatto in data.json); il generatore prende lo `sport` da data.json e scrive un file per comune. Dopo ogni giro: `python3 build.py`, poi controllo che non compaiano righe "social/eventi non abbinato".

### Fonti che funzionano (via WebSearch + WebFetch; curl verso l'esterno è bloccato dal proxy)

**Atletica (FIDAL)**
- Risultati delle gare con classifiche di società in PDF: `https://www.fidal.it/risultati/<anno>/<COD o REG>/...`; la pagina `Index.htm` della gara indica data, luogo e organizzatore. Esempio: CdS FVG 10 km Master, `risultati/2026/COD14772/`.
- Programmi e dispositivi delle gare 2026 (con la società organizzatrice): `https://calendario.fidal.it/files/<nome file>.pdf`. Si trovano con ricerche tipo "calendario.fidal.it files 2026 PROGRAMMA GARA <città>".
- Comunicati stampa FIDAL FVG: `fidal.it/upload/Friuli Venezia Giulia/documentiFVG/Comunicati stampa/<data>_<titolo>/...pdf`.
- Calendari dei circuiti con le società organizzatrici: Libretto Coppa Pordenone (`Comitati Provinciali/Pordenone/LIBRETTO 39^Coppa Pordenone 2026.pdf`) e Regolamento TrofeoFriuli 2026 (`Comitati Provinciali/Udine/TrofeoFriuli 2026 - Regolamento.pdf`).
- worldathletics.org/competition/calendar-results/results/<id>: date e risultati dei CdS (ma senza classifica a punti per società).
- Archivio delle classifiche: `documentiFVG/Classifiche/<anno>/...`. Il file 2026 dei CdS cross non è stato trovato: i nomi indovinati danno errore.

**Sci (FISI FVG)**
- `https://comitati.fisi.org/friuli-venezia-giulia/wp-content/uploads/sites/34/<anno>/<mese>/...pdf`: classifiche ufficiali delle gare regionali, molte con "Classifica società (somma punti)". Per trovarle: "comitati.fisi.org friuli-venezia-giulia 2026 classifica società".
- Calendario FIS FVG 2025-26 (stessa cartella, 2025/11): elenca le società organizzatrici delle gare FIS.
- Nelle gare di scialpinismo non c'è classifica di società: si contano gli atleti classificati per società.

**Vela**
- turismofvg.it/eventi/<slug>: data, luogo e circolo organizzatore delle regate del FVG. È la fonte più rapida.
- Barcolana: articoli di cronaca (yacht.de, barcolana.it).
- pressmare.it e nautica.news per le regate internazionali di Trieste.

### Cosa non funziona
- curl/Bash verso siti esterni (403 dal proxy).
- I PDF FIDAL con nomi indovinati (client_error).
- Coppa Italia Master FISI: nessuna società FVG in classifica.
- Gli articoli di nauticareport spesso non riportano l'anno: verificarlo prima di usarli.
- XIII Zona FIV: non è stata trovata una classifica dei circoli 2026.

### Fonti aggiunte nel secondo giro (25/11/2026)
- **Ciclismo (FCI FVG)**
  - Classifica finale per società del Trofeo Aquilotti: `https://www.fcifriuli.com/classifiche-aquilotti/`, con il PDF in `wp-content/uploads/<anno>/<mese>/`.
  - Classifica FVG MTB Tour: `https://www.fcifriuli.com/classifiche-gare-fuoristrada/` (classifica individuale: si contano gli atleti per società).
  - Calendari XCO FVG MTB Cup e FVG MTB Young Cup con le società organizzatrici: regolamenti su trevisomtb.it (cercare "FVG MTB CUP regolamento <anno>").
  - Eventi organizzati: turismofvg.it/eventi (es. Giro del FVG Juniores) e tuttobiciweb.it.
- **Atletica**
  - `fidal.it/upload/files/Organizzazione/<anno>/Calendario/Assegnazione_Sedi_Campionati_Federali_<anno>_<data>.pdf`: i campionati italiani assegnati alle società del FVG.
- **Canottaggio (FIC)**
  - canottaggio.org `wp-content/uploads/<anno>/<mese>/`: bandi delle regate regionali, Trofeo CONI FVG, programma e classifica del Trofeo Luca Vascotto.
  - "Calendario-flat-<anno>.pdf" e "Calendario-remiero-nazionale-<anno>.pdf": regate nazionali in FVG.
- **Canoa (FICK)**
  - federcanoa.fidalservizi.it: il robots.txt non risulta leggibile e le pagine non si aprono. Le classifiche ECA Cup su kajak.hr funzionano.
- **Vela**
  - grado.it/en/eventi e lignanosabbiadoro.it/en/eventi (stesso schema di turismofvg).
  - snipe.org (report delle regate Snipe, ma senza il circolo degli equipaggi).
- **Sci**
  - Calendario Baby/Cuccioli FVG (`comitati.fisi.org/.../2025/10/Calendario-Sci-Alpino-Baby-Cuccioli-2025_2026-FVG.pdf`) e "programma gara" delle singole gare (società organizzatrice).

### Cosa non funziona (secondo giro)
- FIN FVG (nuoto): risultati e classifiche non indicizzati; nessuna fonte trovata per Nuoto Carnia e SSD Tavagnacco.
- CdS FIDAL di cross 2026: le classifiche finali non sono pubblicate in un PDF trovabile. Il regolamento dà solo le sedi (18/1 Casarsa, 1/2 Majano, 1/3 Povoletto), senza società organizzatrici. L'articolo del Memorial Romano (Povoletto, Libertas Grions) non ha data: non l'ho usato.
- I report Snipe di Monfalcone e Sistiana e le pagine fidal.it/calendario.php non riportano circoli o società utili.

### Ancora scoperti
- Ciclismo: Moser Club Aiello, Pedale Sanvitese, Amici della Pista, Tutti in Pista, BPS Cycling.
- Canottaggio: Canottieri Trieste, SG Triestina Nautica, Nazario Sauro, Canoa Club Naonis, Canoa Kayak Friuli, Polisportiva San Marco.
- Nuoto: Nuoto Carnia, SSD Tavagnacco.
- Vela: circa 25 circoli minori (Duino Aurisina, Monfalcone, Muggia, Lignano, Marano, San Giorgio, Porcia).
- Sci: Sacile, Brdina, Val Gleris, Sci Club Fiumicello, Team Sky Friul.
- Atletica: circa 50 società minori (podismo, trail, triathlon).

### Procedura mensile
1. Atletica: cercare "fidal.it risultati <anno> CdS FVG" e "calendario.fidal.it files <anno> <mese>". Aprire Index.htm e il PDF della classifica di società, poi aggiungere i piazzamenti di tutte le società presenti in data.json (un documento copre decine di società).
2. Sci (dicembre-aprile): cercare "comitati.fisi.org friuli-venezia-giulia <anno>/<mese> classifica società" e usare la tabella "somma punti".
3. Vela: cercare "turismofvg.it eventi regata <mese> <anno>" e la cronaca della Barcolana.
4. Usare il nome esatto di data.json; la data in formato AAAA-MM-GG (AAAA-MM se il giorno non è noto); la fonte è l'URL del documento.
5. Eseguire `python3 build.py` e verificare che non compaiano righe "social/eventi non abbinato".

## Gruppo B: judo e arti marziali, ginnastica, pattinaggio, scherma, tiro, tennistavolo, tennis, danza, bocce, altro (aggiornato 25/11/2026, giro 2)

Patch in `patch/eventi-gruppo-b/<ISTAT>.json` (52 file, 114 società, ~290 eventi; tutte abbinate dal build).
Generatore usato: script Python per sport con lista (codice, nome esatto in data.json, sport in data.json, eventi) -> un file per comune; il build deduplica per data+evento.
Attenzione al campo "sport": deve essere lo sport della società in data.json (es. ASU = "ginnastica" anche per eventi di scherma; S.G. Ginnastica Triestina = "basket"; karate/pugilato/kickboxing = "judo").

### Fonti che funzionano, per sport
- **Judo** – archivio risultati FIJLKAM FVG: https://www.fijlkam.it/fvg/arti-marziali/circolari/friuli_venezia_giulia/risultati/judo-1.html
  "Classifica società" (Valli del Torre, Shimai) = dato migliore; "Campionato Regionale ... Results" = podi per categoria con sigla società; "CLASSIFICHE CRITERIUM/LATISANA" = tabella SOCIETA' ATLETI (partecipazione; la colonna 1°-4° è la CLASSE, non il piazzamento). PAR 2026 (calendario con eventi delle società): https://www.fijlkam.it/fvg/judo/comunicati-e-circolari-judo/par-2026/1894-03-par-2026/file.html
- **Karate** – news karate FIJLKAM FVG (medaglieri per società): https://www.fijlkam.it/fvg/news/12-karate.html ; calendario karate 2026 (gare organizzate dalle società): https://www.fijlkam.it/fvg/comunicati-e-circolari/karate/1858-calendario-2026/file.html
- **Pattinaggio** – sito FISR FVG https://www.fisrfvg.it : elenco comunicati Artistico https://www.fisrfvg.it/docs/sezione.php?IDCat=2 e Corsa https://www.fisrfvg.it/docs/sezione.php?IDCat=3 ; i PDF `https://www.fisrfvg.it/files/comunicati/2026/<N>a26.pdf` (artistico) e `<N>c26.pdf` (corsa) con "ordine di entrata in pista" / "elenco atleti" danno il numero di atleti per società; i comunicati corsa indicano la società organizzatrice. Il comunicato 1a26 è il calendario regionale. Calendario per zona: https://www.fisrfvg.it/core/base_calendario_zona.php?IDZona=1&anno=2026 ("c/o società" = sede). Sito ASD Pattinaggio Ronchi con news risultati.
- **Scherma** – sito Federscherma FVG https://friuliveneziagiulia.federscherma.it (news con medaglie per società); classifica "Gran Premio Giovani per Società" (federscherma.it, PDF "lettera-per-GPGiovani-per-Societa-<stagione>"); comunicati gare (squadre iscritte ai campionati a squadre).
- **Tennistavolo** – news Comitato FITeT FVG: http://fvg.fitet.org/it/friuliveneziagiulia/friuliveneziagiulia/news/news-fvg.html (campionati regionali con titoli per società, tornei nazionali); news nazionali fitet.org (tornei Over/Giornate Rosa in FVG). Siti società: tennistavoloquadrifoglio.org, amicidelluniversita.units.it.
- **Bocce** – calendario gare FIB FVG (volo), con società organizzatrice e link dettaglio per ogni gara: https://www.federbocce.it/friuliveneziagiulia/gare.html?specialita=V&start=0 (pagine successive con start=100, 200...). Ci sono anche referti PDF in `federbocce.it/friuliveneziagiulia/images/friuliveneziagiulia/Anno_2026/Risultati_gare_2026/`.
- **Tiro con l'arco** – risultati FITARCO: `https://www2.fitarco-italia.org/upload_2026/r2607NNN_grid.pdf` (07 = FVG; i PDF riportano solo il codice società 07xxx: 07003 Arcieri Udine, 07009 Cormons, 07014 Arco Club Tolmezzo, 07017 Maniago, 07021 Codroipo, 07001 Arcieri Trieste, 07022 Arco Club Monfalcone, 07026 Trieste Archery Team).
- **Ginnastica** – circolari federginnastica.it con ordine di lavoro delle prove di Serie A (squadre in gara).
- **Tennis** – tennistourtalk.com / ATP per Internazionali FVG di Cordenons; fitp.it (Coppa Belardinelli, elenchi squadre provinciali – spesso senza anno).
- **Altro** – triathleta.it (classifiche gare e atleti per società FVG); sito eventi lignanosabbiadoro.it (organizzatore); sportest.it per football americano.

### Tabella sigle FIJLKAM -> nome in data.json
AZZANESE=A.S.D. Judo Azzanese (093005); KUROKI=A.S.D. Judo Kuroki (030116); DOJO SACILE=A.S.D. Dojo Sacile (093037); SKORPION PN=A.S.D. Skorpion Club Libertas Pordenone (093033); SEKAI BUDO=A.S.D. Sekai-Budo Pordenone; VILLANOVA=Polisportiva Villanova A.S.D.; DLF UDINE / DLF YAMA ARASHI=A.S.D. Polisportiva DLF Udine (030129); SPORT TEAM=A.S.D. Sport Team Judo Udine; SHIRO SAIGO=A.S.D. Judo Shiro Saigo; S. VITO PN=A.S.D. Judo Club San Vito (093041); ACC.MUGGIA=A.S.D. Accademia Muggia (032003); JUDO TAMAI=A.S.D. Polisportiva Tamai sezione Judo Libertas (093007); J.SHIMAI=A.S.D. Pol. Judo Club Shimai Dojo (030037); KEN OTANI=A.S.D. Judo Club Ken Otani Trieste; SGT=Società Ginnastica Triestina A.S.D. (judo); C.TOLMEZZO=A.S.D. Judo Club Tolmezzo; A&RPALESTRE=A&R Palestre S.S. Dilettantistica a r.l.; DLF TRIESTE=S.S.D. D.L.F. Trieste; WHITE TIGER=A.S.D. White Tiger Judo Club (093051); MONTEREALE=Polisportiva Montereale S.D. (judo); CORPOLIBERO=S.S.D. Corpo Libero srl (031016); DOJOTRIESTE=A.S.D. Dojo Trieste; CIVIDALE=A.S.D. Judo Cividale; FENATI=A.S.D. Judo Club Gianfranco Fenati (093044); ISAO OKANO=031012; KYU SHIN RYU=030023; JUDO KAI GRADISCA=031008; SPARTAN=A.S.D. Judo Club Spartan ONLUS; SPORTING LATISANA=030046; FITAPP=FitApp S.r.l. S.S.D. (030026).

### Sigle FISR -> nome in data.json (pattinaggio)
PATT. ART.JOLLY=A.S.D. Pattinaggio Artistico Jolly; POL.DIL.CA OPICINA=Pol. Dilettantistica Opicina; PATT.ART.TRIESTINO=A.S.D. Patt. Artistico Triestino; ACC.PATT.ART. ASD (TS)=Accademia Pattinaggio Artistico ASD; SKATING C.GIONI=Ass.ne Dilettantistica Skating Club Gioni Trieste; PATT.GGIO FIUMICELLO=A.S.D. Pattinaggio Fiumicello; PATT. RONCHI=Ass. Dilettantistica Pattinaggio Ronchi; PATTINAGGIO ART.PN=A.S.D. Pattinaggio Artistico Pordenone; POL.ORGNANO=Polisportiva Orgnano; R.C.IL CASTELLO=A.S.D. Roll Club Il Castello-Saciletto; A.PATT.ART. MUZZANA=AS Dilettantistica Acc. Pattinatori Artistici Muzzana; ROLL CLUB PAVIA=A.S.D. Roll Club - Pavia di Udine; PATT.CIVIDALESE=Ass. Sport. Dilettantistica Patt. Cividalese; R.T.ROMANS D'ISONZO=A.S.D. Roller Time Romans d'Isonzo; P.A. AZZANESE=A.S.D. Patt. Art. Azzanese; VIPAVA=A.S. Slovena Dilettantistica Vipava.

### Cosa non funziona
- curl/Bash verso siti esterni: bloccato dal proxy. Solo WebFetch.
- Pagine costruite a mano (URL non comparsi in un risultato di ricerca o in una pagina letta) possono chiedere un permesso che non arriva (oasport.it): cercarle prima con WebSearch.
- pordenonetoday.it, triesteprima.it: errore del sito (client_error) con WebFetch. udine.plus-center.com: robots.txt non leggibile.
- Conteggi da PDF lunghi fatti dal lettore WebFetch: a volte errati. Usare solo dati coerenti tra due letture; preferire tabelle già aggregate (classifiche società, SOCIETA' ATLETI).
- Ricerche generiche per pattinaggio/tennistavolo/bocce: inutili; andare direttamente ai siti dei comitati (sopra).
- FPI (pugilato) FVG: nessuna news con risultati; classifiche di merito FPI solo 2023-2024. Orienteering FISO: i comunicati non indicano la società organizzatrice. Golf (percorsidigolf.com): solo gare future di circolo. Tiro a segno UITS e tiro a volo FITAV: nessun risultato FVG trovato.
- Ginnastica: la serie dell'Artistica '81 nei documenti FGI non è chiara (A1 o A2) -> registrato solo "in gara nella Serie A2 GAM-GAF" come da ordine di lavoro.

### Ancora scoperti (giro 2)
Judo: Ichiban Budo Dojo, Dojo Judo Udine, Burning Team, Taiji Kase, Shotokan Buja, Fiamma Karate Gemona, Gichin Funakoshi, Ryugin Ju-Jitsu, Centro Studio Karate Monfalcone, Ju-Jitsu Ryu Sakura, Bear Brothers, Sakura ASD, Centro Studi Arti Marziali PN, Budo Life, Sakura-Grado, Kickboxing Bellator e quasi tutti i club di pugilato FPI. Pattinaggio: Taurus Buja, Rollin Skate Carlino, Klan del Bosco, Coniferae, Pattinaggio Udinese, La Fenice Goriziana, Edera, Il Volo Bannia, New Skate Pasiano, S.Vito, Aquileiese, San Daniele. Tennistavolo: Moruzzo, Julijce, Acquamarina, Sicuramente Young, Flumen, Astra. Tennis: TC Udinese, Udine Plus, TC Fiumicello, Borgolauro. Tiro: tiro a segno (Udine, Tolmezzo, Cividale), tiro a volo Campoformido, Arcieri Trieste, Trieste Archery Team, Arco Club Monfalcone. Bocce: Aiello, Moimacco, Pantianicco, Bujese, Cussignacco (nessuna gara di volo nel periodo nel calendario FIB). Danza: Azzurra Danze. Scherma: Sala d'Arme Marozzo. Altro: golf, CAI, volo libero, orienteering, football (tranne Muli), Dart Club, Motoclub Fanna, Bor, In Movimento, Juvenilia, Villa, Il Cane, Biodinamicamente.

### Procedura mensile
1. Judo: archivio risultati FIJLKAM FVG -> nuovi documenti dopo l'ultimo aggiornamento; classifica società se c'è, altrimenti titoli (1° posti) o "partecipazione con N atleti". Karate: news karate FIJLKAM FVG.
2. Pattinaggio: elenco comunicati FISR FVG (artistico e corsa) -> nuovi PDF "ordine di entrata"/"elenco atleti" (conteggio per società) e comunicati con società organizzatrice.
3. Scherma: news Federscherma FVG; a fine stagione la classifica GP Giovani per Società.
4. Tennistavolo: news FITeT FVG + fitet.org (tornei in FVG).
5. Bocce: calendario gare FIB FVG (gare organizzate; referti PDF per i risultati).
6. Tiro con l'arco: cercare "fitarco-italia.org upload_<anno> r<aa>07" per i nuovi PDF regionali.
7. Mappare i nomi con le tabelle sopra, aggiungere al file `patch/eventi-gruppo-b/<ISTAT>.json`, poi `cd /home/claude/fvg && python3 build.py` e verificare che non ci siano righe "social/eventi non abbinato".
