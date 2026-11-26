# Agente CAMPIONATI NAZIONALI — squadre del FVG nei campionati nazionali

Stato al 26/11/2026 (stagione 2026/27; baseball/softball stagione 2026 conclusa). Versione app 1.13.1 beta.
Ruolo: ogni squadra del FVG che gioca un campionato nazionale deve avere in app il suo girone con classifica, risultati
e calendario completo, aggiornati in automatico dove la fonte lo permette. I gironi nazionali hanno gid `<sport>-naz-<campionato>`.
- `"auto": "naz"` = aggiornato da `scripts/nazionali.py` (workflow "Aggiorna nazionali");
- `"auto": "agente"` = caricato a mano (procedura sotto; il controllo serale del coordinatore li aggiorna).
Lavoro precedente sugli altri sport (rugby, baseball, bocce, pallamano, hockey): `pipeline/agenti/sport-altri-nazionali.md`.

## Censimento 2026/27 (squadre FVG → id di data/data.json)

| Sport | Campionato | Squadre FVG (id) | Girone in app | Aggiornamento | Fonte |
|---|---|---|---|---|---|
| Calcio | Serie A | Udinese (030129-1) | calcio-naz-serie-a | automatico (naz) | Lega Serie A (ufficiale) |
| Calcio | Serie B | nessuna (verificato su legab.it/seriebkt/classifica) | — | — | Lega B |
| Calcio | Serie C | nessuna: la Triestina gioca in Serie D (vedi sotto) | — | — | lega-pro.com non leggibile da script (ogni indirizzo restituisce la home) |
| Calcio | Serie D girone C | Triestina (032006-1), Cjarlins Muzane (030018-1), Brian Lignano (030049-1), LME – Lavarian Mortean Esperia (030062-1) | calcio-naz-serie-d-girone-c | manuale (agente) | betexplorer (NON ufficiale, vedi Limiti) |
| Calcio a 5 | Serie A2 Élite girone A | Pordenone C5 (093033-3), Maccan Prata (093034-2) | non caricato | — | Divisione Calcio a 5 (dati da widget Tuttocampo) |
| Calcio a 5 | Serie B girone B | Eagles Futsal (030026-4), C5 Manzano BRN 1988 (030055-2) | non caricato | — | come sopra |
| Calcio femminile | A / B / C | non verificato | — | — | figc.it (serie B femminile: comunicati) |
| Basket | Serie A (LBA) | Pallacanestro Trieste (032006-21), APU Udine (030129-15) | basket-naz-serie-a | manuale (agente) | betexplorer + Tuttosport (lavoro precedente) |
| Basket | Serie A2 | UEB Cividale (030026-1) | basket-naz-serie-a2 | manuale (agente) | betexplorer (classifica calcolata) |
| Basket | Serie B Nazionale | nessuna squadra FVG trovata (legapallacanestro.com/serie/4/classifica) | — | — | LNP |
| Basket | Serie B Interregionale girone B | Dinamo Gorizia, Falconstar Monfalcone, Jadran, Sistema Basket Pordenone | basket-b-interregionale-girone-b | automatico (basket.py) | FIP |
| Basket | Serie A2 femminile girone A | "Trieste" (società da confermare, senza id) | basket-naz-a2-femminile-a | manuale (agente) | betexplorer |
| Pallavolo | SuperLega | Tinet Prata di Pordenone (093034-1) | pallavolo-naz-superlega | automatico (naz) | Lega Pallavolo Serie A (ufficiale) |
| Pallavolo | Serie A2 / A3 maschile | nessuna (verificato su legavolley.it, IdCampionato 1000, 1001, 1002) | — | — | Lega Volley |
| Pallavolo | Serie A1 femminile | CDA Talmassons (030114-1) | pallavolo-naz-a1-femminile | manuale (agente) | betexplorer (lavoro precedente) |
| Pallavolo | Serie B maschile girone A | Libertas Fiume Veneto (093021-9) | non caricato | — | FIPAV (nessuna fonte leggibile trovata) |
| Pallavolo | Serie B2 femminile girone A | Chions Fiume Volley (093013-2), Insieme per Pordenone (093033-27), Sangiorgina, Aquila Spilimberghese | non caricato | — | FIPAV |
| Pallavolo | Serie B1 femminile | Blu Team | non caricato | — | FIPAV |
| Pallamano, rugby, hockey inline, bocce, baseball/softball | vedi sport-altri-nazionali.md | | gironi agente esistenti | manuale | FIGH, FIR, FISR, FIB, FIBS |
| Pallanuoto | Serie B maschile girone 2 | U.S. Triestina Nuoto (032006-48) | non caricato | — | Federnuoto |
| Hockey ghiaccio / pista, football americano, tennistavolo, tennis a squadre | non censiti in questo giro | | | | |

## Fonti verificate e condizioni d'uso

### Lega Serie A — automatico (modulo `serie_a`)
- Pagina: https://www.legaseriea.it/serie-a/classifica (Next.js). I dati vengono dall'API pubblica della piattaforma dati del sito
  (`SDP_API_URL_WITH_VERSION` nella configurazione della pagina), senza chiavi né autenticazione:
  - classifica ufficiale: `https://api-sdp.legaseriea.it/v1/serie-a/football/seasons/<season_id>/standings` (60 kB);
  - tutte le partite della stagione: `.../seasons/<season_id>/matches` (1,2 MB, 380 partite: giornata `matchSet.name`, data e ora
    locali `matchDateLocal`, `status` FINISHED, `providerHomeScore`/`providerAwayScore`, stadio e città);
  - giornate: `.../seasons/<season_id>/matchdays`.
- `season_id` 2026/27: `serie-a::Football_Season::ed7fdc2a3e7b408b942ec177b7b956b5` (in `config/nazionali.json`). Per la stagione
  nuova: nella pagina classifica cercare `"isCurrent":true,"seasonId":"serie-a::Football_Season::...` (Sonda: `trova=` con
  `Football_Season`) oppure `"current_season"`.
- robots.txt (verificato 26/11/2026): `User-agent: * Allow: /`, nessun blocco per l'API. Si legge solo classifica e calendario,
  due richieste per esecuzione. I campi editoriali dell'API (registi, delegati, ecc.) non vengono mai salvati.

### Lega Pallavolo Serie A — automatico (modulo `superlega`)
- Classifica: https://www.legavolley.it/classifica/?IdCampionato=999 (tabella HTML: punti, giocate, vinte, perse, set vinti/persi).
- Calendario: https://www.legavolley.it/calendario/?IdCampionato=999 (una tabella per giornata: data e ora ufficiale, casa,
  risultato in set, ospite, arbitri, impianto). Si salvano giornata, data, ora, squadre, risultato e impianto; MAI gli arbitri.
  Partite senza data propria: data della giornata. Oggi la pagina pubblica solo l'andata (11 giornate): il ritorno arriva quando la
  Lega lo pubblica (le giornate di ritorno sono numerate 12-22).
- Altri campionati (stesso modulo, nuova voce in config con `id_campionato`): A2 = 1000, A3 girone Bianco = 1001, Blu = 1002.
- robots.txt (verificato): vietati solo /wp-admin/, /statistiche/, /rendimento/, /pillole/, /confronti/, /matchdaily.

### Serie D girone C — manuale (`scripts/nazionali_manuale.py`)
- Composizione del girone: LND, 6/8/2026 (riportata da TuttoMercatoWeb e Corriere dello Sport).
- Fonte ufficiale: Dipartimento Interregionale LND su lnd.it. Il robots.txt di lnd.it (verificato 26/11/2026) RISERVA il text and
  data mining (art. 70-quater L. 633/1941) e vieta gli agenti AI (ClaudeBot, Claude-User, ...): non viene letta né dalla Sonda né
  dagli script. Se l'utente ottiene il permesso della LND, si può scrivere un modulo sui comunicati del Dipartimento.
- Fonte usata (NON ufficiale, scritta nel campo "fonte"): https://www.betexplorer.com/football/italy/serie-d-group-c/results/ e
  /fixtures/ (robots.txt permette queste pagine). Classifica calcolata 3-1-0 (penalizzazioni non considerate: nota nel girone).
- Aggiornamento (lunedì-martedì, o nel controllo serale del coordinatore):
  1. Sonda: `testo2=Round@@https://www.betexplorer.com/football/italy/serie-d-group-c/results/` e la stessa con `/fixtures/`;
  2. copiare la riga di testo dei due log in `pipeline/nazionali/serie_d_c_risultati.txt` e `serie_d_c_calendario.txt`;
  3. `python scripts/nazionali_manuale.py serie_d_c pipeline/nazionali/serie_d_c_risultati.txt pipeline/nazionali/serie_d_c_calendario.txt`
     (controlla 18 squadre, una partita per squadra per giornata, nessuna partita futura con risultato; con `--prova` non scrive);
  4. `python scripts/risultati_tools.py check`, poi ics.py, widget_dati.py, commit.
  Gli orari del calendario sono tenuti solo fino a `ora_fino_a` (config): più avanti l'orario non è ancora fissato.

### Fonti provate e NON utilizzabili
- lega-pro.com: ogni indirizzo (anche robots.txt e /classifiche) restituisce la home; dati caricati con JavaScript.
- divisionecalcioa5.it: API SportsPress pubblica (`/wp-json/sportspress/v2/...`) ferma alla stagione 2024/25; dal 2025/26 risultati
  e classifiche sono widget di Tuttocampo (non ufficiale).
- legavolleyfemminile.it: robots.txt con `Content-Signal: ai-train=no` e blocco di ClaudeBot, Claude-Web, anthropic-ai: non letto.
- legapallacanestro.com (LNP): pagine Drupal, ma classifica e calendario arrivano con un modulo ajax (`lnp-classifica-form`); robots
  senza blocchi, Crawl-delay 10. Da approfondire con la Sonda (chiamata POST del form).
- legabasket.it: robots con Crawl-delay 2 e blocchi solo su statistiche giocatori; pagina standings senza API visibile. Da approfondire.

## Script e workflow
- `scripts/nazionali.py [--prova] [--solo serie_a,superlega]`: un modulo per fonte; scrive i gironi `auto: "naz"` in
  data/risultati.json (con `--prova` in /tmp/risultati_prova.json). Se un modulo fallisce o i controlli non passano (squadre in meno,
  squadra due volte nella stessa giornata, partita futura con risultato) il girone precedente resta. Rimette a ogni esecuzione gli id
  FVG dei gironi "agente" elencati in `config/nazionali.json` → `alias_gironi`.
- `config/nazionali.json`: per ogni modulo gid, stagione, id della fonte, alias nome → id (solo società FVG); `manuali` per i gironi agente.
- `.github/workflows/aggiorna-nazionali.yml`: cron `37 11-23/2 * * 5,6,0,1` (ogni 2 ore da venerdì a lunedì, i giorni di gara) e
  `37 22 * * 2-4` (una volta negli altri giorni; i turni infrasettimanali di Serie A e SuperLega si vedono la sera stessa);
  concurrency `aggiorna-dati`; passi: script → variazioni.py → risultati_tools.py check → avvisi.py → ics.py → widget_dati.py →
  commit con 4 tentativi di `pull --rebase` + push. Lancio manuale con input `opzioni` (`--prova`) e `silenzioso`; sulle PR che
  toccano lo script gira in prova. NB: un workflow nuovo si lancia a mano solo dopo il merge su main; prima si prova con la Sonda:
  `nazionali=--solo,serie_a` (esegue lo script in prova, variazioni e check, e stampa i gironi tra `@@INIZIO_NAZ@@` e `@@FINE_NAZ@@`).
- Sonda fonti, modi nuovi: `trova=<regex>@@<url>` (tutte le corrispondenze distinte), `json=<url>[@@<n>]` (risposta grezza, prime n
  battute: utile anche per scaricare un HTML intero e provarne il parser in locale), `nazionali=<opzioni>`.
  Nella regex niente spazi (usare `\s`), `,,` per `|`, `~` per `&` negli URL.

## App
- Scheda società (es. Udinese `#s-030129-1`): il riquadro "Risultati e classifica" in alto mostra posizione, ultima e prossima
  partita (con stadio) dal girone nazionale, perché la classifica ha l'id della società.
- Nastro dei risultati in home (1.13.1): dopo i preferiti vengono le partite dei gironi `-naz-` (sempre limitate alle ultime 72 ore).

## Limiti e cose da fare
- Calcio a 5 (A2 Élite e Serie B), pallavolo Serie B/B1/B2, pallanuoto Serie B, calcio femminile: gironi non caricati.
- Basket LBA, A2, A2 femminile e A1 femminile pallavolo restano manuali (fonti non ufficiali del lavoro precedente).
- SuperLega: ritorno non ancora pubblicato; Serie D: classifica calcolata, senza eventuali penalizzazioni.
- Serie C: assenza di squadre FVG non verificata sul sito della Lega Pro (illeggibile), dedotta dalla composizione della Serie D.

## Registro
- 2026-11-26 — Prima versione (branch dati/nazionali): Serie A e SuperLega automatiche, Serie D girone C manuale, nastro 1.13.1.
