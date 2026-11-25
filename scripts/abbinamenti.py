"""Abbinamenti delle squadre senza id: funzioni comuni a volley.py, basket.py, calcio.py e applica_abbinamenti.py.

- config/squadre_comune.json  {"<nome squadra>": {"comune": "<ISTAT>", "prova": "..."}}
  squadre del FVG che non si possono ancora agganciare a una società: si scrive solo il comune in cui giocano.
  Nei gironi: classifica[].comune e partite[].comune_casa / comune_ospite, SOLO dove manca l'id.
- config/abbinamenti_prove.json  [{"nome", "sport", "id", "prova", "fonte", "gironi"?}]
  abbinamenti certi a una società (la prova è obbligatoria); usati da applica_abbinamenti.py.
I nomi si confrontano senza maiuscole, spazi e punteggiatura.
"""
import json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMUNI = os.path.join(ROOT, "config", "squadre_comune.json")
PROVE = os.path.join(ROOT, "config", "abbinamenti_prove.json")


def chiave(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def carica_comuni():
    try:
        return {chiave(k): v["comune"] for k, v in json.load(open(COMUNI, encoding="utf-8")).items() if v.get("comune")}
    except (OSError, ValueError):
        return {}


def applica_comuni(gironi, comuni=None):
    """Mette il comune (ISTAT) alle squadre senza id; lo toglie a quelle che hanno l'id. Restituisce quante righe ha toccato."""
    comuni = carica_comuni() if comuni is None else comuni
    n = 0
    for g in gironi:
        for r in g.get("classifica") or []:
            c = None if r.get("id") else comuni.get(chiave(r.get("squadra")))
            if c:
                n += r.get("comune") != c
                r["comune"] = c
            elif "comune" in r:
                del r["comune"]
        for p in g.get("partite") or []:
            for lato in ("casa", "ospite"):
                c = None if p.get("id_" + lato) else comuni.get(chiave(p.get(lato)))
                if c:
                    n += p.get("comune_" + lato) != c
                    p["comune_" + lato] = c
                elif "comune_" + lato in p:
                    del p["comune_" + lato]
    return n


def applica_id(gironi, prove=None):
    """Mette l'id delle società abbinate con prova (config/abbinamenti_prove.json) dove manca. Non cambia mai un id già presente."""
    if prove is None:
        try:
            prove = json.load(open(PROVE, encoding="utf-8"))
        except (OSError, ValueError):
            prove = []
    n = 0
    for e in prove:
        k = chiave(e["nome"])
        for g in gironi:
            if g.get("sport") != e["sport"] or (e.get("gironi") and g.get("gid") not in e["gironi"]):
                continue
            for r in g.get("classifica") or []:
                if not r.get("id") and chiave(r.get("squadra")) == k:
                    r["id"] = e["id"]; n += 1
            for p in g.get("partite") or []:
                for lato in ("casa", "ospite"):
                    if not p.get("id_" + lato) and chiave(p.get(lato)) == k:
                        p["id_" + lato] = e["id"]; n += 1
    return n
