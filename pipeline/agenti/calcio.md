# Agente CALCIO FVG (LND FVG + FIGC SGS + Divisione Calcio a 5)

Ambito: calcio a 11 maschile e femminile, calcio a 5, tutte le categorie da Under 12 in su.
Categorie federali (stagione 2026/27): Esordienti (U12/U13), Giovanissimi (U14/U15), Allievi (U16/U17), Juniores (U19), Prima squadra (Serie C/D, Eccellenza, Promozione, Prima, Seconda, Terza, Campionato Carnico), femminile (Serie C, Eccellenza, U15/U17 F), calcio a 5 (Serie A2 Elite, B, C1, C2, giovanili).
Nel campo "categoria" usa: Under 12, Under 13, Under 14, Under 15, Under 16, Under 17, Under 18, Juniores (U19), Prima squadra, Seconda squadra (e "Calcio a 5" per la squadra C5 di una società di calcio a 11); nel "campionato" la denominazione federale (es. "Giovanissimi Under 15 regionali girone A").

## Struttura dei campionati 2026/27 (verificata)
- Regionali (Comitato Regionale, CR): Eccellenza girone A (unico, 18 sq.), Promozione girone A (unico, 18), Prima Categoria gironi A (ovest/PN) e B (est/UD-GO-TS), 18 sq. ciascuno; Juniores U19 regionale A (20), Under 18 regionale A (19), Under 17 regionale A (17), Under 16 regionale A (18), Under 15 regionale A (17); Calcio a 5 Serie C1 regionale girone A.
- Delegazioni: Seconda Categoria gironi A (PN), B e C (UD), D (TS, con squadre goriziane); Terza Categoria gironi A (PN), B e C (UD), D (GO/TS).
  Giovanili provinciali: Under 19, Under 17, Under 16, Under 15 con un girone per Delegazione (Udine U17 ha A e B); Under 14 gironi A-B (PN), C-D (UD), E (GO), F (TS).
- Campionato Carnico (Delegazione di Tolmezzo), anno solare (2026: aprile-ottobre): 1ª Categoria girone 6A, 2ª girone 6B, 3ª girone 6C, più Giovanissimi ed Esordienti Carnico.
- Nei CU le squadre con "sq. B" sono seconde squadre della stessa società nella stessa categoria.
- Omonimie: "TORRE" = A.S.D. Torre di Pordenone (Prima A, giovanili PN); "TORRE TC" (o TORRE nei gironi di Trieste/Gorizia) = A.S.D. Torre di Campolongo Tapogliano. "AUDAX" nel Carnico = Pol. Audax di Forni di Sotto, diversa da Audax Sanrocchese (Gorizia).

## Fonti verificate (stagione 2026/27)
Tutto il sito friuliveneziagiulia.lnd.it va letto SOLO con WebFetch (curl -> 403 dal proxy). I PDF lunghi vanno letti a pezzi con offset (100000 caratteri per pezzo).
- Archivio file (API WordPress), il modo più rapido per trovare i CU:
  https://friuliveneziagiulia.lnd.it/wp-json/wp/v2/media?after=2026-11-01T00:00:00&before=2026-11-25T00:00:00&mime_type=application/pdf&per_page=100&_fields=date,source_url
  (search=<testo> funziona solo sul titolo; "calend" trova solo CU-12 e il PDF di Trieste; "carnico" e "femminil" non trovano calendari 2026/27).
- Calendari regionali (Eccellenza, Promozione, Prima A/B, U19, U18, U17, U16, U15 regionali): CR CU n.12 del 21/08/2026
  https://friuliveneziagiulia.lnd.it/wp-content/uploads/2026/08/CU-12-CALENDARI-UFFICIALI-20262027.pdf
- Gironi Under 19 provinciali (GO, UD, PN): Delegazione Udine CU n.8 del 28/08/2026
  https://friuliveneziagiulia.lnd.it/wp-content/uploads/2026/08/CU-08-1.pdf (stesso testo in /2026/08/go_cu_8_2026_-_2027.pdf)
- Gironi U17, U16, U15, U14 provinciali di tutte le Delegazioni: Delegazione Udine CU n.9 del 04/09/2026 (versione aggiornata, U15 Udine senza Tamai sq. B e con Unione SMT)
  https://friuliveneziagiulia.lnd.it/wp-content/uploads/2026/09/CU_09.pdf (prima versione in /2026/09/go_cu_9_2026_-_2027.pdf)
- Calendari Delegazione Trieste (Seconda D, U17, U15, U14):
  https://friuliveneziagiulia.lnd.it/wp-content/uploads/2026/09/CALENDARI-TRIESTE-2CAT-U17-U15-U14.pdf
- Seconda/Terza Categoria UD, PN, GO: i calendari sono solo negli allegati ZIP; le squadre si ricavano dai risultati di una giornata completa nei CU settimanali (vedi sotto). Usati: Udine CU n.27 (19/11/2026) /2026/11/CU-27.pdf; Pordenone CU n.37 (18/11/2026) /2026/11/2026-C.U.-N.-37-Delegazione-PN-2026-2027.pdf; Gorizia CU n.24 (19/11/2026) /2026/11/go_cu_24_2026_-_2027.pdf.
- Campionato Carnico 2026: Delegazione Tolmezzo CU n.21 del 30/09/2026 (risultati 1ª/2ª/3ª categoria e Giovanissimi)
  https://friuliveneziagiulia.lnd.it/wp-content/uploads/2026/09/Comunicato-Ufficiale-nr-21-del-30092026.pdf
- Calcio a 5 Serie C1 regionale: risultati nel CR CU del giovedì, es. CU n.50 del 19/11/2026 /2026/11/CU-50.pdf
- Annuario 2026/27 (società, matricola, campo di gioco con località): 
  https://friuliveneziagiulia.lnd.it/wp-content/uploads/2026/11/ANNUARIO-2026-2027-aggiornato-al-19.11.26.pdf (127.000 caratteri: due pezzi, offset 100000). Viene ripubblicato con nuova data (…aggiornato-al-DD.MM.YY.pdf).
- Classifiche ufficiali 2022/23: /wp-content/uploads/2023/06/all_tscu103_Classifiche-Ufficiali.pdf
- Divisione Calcio a 5: classifiche serie nazionali della stagione in corso.

## Non funzionano / non contengono quanto serve
- Tuttocampo, FriuliGol, web.archive.org, tabelle classifica di Wikipedia.
- Allegati ZIP (Calendari-AdB.zip, CU-xx-Allegati.zip, Allegati_tscuNN.zip, cu_N_allegati.zip): contengono i calendari di Seconda/Terza, femminile, Esordienti ma non sono leggibili.
- URL indovinati: un PDF caricato a settembre sta in /2026/09/ anche se il CU è di agosto (es. go_cu_9 non è in /2026/08/). Ricavare sempre l'URL dall'API media.
- CR CU del lunedì (es. CU-52 23/11/2026) e CU del venerdì (CU-51): quasi nessun risultato.
- CR CU-106 del 11/05/2026: nessuna classifica finale 2025/26 (solo play-off/play-out).
- Pagina Delegazione di Tolmezzo e menu del sito: nessun link a calendari/classifiche.
- Calcio femminile regionale e calcio a 5 C2/giovanili C5: nessun calendario o risultato trovato nei CU di novembre (CU-44, CU-50, CU-51); probabilmente solo negli allegati ZIP.
- Identificativi ufficiali dei gironi (id_fonte): i PDF dei CU non ne hanno; non trovati.

## Per i risultati in tempo reale
Nessuna fonte ufficiale pubblica le CLASSIFICHE in corso di stagione: i CU 2026/27 riportano solo i risultati ("RISULTATI UFFICIALI GARE DEL gg/mm/aaaa", per girone e giornata, con "(1) disputata il …" per gli anticipi) e le decisioni del Giudice Sportivo. Le classifiche vanno calcolate dai risultati (3-1-0) tenendo conto delle decisioni del Giudice (gare "v.del." = vedi delibera, sospese, 0-3 a tavolino) pubblicate nello stesso CU o nei successivi.
Come trovare il CU giusto: API media con after=<lunedì della settimana> e mime_type=application/pdf; i file del giorno compaiono entro le 20:00.

Fonte per campionato (frequenza e nome file osservati a novembre 2026):
- Eccellenza A, Promozione A, Prima Categoria A e B, Under 16 regionale, Calcio a 5 C1 girone A: CR FVG, CU del giovedì (es. CU n.50 19/11/2026 con le gare del 14-15/11). File /AAAA/MM/CU-NN.pdf (numerazione CR: 50, 51, 52, 53…; tre-quattro CU a settimana; quelli di lunedì/venerdì contengono solo recuperi e gare sospese). Nel CU n.50 non c'erano risultati di U19, U18, U17, U15 regionali: verificare nei CU successivi.
- Seconda B e C, Terza B e C, U19/U17 (A, B)/U16/U15/U14 (C, D) provinciali Udine, più Esordienti e Pulcini (solo "DISP."): Delegazione Udine, CU settimanale del giovedì, file /AAAA/MM/CU-NN.pdf con numerazione propria (n.27 = 19/11/2026; da non confondere con la serie CR, che ha numeri più alti).
- Seconda A, Terza A, U19/U17/U16/U15/U14 (A, B) provinciali Pordenone: Delegazione Pordenone, CU del mercoledì per la giornata del weekend (n.37 18/11/2026) più CU di giovedì/venerdì/lunedì per i recuperi. File /AAAA/MM/2026-C.U.-N.-NN-Delegazione-PN-2026-2027.pdf (a volte con suffisso -1, -2).
- Terza D, U19/U16/U15 provinciali Gorizia, U14 girone E, Esordienti/Pulcini misti GO: Delegazione Gorizia, CU del giovedì, /AAAA/MM/go_cu_NN_2026_-_2027.pdf (n.24 19/11/2026).
- Seconda D, U17/U15/U14 (F) provinciali Trieste: Delegazione Trieste, /AAAA/MM/ts_cu_NN_2026-2027.pdf (2-4 a settimana, n.41 24/11/2026; non ancora verificato quale contiene i risultati).
- Campionato Carnico (aprile-ottobre): Delegazione Tolmezzo, /AAAA/MM/Comunicato-Ufficiale-nr-NN-del-GGMMAAAA.pdf (settimanale, n.21 30/09/2026 con risultati 1ª/2ª/3ª e Giovanissimi). D'inverno la serie continua (n.29 24/11/2026) ma senza gare.
- Serie D, Serie A2 Élite/B calcio a 5: fonti nazionali (LND Dipartimento Interregionale, Divisione Calcio a 5), non coperte qui.
Verificato il 24/11/2026 (regionali), tutte le giornate 1-11 lette:
- Giornate di andata (CU-12): Eccellenza e Promozione dal 6/9 ogni domenica; Prima A/B g1 13/9, g2 sab 19/9, g3 mer 23/9, poi domeniche dal 27/9 (g4) come Ecc/Prom; g12 22/11, g13 29/11, g14 5/12, g15 mar 8/12, g16 13/12, g17 19-20/12. Orario ufficiale g12 = 14:30 per tutti e quattro (CU-12 dà l'orario per colonna di giornate, non per gara; le variazioni stanno in "MODIFICHE AL PROGRAMMA GARE" dei CU). CU-12 ha anche l'"ELENCO CAMPI DA GIOCO" per società (campo = squadra di casa; non ancora estratto).
- Mappa CR CU -> giornata (base https://friuliveneziagiulia.lnd.it/wp-content/uploads/):
  2026/09/CU-20.pdf (10/9): g1 Ecc, Prom | 2026/09/CU-23.pdf (17/9): g2 Ecc, Prom, g1 Prima A/B | 2026/09/CU-25.pdf (22/9, martedi): g2 Prima A/B | 2026/09/CU-26.pdf (24/9): g3 Ecc, Prom | 2026/09/CU-27.pdf (25/9): g3 Prima A/B (Unione Friuli Isontina-Isonzo spostata al 30/9) | 2026/10/CU-29.pdf (1/10): g4 tutti | 2026/10/CU-31.pdf (8/10): g5 tutti + recupero UFI-Isonzo | 2026/10/CU-34.pdf (15/10): g6 tutti (CU-35 = solo assemblea) | 2026/10/CU-37.pdf (22/10): g7 | 2026/10/CU-41.pdf (29/10): g8 | 2026/11/CU-43.pdf (5/11): g9 | 2026/11/CU-47.pdf (11/11, mercoledi): g10 | 2026/11/CU-50.pdf (19/11): g11. CU-42, CU-44: nessun risultato di campionato. Nessuna gara a tavolino o penalizzazione per Ecc/Prom/Prima fino al CU-50.
- Regola pratica: il CU con i risultati del weekend esce di solito giovedì (a volte mercoledì o martedì); usare l'API media con after=<lunedì> e prendere il primo CU-NN.pdf del CR (numero > 50) che contenga "GIRONE A - N Giornata".
- IMPAGINAZIONE: nel testo estratto i blocchi di risultato finiscono quasi sempre sotto intestazioni sbagliate (Promozione sotto "Under 17"/"Under 18"/"Juniores", Prima sotto "Under 17"/"Coppa Regione"), e il riassuntore li scarta o li attribuisce male. Prompt che funziona: "Elenca VERBATIM TUTTI i blocchi di risultati (riga GIRONE X - N Giornata - A + righe + note) che contengono almeno una di queste squadre, ignorando le intestazioni: <2 squadre per girone>". Poi attribuire il girone dall'insieme completo delle 18 squadre (le giovanili regionali hanno nomi simili ma avversari diversi, es. SANTAMARIA, CHIAVRIS, S.GOTTARDO, REANESE = giovanili).
- Controllo: per ogni girone 9 gare per giornata, ogni squadra una volta, nessuna coppia ripetuta nell'andata (script di controllo e generazione: /home/claude/fvg/risultati/calcio/_lavoro/script/genera.py; dati in _lavoro/ris.txt, giornata successiva in _lavoro/g12.txt).
- Aggiornamento settimanale: 1) leggere il nuovo CU (giornata N) e aggiungere a ris.txt le 36 righe; 2) leggere da CU-12 gli accoppiamenti della giornata N+1 (in g12.txt, rinominarlo) e l'orario; 3) controllare "MODIFICHE AL PROGRAMMA GARE" e decisioni del Giudice (0-3, penalizzazioni: vanno applicate a mano nello script); 4) rilanciare genera.py (python3 -I) dopo aver aggiornato giornata/aggiornato/fonte.
- Abbinamento id: tutti i 72 nomi CU di Ecc/Prom/Prima A/B sono in IDS dentro genera.py (verificati sui nomi di data.json). CALCIO MANIAGO VAJONT (093025-1) in data.json risulta in "Seconda Categoria girone A" ma gioca in Prima A: da correggere in data.json.
Aggiornamento 25/11/2026 (sessione agente risultati calcio):
- ACCESSO WEB (vincolo forte): WebFetch apre senza conferma solo gli URL comparsi in un risultato di WebSearch (e, non sempre, quelli comparsi in un risultato di WebFetch). Gli URL "costruiti" (API media, CU-NN.pdf noti, /comunicati/2/) danno PROVENANCE_REQUIRED se l'utente non approva la richiesta di permesso: in una sessione senza utente presente sono di fatto bloccati e NON vanno ritentati. Con l'utente presente (sessione principale) l'API media resta il metodo migliore.
- Ingresso che funziona: WebSearch con "comunicati" fa emergere https://friuliveneziagiulia.lnd.it/comunicati/ (e https://friuliveneziagiulia.lnd.it/index.php?lang=it). La pagina /comunicati/ elenca gli ultimi 20 CU di CR e Delegazioni (ente, data, numero) con link https://friuliveneziagiulia.lnd.it/comunicati_post/comunicato-ufficiale-n-NN-XX/ (XX = progressivo dello slug, non la stagione); ogni pagina post contiene il link al PDF (/wp-content/uploads/AAAA/MM/...) e allo ZIP allegati. Paginazione /comunicati/2/ … /comunicati/304/. Al 25/11 l'indice di ricerca non contiene i PDF FVG di ottobre-novembre 2026 (solo fino a settembre).
- Come leggere i CU con WebFetch: la richiesta "copia VERBATIM" viene rifiutata dal riassuntore (limite citazioni). Funziona chiedere una TABELLA di dati: "CATEGORIA | GIRONE | GIORNATA | CASA | OSPITE | GOL CASA | GOL OSPITE | DATA, nomi con la grafia esatta del documento (maiuscolo)", più una seconda tabella "MODIFICHE AL PROGRAMMA GARE: CASA | OSPITE | DATA | ORA".
- Seconda B e C (14 squadre, 7 gare/giornata) e Terza B e C (12 squadre, 6 gare) della Delegazione di Udine: giornata 8 = 14-15/11/2026 (CU Udine n.27, /2026/11/CU-27.pdf), quindi giornata 9 = 21-22/11 (risultati nel CU Udine del 26/11, n.28). Nei gironi di Terza B/C CHIAVRIS, TARCENTINA, BISIACA ROMANA sono seconde squadre (data.json le ha già in Terza). Tutti i 52 nomi abbinati agli id (tabella IDS in _lavoro/script/genera_delegazioni.py).
- CR CU n.29 (1/10/2026) esiste anche come /2026/10/CU-29-1.pdf e contiene risultati Juniores U19, U18, U17 regionali (U16/U15 sezione vuota): i CR CU del giovedì sono la fonte anche per le giovanili regionali.
- Delegazione Trieste CU n.29 dell'8/10/2026: /2026/10/ts_cu_29_2026-2027.pdf (non letto).
- Procedura settimanale Seconda/Terza: 1) aprire /comunicati/ e il post del CU della Delegazione (Udine giovedì, Pordenone mercoledì, Gorizia giovedì, Trieste più CU a settimana); 2) estrarre la tabella risultati e modifiche; 3) aggiungere le righe a _lavoro/ris_deleg.txt (girone|giornata|data|ora|casa|ospite|gc|go|fonte; gc/go vuoti = da giocare) e la sigla del CU nel dizionario CU dello script; 4) python3 -I risultati/calcio/_lavoro/script/genera_delegazioni.py (scrive la classifica solo quando le giornate 1..N sono tutte presenti; altrimenti classifica vuota e "dati_parziali": true); 5) python3 build_risultati.py. Per completare la stagione servono i CU Udine delle giornate 1-7 (circa n.20-26, dal 1/10 al 13/11/2026).
Formato: PDF di testo, letto bene da WebFetch chiedendo "tutte le righe di risultato verbatim, con girone e giornata". Il modello che riassume può attribuire male i blocchi quando l'impaginazione è confusa (successo con go_cu_24: un blocco Under 19 è stato etichettato Under 14): controllare i nomi con le composizioni dei gironi sopra.
