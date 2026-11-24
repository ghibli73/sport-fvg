"""Rigenera config/pallavolo.json dai gironi di pallavolo presenti in data/risultati.json.

Per ogni girone salva: portale, CId della classifica, pagina risultati (PId), dati descrittivi e la tabella
"nome squadra sul portale -> id società nell'app" (presa dalle classifiche già abbinate).
I gironi già presenti nel config mantengono le voci aggiunte a mano (alias extra, disattivazioni).
Uso:  python scripts/genera_config.py
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
CFG = os.path.join(ROOT, "config", "pallavolo.json")


def main():
    old = {}
    if os.path.exists(CFG):
        old = {g["slug"]: g for g in json.load(open(CFG))["gironi"]}
    out = []
    for g in json.load(open(RIS)):
        if g["sport"] != "pallavolo":
            continue
        m = re.search(r"https?://([^/\s]+)/classifica\.aspx\?CId=(\d+)", g["fonte"])
        if not m:
            continue
        host, cid = m.group(1), m.group(2)
        pm = re.search(r"PId=(\d+)", g["fonte"])
        cm = re.search(r"ComitatoId=(\d+)", g["fonte"])
        slug = g["gid"][len("pallavolo-"):]
        alias = {r["squadra"]: r["id"] for r in g["classifica"] if r.get("id")}
        prev = old.get(slug, {})
        alias.update(prev.get("alias", {}))
        out.append({
            "slug": slug, "attivo": prev.get("attivo", True), "host": host, "cid": cid,
            "pid": pm.group(1) if pm else prev.get("pid"), "comitato_id": cm.group(1) if cm else prev.get("comitato_id"),
            "girone": g["girone"], "categoria": g["categoria"], "genere": g["genere"], "stagione": g["stagione"],
            "comitato": g["comitato"], "alias": alias,
        })
    for slug, g in old.items():  # gironi aggiunti a mano e non ancora in risultati.json
        if slug not in {x["slug"] for x in out}:
            out.append(g)
    json.dump({"nota": "Generato da scripts/genera_config.py; si può modificare a mano (alias, attivo).", "gironi": out},
              open(CFG, "w"), ensure_ascii=False, indent=1)
    print(f"config/pallavolo.json: {len(out)} gironi")


if __name__ == "__main__":
    main()
