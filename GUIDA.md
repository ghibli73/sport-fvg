# Sport in FVG — guida alla pubblicazione su GitHub

Tempo: circa 20 minuti, da computer (da telefono GitHub è scomodo). Costo: zero.
Alla fine avrai: l'app online a un indirizzo pubblico, installabile sul telefono, con la pallavolo che si aggiorna da sola.

## Passo 1 — Account GitHub
1. Vai su https://github.com e crea un account gratuito (se non l'hai già).
2. Conferma l'email.

## Passo 2 — Crea il repository
1. In alto a destra: **+** → **New repository**.
2. Nome: `sport-fvg`. Visibilità: **Public** (GitHub Pages gratuito richiede un repository pubblico).
3. Lascia vuote le altre opzioni e premi **Create repository**.

## Passo 3 — Carica i file
1. Estrai lo zip `sport-fvg.zip` sul computer.
2. Nella pagina del repository vuoto clicca **uploading an existing file**.
3. Trascina **tutto il contenuto** della cartella estratta (index.html, data, scripts, config, icons, ecc.).
   Attenzione: la cartella `.github` è nascosta su alcuni computer. Se non la vedi, la creiamo al passo 5.
4. In basso premi **Commit changes**.

## Passo 4 — Accendi il sito (GitHub Pages)
1. Nel repository: **Settings** → **Pages**.
2. In "Build and deployment" → Source: **Deploy from a branch**; Branch: **main**, cartella **/ (root)** → **Save**.
3. Dopo 1–2 minuti in alto compare l'indirizzo, tipo `https://<tuo-utente>.github.io/sport-fvg/`. Aprilo: è la tua app.

## Passo 5 — Accendi l'aggiornamento automatico
1. **Settings** → **Actions** → **General** → in fondo "Workflow permissions": scegli **Read and write permissions** → **Save**.
2. Se al passo 3 la cartella `.github` non è stata caricata: **Add file** → **Create new file**, nome
   `.github/workflows/aggiorna-pallavolo.yml`, incolla il contenuto del file con lo stesso nome dallo zip, **Commit**.
   Ripeti per `.github/workflows/diagnosi-pallavolo.yml`.
3. Scheda **Actions** → se richiesto, premi **I understand my workflows, go ahead and enable them**.

## Passo 6 — Prima prova
1. Scheda **Actions** → **Diagnosi pallavolo (solo lettura)** → **Run workflow**.
   Legge i portali FIPAV senza modificare nulla e allega le pagine scaricate.
2. Poi **Aggiorna pallavolo** → **Run workflow**. Se diventa verde, i dati sono aggiornati e salvati.
3. Se diventa rosso: nessun dato viene rovinato. Dimmi "controlla GitHub": l'agente legge l'errore, corregge lo script e riprova.

## Passo 7 — Collega GitHub a Claude (per l'agente)
Così l'agente "GitHub Sport FVG" può pubblicare aggiornamenti, correggere gli script e caricare i risultati di basket e calcio:
1. In claude.ai: **Impostazioni → Connettori → GitHub** e autorizza l'accesso al repository `sport-fvg`.
2. Scrivi a Claude, nel progetto Sport FvG: "collega il repository <tuo-utente>/sport-fvg".

## Passo 8 — Installa l'app sul telefono
- Android (Chrome): apri l'indirizzo → menu ⋮ → **Installa app** / **Aggiungi a schermata Home**.
- iPhone (Safari): apri l'indirizzo → pulsante **Condividi** → **Aggiungi alla schermata Home**.

## Passo 9 (facoltativo) — Indirizzo tuo
1. Compra un dominio (es. `sportfvg.it`, circa 10 €/anno) da un registrar italiano.
2. **Settings → Pages → Custom domain**: scrivi il dominio e segui le istruzioni DNS indicate da GitHub.
3. Attiva **Enforce HTTPS**.

## Prima della diffusione pubblica
- Completa `note-legali.html` con il tuo nome/contatto (cerca "DA COMPLETARE").
- Scrivi ai comitati regionali FIPAV, FIP e LND FVG per presentare il progetto e chiedere il consenso all'uso dei dati (bozza disponibile su richiesta).

## Cosa si aggiorna da solo e cosa no
| Sport | Come | Quando |
|---|---|---|
| Pallavolo | script automatico dai portali FIPAV (classifiche e risultati) | weekend ogni ora 14–23, feriali alle 21 |
| Basket | agente (omologazioni FIP in PDF); in futuro script | giornaliero tramite il coordinatore |
| Calcio | agente (comunicati LND in PDF) | giornaliero tramite il coordinatore |
