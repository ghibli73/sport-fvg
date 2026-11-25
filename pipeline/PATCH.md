# Secondo giro — come consegnare i dati

Ogni agente scrive SOLO nella sua cartella: /home/claude/fvg/patch/<NOME-AGENTE>/<codice ISTAT>.json
(un file per comune, array di società nel formato di SCHEMA.md, con "codice" e "comune").

- Per società GIÀ presenti nell'app (vedi /home/claude/fvg/app/data.json, campi codice/comune/nome/sport):
  riusa lo stesso "nome" e "sport" e includi solo i campi che aggiungi o correggi (es. "storico", "indirizzo",
  "categorie"). Il merge le unisce per comune + sport + nome; lo storico viene fuso stagione per stagione
  (il tuo dato vince sul vecchio).
- Per società NUOVE: oggetto completo come da SCHEMA.md.
- Il comune è quello dove la società ha sede o gioca le partite in casa (impianto). L'elenco dei comuni con
  codice ISTAT è in /home/claude/fvg/comuni_fvg.json. Attenzione alle frazioni: assegnale al comune giusto.
- Storico: stagioni 2021/22, 2022/23, 2023/24, 2024/25, 2025/26 (+ "campionato_attuale" per il 2026/27).
  "pos" numerico se è il piazzamento finale in classifica; testo breve per esiti (es. "1 (promossa)").
- Mai inventare. Ogni società con campo "fonte".

## Correzioni strutturali (patch/correzioni/) — unire, spostare, rinominare, rimuovere

Oltre alle normali patch di società, in `patch/correzioni/` si possono scrivere **azioni**: oggetti con il campo
`"azione"`. Vanno in un file `patch/correzioni/azioni-<tema>.json` (array) oppure dentro un `<ISTAT>.json`
insieme alle società. `build.py` le applica **dopo** aver assegnato gli id, in ordine di nome file e poi di riga.
Ogni azione deve avere `"motivo"` e `"fonte"` (altrimenti viene ignorata e segnalata con "!").

| azione | campi | effetto |
|---|---|---|
| `unisci` | `da`, `in`, opz. `nome` | porta in `in` storico, squadre, categorie, social, eventi, fonti e note di `da`, poi toglie `da`. Sui campi già valorizzati vince `in`. Se le due voci hanno una squadra con la stessa categoria+genere ma campionato diverso, quella di `da` diventa la successiva (Prima → Seconda squadra; Under 15 → Under 15 (2ª squadra)). `in` riceve `id_vecchi: [da]`. |
| `sposta` | `id`, `codice`, opz. `indirizzo` | cambia comune (codice ISTAT, nome, provincia). **L'id resta quello vecchio** (anche se il prefisso non coincide più con il comune). |
| `rinomina` | `id`, `nome` | cambia il nome (l'id resta). |
| `modifica` | `id`, `campi: {…}` | sostituisce i campi indicati; ammessi: nome, indirizzo, fondata, note, categorie, attuale, altri_sport. |
| `rimuovi` | `id` | toglie la società (es. inesistente o fuori regione). |
| `cancella_social` | `id`, opz. `campi: ["facebook","instagram","sito"]` (default tutti), opz. `social_verifica` | toglie i profili indicati (le patch normali possono solo aggiungere). |
| `rimuovi_squadra` | `id`, `categoria`, `genere` | toglie una voce da "squadre". |
| `sposta_squadra` | `id`, `in`, `categoria`, `genere`, opz. `squadra: {…}` | sposta la voce su un'altra società (sostituisce quella con stessa categoria+genere), con eventuali campi corretti. |

Esempio:
```json
[{"azione": "unisci", "da": "030114-5", "in": "030114-1", "nome": "SSD Volley Talmassons a r.l. (CDA Volley Talmassons FVG)",
  "motivo": "stessa società (cod. FIPAV 07.032.0128)", "fonte": "Regione FVG, relazione SSD Volley Talmassons A1"},
 {"azione": "cancella_social", "id": "030091-2", "campi": ["facebook", "instagram"], "motivo": "profili della società madre", "fonte": "…"}]
```

**Id stabili.** Le società che restano tengono il loro id (preferiti degli utenti, risultati.json, config). Gli id
uniti o rimossi non vengono riusati (la numerazione ha un buco). Per le società nuove l'id è il primo numero libero
del comune *in fondo*: non cambia quelli esistenti.

**Dopo un'unione** `build.py` scrive `app/id_alias.json` ({id_vecchio: id_nuovo, null se rimossa}). Nel repository:
1. copiare `app/data.json` → `data/data.json`, `app/comuni.json` → `data/comuni.json`, `app/id_alias.json` → `data/id_alias.json`;
2. `python scripts/rimappa_id.py --extra /home/claude/fvg/risultati` aggiorna gli id in data/risultati.json
   (classifica.id, partite.id_casa/id_ospite), data/luoghi.json, config/calcio_alias.json, config/pallavolo.json,
   config/basket/*.json e nei file degli agenti. Con `--regola "basket:^APU NEXT ?GEN=030129-59"` riassegna per nome
   le squadre attribuite alla società sbagliata. `--prova` mostra i cambi senza scrivere;
3. `python scripts/test_dati.py`: il controllo `id_alias_usato` deve essere 0.
L'app sposta da sola i preferiti salvati con un id unito (campo `id_vecchi` della società che resta).
