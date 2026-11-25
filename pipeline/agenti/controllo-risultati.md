# Controllo qualità risultati — Zuìn / Sport in FVG

**Data:** 25/11/2026. Ho controllato `data/risultati.json` su `main` (7226a76), che contiene 162 gironi.

**Metodo**
- Ho confrontato i gironi del campione con le fonti ufficiali, usando WebFetch e il workflow "Sonda fonti" sul branch `controllo/risultati-calcio`.
- Alcune pagine non hanno ricevuto il permesso in tempo, quindi le ho lette con la sonda da GitHub Actions:
  - pordenone.portalefipav.net;
  - trieste.portalefipav.net;
  - i PDF di friuliveneziagiulia.fip.it.
- Ho fatto anche controlli automatici su tutti i 162 gironi (script /tmp/qc/check.py).

## 1. Gironi verificati (24)

### Pallavolo (6): tutti corretti
| Girone | Fonte | Esito |
|---|---|---|
| Serie C femminile FVG | friulivg CId 92843 | Classifica identica (14 squadre). Giornate 1-6 e prossima giornata coerenti. |
| U13 F UD girone D | udine CId 94330 + risultati 16/11 | Classifica identica. Il "doppione" di giornata 2 (Stella Volley Azzurra) è anche nel portale: la gara 13157 ha G=2. Non è un errore dello script. |
| U17 M PN-UD | udine CId 93940 | Classifica identica. |
| Prima Divisione M PN | pordenone CId 93936 (sonda) | Classifica identica. |
| Seconda Divisione F TS-GO girone A | trieste CId 93456 (sonda) | Classifica identica. |
| U15 F PN girone B | pordenone CId 93620 (sonda) | Classifica identica. |

### Basket (6): risultati corretti, 2 errori dello script
| Girone | Fonte | Esito |
|---|---|---|
| U17 Regionale GO/TS | CU 164 | 8 risultati su 8 uguali. **Errore:** la gara 2978 Don Bosco-Cervignanese "0-0" è in "RIPETIZIONE GARE" ma è contata come sconfitta per tutte e due le squadre (vinte 15, perse 17). |
| U13 PN girone B | CU 168 + calendario CU 104 | 6 risultati su 6 uguali. **Errore:** la gara 4629 Cordovado-Casarsa 96-26 è "giocata il 09/11/2026", ma l'app la mostra l'11/01/2027 (partita futura con risultato). |
| Serie C girone D | CU 152 | 7 su 7 uguali (giornata 8). |
| DR1 Est | CU 153 | 5 su 5 uguali. |
| U19 Gold A | CU 160 | 7 su 7 uguali. |
| U14 femminile B | CU 172 | 8 su 8 uguali. |

### Calcio (8 + Udine/Trieste in blocco): diversi errori sistematici
| Girone | Fonte | Esito |
|---|---|---|
| Eccellenza A | CU 50, CU 37-1 | Giornata 11 identica (9 gare). **Data sbagliata:** Casarsa-Tolmezzo è stata giocata il 18/10, nell'app è il 16/10. |
| Promozione A | CU 50 | Giornata 11 identica. |
| U17 / U16 / U15 regionali A | CU 53 | Giornata 12 identica. Il rinvio Cordovado-Reanese non è inserito, giustamente. **La classifica conta solo le giornate 6-12** (vedi errori). |
| Gorizia Terza Cat. D | go CU 24, 21 | **Mancano le giornate 7 (in parte) e 8.** L'app è ferma alla giornata 7. |
| Gorizia U15 prov. A | go CU 24 | 6 su 6. **Data sbagliata:** Cometazzurra-Corno è stata giocata il 14/11, nell'app è il 16/11. |
| Gorizia U14 prov. E | go CU 24 | 5 su 5. Le giornate 7 e 8 sono finite in gironi "fantasma". |
| Udine, tutti i gironi del CU 27 | CU 27 | 61 gare uguali. **Ne mancano 11:** U19 prov. A giornata 8 (6 gare) e U14 D giornata 7 (5 gare). |
| Calcio a 5 regionale A | CU 50 | 4 su 4. La serie (C1/C2) non è indicata nel titolo e resta "regionale". |

### Gironi "agente" (4)
| Girone | Fonte | Esito |
|---|---|---|
| Pallamano Serie B M Area 3 | federhandball | Corretto: 30 gare e giornata 7. |
| Rugby Serie C territoriale girone 1 | CRV comunicato GST n.4 | Corretto: risultati e classifica (punti, G, V, N, P, PF, PS). |
| Hockey inline Serie A | articolo FISR 6ª giornata | Punti e risultati della giornata 6 corretti. **Manca la gara della giornata 4** tra Asiago Vipers ed Edera Trieste (in classifica hanno 5 e 6 partite). Le gare della giornata 4 non hanno la data. |
| Bocce volo Serie B girone 5 Est | federbocce | Punti, fatti e subiti corretti. **ASD Tre Stelle Ronchi (GO) manca in classifica**: ha riposato alla giornata 1 ma è nel calendario. Le gare della giornata 1 non hanno la data (21-22/11). Le colonne G/V/P dell'app contano gli incontri, non le partite come la fonte: è una scelta, non un errore. |

**Totale:** 24 gironi verificati.
- 15 corretti: 6 di pallavolo, 4 di basket, Promozione A, U17/U16/U15 regionali per i risultati, pallamano, rugby.
- 9 con errori: 2 di basket, 5 di calcio, hockey, bocce.

## 2. Controlli automatici su tutti i gironi
- **Squadra due volte nella stessa giornata:**
  - pallavolo U13 F UD girone D e U12 F UD girone C: come sul portale (gare aggiunte dopo);
  - baseball A Silver, A2 softball e B (agente): la "giornata" è usata per serie di più partite.
- **Partite future con risultato:** solo basket U13 PN B, gara 4629. Corretta dalla PR #9.
- **Somma delle vinte diversa dalla somma delle perse:** solo basket U17 regionale GO/TS. Corretta dalla PR #9.
- **Date:** tutte nella stagione. Gare senza data:
  - basket B Interregionale (25) e U15 regionale GO-TS/PN/UD;
  - A2 (agente);
  - hockey;
  - bocce.
- **Giornata diversa dalla più alta giocata:**
  - basket: per anticipi e recuperi (lo script usa "metà delle gare giocate"), va bene così;
  - SuperLega (agente): giornata 6 con gare fino alla 11;
  - pallamano U16 M girone C (agente): giornata 6 ma solo la giornata 1 giocata. **Da controllare.**
- **Calcio "lnd", numero di squadre:**
  - sono plausibili, da 10 a 20;
  - restano fuori i gironi già scartati (Gorizia U19 A 30 squadre, U16 A 24);
  - sono **fantasmi** `calcio-gor-under-19-provinciali-e`, `-under-15-provinciali-e` e `-under-16-provinciali-e`: contengono gare dei Giovanissimi U14 girone E (a Gorizia il girone E esiste solo per l'U14).

## 3. Errori trovati (cause)

### Calcio (`scripts/calcio.py`)
1. **Blocchi di gare persi.** La categoria era cercata solo nelle 3 righe prima di "RISULTATI UFFICIALI GARE DEL". Un secondo blocco di data della stessa categoria (recupero + giornata, oppure girone C seguito dal girone D) veniva scartato.
   - Causa: partita mancante.
   - Esempi: Gorizia Terza D giornate 7-8; Gorizia U16 A giornata 8; Udine U19 A giornata 8; Udine U14 D giornata 7.
2. **Data "DEL L'1/11/2026" / "DELL'1/11/2026" non riconosciuta.** Le gare restavano nella categoria e nel girone del blocco precedente.
   - Causa: gara assegnata al girone sbagliato.
   - Risultato: Gorizia U19 A fuso con U16 e U15 (30 squadre), più tre gironi fantasma "E".
3. **Note "(1) - disputata il …" globali per tutto il CU.** Valeva l'ultima nota del CU.
   - Causa: data sbagliata.
   - Esempi: Casarsa-Tolmezzo, Tagliamento-Basiliano, Cometazzurra-Corno.
4. **`unifica_nomi` modificava `calcio_stato.json`.** Un'unificazione sbagliata restava per sempre.
   - Causa: nome squadra unito male.
   - Esempio: "CAMPANELLE - CAMPANELLE sq.B 12-5" diventato "CAMPANELLE sq.B - CAMPANELLE sq.B" (Trieste U17).
5. **Classifiche incomplete in tutti i 25 gironi "lnd".** L'archivio WordPress parte da ottobre. Per esempio U17 regionali: giornata 12, ma le squadre hanno da 5 a 7 partite; Gorizia U14 E da 1 a 3.
   - L'app scrive "Classifica calcolata dai risultati ufficiali: a pari punti possibili differenze…", che è fuorviante.
   - Causa: classifica calcolata diversa dall'ufficiale.
6. **Altri problemi minori:**
   - gare U17-U19 di calcio a 5 finite in "Under 19 regionali B" per l'impaginazione a due colonne del CU 37-1 (girone scartato);
   - `classifica_cat` non riconosce "C5" (lo fa solo `calcio5()`);
   - la riga "… 4 - 0 Y" non viene letta;
   - nomi troncati: "TRIESTE VICTORY ACADESQ.B", "ATLAS FOOTBALL ACCADEMY S".
7. **Copertura:** nell'archivio non ci sono CU della Delegazione di Pordenone. Gli "Comunicato-Ufficiale-nr-…" sono di Tolmezzo e senza risultati in questo periodo. Nell'app non c'è nessun girone provinciale di Pordenone.

### Basket (`scripts/basket.py`)
1. La data "giocata il" delle omologazioni veniva ignorata. La prova `--tutto --prova` trova **21 gare** con data diversa dal calendario, tra cui la 4629 (Cordovado-Casarsa: 11/01/2027 → 09/11/2026).
2. Le righe "0 - 0" (RIPETIZIONE GARE) venivano contate come risultato. Causa: sconfitte doppie in classifica, e il risultato vero sarebbe stato rifiutato.
3. **Possibile divergenza:** la classifica calcolata ordina per vinte, poi differenza canestri, poi punti fatti. La FIP usa gli scontri diretti. Non l'ho potuto verificare: la FIP non pubblica la classifica nel PDF.

### Pallavolo (`scripts/volley.py`)
Nessun errore nel campione.

### Gironi "agente"
- Hockey: manca Asiago-Edera della giornata 4.
- Bocce: manca Tre Stelle Ronchi in classifica e mancano le date della giornata 1.
- Pallamano U16 M girone C: giornata 6 con una sola giornata giocata.

## 4. Correzioni proposte (PR aperte, nessun merge)
- **PR #8** `controllo/risultati-calcio` → https://github.com/ghibli73/sport-fvg/pull/8
  - Correggono gli errori 1-4:
    - `RX_DATA` con la forma "L'" e il giorno a una cifra;
    - categoria che continua solo se subito prima c'erano gare;
    - girone azzerato a ogni blocco di data;
    - note valide per il loro blocco;
    - unificazione dei nomi su copie;
    - chiave della gara senza sigla societaria.
  - `calcio_stato.json` ripulito dai gironi fusi o fantasma, con l'elenco dei CU letti azzerato (rilettura dei 72 CU).
  - Sonda fonti: modalità `righe=` e `testo=`.
  - **Prova** (run 45601953522, `--prova --diag`): 31 gironi.
    - Gor Terza D: giornata 8, 38 gare.
    - Gor U19 A: 12 squadre; Gor U16 A: 13 squadre.
    - Udi U14 D: giornata 7.
    - Udi U19 A: giornata 8.
    - Udi U17 A/B: 34 e 29 gare.
    - Tri U17 A di nuovo presente.
  - **Resta da fare:**
    - `gor-under-15-provinciali-e` è ancora un fantasma (11 gare U14 E da un CU di Gorizia, da controllare con `righe=` su go_cu_22/23);
    - nome "ATLAS FOOTBALL ACCADEMY S".
- **PR #9** `controllo/risultati-basket` → https://github.com/ghibli73/sport-fvg/pull/9
  - Legge "giocata il" e ignora i punteggi pari.
  - **Prova** (run 45601775013, `--tutto --prova`): 730 risultati uguali, 0 diversi, 21 date corrette.
  - Dopo il merge serve un `--tutto` reale.

**Da fare a mano (agenti):**
- hockey: aggiungere Asiago-Edera della giornata 4;
- bocce: aggiungere Tre Stelle Ronchi in classifica e le date della giornata 1;
- pallamano U16 M girone C: ricontrollare;
- SuperLega: controllare la giornata.

## 5. Consigli per il controllo quotidiano
1. Dopo ogni workflow eseguire i controlli automatici di /tmp/qc/check.py; conviene portarli in `risultati_tools.py check`:
   - squadra due volte nella stessa giornata;
   - partita futura con risultato;
   - somma vinte = somma perse;
   - pareggi pari;
   - g = v + n + p;
   - gol fatti = gol subiti;
   - squadre delle partite presenti in classifica.
   Far fallire il workflow per "futura con risultato" e "vinte ≠ perse".
2. Calcio:
   - controllare nel log le righe "scartato" (un girone scartato vuol dire gare finite nel girone sbagliato);
   - controllare i gironi con molte più squadre del solito;
   - controllare i gironi in cui la giornata cresce ma il numero di gare no (blocchi persi).
3. Per ogni nuovo formato di CU, provare il parser con `Sonda fonti` e `righe=<url>` prima di fidarsi.
4. Calcio "lnd": segnare la classifica come **parziale** ("dalla giornata N") finché mancano le prime giornate, oppure prendere la classifica ufficiale. Il testo attuale dell'app la presenta come completa.
5. Cercare dove pubblica la Delegazione di Pordenone: nell'archivio non ci sono suoi CU.
6. Basket: dopo il merge della PR #9, lanciare una volta "Aggiorna basket" con `--tutto`. Poi tenere d'occhio nel log le righe "giocata il".
7. Gironi "agente": controllare che le squadre a riposo siano in classifica e che ogni gara abbia la data.
