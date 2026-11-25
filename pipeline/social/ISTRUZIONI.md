# Profili social delle società — istruzioni

Per ogni società del tuo lotto (file /home/claude/fvg/social/lotti/<LOTTO>.json, già in ordine di priorità) trova:
- pagina Facebook ufficiale (URL https://www.facebook.com/...),
- profilo Instagram ufficiale (URL https://www.instagram.com/<handle>/),
- sito web ufficiale, se esiste.

## Consegna
Scrivi /home/claude/fvg/patch/social-<LOTTO>/<codice>.json: un array per comune, una voce per società (anche se non trovi nulla):
  {"codice": "030118", "comune": "Tavagnacco", "nome": "<identico al lotto>", "sport": "<identico al lotto>",
   "social": {"facebook": "https://www.facebook.com/...", "instagram": "https://www.instagram.com/.../", "sito": "https://..."},
   "social_verifica": "sito ufficiale" | "corrispondenza nome e comune" | "non trovato",
   "fonte": "dove hai trovato i link"}
Ometti le chiavi che non trovi. Se non trovi nulla: "social": {} e "social_verifica": "non trovato".
Se il file del comune esiste già (lavoro tuo di un turno precedente), aggiorna senza perdere le voci presenti.

## Regole di verifica (fondamentali)
1. Il metodo migliore: trova il sito ufficiale della società e prendi i link social dal sito (header/footer). Livello "sito ufficiale".
2. Altrimenti accetta un profilo SOLO se nel nome o nella descrizione del profilo (come appare nei risultati di ricerca) compaiono il nome della società E il comune o la frazione (o lo sport in modo inequivocabile). Livello "corrispondenza nome e comune".
3. Scarta: profili di omonimi in altre regioni, pagine di tifosi/fan, profili personali di allenatori o dirigenti, pagine dello sponsor, pagine "luogo" generate automaticamente, profili di altre sezioni della stessa polisportiva se non sono quelli della sezione giusta (in tal caso puoi usare il profilo della polisportiva, scrivendolo in "fonte").
4. Mai costruire un URL indovinando l'handle: usa solo URL visti in una pagina o in un risultato di ricerca.
5. Normalizza: https, www.facebook.com, niente parametri (?ref=…), Instagram con "/" finale.

## Budget
Il limite di ricerche web è condiviso da 4 agenti (circa 200 per turno in totale): usa al massimo ~45 WebSearch. Una ricerca tipo "<nome società> <comune> facebook instagram" spesso restituisce entrambi. Usa WebFetch sui siti ufficiali (non su facebook/instagram, che richiedono login). Procedi nell'ordine del lotto; quando finisci il budget, fermati.
Alla fine rispondi con: società lavorate, trovate (FB / IG / sito), non trovate, casi dubbi, e il nome dell'ultima società lavorata.

## Precisazione (dal secondo giro)
Il gentilizio o il toponimo nel nome del profilo (es. "Reanese", "Varmese", "Assosangiorgina") vale come comune SOLO se non esistono località omonime fuori dal FVG con società dello stesso sport (es. Palazzolo, Pavia, Magnano, Prata: ambigui → scartare).
