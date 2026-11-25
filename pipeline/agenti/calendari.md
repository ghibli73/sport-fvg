# Agente CALENDARI — calendari completi e partite spostate

Ruolo: tenere in `data/risultati.json` il calendario completo di ogni girone (partite future con giornata, data, ora e campo)
dovunque la fonte ufficiale lo pubblichi, e tenerlo aggiornato quando date, orari e campi cambiano (anticipi, posticipi,
cambi di palestra o di campo, recuperi). Gli script girano solo su GitHub Actions (unico ambiente che raggiunge i siti
delle federazioni); per guardare una fonte si usa il workflow "Sonda fonti" (vedi in fondo).

## Formato
Ogni partita futura ha `risultato: ""`, `giornata`, `data` (AAAA-MM-GG), `ora` (HH:MM, se nota), `campo` (se noto) e,
per pallavolo e basket, `gara` (numero gara federale). Se una partita non giocata cambia data o ora,
`scripts/variazioni.py` (passo "Partite spostate" dei workflow, dopo lo script dello sport) aggiunge:
- `variata`: "AAAA-MM-GG", giorno in cui ce ne siamo accorti;
- `data_prec`: la data di prima (se è cambiata la data) oppure `ora_prec` (se è cambiata solo l'ora).
I segni vengono riportati agli aggiornamenti successivi e tolti dopo 30 giorni. In app (index.html) la partita mostra per
7 giorni l'etichetta "Spostata" (data cambiata) o "Orario cambiato", sotto data e ora; la scheda società la mostra accanto
alla prossima partita. Un cambio del solo campo aggiorna il campo ma non è una "variata".

Come si riconosce la stessa partita tra prima e dopo: stesso girone e stesso numero gara (`gara`); in mancanza, stesse
squadre (casa, ospite) e stessa giornata. La giornata non cambia mai per uno spostamento.

## Avvisi
`scripts/avvisi.py`: oltre ai risultati, "Partita spostata: Casa – Ospite" con testo "sab 28/11 ore 14:30 (era dom 29/11
ore 14:30) · girone" alle due società (argomento ntfy `zuin-fvg-<id>`), Tags `calendar`, solo se la data nuova o vecchia
cade entro i prossimi 10 giorni. Stesse regole e stesso limite (200 avvisi, 8 minuti) degli avvisi dei risultati, che
hanno la precedenza. Input `silenzioso` e `--prova` come prima.

## Pallavolo (scripts/volley.py)
- Fonte: pagine settimanali dei portali FIPAV (PowerSPORT)
  `https://<host>/risultati-classifiche.aspx?[ComitatoId=<id>&]DataDa=<lunedì gg/mm/aaaa>&StatoGara=&CId=&SId=&PId=<pid>&btFiltro=CERCA`
  con host: pordenone.portalefipav.net (PId 7581), trieste.portalefipav.net (7285), udine.federvolley.it (15544),
  friulivg.portalefipav.net (ComitatoId 28, PId 7274). Ogni riga gara: numero, giornata (G), data e ora, squadre,
  risultato, parziali, impianto. Una pagina per comitato e settimana vale per tutti i gironi del comitato.
- Frequenza: esecuzioni normali (ogni ora sab-dom pomeriggio/sera, una sera nei feriali) settimana scorsa, corrente e
  prossima (3 pagine per comitato); ogni notte (cron `7 1 * * *`, opzione `--completo`) dalla settimana scorsa in avanti
  finché le pagine hanno gare: ci si ferma dopo 3 settimane vuote di fila, al massimo 30 settimane (circa 30 pagine per
  comitato, 1,5 s di pausa tra le pagine).
- Variazione: la gara si riconosce per numero gara; data, ora e impianto vengono sostituiti, la giornata resta.
  Stesse squadre ma numero diverso = altra gara (gironi a più turni).
- Limiti: lo spostamento oltre la settimana prossima si vede alla lettura notturna; le gare non ancora pubblicate dal
  comitato (ritorno, fasi successive) arrivano quando compaiono sul portale. "Tutte le date" (DataDa vuoto) non
  restituisce le gare: si legge per settimana.

## Basket (scripts/basket.py)
- Calendario completo: PDF "Calendario Definitivo" di ogni girone (archivio media WordPress del Comitato FIP FVG,
  `https://friuliveneziagiulia.fip.it/wp-json/wp/v2/media?search=Calendario&after=2026-08-15T00:00:00`), letto una volta
  (`config/basket_stato.json`, `calendari_letti`). Ora l'app riceve tutte le gare non giocate, non solo la giornata dopo.
- Calendari riemessi: ogni PDF "Calendario" nuovo dell'archivio (anche con un nome diverso) viene confrontato con i gironi:
  se almeno l'80% delle gare ha stesso numero e stesse squadre di un girone, aggiorna per numero gara data, ora e campo
  delle gare non giocate e diventa il nuovo `id_fonte`.
- Spostamenti: l'archivio del Comitato NON pubblica documenti di spostamenti/variazioni/recuperi/anticipi (ricerche
  "Spostament", "Variazion", "Recuper", "Anticip" senza risultati nella stagione 2026/27; nei post solo notizie). Il
  calendario aggiornato è sul portale risultati FIP:
  `https://fip.it/risultati/?group=campionati-regionali&regione_codice=RFR&comitato_codice=RFR&sesso=M&codice_campionato=D&codice_fase=1&codice_girone=85168&codice_ar=1&giornata=3`
  (una pagina per giornata: squadre, "14 Gennaio 2027 21:00", numero gara "000261", "Campo di gioco ..."; codice_ar=1
  andata, 0 ritorno). `config/basket_fip.json` abbina slug -> parametri del girone FIP: si compila da solo
  (`--scopri-fip`, o in automatico una volta alla settimana se mancano gironi) leggendo l'elenco dei campionati, i link
  delle giornate e confrontando i numeri gara con il calendario (almeno 3 gare con stesso numero e squadre).
- Frequenza: in ogni esecuzione le giornate con gare non giocate entro 14 giorni (e i recuperi); ogni notte (cron
  `53 1 * * *`, `--completo`) tutte le giornate future. 1,5 s tra le pagine FIP.
- Variazione: per numero gara (con controllo della squadra di casa) cambiano data, ora e campo; la data effettiva delle
  gare giocate resta quella "giocata il" delle omologazioni.
- Limiti: i gironi non trovati sul portale FIP (elencati nel log, "senza abbinamento") restano con il calendario PDF;
  il portale mostra un girone per campionato nel link predefinito: gli altri gironi si trovano solo se il loro codice
  compare nella pagina. La B Interregionale (Comitato Veneto) non è sul portale regionale FVG.

## Calcio (scripts/calcio.py + scripts/calcio_calendari.py)
- Calendari ufficiali in formato LND ("* ECCELLENZA GIRONE: A *", blocchi "ANDATA: 6/09/26 ! 1 G I O R N A T A !
  RITORNO: 10/01/27" e "ORE...: 15:30", righe "I CASA - OSPITE I", poi "ELENCO CAMPI DA GIOCO" con campo e indirizzo):
  - regionali: CU n.12 del CR `https://friuliveneziagiulia.lnd.it/wp-content/uploads/2026/08/CU-12-CALENDARI-UFFICIALI-20262027.pdf`
    (Eccellenza, Promozione, Prima A/B, U19, U18, U17, U16, U15 regionali);
  - delegazioni: `.../2026/09/CALENDARI-TRIESTE-2CAT-U17-U15-U14.pdf` e i PDF con "calendar" nel nome dentro gli ZIP
    degli allegati dei CU (`media?search=allegat&mime_type=application/zip`): dello ZIP si leggono solo l'indice e i
    file voluti (richieste HTTP Range), mai l'intero archivio se il server accetta Range.
  Un calendario più recente dello stesso girone (comitato, categoria, girone) sostituisce il vecchio.
- Abbinamento ai gironi: categoria e girone normalizzati con le stesse funzioni di calcio.py (canon_cat, classifica_cat),
  comitato dal titolo o dal nome del file; nomi delle squadre abbinati ai nomi del girone (chiave senza sigle, prefisso,
  parole in comune; solo abbinamenti unici). Se meno del 60% delle squadre è riconosciuto il calendario è scartato.
  Partite future = partite del calendario con coppia casa/ospite non ancora giocata e data da oggi; una partita che
  metterebbe una squadra due volte nella stessa giornata viene scartata.
- Variazioni: sezione "MODIFICHE AL PROGRAMMA GARE" di ogni Comunicato (Recupero Gare, Variazioni Gare, Altre
  Variazioni, Ripetizione Gara). Formato CR: "Girone N°Gior A/R Squadra1 Squadra2 Data Ora Campo"; formato Delegazioni:
  "GIRONE X" e poi "Data N°Gior A/R Squadra1 Squadra2 [Data Orig.] Ora Var. [Ora Orig.] [Impianto]". Le due squadre
  sono scritte senza separatore: si dividono con i nomi del girone. In più "IL SABATO DEL NOSTRO CALCIO" del CR (anticipi
  al sabato: "13 GIORNATA ANDATA SABATO 28.11.2026", "ECC JUVENTINA S.ANDREA – PRO GORIZIA 14:30"). Le variazioni si
  applicano in ordine di pubblicazione; una partita non in calendario e non giocata diventa un recupero.
- Frequenza: con le esecuzioni del calcio (feriali 2 volte, weekend 1). Ogni comunicato si legge una volta
  (`config/calcio_calendari.json`: calendari_letti, zip_letti, modifiche_lette); alla prima esecuzione si rileggono le
  variazioni dei comunicati degli ultimi 35 giorni. Variazioni tenute 60 giorni. Ritmo: 1,5 s tra i file, 1 s tra le
  richieste Range; al massimo 15 ZIP e 25 comunicati nuovi per esecuzione (il resto alla successiva). Se il sito risponde
  con qualcosa che non è un PDF/ZIP (pagina d'errore: succede se si chiede troppo in fretta) la lettura delle fonti si
  ferma per quella esecuzione e i file non letti restano da leggere.
- Limiti: formato del calendario della Delegazione di Udine ("27/09/2026 - 1^ Giornata ore 10.30 - 13/12/2026" a due
  colonne) non letto; Campionato Carnico (anno solare) e calcio a 5 solo se il calendario è in formato LND; "DATA DA
  DESTINARSI" non dà una data (la partita resta fuori finché non viene fissata); l'ora di una variazione con una sola ora
  è presa come ora nuova; i gironi esistono in app solo se hanno almeno un risultato letto.

## Sport "agente" (aggiornati a mano)
Calendari ufficiali da cui copiare date e campi (nessuno script):
- Rugby: portale FIR `https://www.federugby.it/` (Serie B/C, calendari per girone con data e campo).
- Pallamano: FIGH `https://www.figh.it/` (calendari Serie A2/B per girone).
- Hockey su pista: FISR `https://www.fisr.it/hockey-pista.html`.
- Baseball/softball: FIBS `https://www.fibs.it/` (doppi incontri nella stessa giornata: normale).
- Bocce: FIB `https://www.federbocce.it/`.
- Pallavolo nazionale: Lega Volley, Lega Volley Femminile, FIPAV Serie B; basket nazionale: LBA, LNP, fip.it/risultati
  (campionati nazionali, stesso formato del regionale).

## Prove
Ogni workflow `aggiorna-*.yml` ha l'input `opzioni`; con `--prova` lo script scrive solo `/tmp/risultati_prova.json`,
il passo "Partite spostate" stampa partite future prima/dopo per sport, partite spostate e controlli (squadra due volte
nella stessa giornata, partita futura con risultato), gli avvisi sono solo stampati, niente ics né commit.
Esempi: pallavolo `--prova --completo`, basket `--prova --completo`, calcio `--prova --diag`.
Sonda: `gh api -X POST repos/ghibli73/sport-fvg/actions/workflows/sonda-fonti.yml/dispatches -f ref=<branch> -f "inputs[prove]=..."`
con `media=<sito>|<parole>|<dopo AAAA-MM-GG>|<mime>`, `html=<url>|<regex>`, `pagina=<url>|<regex>`,
`cerca=<url PDF o ZIP>|<regex>[@<regex file>]` (niente spazi: usare `\s`).

## Registro
(una riga per intervento: data — cosa — esito)
- 2026-11-25 — Prima versione (1.11.0 beta), vedi la PR "Calendari completi e partite spostate".
