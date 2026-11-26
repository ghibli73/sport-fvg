# Barra dei campionati — Zuìn 1.16.0 beta (prototipo)

In "Partite e classifiche" (`#risultati`), dopo lo sport, la seconda riga non è più il comitato ma una **barra scorrevole dei campionati**, in ordine di importanza (dal più alto al più giovane). Tutto calcolato nel browser da `data/risultati.json`: nessun campo nuovo, nessuno script toccato.

## Tabella e regole (index.html, blocco `CAMP-INIZIO … CAMP-FINE`)
- `CAMP[sport]` = elenco ordinato delle voci `{k, l, t, r, u, p}` (chiave URL, etichetta del chip, nome per esteso, regex sul nome del girone, età Under, voce trasversale).
- `campDi(g)`: 1) voci `p` (calcio femminile, calcio a 5); 2) età da categoria "Under NN" o dal nome (Esordienti = 12, Juniores = 19, Allievi = 17, Giovanissimi = 15, "B" = un anno meno); 3) prima regex della tabella; 4) ripiego generico "Serie X" / "Under NN" inserito accanto alle voci vicine; 5) "Altro".
- Ordine: basket Serie A · A2 · B · C · DR1 · DR2 · DR3 · U19 · U17 · U15 · U14 · U13 · Esordienti; calcio Serie A–D · Eccellenza · Promozione · Prima/Seconda/Terza Cat. · Juniores · U18 · Allievi U17 · U16 · U15 · U14 · Esordienti · Femminile · Calcio a 5; pallavolo SuperLega/A1 · A2 · A3 · B · B1 · B2 · C · D · 1ª/2ª/3ª Divisione · U19 … U12; baseball/softball, bocce, pallamano, rugby, hockey, calcio a 5: serie nazionali → regionali → giovanili. Nella barra compaiono solo i campionati con gironi.
- Zone (`campZone`): UD, PN, GOTS, REG (regionale FVG), NAZ (nazionale/interregionale) dal nome del girone e dal comitato; un girone a cavallo ("PN/UD") sta in tutte le sue province.
- **Controllo**: `node tests/campionati.test.js` stampa il rapporto per sport ed esce con 1 se un girone finisce in "Altro". Rilanciarlo quando arrivano gironi nuovi; se serve, aggiungere la voce alla tabella.

## Comportamento
- Tocco su un campionato: solo i suoi gironi; se ne ha **uno solo** si apre il girone (il "‹ Partite" del girone torna alla lista filtrata).
- Genere (Tutti/M/F/Misto) solo se il campionato scelto ha più generi; Zona in una tendina solo se ci sono almeno due zone. Scelte non più valide tornano a "Tutti".
- Sport con un solo campionato (hockey, calcio a 5): nessuna barra. Gli sport della sola agenda non hanno gironi e non compaiono.
- Sport + campionati agganciati sotto la barra blu (`--toph` misurata con ResizeObserver); cambiando campionato da agganciati la lista ricomincia sotto la barra.
- Stato in `#risultati?sport=basket&camp=u13&genere=F&zona=UD` (condivisibile, `replaceState`), in `localStorage` `sfvg-ris` e in memoria se lo storage è bloccato.
- Accessibilità: barre `role=tablist` con tabindex mobile, frecce/Inizio/Fine spostano il fuoco, Invio/Spazio attiva (attivazione manuale, così una freccia non apre un girone); chip ≥ 44 px; sfumature ai lati quando la barra continua; chip scelto portato in vista (morbido solo senza `prefers-reduced-motion`). Da 760 px i chip vanno a capo.
- Prova: `design/screenshot/campionati/` (schermate, `barra-scorrimento-selezione.gif`, `tavola-riepilogo.png`). axe-core 0 violazioni a 320/390/1280 px chiaro e scuro.
