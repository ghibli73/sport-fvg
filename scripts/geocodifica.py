"""Geocodifica delle società per la mappa dell'app Zuìn – Sport in FVG.

  python scripts/geocodifica.py [--max-minuti 80] [--solo-cache]

Per ogni società di data/data.json cerca l'indirizzo (campo indirizzo + comune + "Friuli-Venezia Giulia")
con Nominatim di OpenStreetMap; se non lo trova (o il punto è lontano dal comune) usa il centro del comune.
Scrive data/luoghi.json: {id_società: [lat, lon, precisione]} con precisione "indirizzo" o "comune".

Regole d'uso di Nominatim (https://operations.osmfoundation.org/policies/nominatim/): una richiesta ogni
1,1 s, User-Agent che identifica l'app, risultati in cache (config/geocodifica_cache.json, da committare:
le esecuzioni successive interrogano solo gli indirizzi nuovi). Dati © OpenStreetMap contributors (ODbL).
"""
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CACHE = os.path.join(BASE, "config", "geocodifica_cache.json")
OUT = os.path.join(BASE, "data", "luoghi.json")
URL = "https://nominatim.openstreetmap.org/search"
UA = "Zuin-SportFVG/1.0 (https://ghibli73.github.io/sport-fvg/)"
REGIONE = "Friuli-Venezia Giulia"
PAUSA = 1.1
BBOX = (45.55, 46.70, 12.30, 13.95)  # lat min, lat max, lon min, lon max (FVG con un po' di margine)
DIST_MAX_KM = 20  # un indirizzo più lontano di così dal centro del comune è considerato sbagliato
VIA = re.compile(r"^(via|viale|v\.le|piazza|p\.za|piazzale|p\.le|largo|loc\.|località|localita|strada|str\.|borgo|vicolo|"
                 r"corso|riva|salita|contrada|calle|rione|androna|scala|passeggio|lungomare)\b", re.I)

_ultima = 0.0


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def in_regione(p):
    return BBOX[0] <= p[0] <= BBOX[1] and BBOX[2] <= p[1] <= BBOX[3]


def cerca(q, cache, stat):
    """Restituisce [lat, lon] oppure None; usa la cache (anche per le ricerche senza risultato)."""
    global _ultima
    if q in cache:
        return cache[q]
    if stat.get("solo_cache") or time.time() > stat["scadenza"]:
        stat["saltate"] += 1
        return None
    attesa = PAUSA - (time.time() - _ultima)
    if attesa > 0:
        time.sleep(attesa)
    par = urllib.parse.urlencode({"q": q, "format": "jsonv2", "countrycodes": "it", "limit": 3})
    req = urllib.request.Request(URL + "?" + par, headers={"User-Agent": UA, "Accept-Language": "it"})
    ris = None
    for tentativo in range(3):
        try:
            _ultima = time.time()
            with urllib.request.urlopen(req, timeout=30) as r:
                dati = json.load(r)
            for x in dati:
                p = [round(float(x["lat"]), 5), round(float(x["lon"]), 5)]
                if in_regione(p):
                    ris = p
                    break
            break
        except Exception as e:
            print("  errore", q, "->", e)
            time.sleep(5 * (tentativo + 1))
    else:
        stat["errori"] += 1
        return None  # errore di rete: non va in cache, si riprova la prossima volta
    stat["richieste"] += 1
    cache[q] = ris
    if stat["richieste"] % 50 == 0:
        salva_cache(cache)
        print(f"  {stat['richieste']} richieste...")
    return ris


def salva_cache(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, CACHE)


def ricerche(indirizzo, comune):
    """Le ricerche da provare per un indirizzo, dalla più precisa: dalla prima parte che sembra una via in poi."""
    if not indirizzo or re.search(r"non pubblicat", indirizzo, re.I):
        return []
    parti = [p.strip() for p in indirizzo.split(",") if p.strip()]
    parti = [re.sub(r"\b\d{5}\b\s*", "", p).strip() for p in parti]  # via il CAP
    parti = [p for p in parti if p and p.lower() != comune.lower()]
    k = next((i for i, p in enumerate(parti) if VIA.match(p)), None)
    out = []
    if k is not None:
        via = parti[k]
        out.append(f"{via}, {comune}, {REGIONE}")
        senza_num = re.sub(r"\s+\d+\s*[\w/]*$", "", via)
        if senza_num != via:
            out.append(f"{senza_num}, {comune}, {REGIONE}")
    elif parti:
        out.append(f"{parti[0]}, {comune}, {REGIONE}")  # es. nome di un impianto
    return out


def main(argv):
    max_min = 80
    if "--max-minuti" in argv:
        max_min = float(argv[argv.index("--max-minuti") + 1])
    stat = {"richieste": 0, "errori": 0, "saltate": 0, "scadenza": time.time() + max_min * 60,
            "solo_cache": "--solo-cache" in argv}
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    soc = json.load(open(os.path.join(BASE, "data", "data.json"), encoding="utf-8"))
    comuni = {c["codice"]: c for c in json.load(open(os.path.join(BASE, "data", "comuni.json"), encoding="utf-8"))["comuni"]}
    centri = {}
    for cod in sorted({s["codice"] for s in soc}):
        nome = comuni.get(cod, {}).get("nome") or next(s["comune"] for s in soc if s["codice"] == cod)
        p = cerca(f"{nome}, {REGIONE}, Italia", cache, stat)
        if p:
            centri[cod] = p
    print(f"Centri dei comuni: {len(centri)} su {len({s['codice'] for s in soc})}")
    luoghi, n_ind, n_com, senza = {}, 0, 0, []
    for s in soc:
        centro = centri.get(s["codice"])
        trovato = None
        for q in ricerche(s.get("indirizzo") or "", s["comune"]):
            p = cerca(q, cache, stat)
            if p and (not centro or km(p, centro) <= DIST_MAX_KM):
                trovato = p
                break
        if trovato:
            luoghi[s["id"]] = [trovato[0], trovato[1], "indirizzo"]
            n_ind += 1
        elif centro:
            luoghi[s["id"]] = [centro[0], centro[1], "comune"]
            n_com += 1
        else:
            senza.append(s["id"])
    salva_cache(cache)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(luoghi, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    print(f"Società: {len(soc)} — all'indirizzo {n_ind}, al centro del comune {n_com}, senza posizione {len(senza)}")
    print(f"Richieste a Nominatim: {stat['richieste']}, errori {stat['errori']}, saltate per tempo {stat['saltate']}")
    if senza:
        print("Senza posizione:", ", ".join(senza[:30]))


if __name__ == "__main__":
    main(sys.argv[1:])
