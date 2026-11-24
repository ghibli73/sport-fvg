"""Strumenti del coordinatore risultati di "Sport in FVG".

  python3 risultati_tools.py split  risultati.json  cartella/      -> un file per girone: cartella/<sport>/<slug>.json
  python3 risultati_tools.py build  cartella/  data.json  out.json -> unisce i gironi in out.json (formato dell'app)
  python3 risultati_tools.py check  vecchio.json nuovo.json        -> controlli prima di pubblicare

Formato di un girone: vedi claude/agenti/formato-risultati.md nel progetto.
"""
import json, glob, os, re, sys


def split(src, dst):
    for g in json.load(open(src)):
        sport = g["sport"]
        slug = g["gid"][len(sport) + 1:] if g["gid"].startswith(sport + "-") else g["gid"]
        os.makedirs(os.path.join(dst, sport), exist_ok=True)
        f = {"sport": sport, "girone": g["girone"], "categoria": g.get("categoria", ""), "genere": g.get("genere", ""),
             "stagione": g.get("stagione", ""), "comitato": g.get("comitato", ""), "fonte": g["fonte"],
             "aggiornato": g["aggiornato"], "giornata": g.get("giornata"), "classifica_calcolata": g.get("calcolata", False),
             "classifica": g.get("classifica", []), "partite": g.get("partite", [])}
        json.dump(f, open(os.path.join(dst, sport, slug + ".json"), "w"), ensure_ascii=False, indent=1)
    print("gironi scritti in", dst)


def build(folder, data, out):
    ids = {c["id"] for c in json.load(open(data))}
    res, problems = [], []
    for p in sorted(glob.glob(os.path.join(folder, "*", "*.json"))):
        sport = os.path.basename(os.path.dirname(p)); slug = os.path.basename(p)[:-5]
        try:
            g = json.load(open(p))
        except Exception as e:
            problems.append(f"{p}: {e}"); continue
        if not (g.get("classifica") or g.get("partite")) or not g.get("fonte") or not g.get("aggiornato"):
            problems.append(f"{p}: vuoto o senza fonte/data"); continue
        ok = lambda i: i if i in ids else None
        cl = [{**r, "id": ok(r.get("id"))} for r in g.get("classifica") or []]
        pa = [{**m, "id_casa": ok(m.get("id_casa")), "id_ospite": ok(m.get("id_ospite"))} for m in g.get("partite") or []]
        pa.sort(key=lambda m: (m.get("giornata") or 0, m.get("data") or "9999", m.get("ora") or ""))
        res.append({"gid": re.sub(r"[^a-z0-9-]", "-", f"{sport}-{slug}".lower()), "sport": g.get("sport", sport),
                    "girone": g.get("girone", slug), "categoria": g.get("categoria", ""), "genere": g.get("genere", ""),
                    "stagione": g.get("stagione", ""), "comitato": g.get("comitato", ""), "fonte": g["fonte"],
                    "aggiornato": g["aggiornato"], "giornata": g.get("giornata"), "calcolata": bool(g.get("classifica_calcolata")),
                    "classifica": cl, "partite": pa})
    res.sort(key=lambda g: (g["sport"], g["categoria"] != "Prima squadra", g["girone"]))
    json.dump(res, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"gironi {len(res)} | squadre {sum(len(g['classifica']) for g in res)} | abbinate {sum(1 for g in res for r in g['classifica'] if r['id'])}")
    for x in problems: print("  !", x)


def check(old, new):
    o = {g["gid"]: g for g in json.load(open(old))}; n = {g["gid"]: g for g in json.load(open(new))}
    bad = 0
    for gid in o:
        if gid not in n: print("! girone sparito:", gid); bad += 1
    for gid, g in n.items():
        if gid in o:
            if len(g["classifica"]) < len(o[gid]["classifica"]): print("! squadre in meno:", gid); bad += 1
            if g["aggiornato"] < o[gid]["aggiornato"]: print("! data più vecchia:", gid); bad += 1
            go, gn = o[gid].get("giornata") or 0, g.get("giornata") or 0
            if gn < go: print("  nota: giornata corretta all'indietro (", go, "->", gn, ") in", gid)
        pts = [r.get("g") for r in g["classifica"] if r.get("g") is not None]
        if pts and max(pts) - min(pts) > 3: print("  nota: partite giocate molto diverse in", gid)
    print("nuovi gironi:", len(set(n) - set(o)), "| aggiornati:", sum(1 for k in n if k in o and n[k]["aggiornato"] != o[k]["aggiornato"]), "| problemi:", bad)
    return bad


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "split": split(sys.argv[2], sys.argv[3])
    elif cmd == "build": build(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "check": sys.exit(1 if check(sys.argv[2], sys.argv[3]) else 0)
