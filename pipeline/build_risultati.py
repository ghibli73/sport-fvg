"""Unisce risultati/<sport>/*.json in app/risultati.json (esclude le cartelle di lavoro)."""
import json, glob, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
ids = {c["id"] for c in json.load(open(os.path.join(BASE, "app", "data.json")))}
out, problems = [], []
for p in sorted(glob.glob(os.path.join(BASE, "risultati", "*", "*.json"))):
    sport = os.path.basename(os.path.dirname(p))
    slug = os.path.basename(p)[:-5]
    try:
        g = json.load(open(p))
    except Exception as e:
        problems.append(f"{p}: {e}"); continue
    if not g.get("classifica") and not g.get("partite"):
        problems.append(f"{p}: vuoto"); continue
    if not g.get("fonte") or not g.get("aggiornato"):
        problems.append(f"{p}: senza fonte o data"); continue
    gid = re.sub(r"[^a-z0-9-]", "-", f"{sport}-{slug}".lower())
    def chk(i):
        return i if i in ids else None
    cl = []
    for r in g.get("classifica") or []:
        r = dict(r); r["id"] = chk(r.get("id")); cl.append(r)
    pa = []
    for m in g.get("partite") or []:
        m = dict(m); m["id_casa"] = chk(m.get("id_casa")); m["id_ospite"] = chk(m.get("id_ospite")); pa.append(m)
    pa.sort(key=lambda m: (m.get("data") or "9999", m.get("ora") or ""))
    out.append({"gid": gid, "sport": g.get("sport", sport), "girone": g.get("girone", slug), "categoria": g.get("categoria", ""),
                "genere": g.get("genere", ""), "stagione": g.get("stagione", ""), "comitato": g.get("comitato", ""),
                "fonte": g["fonte"], "aggiornato": g["aggiornato"], "giornata": g.get("giornata"),
                "calcolata": bool(g.get("classifica_calcolata")), "classifica": cl, "partite": pa})
out.sort(key=lambda g: (g["sport"], g["categoria"] != "Prima squadra", g["girone"]))
json.dump(out, open(os.path.join(BASE, "app", "risultati.json"), "w"), ensure_ascii=False, separators=(",", ":"))
lk = sum(1 for g in out for r in g["classifica"] if r["id"])
print(f"gironi {len(out)} | squadre in classifica {sum(len(g['classifica']) for g in out)} di cui abbinate {lk}")
for x in problems: print("  !", x)
