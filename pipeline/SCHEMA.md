# Formato dati — un file per comune: /home/claude/fvg/raw/<codice ISTAT>.json

Il file è un array JSON di società. Ogni società:

{
  "codice": "030118",              // codice ISTAT del comune (dal file batch)
  "comune": "Tavagnacco",
  "prov": "UD",
  "nome": "ASD Deportivo Junior",  // denominazione ufficiale se nota
  "sport": "calcio",               // UNA chiave tra quelle sotto (sport principale)
  "altri_sport": ["calcio5"],      // opzionale, altre discipline praticate
  "indirizzo": "Via Tolmezzo, 33010 Tavagnacco",   // sede o impianto principale; "" se non trovato
  "fondata": 1989,                 // opzionale, solo se trovato
  "categorie": ["Prima squadra", "Under 17", "Scuola calcio"],
  "storico": [                     // prima squadra, stagioni 2021/22 → 2025/26; solo stagioni verificate
    {"stagione": "2024/25", "campionato": "Prima Categoria, girone B", "pos": "1 (promossa)"},
    {"stagione": "2025/26", "campionato": "Promozione", "pos": 7}
  ],
  "campionato_attuale": "Promozione 2026/27",   // opzionale
  "note": "",
  "fonte": "Annuario LND FVG 2025/26; FriuliGol"  // nomi delle fonti usate
}

Chiavi sport ammesse:
calcio, calcio5, pallavolo, basket, rugby, pallanuoto, pallamano, hockey, baseball, nuoto, tennis (anche padel),
atletica, ciclismo, scherma, ginnastica, judo (judo, karate, arti marziali), danza, sci, canottaggio (anche canoa),
vela, bocce, tiro (tiro a segno/volo/arco), equitazione, tennistavolo, altro

Regole:
- "pos": numero se è un piazzamento numerico; altrimenti testo breve ("promossa", "play-off", "n.d.").
- Mai inventare: se un dato non si trova, ometti la stagione o usa "n.d."; indirizzo "" se ignoto.
- Un comune senza società trovate → file con array vuoto [] (così si sa che è stato cercato).
- Scrivi il file del comune appena finito, prima di passare al successivo.

## Campo "squadre" (stagione in corso 2026/27)
Elenco delle squadre iscritte, una voce per categoria e genere:
  "squadre": [
    {"categoria": "Prima squadra", "genere": "M", "campionato": "Promozione girone A", "stagione": "2026/27"},
    {"categoria": "Under 17", "genere": "M", "campionato": "Allievi regionali girone B", "stagione": "2026/27"},
    {"categoria": "Under 14", "genere": "F", "campionato": "Under 14 femminile girone A (CT Udine)", "stagione": "2026/27", "id_fonte": "CId=92422"}
  ]
- "categoria": usa la dicitura federale per età (Under 12, Under 13, …, Under 19, Juniores, Prima squadra, Seconda squadra).
- "genere": "M", "F" o "misto". "campionato": nome ufficiale con girone. "id_fonte": opzionale, codice/URL del girone sulla fonte ufficiale (servirà per i risultati in tempo reale).
- Il merge sostituisce la voce con stessa categoria+genere.
