"""Diagnosi: stampa nel log la struttura della pagina risultati attorno alle righe che contengono un testo.
Uso: python scripts/mostra_pagina.py <slug> <testo> [offset_settimane]"""
import json, sys, datetime as dt, os
sys.path.insert(0, os.path.dirname(__file__))
import volley
from bs4 import BeautifulSoup
slug, testo = sys.argv[1], sys.argv[2].lower()
off = int(sys.argv[3]) if len(sys.argv) > 3 else -1
cfg = next(g for g in json.load(open(volley.CFG))["gironi"] if g["slug"] == slug)
url = volley.url_settimana(cfg, volley.lunedi(dt.date.today()) + dt.timedelta(days=7 * off))
print(url)
soup = BeautifulSoup(volley.get(url), "html.parser")
righe = soup.find_all("tr")
for i, tr in enumerate(righe):
    if testo in tr.get_text(" ").lower():
        print("=" * 20)
        for t in righe[max(0, i - 4):i + 1]:
            print([volley.norm(td.get_text(" ")) for td in t.find_all(["td", "th"])][:12])
        tab = tr.find_parent("table")
        prev = [volley.norm(x) for x in tab.find_all_previous(string=True, limit=40) if volley.norm(x)][:8]
        print("  testi prima della tabella:", prev)
        print("  link nella tabella/vicino:", [a.get("href") for a in tab.find_all_previous("a", limit=4)])
