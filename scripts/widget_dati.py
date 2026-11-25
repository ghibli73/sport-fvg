"""Dati piccoli per il widget di Zuìn sui siti di società, comitati e giornali (widget.js).

  python scripts/widget_dati.py        -> scrive data/widget/s/<id società>.json, data/widget/g/<gid>.json
                                          e data/widget/indice.json

- s/<id>.json: per ogni società che ha squadre nei gironi di data/risultati.json (in classifica o nelle
  partite), una voce per squadra: sport, categoria, girone, posizione, punti, numero di squadre, ultimo
  risultato (con esito per la società), prossima partita, gid e data di aggiornamento del girone.
- g/<gid>.json: per ogni girone la classifica compatta, l'ultima giornata giocata e la prossima.
- indice.json: elenco di società e gironi con widget, per la ricerca nella pagina widget.html.

Stesso ordinamento delle squadre e stesso calcolo dell'esito della scheda società in index.html.
I file vengono riscritti solo se cambiano; quelli di società o gironi spariti vengono tolti.
Non fa mai fallire il workflow.
"""
import datetime as dt
import json
import os
import re
import sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CARTELLA = os.path.join(BASE, "data", "widget")
MAX_PARTITE = 10  # partite al massimo per giornata nel file del girone

# stesso ordine di CORD e LV in index.html
CORD = ["Prima squadra", "Seconda squadra", "Terza squadra", "Juniores", "Under 21", "Under 20", "Under 19",
        "Under 18", "Under 17", "Under 16", "Under 15", "Under 14", "Under 13", "Under 12"]
LV = [r"serie a1|superlega|serie a\b|lba", r"serie a2", r"serie a3|b nazionale", r"serie b1|b interregionale",
      r"serie b2", r"serie b", r"serie c", r"serie d", r"eccellenza", r"promozione", r"prima categoria",
      r"prima divisione|divisione regionale 1|dr1", r"seconda categoria",
      r"seconda divisione|divisione regionale 2|dr2", r"terza categoria",
      r"terza divisione|divisione regionale 3|dr3", r"carnico", r"gold", r"silver", r"regionale", r"provincial"]
LV = [re.compile(x, re.I) for x in LV]
DATA = re.compile(r"\d{4}-\d\d-\d\d")


def cidx(c):
    c = c or ""
    return next((i for i, o in enumerate(CORD) if c.startswith(o)), 99)


def lidx(n):
    return next((i for i, r in enumerate(LV) if r.search(n or "")), 99)


def ordine(x):
    return (x.get("data") or "") + str(x.get("giornata") if x.get("giornata") is not None else "").zfill(3)


def esito(x, sid):
    m = re.match(r"^\s*(\d+)\s*[-–:]\s*(\d+)", x.get("risultato") or "")
    if not m:
        return ""
    a, b = int(m[1]), int(m[2])
    mio, loro = (a, b) if x.get("id_casa") == sid else (b, a)
    return "v" if mio > loro else "p" if mio < loro else "n"


def futura(x, oggi):
    d = x.get("data") or ""
    return not x.get("risultato") and bool(DATA.fullmatch(d)) and d >= oggi


def categoria(g):
    c = g.get("categoria") or ""
    if g.get("genere") and g.get("genere") != "misto":
        c = (c + " " + g["genere"]).strip()
    return c


def partita(x):
    p = {"data": x.get("data") or None, "ora": x.get("ora") or None, "casa": x.get("casa"),
         "ospite": x.get("ospite"), "risultato": x.get("risultato") or None}
    for k in ("id_casa", "id_ospite", "campo"):
        if x.get(k):
            p[k] = x[k]
    return {k: v for k, v in p.items() if v is not None}


def scheda_societa(c, gironi, oggi):
    sid = c["id"]
    squadre = []
    for g in gironi:
        cl = g.get("classifica") or []
        mie = [x for x in g.get("partite") or [] if sid in (x.get("id_casa"), x.get("id_ospite"))]
        riga = next((r for r in cl if r.get("id") == sid), None)
        if not riga and not mie:
            continue
        giocate = sorted((x for x in mie if x.get("risultato")), key=ordine)
        prossime = sorted((x for x in mie if futura(x, oggi)), key=lambda x: (x["data"], x.get("ora") or ""))
        s = {"sport": g.get("sport"), "categoria": categoria(g), "girone": g.get("girone"), "gid": g["gid"],
             "pos": riga.get("pos") if riga else None, "punti": riga.get("punti") if riga else None,
             "n": len(cl), "aggiornato": g.get("aggiornato")}
        if giocate:
            u = giocate[-1]
            s["ultima"] = {"data": u.get("data"), "casa": u.get("casa"), "ospite": u.get("ospite"),
                           "risultato": u.get("risultato"), "esito": esito(u, sid),
                           "in_casa": u.get("id_casa") == sid}
        if prossime:
            p = prossime[0]
            casa = p.get("id_casa") == sid
            s["prossima"] = {"data": p.get("data"), "ora": p.get("ora") or None,
                             "avversario": p.get("ospite") if casa else p.get("casa"), "in_casa": casa,
                             "campo": p.get("campo") or None}
        squadre.append({k: v for k, v in s.items() if v not in (None, "")})
    squadre.sort(key=lambda s: (cidx(s.get("categoria")), lidx(s.get("girone")), s.get("girone") or ""))
    if not squadre:
        return None
    return {"id": sid, "nome": c["nome"], "comune": c.get("comune"), "sport": c.get("sport"),
            "aggiornato": max((s.get("aggiornato") or "" for s in squadre), default="") or None,
            "squadre": squadre}


def giornata_di(ps, chi):
    """Partite della giornata più recente (chi='ultima') o più vicina (chi='prossima')."""
    if not ps:
        return None
    con_g = [x for x in ps if x.get("giornata") is not None]
    if con_g:
        n = max(x["giornata"] for x in con_g) if chi == "ultima" else min(x["giornata"] for x in con_g)
        sel = [x for x in con_g if x["giornata"] == n]
    else:  # gironi senza numero di giornata: si raggruppa per data
        ds = sorted({x.get("data") for x in ps if x.get("data")})
        if not ds:
            return None
        d = ds[-1] if chi == "ultima" else ds[0]
        sel, n = [x for x in ps if x.get("data") == d], None
    sel = sorted(sel, key=lambda x: (x.get("data") or "", x.get("ora") or ""))[:MAX_PARTITE]
    return {k: v for k, v in {"giornata": n, "partite": [partita(x) for x in sel]}.items() if v is not None}


def scheda_girone(g, oggi):
    ps = g.get("partite") or []
    cl = []
    for r in g.get("classifica") or []:
        v = {"pos": r.get("pos"), "squadra": r.get("squadra"), "id": r.get("id"), "punti": r.get("punti"),
             "g": r.get("g")}
        cl.append({k: x for k, x in v.items() if x is not None})
    giocate = [x for x in ps if x.get("risultato")]
    fut = [x for x in ps if futura(x, oggi)]  # partite senza risultato con data da oggi in poi
    d = {"gid": g["gid"], "sport": g.get("sport"), "girone": g.get("girone"), "categoria": categoria(g),
         "comitato": g.get("comitato"), "stagione": g.get("stagione"), "aggiornato": g.get("aggiornato"),
         "nota_parziale": g.get("nota_parziale"), "n": len(cl), "classifica": cl,
         "ultima": giornata_di(giocate, "ultima"), "prossima": giornata_di(fut, "prossima")}
    return {k: v for k, v in d.items() if v not in (None, "") or k == "classifica"}


def scrivi(percorso, dati, scritti):
    txt = json.dumps(dati, ensure_ascii=False, separators=(",", ":")) + "\n"
    vecchio = open(percorso, encoding="utf-8").read() if os.path.exists(percorso) else None
    if vecchio != txt:
        with open(percorso, "w", encoding="utf-8") as f:
            f.write(txt)
    scritti.add(os.path.abspath(percorso))


def nome_file(s):
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(s)) + ".json"


def main():
    oggi = dt.date.today().isoformat()
    gironi = json.load(open(os.path.join(BASE, "data", "risultati.json"), encoding="utf-8"))
    societa = json.load(open(os.path.join(BASE, "data", "data.json"), encoding="utf-8"))
    for sub in ("s", "g"):
        os.makedirs(os.path.join(CARTELLA, sub), exist_ok=True)
    scritti = set()
    ids = set()
    for g in gironi:
        ids.update(r.get("id") for r in g.get("classifica") or [])
        for x in g.get("partite") or []:
            ids.update((x.get("id_casa"), x.get("id_ospite")))
    ids.discard(None)
    ids.discard("")
    ind_s, ind_g = [], []
    for c in societa:
        if c["id"] not in ids:
            continue
        sch = scheda_societa(c, gironi, oggi)
        if not sch:
            continue
        scrivi(os.path.join(CARTELLA, "s", nome_file(c["id"])), sch, scritti)
        ind_s.append([c["id"], c["nome"], c.get("comune") or "", c.get("sport") or "", len(sch["squadre"])])
    for g in gironi:
        scrivi(os.path.join(CARTELLA, "g", nome_file(g["gid"])), scheda_girone(g, oggi), scritti)
        ind_g.append([g["gid"], g.get("girone") or "", g.get("sport") or "", categoria(g), g.get("comitato") or ""])
    ind_s.sort(key=lambda r: r[1].lower())
    ind_g.sort(key=lambda r: (r[2], cidx(r[3]), lidx(r[1]), r[1]))
    scrivi(os.path.join(CARTELLA, "indice.json"), {"societa": ind_s, "gironi": ind_g}, scritti)
    tolti = 0
    for sub in ("s", "g"):
        d = os.path.join(CARTELLA, sub)
        for f in os.listdir(d):
            p = os.path.abspath(os.path.join(d, f))
            if f.endswith(".json") and p not in scritti:
                os.remove(p)
                tolti += 1
    print(f"Widget: {len(ind_s)} società, {len(ind_g)} gironi, {tolti} file tolti")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # il widget non deve mai bloccare la pubblicazione dei risultati
        print("widget_dati.py: errore", e, file=sys.stderr)
        sys.exit(0)
