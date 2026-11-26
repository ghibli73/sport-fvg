# Agente TEMPO REALE — dal risultato ufficiale al telefono nel minor tempo possibile

Ruolo: ridurre il tempo tra la pubblicazione di un risultato su una fonte ufficiale e la sua comparsa nell'app, senza
sovraccaricare i portali delle federazioni e senza fonti non ufficiali. Dalla 1.13.1 beta.

## In breve
| Sport | Fonte veloce (ufficiale) | Ogni | Cosa compare | Poi confermato da |
|---|---|---|---|---|
| Pallavolo | pagine settimanali dei risultati dei 4 portali FIPAV (regionale, Udine, Pordenone, Trieste-Gorizia) | 15 min nelle fasce | risultato e parziali; classifica ufficiale o, se il portale non l'ha ancora aggiornata, "provvisoria" | classifica del portale (`classifica.aspx?CId=`) |
| Basket | portale `fip.it/risultati` (pagine per giornata, punteggio del referto elettronico) | 15 min nelle fasce | punteggio con etichetta **"da omologare"**, classifica "provvisoria" | PDF "Omologazione gare" del Giudice sportivo (vale l'omologazione se diversa) |
| Calcio | **Quadro gare LND** `https://gare.lnd.it` (servizio pubblico della LND, lo stesso del sito LND FVG "Risultati e classifiche") | 15 min nelle fasce | gol con etichetta **"provvisorio"**, classifica "provvisoria" | risultati del Comunicato Ufficiale (CR il martedì-giovedì, Delegazioni mercoledì-giovedì) |

Fasce di gara (ora italiana): **sabato 15:00–23:30, domenica 15:00–21:30, lunedì–venerdì 20:00–23:30**.
I cron sono in UTC e coprono ora solare e legale (`giro-rapido.yml`: sab `13-22`, dom `13-20`, lun-ven `18-22` UTC ai minuti
4, 19, 34, 49); il primo passo controlla l'ora di Roma e fuori fascia chiude in pochi secondi senza leggere nessun portale
(tolleranza 15 minuti dopo la fine della fascia).

## Misure (26/11/2026)
### Prima (esecuzioni del 24–26/11)
- **Cron di GitHub**: dei cron previsti dopo l'ultimo cambio dei workflow, metà non è partita e quelli partiti avevano
  ritardi enormi: pallavolo `37 20 * * 1-5` (21:37 italiane) partito alle 03:02 UTC (**+6 h 25**); calcio `23 18`
  partito alle 22:36 (**+4 h 13**); basket `41 17` partito alle 23:16 (**+5 h 35**); pallavolo notturno `7 1` e basket
  notturno `53 1` alle 07:45 UTC non erano ancora partiti (**> 6 h**). Calcio `23 13` e basket `41 14` del 25/11: saltati.
  È il comportamento noto di GitHub per i repository nuovi o poco attivi: i cron sono "best effort".
- **Durata dei workflow** (passi): pip 4 s, checkout 3 s, variazioni/controlli/ics/widget 1–2 s ciascuno, commit 2–3 s.
  Il tempo è tutto nella lettura delle fonti: pallavolo 2 min 12 s (12 pagine settimanali + 60 classifiche, 1,5 s di
  pausa); pallavolo `--completo` circa 5 min; calcio 4–7 min (comunicati PDF); basket 4 min normale, **17 min 34 s** quando
  parte la scoperta settimanale dei gironi FIP (oltre 600 pagine).
- **Annullamenti**: un unico gruppo `aggiorna-dati` per tutti i workflow: GitHub tiene una sola esecuzione in coda per
  gruppo, le altre vengono annullate (basket annullato 2 volte il 25/11 alle 18:22 e alle 20:29, dietro a pallavolo e calcio).
- **GitHub Pages**: "pages build and deployment" parte nello stesso secondo del commit e dura **40–50 s**
  (es. commit 03:04:40, pubblicato 03:05:28; `Last-Modified` di `data/risultati.json` = ora della pubblicazione).
- **Cache HTTP su Pages**: `Cache-Control: max-age=600` (10 minuti) per `data/*.json` e `index.html`, CDN Fastly
  (`X-Cache: HIT` alla seconda richiesta), `ETag` debole, `Access-Control-Allow-Origin: *`. `data/risultati.json` pesa
  **2,4 MB**.
- **Dal risultato all'app (weekend 20–22/11)**:
  - pallavolo: risultati sui portali la sera stessa della gara; in app al giro successivo (allora ogni ora nel weekend,
    una volta la sera nei feriali) più i ritardi dei cron: da **1 ora a oltre 6 ore**;
  - basket: gare del 20–22/11 omologate nei PDF del 25/11 alle 14:11–14:15 (**4–5 giorni**), in app alle 14:56 solo
    grazie a un lancio manuale (il cron delle 14:41 era saltato, quello delle 17:41 è partito alle 23:16);
  - calcio: gare del 21–22/11 nei CU del 24/11 16:25 (CR CU-53), 24/11 12:02 (Trieste) e 25/11 16:18 (CR CU-54),
    in app il 25/11 alle 22:40 UTC: **3 giorni e 7 ore** dalla fine della gara (di cui 6 h 20 di attesa del cron).

### Dopo (stima, con le prove del 26/11 sul branch `funzioni/tempo-reale`)
- Giro rapido: durata della lettura vedi "Prove" più sotto; con checkout, pip in cache e commit circa 1–2 minuti.
- Ritardo atteso dalla pubblicazione sulla fonte al telefono = attesa del giro (in media 7–8 min, al massimo 15) +
  durata del giro (1–2 min) + Pages (1 min) + controllo dell'app (in media 1,5 min, al massimo 3; la CDN non pesa perché
  `data/stato.json` si chiede con `?t=<minuto>` e `data/risultati.json` con `?v=<impronta>`, due indirizzi nuovi a ogni
  cambio): **in media 10–12 minuti, al massimo circa 20**, se i cron partono in orario.
  - pallavolo: ~10–20 min dal risultato sul portale (prima: 1–6 h);
  - basket: ~10–20 min dal punteggio sul portale FIP, cioè la sera stessa invece di 4–5 giorni (con "da omologare");
  - calcio: ~10–20 min da quando il Quadro gare LND mostra il risultato. Al 26/11 il Quadro gare aveva già la 12ª
    giornata (21–22/11) giocata e in classifica; quanto presto la sera della gara compaiano i gol va verificato sabato
    28/11 (vedi "Da verificare"). Senza il Quadro gare: 3 giorni.
- **Limite vero: i cron di GitHub.** Con ritardi di ore come quelli misurati il giro rapido serve a poco: per questo c'è
  l'avvio esterno (sotto). Con un servizio esterno che avvia il giro ogni 15 minuti il ritardo resta quello stimato.

## Come funziona
### Giro rapido (`.github/workflows/giro-rapido.yml`)
1. fascia di gara? (solo Python del runner, nessun checkout) — se no, fine;
2. `python scripts/volley.py --rapido`: solo le pagine `risultati-classifiche.aspx?...&DataDa=<lunedì>` dei 4 portali,
   settimana corrente (lunedì e martedì anche la precedente): al massimo 8 pagine. La classifica (`classifica.aspx?CId=`)
   si rilegge **solo nei gironi con risultati nuovi**. Se la classifica letta conta meno gare di quelle con risultato
   (il portale la aggiorna dopo), le gare mancanti vengono sommate (3-0 e 3-1: 3 punti; 3-2: 2 e 1; set) e il girone ha
   `classifica_provvisoria: true` (e `classifica_ufficiale` con l'ultima ufficiale). Le somme si fanno solo se i conti
   tornano squadra per squadra (partite giocate = G della classifica + gare sommate), altrimenti resta l'ufficiale;
3. `python scripts/basket.py --rapido`: per i gironi abbinati in `config/basket_fip.json` legge le pagine giornata di
   `fip.it/risultati` delle gare **finite** (inizio + 105 minuti) negli ultimi 3 giorni e non ancora omologate. Il
   punteggio è nel testo "CASA 80 OSPITE 71 20 Novembre 2026 21:15 000225 … Squadra di casa CASA Squadra ospite OSPITE"
   (`fip_punteggi`); il portale scrive anche "Gara omologata" (salvato come `omologata_portale`, solo informativo);
4. `python scripts/calcio_live.py`: per i gironi abbinati in `config/calcio_lnd.json` legge la pagina del Quadro gare
   della giornata (`?cr=07&campionato=<cod>&girone=<cod>&giornata=<n>&leg=first|second`) se ci sono partite finite
   (inizio + 115 minuti) negli ultimi 3 giorni senza risultato del Comunicato. Dati della pagina (Inertia `data-page`):
   `homeGoals`, `awayGoals`, `isPlayed`, `isLive` (le gare in corso si saltano), `resultState` e `outcome`
   (es. 4 / "Da Giudice sportivo" quando il Giudice le ha già omologate). Al massimo 60 pagine per giro;
5. variazioni, `risultati_tools.py check`, avvisi ntfy (anche per i provvisori: l'avviso dice il risultato appena
   pubblicato), `.ics` e widget **solo se** `data/risultati.json` è cambiato, `data/stato.json`, salvataggio.

### Provvisori (`config/live.json`, `scripts/tempo_reale.py`)
- Basket e calcio: `{"gironi": {"<gid>": {"<chiave partita>": {"r": "80-71", "data": ..., "letto": ..., "fonte": ...}}}}`;
  chiave = `gara:<numero>` (basket) o `<casa>|<ospite>|<giornata>` normalizzati (calcio).
- `tempo_reale.applica()` mette il risultato solo nelle partite **senza risultato ufficiale**, con il segno
  `non_omologato: true` (basket) o `provvisorio: true` (calcio), e somma la partita alla classifica (basket 2 punti a
  vittoria, calcio 3-1-0) segnando `classifica_provvisoria: true`. È idempotente e corregge la classifica se il punteggio
  provvisorio cambia.
- `basket.py` e `calcio.py` (esecuzioni normali) ricostruiscono i gironi dalle fonti ufficiali e poi riapplicano i
  provvisori ancora senza conferma: quando arriva l'omologazione o il Comunicato il segno sparisce da solo.
- Il giro rapido (unico a scrivere `config/live.json`) toglie i provvisori confermati e stampa le differenze
  ("provvisorio 80-71, ufficiale 80-73 (vale l'ufficiale)"); dopo 21 giorni senza conferma un provvisorio viene tolto.
- `calcio.py` non usa mai i provvisori come base dei risultati del Comunicato.
- In app: etichetta "da omologare" / "provvisorio" accanto al risultato (nastro della home, giornate del girone) e nota
  "provvisoria" sopra la classifica.

### Salvataggio senza annullamenti (`scripts/salva_dati.sh`, `scripts/unisci_gironi.py`)
- Ogni workflow ha il suo gruppo di concorrenza (`aggiorna-pallavolo`, `aggiorna-basket`, `aggiorna-calcio`,
  `giro-rapido`, `aggiorna-agenda`): non si annullano più a vicenda. Dentro lo stesso gruppo GitHub tiene comunque una
  sola esecuzione in coda (una più nuova sostituisce quella in attesa: per lo stesso workflow va bene).
- Nessun commit se non è cambiato nulla. Push con 5 tentativi: `git rebase origin/main`; se c'è conflitto (sempre, se due
  workflow hanno cambiato `data/risultati.json`, che è una riga sola) si riparte da `origin/main` e si uniscono i gironi a
  tre vie: i gironi cambiati da questo workflow prendono la sua versione, tutti gli altri restano quelli di main; poi si
  rigenerano `.ics`, widget e `data/stato.json`.
- `pip` in cache (`actions/setup-python` con `cache: pip`).

### App (index.html 1.13.1 beta, sw.js `sportfvg-shell-v20`)
- All'avvio legge `data/stato.json` (`versione` = impronta di `data/risultati.json`, `aggiornato` = ora del salvataggio).
- Con l'app aperta e visibile: controllo ogni **3 minuti nelle fasce** di gara e ogni **15 minuti fuori**; subito quando
  l'app torna in primo piano dopo più di 2 minuti. Chiede `data/stato.json?t=<minuto>` (pochi byte) e scarica
  `data/risultati.json?v=<impronta>` solo se l'impronta è cambiata (senza `stato.json` confronta i risultati scaricati).
- Ridisegna la vista corrente (anche il nastro dei risultati della home) tenendo la posizione di scorrimento e il fuoco;
  se è aperta una scheda società o si sta scrivendo in un campo, aspetta.
- "Aggiornato alle HH:MM" in piccolo nella pagina Risultati e nell'intestazione del nastro (solo l'ora, testo completo per
  i lettori di schermo).
- `sw.js`: i file di `data/` restano "prima la rete"; la copia offline è salvata senza parametri (una sola copia di
  `risultati.json` e `stato.json`, non una per versione).

## Avvio esterno (se i cron di GitHub restano inaffidabili) — PREPARATO, NON ATTIVO
`giro-rapido.yml` ha `workflow_dispatch`: un servizio esterno può avviarlo ogni 15 minuti. Fuori fascia il giro si chiude
da solo, quindi il servizio può chiamare anche sempre (meglio solo nelle fasce, per non consumare richieste).
Cosa deve fare l'utente (una volta):
1. GitHub → Settings (del profilo) → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate
   new token: nome "Zuìn giro rapido", scadenza 1 anno, **Repository access: Only select repositories → sport-fvg**,
   **Permissions → Repository permissions → Actions: Read and write** (nient'altro; "Metadata: Read" si aggiunge da
   solo). Copiare il token (inizia con `github_pat_`).
2. https://cron-job.org (gratuito) → Create cronjob:
   - URL: `https://api.github.com/repos/ghibli73/sport-fvg/actions/workflows/giro-rapido.yml/dispatches`
   - Schedule: ogni 15 minuti; fuso orario Europe/Rome; (facoltativo) solo nelle fasce: sab 15–23, dom 15–21, lun–ven 20–23;
   - Advanced → Request method **POST**; Headers: `Accept: application/vnd.github+json`,
     `Authorization: Bearer <token>`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`;
     Request body: `{"ref":"main"}`;
   - risposta attesa: HTTP 204.
3. A quel punto si possono togliere (o lasciare: il gruppo di concorrenza evita doppioni) i `schedule` di
   `giro-rapido.yml`. Il token non dà accesso al codice: può solo avviare e leggere le esecuzioni dei workflow.
Rinnovare il token alla scadenza (GitHub manda un'email una settimana prima).

## Fonti per sport (dettagli)
- **Pallavolo**: come `pipeline/agenti/pallavolo.md`/`calendari.md`. Nessuna fonte più veloce del portale: i risultati
  compaiono a fine gara (a volte "ufficioso" la domenica sera). Classifica del portale aggiornata dopo i risultati:
  nel frattempo "provvisoria".
- **Basket**: `fip.it/risultati` (portale nazionale FIP, gironi regionali con `regione_codice=RFR`). Ogni pagina di
  giornata ha punteggio, data/ora, numero gara, campo e, se c'è, "Gara omologata". Il sito usa anche
  `https://backend.fip.it/api/v1/` (`risultati`, `classifica`, `info-nazionali`: `punti_casa`/`punti_casa_uff`), non
  usato qui. **Gironi non sul portale**: la scoperta legge solo il primo girone di ogni campionato dal link predefinito;
  dalla 1.13.1 prova anche i codici girone vicini (±3: DR1 Est 85168, DR1 Ovest 85169). Restano fuori la B
  Interregionale (Comitato Veneto, solo omologazioni del Veneto) e i gironi senza calendario sul portale: per questi non
  è stata trovata un'altra fonte ufficiale dello stesso giorno (il Comitato FVG pubblica solo i PDF delle omologazioni).
- **Calcio**: Quadro gare LND `https://gare.lnd.it/?cr=07` (Comitato FVG: campionati regionali e di tutte le
  Delegazioni, con codici `campionato` e `girone`; es. Eccellenza `EC`/`A`, Promozione `PR`, Prima categoria `1C` A/B,
  Seconda Pordenone `23`, Terza Gorizia `32`, giovanili). Classifica pubblica anche in
  `https://gare.lnd.it/api/quadro-gare/girone/07/<campionato>/<girone>/classifica` (non usata: l'app calcola la sua).
  NON usato: il widget della pagina "Risultati e classifiche" del sito LND FVG chiama
  `gare.lnd.it/api/as400/calendario/...` con una chiave API legata al dominio del sito LND (errori "Domain not allowed"):
  non è una chiave nostra e non va usata. Se servisse un accesso diretto, chiederlo alla LND FVG.
  Verificato che NON danno risultati prima del Comunicato: news del sito LND FVG (nessun post di risultati),
  CU del lunedì (quasi solo recuperi), archivio media (solo PDF dei CU).

## Limiti
- Cron di GitHub: ritardi di ore e salti (misurati sopra). Rimedio: avvio esterno.
- Cache di Pages: `max-age=600`; l'app la evita con indirizzi nuovi (`?t=`, `?v=`), un browser senza l'app aggiornata
  (versione < 1.13.1) può vedere dati vecchi fino a 10 minuti.
- Pubblicazione di Pages: circa 45 s dopo ogni commit; molti commit ravvicinati si accodano (si annullano le
  pubblicazioni intermedie, quella finale arriva sempre).
- Pallavolo: la classifica provvisoria si calcola solo se i conti tornano squadra per squadra; altrimenti resta quella
  ufficiale fino all'aggiornamento del portale. Penalizzazioni e gare a tavolino arrivano solo con la classifica ufficiale.
- Basket: il punteggio del portale può essere corretto dall'omologazione (vale l'omologazione); gare sospese o con
  provvedimenti restano "da omologare" fino al PDF. Sconfitte a tavolino e penalizzazioni solo dalle omologazioni.
- Calcio: i gol del Quadro gare possono essere corretti dal Giudice sportivo (vale il Comunicato); i gironi dell'app
  senza abbinamento nel Quadro gare (meno del 60% di squadre uguali) restano con i soli Comunicati.
- Rispetto dei portali: pausa di almeno 1,5 s tra le pagine, ogni pagina al massimo una volta ogni 15 minuti; fuori dalle
  fasce nessuna lettura del giro rapido; la pallavolo non ha più i giri orari del weekend (li fa il giro rapido) ma una
  lettura completa al giorno (`17 11 * * *` UTC) e la notturna.

## Da verificare
- Sabato 28/11: a che ora il Quadro gare LND mostra i gol (guardare `letto` in `config/live.json` rispetto all'ora di
  fine gara) e il significato dei valori di `resultState` diversi da 0 (da giocare) e 4 ("Da Giudice sportivo").
- I primi cron del giro rapido dopo l'unione: ritardo tra il minuto previsto e `run_started_at`
  (`gh api repos/ghibli73/sport-fvg/actions/workflows/giro-rapido.yml/runs`). Se supera spesso i 15 minuti, attivare
  l'avvio esterno.

## Prove
- Giro rapido da un branch (il `workflow_dispatch` funziona solo per i workflow già su main): Sonda fonti con
  `giro=pallavolo,basket,calcio` (aggiungere `scopri` per rifare l'abbinamento dei gironi del calcio). Esegue gli stessi
  script sulla copia del runner, poi variazioni, `risultati_tools.py check`, avvisi in prova e stampa `stato.json`,
  `config/live.json` e `config/calcio_lnd.json`. Nessun commit.
- Dopo l'unione: `gh api -X POST .../workflows/giro-rapido.yml/dispatches -f ref=main -f "inputs[opzioni]=--prova"`.
- Sonda: nuove modalità `testa=<url>` (intestazioni HTTP: cache di Pages), `giri=<url>|<n>|<secondi>` (letture
  ripetute), `inertia=<url>[|<regex>]` (dati delle pagine del Quadro gare), `html=<url>|<regex>@@<caratteri>`.

## Registro
(una riga per intervento: data — cosa — esito)
- 2026-11-26 — Prima versione (1.13.1 beta), PR "Tempo reale": misure, giro rapido, provvisori basket/calcio, ricarica in app.
