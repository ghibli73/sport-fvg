#!/bin/bash
# Salva i dati prodotti da un workflow (manuale: pipeline/agenti/tempo-reale.md).
# Uso: bash scripts/salva_dati.sh "<messaggio di commit>" "<sport per data/stato.json>" <percorsi da salvare...>
# - nessun commit se non è cambiato nulla;
# - push con fino a 5 tentativi: se main è andato avanti, prima git rebase; se c'è conflitto (succede sempre quando due
#   workflow hanno cambiato data/risultati.json, che è una riga sola) si riparte da origin/main, si uniscono i gironi
#   (scripts/unisci_gironi.py: i gironi cambiati da questo workflow + tutti gli altri di main), si rimettono i file di
#   config di questo workflow e si rigenerano calendari .ics, widget e data/stato.json.
set -u
MSG="$1"; SPORT="$2"; shift 2; PERCORSI="$*"
python scripts/tempo_reale.py stato $SPORT
if [ -z "$(git status --porcelain $PERCORSI)" ]; then echo "Nessuna novità: nessun commit"; exit 0; fi
git config user.name "sport-fvg-bot"
git config user.email "sport-fvg-bot@users.noreply.github.com"
rm -rf /tmp/salva && mkdir -p /tmp/salva
cp data/risultati.json /tmp/salva/nostro.json
git status --porcelain config/ | awk '{print $NF}' > /tmp/salva/config.txt
while read -r f; do [ -f "$f" ] && mkdir -p "/tmp/salva/$(dirname "$f")" && cp "$f" "/tmp/salva/$f"; done < /tmp/salva/config.txt
git add $PERCORSI
git commit -q -m "$MSG"
for i in 1 2 3 4 5; do
  git fetch -q origin main
  if git rebase -q origin/main 2>/dev/null; then
    if git push -q origin HEAD:main; then echo "Salvato (tentativo $i)"; exit 0; fi
  else
    git rebase --abort 2>/dev/null
    echo "Conflitto con un altro aggiornamento: unione per girone (tentativo $i)"
    git reset -q --hard origin/main
    python scripts/unisci_gironi.py /tmp/risultati_prima.json /tmp/salva/nostro.json data/risultati.json
    while read -r f; do [ -f "/tmp/salva/$f" ] && cp "/tmp/salva/$f" "$f"; done < /tmp/salva/config.txt
    python scripts/ics.py > /dev/null || true
    python scripts/widget_dati.py > /dev/null || true
    python scripts/tempo_reale.py stato $SPORT
    git add $PERCORSI
    if git diff --cached --quiet; then echo "Dopo l'unione nessuna novità"; exit 0; fi
    git commit -q -m "$MSG (unito)"
    if git push -q origin HEAD:main; then echo "Salvato dopo l'unione (tentativo $i)"; exit 0; fi
  fi
  sleep $((i * 7))
done
echo "::error::push non riuscito dopo 5 tentativi"; exit 1
