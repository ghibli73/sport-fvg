# Widget di Zuìn per i siti esterni — manuale

Dalla 1.10.0 beta. Il widget mostra classifiche e risultati di una società o di un girone sui siti di società, comitati e giornali. È in JavaScript puro, senza librerie e senza cookie, e non fa tracciamento.

## Come si usa
Si incolla una riga nel sito, nel punto in cui deve comparire il widget:

```html
<script src="https://ghibli73.github.io/sport-fvg/widget.js" data-societa="030129-53" async></script>
<script src="https://ghibli73.github.io/sport-fvg/widget.js" data-girone="pallavolo-serie-c-femminile-fvg" data-tema="auto" async></script>
```

La pagina **widget.html** ("Metti Zuìn sul tuo sito") prepara il codice. Si cerca la società o il girone, si vede l'anteprima dal vivo e si copia il codice con il pulsante "Copia". La pagina ha anche le istruzioni per WordPress (blocco "HTML personalizzato"), Wix (Incorpora HTML) e Google Sites (Incorpora codice). Accetta un indirizzo diretto, `widget.html#s-<id>` o `widget.html#g-<gid>`. L'app la collega dalla scheda società ("Metti i risultati sul tuo sito", solo per le società con squadre nei gironi), dalla pagina del girone ("Metti sul tuo sito") e dalla pagina Info.

## Opzioni (attributi dello script)
| attributo | valori | effetto |
|---|---|---|
| `data-societa` | id della società (data/data.json) | posizione, punti, ultimo risultato con esito (V/P/N colorato) e prossima partita di ogni squadra |
| `data-girone` | gid (data/risultati.json) | classifica e ultima giornata giocata; se nessuna giornata è stata giocata, la prossima |
| `data-tema` | `chiaro` (predefinito), `scuro`, `auto` | `auto` segue il tema chiaro o scuro del dispositivo |
| `data-squadre` | numero (1–40) | società: numero massimo di squadre (predefinito 5); girone: numero massimo di righe di classifica (predefinito 20). Le squadre o righe in più si raggiungono con un link a Zuìn |

In fondo al widget compaiono "Risultati da Zuìn · Sport in FVG", con il link alla pagina dell'app (`#s-<id>` o `#g-<gid>`), e la data di aggiornamento.
Chi scrive codice può usare anche `ZuinWidget.mount(elemento, {societa|girone, tema, squadre})`, che è quello che fa l'anteprima di widget.html.

## Come è fatto
- **Shadow DOM**: il widget non subisce gli stili del sito ospite e non li modifica. `:host{all:initial!important}` blocca anche le proprietà ereditate, come font e colore, perché le regole `!important` dentro lo shadow tree prevalgono su quelle della pagina. Gli stili si applicano con `adoptedStyleSheets`, che funziona anche con una CSP restrittiva sugli stili in linea, e in alternativa con un `<style>`.
- **Responsive** da 280 a 600 px, con larghezza massima 600 px. Sotto i 380 px una container query compatta le righe e nasconde la colonna G.
- **Più widget** nella stessa pagina: ogni `<script>` viene marcato con `data-zuin`, `widget.js` si definisce una volta sola e le richieste uguali si fanno una volta sola.
- **Errori**: se una richiesta non riesce o scade dopo 12 s, il widget mostra il messaggio discreto "Risultati non disponibili in questo momento" con il link a Zuìn e non lancia eccezioni nella pagina ospite. Per un id inesistente il browser registra in console il 404 della richiesta. È l'unica traccia e non si può evitare.
- **Privacy**: nessun cookie (`credentials: 'omit'`), nessun conteggio visite, niente GoatCounter. Il browser scarica solo `widget.js`, il file JSON e l'icona `icons/icon-192.png`, tutti da ghibli73.github.io.
- Peso: `widget.js` meno di 15 kB (circa 14 kB non minimizzato). Un file della società è di 1–6 kB, uno del girone di 1–5 kB.

## CORS di GitHub Pages
Il widget legge i JSON con `fetch` da un altro dominio, quindi serve l'intestazione `Access-Control-Allow-Origin`. La documentazione ufficiale di GitHub Pages non descrive le intestazioni. In una discussione della community GitHub (github.com/orgs/community/discussions/22399, 2021) si legge: "Pages allows CORS (`access-control-allow-origin` header is set to `*`) for public sites only." Il repository è pubblico, quindi le richieste del widget sono permesse.
Da questo ambiente (proxy) non è stato possibile leggere le intestazioni del sito vero. Dopo il merge verificare con:
`curl -sI -H "Origin: https://esempio.it" https://ghibli73.github.io/sport-fvg/data/widget/indice.json | grep -i access-control`
Il risultato atteso è `access-control-allow-origin: *`. Se il repository diventasse privato, il widget smetterebbe di funzionare sui siti esterni.

## File generati (`scripts/widget_dati.py`)
- `data/widget/s/<id>.json`: uno per ogni società che compare in un girone, in classifica o nelle partite, e che esiste in data.json. Contiene `id, nome, comune, sport, aggiornato, squadre[]`. Ogni squadra ha `sport, categoria, girone, gid, pos, punti, n` (numero di squadre), `aggiornato`, `ultima {data, casa, ospite, risultato, esito v|p|n, in_casa}` e `prossima {data, ora, avversario, in_casa, campo}`. Le squadre seguono l'ordine della scheda società (categoria, poi livello del campionato).
- `data/widget/g/<gid>.json`: uno per girone. Contiene `gid, sport, girone, categoria, comitato, stagione, aggiornato, nota_parziale, n, classifica[{pos, squadra, id, punti, g}]`, `ultima` (la giornata più alta tra quelle giocate) e `prossima` (la giornata più bassa tra le partite future). Ogni giornata ha al massimo 10 partite. Per i gironi senza numero di giornata si raggruppa per data.
- `data/widget/indice.json`: elenco di società e gironi per la ricerca in widget.html.
- I caratteri diversi da `A-Za-z0-9._-` nei nomi dei file diventano `_`, e widget.js fa la stessa conversione.
- Un file viene riscritto solo se cambia, e i file di società o gironi spariti vengono tolti. Lo script esce sempre con 0. L'esito e la prossima partita dipendono dalla data del giorno, quindi alcuni file cambiano anche senza risultati nuovi.
- Workflow: passo "Widget per i siti (data/widget)" subito dopo "Calendari delle società (data/ics)" in `aggiorna-calcio/basket/pallavolo.yml`. Il commit esistente su `data/` include anche questi file. Dopo una correzione a mano di data/risultati.json eseguire `python scripts/widget_dati.py`.

## Aggiornamento e cache
- GitHub Pages serve i file con `Cache-Control: max-age=600`, quindi i siti esterni vedono un nuovo `widget.js` o nuovi dati entro circa 10 minuti. Il widget chiede i JSON con `cache: 'no-cache'`, cioè con una richiesta di convalida.
- Service worker (`sw.js`): `widget.js` non viene mai messo in cache e lo gestisce il browser, mentre `data/widget/` resta network-first come tutto `data/`. Sui siti esterni il service worker di Zuìn non è attivo.
- Le modifiche a `widget.js` devono restare compatibili: attributi e nomi dei campi JSON sono un'interfaccia pubblica, usata da siti che non controlliamo.

## Prove
- `tests/widget-test.html` (non collegata dall'app, `noindex`) è una pagina ospite con `* { font: 30px serif !important; color: red }` e altri stili ostili (bordi, padding, `display: inline !important`, `.zuin-widget{display:none}`). Contiene quattro widget: società, girone scuro, la stessa società una seconda volta e un id inesistente. Va servita dalla radice del repository (`python3 -m http.server`) e aperta su `/tests/widget-test.html`.
- La prova del 25/11/2026 è stata fatta con playwright e Chrome a 320, 390 e 1280 px. Font, colore e larghezza sono rimasti corretti e non c'è scorrimento orizzontale. axe-core non ha trovato violazioni nei widget, in widget.html né nell'app. Gli screenshot sono in `design/screenshot/widget/`.

## Limiti
- I dati sono quelli di Zuìn: aggiornati dai workflow (calcio due volte al giorno nei feriali, pallavolo e basket secondo i propri cron), non in tempo reale. Fa fede la federazione.
- Funziona solo per società e gironi presenti in data/risultati.json. Per le società senza squadre nei gironi non c'è il file e il widget mostra il messaggio di errore.
- I siti che non permettono script esterni non possono usarlo: WordPress.com con i piani senza plugin e alcune piattaforme con CSP severa (serve `script-src` e `connect-src` verso ghibli73.github.io). Su Google Sites il codice incorporato gira in un iframe, quindi bisogna regolare a mano l'altezza del riquadro.
- Il widget non ha il link "Condividi" né il calendario: per quelli si va nell'app.
- I nomi delle squadre sono quelli delle federazioni, spesso in maiuscolo.
