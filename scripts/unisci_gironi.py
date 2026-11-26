"""Unione a tre vie di data/risultati.json, girone per girone (per i push in conflitto tra workflow diversi).
Uso: python scripts/unisci_gironi.py <base> <nostro> <corrente>
  base     = il file com'era quando questo workflow è partito (/tmp/risultati_prima.json)
  nostro   = il file prodotto da questo workflow
  corrente = il file di origin/main (scritto nel frattempo da un altro workflow): viene riscritto con l'unione.
Regola: un girone cambiato da noi (nostro != base) prende la nostra versione; tutti gli altri restano quelli di main.
Così pallavolo, basket, calcio e giro rapido possono salvare a pochi secondi di distanza senza perdere nulla."""
import json, sys

base, nostro, corr = (json.load(open(p)) for p in sys.argv[1:4])
B = {g["gid"]: g for g in base}
N = {g["gid"]: g for g in nostro}
out, visti, nostri = [], set(), 0
for g in corr:
    gid = g["gid"]; visti.add(gid)
    if gid in N and N[gid] != B.get(gid):
        out.append(N[gid]); nostri += 1
    elif gid not in N and gid in B:
        nostri += 1  # tolto da noi
    else:
        out.append(g)
for gid, g in N.items():
    if gid not in visti and gid not in B:
        out.append(g); nostri += 1  # girone nuovo nostro
json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, separators=(",", ":"))
print(f"unione: {nostri} gironi nostri, {len(out) - nostri} da main")
