"""Gironi nazionali "agente" (aggiornati a mano) da un testo di risultati e calendario.

Serve per i campionati senza una fonte ufficiale leggibile da uno script (oggi: Serie D girone C).
Si legge il testo con la Sonda fonti (modo testo2=Round@@<url>) e lo si passa a questo script, che ricostruisce
il girone (tutte le partite con giornata e data, classifica calcolata 3-1-0) e lo scrive in data/risultati.json.
  python scripts/nazionali_manuale.py <chiave> <risultati.txt> <calendario.txt> [--prova]
<chiave> è una voce "manuali" di config/nazionali.json (gid, girone, stagione, fonte, alias, ora_fino_a).
Formato del testo (pagine results/fixtures di betexplorer lette dalla Sonda): "13. Round | 1 | X | 2 | Casa | - | Ospite | 2:1 | 22.11. | ..."
e nel calendario "14. Round | B's | 1 | X | 2 | 28.11. 15:00 | Casa | - | Ospite | ...".
Manuale: pipeline/agenti/nazionali.md
"""
import datetime as dt, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
CONF = os.path.join(ROOT, "config", "nazionali.json")


def anno(gg, mm, inizio):
    """Le date senza anno: da luglio a dicembre = primo anno della stagione."""
    a = int(inizio[:4])
    return a if int(mm) >= 7 else a + 1


def celle(testo):
    t = testo.split("round |", 1)[-1]
    return [c.strip() for c in t.split("|")]


def leggi_risultati(testo, stagione):
    C, out, g, i = celle(testo), [], None, 0
    while i < len(C):
        m = re.fullmatch(r"(\d+)\. Round", C[i])
        if m: g = int(m.group(1)); i += 1; continue
        if g and i + 4 < len(C) and C[i + 1] == "-" and re.fullmatch(r"\d+:\d+", C[i + 3]) and re.fullmatch(r"\d\d\.\d\d\.(\d{4})?", C[i + 4]):
            d, mth = C[i + 4][:2], C[i + 4][3:5]
            y = C[i + 4][6:10] or anno(d, mth, stagione)
            out.append({"giornata": g, "data": f"{y}-{mth}-{d}", "casa": C[i], "ospite": C[i + 2], "risultato": C[i + 3].replace(":", "-")})
            i += 5; continue
        i += 1
    return out


def leggi_calendario(testo, stagione):
    C, out, g, data, ora, i = celle(testo), [], None, None, None, 0
    while i < len(C):
        m = re.fullmatch(r"(\d+)\. Round", C[i])
        if m: g = int(m.group(1)); i += 1; continue
        m = re.fullmatch(r"(\d\d)\.(\d\d)\.(\d{4})?\s*(\d\d:\d\d)?", C[i])
        if m:
            data = f"{m.group(3) or anno(m.group(1), m.group(2), stagione)}-{m.group(2)}-{m.group(1)}"; ora = m.group(4); i += 1; continue
        if g and data and i + 2 < len(C) and C[i + 1] == "-" and C[i] and C[i + 2] and not re.fullmatch(r"[\d:.X]+", C[i + 2]):
            out.append({"giornata": g, "data": data, "ora": ora, "casa": C[i], "ospite": C[i + 2], "risultato": ""})
            i += 3; continue
        i += 1
    return out


def classifica(partite, alias):
    T = {}
    for x in partite:
        for s in (x["casa"], x["ospite"]):
            T.setdefault(s, {"squadra": s, "id": alias.get(s), "punti": 0, "g": 0, "v": 0, "n": 0, "p": 0, "gf": 0, "gs": 0})
        if not x["risultato"]: continue
        a, b = map(int, x["risultato"].split("-"))
        for s, f, c in ((x["casa"], a, b), (x["ospite"], b, a)):
            r = T[s]; r["g"] += 1; r["gf"] += f; r["gs"] += c
            k = "v" if f > c else "n" if f == c else "p"; r[k] += 1; r["punti"] += 3 if k == "v" else 1 if k == "n" else 0
    L = sorted(T.values(), key=lambda r: (-r["punti"], -(r["gf"] - r["gs"]), -r["gf"], r["squadra"]))
    return [{"pos": i + 1, **r} for i, r in enumerate(L)]


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    prova = "--prova" in sys.argv
    cfg = json.load(open(CONF, encoding="utf-8"))["manuali"][a[0]]
    alias = cfg.get("alias", {})
    ris = leggi_risultati(open(a[1], encoding="utf-8").read(), cfg["stagione"])
    cal = leggi_calendario(open(a[2], encoding="utf-8").read(), cfg["stagione"])
    giocate = {(x["casa"], x["ospite"]) for x in ris}
    oggi = dt.date.today().isoformat()
    fut = [x for x in cal if (x["casa"], x["ospite"]) not in giocate]
    for x in fut:
        if not x["ora"] or x["data"] > cfg.get("ora_fino_a", "0000"): x.pop("ora")
    P = sorted(ris + fut, key=lambda x: (x["giornata"], x["data"], x.get("ora") or "", x["casa"]))
    for x in P: x["id_casa"] = alias.get(x["casa"]); x["id_ospite"] = alias.get(x["ospite"])
    # controlli: una squadra una volta per giornata, nessuna partita futura con risultato
    vis, err = set(), []
    for x in P:
        for s in (x["casa"], x["ospite"]):
            if (x["giornata"], s) in vis: err.append(f"{s} due volte nella giornata {x['giornata']}")
            vis.add((x["giornata"], s))
        if x["risultato"] and x["data"] > oggi: err.append("futura con risultato: " + str(x))
    n = len({s for x in P for s in (x["casa"], x["ospite"])})
    if err: sys.exit("ERRORI:\n" + "\n".join(err))
    if n != cfg["squadre"]: sys.exit(f"ERRORE: {n} squadre invece di {cfg['squadre']}")
    if len(P) != cfg["squadre"] * (cfg["squadre"] - 1): print(f"ATTENZIONE: {len(P)} partite su {cfg['squadre'] * (cfg['squadre'] - 1)}")
    g = {"gid": cfg["gid"], "sport": cfg["sport"], "girone": cfg["girone"], "categoria": "Prima squadra", "genere": cfg.get("genere", "M"),
         "stagione": cfg["stagione"], "comitato": cfg["comitato"], "fonte": cfg["fonte"], "aggiornato": oggi,
         "giornata": max([x["giornata"] for x in ris] or [0]), "calcolata": True, "nota_parziale": cfg.get("nota", ""),
         "classifica": classifica(P, alias), "partite": P, "auto": "agente"}
    tutti = [x for x in json.load(open(RIS, encoding="utf-8")) if x["gid"] != g["gid"]] + [g]
    tutti.sort(key=lambda x: (x["sport"], x.get("categoria") != "Prima squadra", x["girone"]))
    out = "/tmp/risultati_prova.json" if prova else RIS
    json.dump(tutti, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{g['gid']}: {n} squadre, {len(P)} partite ({len(fut)} da giocare), giornata {g['giornata']} -> {out}")
    for r in g["classifica"]:
        if r["id"]: print(f"  FVG {r['squadra']} ({r['id']}): {r['pos']}° {r['punti']} punti in {r['g']} partite")


if __name__ == "__main__":
    main()
