# Formato dei risultati (data/risultati.json)

Copia nel repository del formato usato da tutti gli script e dagli agenti per sport (il documento del progetto
`claude/agenti/formato-risultati.md` va tenuto allineato a questo). `data/risultati.json` è un array di gironi.

## Girone
| campo | significato |
|---|---|
| `gid` | `<sport>-<slug>`, stabile (es. `pallavolo-serie-c-femminile`, `calcio-eccellenza-a`) |
| `sport`, `girone`, `categoria`, `genere`, `stagione`, `comitato` | descrizione del girone |
| `fonte`, `aggiornato` | URL della fonte ufficiale e data (AAAA-MM-GG) dell'ultimo aggiornamento |
| `giornata` | ultima giornata giocata |
| `calcolata` | `true` se la classifica è calcolata dai risultati (basket, calcio) |
| `classifica` | righe `pos`, `squadra`, `id`, `punti`, `g`, `v`, (`n`), `p`, poi `set_v`/`set_p` (pallavolo), `f`/`s` (basket), `gf`/`gs` (calcio) |
| `partite` | tutte le partite, giocate e future (vedi sotto) |
| `classifica_provvisoria`, `nota_parziale`, `nota`, `minibasket`, `auto` | come prima (tempo reale, gironi parziali, minibasket, gironi automatici) |
| `nota_penalita` | **dalla 1.19.0** (calcio): testo della nota sotto la classifica con le penalizzazioni |

Riga di classifica, **dalla 1.19.0**: `penalita` = punti di penalizzazione (calcio, `standings[].penalties` del Quadro gare
LND); i `punti` della riga sono già al netto della penalizzazione. Assente se 0.

## Partita
Campi di base: `giornata`, `gara` (numero gara, pallavolo e basket), `data` (AAAA-MM-GG), `ora` (HH:MM), `casa`, `ospite`,
`id_casa`, `id_ospite`, `risultato` (`"3-1"`, `""` se non giocata), `parziali` (pallavolo), `campo`, `comune_casa`/`comune_ospite`.
Segni già esistenti: `non_omologato` (basket, portale FIP), `provvisorio` (calcio, Quadro gare), `variata`/`data_prec`/`ora_prec`
(scripts/variazioni.py), `rinviata`, `stato`, `note`.

### Dati della gara (dalla 1.19.0)
Tutti facoltativi: un campo assente vuol dire "nessuna informazione", mai il contrario. Scritti solo dagli script,
nelle Actions esistenti, senza agenti.

| campo | sport | valore | fonte | quando |
|---|---|---|---|---|
| `stato_gara` | pallavolo | `"omologata"`, `"ufficioso"` (gare con risultato); `"rinviata"`, `"sospesa"` (gare senza risultato) | icona "statogara" delle pagine risultati FIPAV (tutti e 4 i comitati) | a ogni lettura della settimana (giro rapido, giornaliero, notturno; settimane da -2 a +1). `ufficioso` non riletto da 14 giorni viene tolto |
| `stato_letto` | pallavolo | AAAA-MM-GG | interno: ultima lettura di `stato_gara` | |
| `designata` | pallavolo, basket | `true` | pallavolo: tooltip dello stato ("Arbitro designato") o blocco "Designazioni" dei portali regionale, Udine e Trieste-Gorizia (Pordenone escluso: non le pubblica); basket: scheda "Info" delle pagine giornata di fip.it/risultati (1° arbitro presente o "Arbitri designati") | solo gare **senza risultato e con data da oggi a 7 giorni**; tolto quando la gara è giocata o passata |
| `data_cal` | basket, calcio | AAAA-MM-GG | basket: data del calendario quando l'omologazione dice "giocata il" un altro giorno (gare giocate); calcio: `change.originalDate` delle variazioni **ufficializzate** del Quadro gare | basket: lettura delle omologazioni (e una volta per girone dal PDF del calendario per le gare omologate prima della 1.19.0); calcio: `calcio_live.py --dettagli` e giro rapido |
| `campo_cal` | calcio | testo (nome del campo) | `change.originalField` quando diverso dal campo attuale (che va in `campo`) | come sopra |
| `esito` | calcio | etichetta fissa: `"rinviata"`, `"sospesa"`, `"non disputata"`, `"da ripetere"`, `"a tavolino"`, `"annullata"` | `outcome`/`publicNote`/`flags` del Quadro gare tradotti in etichette fisse (mai il testo libero). `"Da Giudice sportivo"` è l'esito di tutte le gare giocate prima del Comunicato e non viene salvato | come sopra |

Regole:
- **Mai un rinvio diventa un risultato**: con `esito` rinviata/sospesa/non disputata/da ripetere/annullata e senza risultato
  la partita riceve `rinviata: true` e resta `risultato: ""`. Se poi arriva un risultato (CU), `rinviata` sparisce.
- Calcio: con `data_cal` su una partita futura, `data`/`ora` diventano quelle ufficializzate dal Quadro gare.
- Calcio: i dati stanno in `config/calcio_dettagli.json` (`gironi` → `casa|ospite|giornata` → campi, `penalita`, `letture`)
  e vengono applicati da `calcio_live.applica_dettagli` dopo `calcio.py` (che ricostruisce i gironi) e nel giro rapido.
- Basket: `data_cal` e `designate` stanno in `config/basket/<slug>.json` (`data_cal`: numero gara → data; `designate`:
  numero gara → true; `data_cal_pdf`: PDF del calendario già usato per la ricostruzione).
- **Privacy**: di arbitri, osservatori e ufficiali di campo si legge solo la *presenza* di un testo. Nomi, comuni e sezioni
  non vengono mai salvati, stampati nei log, committati né mostrati. Niente segnale nel calcio (nessuna fonte pubblica)
  e nella pallavolo di Pordenone. Niente nomi di atleti.

### In app (index.html, dalla 1.19.0)
Nella riga informativa delle partite (vista Partite e girone), in piccolo: "✓ Arbitri designati" (testo verde, icona
nascosta ai lettori di schermo), "omologata" (grigio), "giocata il 20/11 · in calendario il 22/11", "anticipata/posticipata ·
in calendario il …", "campo cambiato · in calendario: …", l'esito (es. "a tavolino"). "ufficioso" accanto al risultato
come "da omologare"/"provvisorio". Le rinviate usano l'etichetta "Rinviata" già esistente. Con `data_cal` l'etichetta
"Spostata" di `variata` non viene ripetuta. In classifica `−n` accanto ai punti e la nota "Penalizzazioni". Legenda in Info
("Le etichette delle partite").
