"""Aggiorna gli id delle società dopo un'unione (o una squadra riattribuita) in risultati e config.

Uso:
    python scripts/rimappa_id.py [--alias data/id_alias.json] [--regola "basket:^APU NEXT ?GEN=030129-59" ...]
                                 [--extra /home/claude/fvg/risultati] [--prova]

--alias   JSON {id_vecchio: id_nuovo} scritto da build.py (app/id_alias.json, copiato in data/id_alias.json).
          id_nuovo null = società rimossa: l'id viene tolto (squadra senza id).
--regola  "<sport>:<regex sul nome squadra>=<id>": assegna l'id alle squadre di quello sport il cui nome
          corrisponde (maiuscole/minuscole ignorate). Serve quando una squadra era attribuita alla società
          sbagliata (es. "APU Next Gen" sulla APU Udine).
--extra   cartella con i file degli agenti (<sport>/*.json, formato dei gironi) da aggiornare allo stesso modo.
--prova   mostra cosa cambierebbe senza scrivere.

File toccati: data/risultati.json (classifica.id, partite.id_casa/id_ospite), data/luoghi.json (chiavi),
config/calcio_alias.json, config/pallavolo.json (gironi[].alias), config/basket/*.json (ids).
"""
import argparse
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


ORIG = {}


def carica(p):
    obj = json.load(open(p, encoding="utf-8"))
    ORIG[p] = json.dumps(obj, sort_keys=True)
    return obj


def salva(p, obj, stile):
    with open(p, "w", encoding="utf-8") as f:
        if stile == "compatto":
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=stile)


def stile_di(p):
    t = open(p, encoding="utf-8").read(400)
    if "\n" not in t.strip()[:200]:
        return "compatto"
    m = re.search(r"\n( +)\S", t)
    return len(m.group(1)) if m else 0


class Rimappa:
    def __init__(self, alias, regole):
        self.alias, self.regole, self.cambi = alias, regole, []

    def nuovo(self, vecchio, nome, sport, dove):
        n = vecchio
        if vecchio in self.alias:
            n = self.alias[vecchio]
        for sp, rx, i in self.regole:
            if (sp in ("*", sport)) and nome and rx.search(str(nome)):
                n = i
        if n != vecchio:
            self.cambi.append(f"{dove}: «{nome}» {vecchio} → {n}")
        return n

    def girone(self, g, dove, sport=None):
        sport = g.get("sport") or sport
        for r in g.get("classifica") or []:
            n = self.nuovo(r.get("id"), r.get("squadra"), sport, f"{dove} classifica")
            if n != r.get("id"):
                r["id"] = n
        for p in g.get("partite") or []:
            for lato in ("casa", "ospite"):
                k = "id_" + lato
                n = self.nuovo(p.get(k), p.get(lato), sport, f"{dove} partita")
                if n != p.get(k):
                    p[k] = n

    def mappa(self, d, sport, dove):
        for nome, i in list(d.items()):
            d[nome] = self.nuovo(i, nome, sport, dove)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--alias", default=os.path.join(ROOT, "data", "id_alias.json"))
    ap.add_argument("--regola", action="append", default=[])
    ap.add_argument("--extra")
    ap.add_argument("--prova", action="store_true")
    a = ap.parse_args()
    alias = carica(a.alias) if os.path.exists(a.alias) else {}
    regole = []
    for r in a.regola:
        sp, resto = r.split(":", 1)
        rx, i = resto.rsplit("=", 1)
        regole.append((sp, re.compile(rx, re.I), i))
    rm = Rimappa(alias, regole)
    scritti = []

    p = os.path.join(ROOT, "data", "risultati.json")
    ris = carica(p)
    for g in ris:
        rm.girone(g, g.get("gid"))
    scritti.append((p, ris))

    p = os.path.join(ROOT, "data", "luoghi.json")
    if os.path.exists(p) and alias:
        lu = carica(p)
        for v, n in alias.items():
            if v in lu:
                if n and n not in lu:
                    lu[n] = lu[v]
                del lu[v]
                rm.cambi.append(f"luoghi.json: {v} → {n or 'tolto'}")
        scritti.append((p, lu))

    p = os.path.join(ROOT, "config", "calcio_alias.json")
    if os.path.exists(p):
        ca = carica(p)
        rm.mappa(ca, "calcio", "calcio_alias.json")
        scritti.append((p, ca))
    p = os.path.join(ROOT, "config", "pallavolo.json")
    if os.path.exists(p):
        pv = carica(p)
        for g in pv.get("gironi", []):
            rm.mappa(g.get("alias") or {}, "pallavolo", f"pallavolo.json {g.get('slug')}")
        scritti.append((p, pv))
    for p in sorted(glob.glob(os.path.join(ROOT, "config", "basket", "*.json"))):
        b = carica(p)
        rm.mappa(b.get("ids") or {}, "basket", f"basket/{os.path.basename(p)}")
        scritti.append((p, b))

    if a.extra:
        for p in sorted(glob.glob(os.path.join(a.extra, "*", "*.json"))):
            try:
                g = carica(p)
            except ValueError:
                continue
            if isinstance(g, dict) and ("classifica" in g or "partite" in g):
                rm.girone(g, os.path.relpath(p, a.extra), sport=os.path.basename(os.path.dirname(p)))
                scritti.append((p, g))

    for c in rm.cambi:
        print(" ", c)
    print(f"{len(rm.cambi)} cambi" + (" (prova: nulla scritto)" if a.prova else ""))
    if not a.prova:
        for p, obj in scritti:
            if json.dumps(obj, sort_keys=True) != ORIG[p]:
                salva(p, obj, stile_di(p))
                print("  scritto", os.path.relpath(p, ROOT) if p.startswith(ROOT) else p)


if __name__ == "__main__":
    main()
