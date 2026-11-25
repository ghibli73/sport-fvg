"""Unisce i file raw/<codice>.json in app/data.json e app/comuni.json."""
import json, glob, os, sys
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
SPORTS = {"calcio","calcio5","pallavolo","basket","rugby","pallanuoto","pallamano","hockey","baseball","nuoto",
          "tennis","atletica","ciclismo","scherma","ginnastica","judo","danza","sci","canottaggio","vela","bocce",
          "tiro","equitazione","tennistavolo","pattinaggio","altro"}

comuni = json.load(open(os.path.join(BASE, "comuni_fvg.json")))
by_code = {c["codice"]: c for c in comuni}
clubs, done, problems = [], set(), []

for path in sorted(glob.glob(os.path.join(BASE, "raw", "*.json"))):
    code = os.path.basename(path)[:-5]
    if code not in by_code:
        problems.append(f"{code}: codice non FVG"); continue
    try:
        rows = json.load(open(path))
    except Exception as e:
        problems.append(f"{code}: JSON non valido ({e})"); continue
    if not isinstance(rows, list):
        problems.append(f"{code}: non è un array"); continue
    done.add(code)
    c = by_code[code]
    for r in rows:
        if not isinstance(r, dict) or not r.get("nome"):
            continue
        sp = str(r.get("sport", "altro")).lower().strip()
        if sp not in SPORTS:
            problems.append(f"{code}: sport '{sp}' → altro ({r.get('nome')})"); sp = "altro"
        storico = []
        for s in r.get("storico") or []:
            if isinstance(s, dict) and s.get("stagione"):
                storico.append({"stagione": str(s["stagione"]), "campionato": str(s.get("campionato", "")),
                                "pos": s.get("pos", "n.d.")})
        storico.sort(key=lambda s: s["stagione"])
        clubs.append({
            "id": f"{code}-{len([k for k in clubs if k['codice']==code])+1}",
            "codice": code, "comune": c["nome"], "prov": c["prov"],
            "nome": str(r["nome"]).strip(), "sport": sp,
            "altri_sport": [x for x in (r.get("altri_sport") or []) if x in SPORTS and x != sp],
            "indirizzo": r.get("indirizzo") or "", "fondata": r.get("fondata") or None,
            "categorie": [str(x) for x in (r.get("categorie") or [])],
            "storico": storico, "attuale": r.get("campionato_attuale") or "",
            "note": r.get("note") or "", "fonte": r.get("fonte") or "", "squadre": r.get("squadre") or [],
        })


import re
STOP={"asd","a.s.d.","ssd","a.s.","s.s.d.","pol.","polisportiva","associazione","sportiva","dilettantistica","societa","società","a","r.l.","arl","s.r.l.","srl","u.s.","us","g.s.","gs","ac","a.c.","sd","s.d.","apd","asdr","scsd","s.c.s.d.","volley","pallavolo","calcio","basket","pallacanestro","di","del","della"}
def key(n):
    t=[w for w in re.sub(r"[^a-z0-9 ]"," ",n.lower().replace("'"," ")).split() if w not in STOP]
    return " ".join(t)
merged=added=0
for path in sorted(glob.glob(os.path.join(BASE,"patch","*","*.json")),key=lambda p:(3 if os.path.basename(os.path.dirname(p)).startswith("correzioni") else 2 if os.path.basename(os.path.dirname(p)).startswith(("social-","eventi-")) else 1 if "squadre" in os.path.basename(os.path.dirname(p)) else 0,p)):
    code=os.path.basename(path)[:-5]
    if code.startswith("azioni"): continue   # file di sole azioni (unisci, sposta, ...): applicati dopo, vedi sotto
    if code not in by_code: problems.append(f"patch {path}: codice non FVG"); continue
    try: rows=json.load(open(path))
    except Exception as e: problems.append(f"patch {path}: {e}"); continue
    c=by_code[code]; done.add(code)
    for r in rows if isinstance(rows,list) else []:
        if not isinstance(r,dict) or not r.get("nome") or r.get("azione"): continue
        sp=str(r.get("sport","altro")).lower().strip(); sp=sp if sp in SPORTS else "altro"
        k=key(r["nome"])
        hit=next((x for x in clubs if x["codice"]==code and x["sport"]==sp and (key(x["nome"])==k or (k and min(len(k.split()),len(key(x["nome"]).split()))>=2 and (k in key(x["nome"]) or key(x["nome"]) in k)))),None)
        st=[{"stagione":str(s["stagione"]),"campionato":str(s.get("campionato","")),"pos":s.get("pos","n.d.")} for s in (r.get("storico") or []) if isinstance(s,dict) and s.get("stagione")]
        if hit:
            byS={s["stagione"]:s for s in hit["storico"]}
            for s in st: byS[s["stagione"]]=s
            hit["storico"]=sorted(byS.values(),key=lambda s:s["stagione"])
            for f in ("indirizzo","fondata","note"):
                if r.get(f): hit[f]=r[f]
            if r.get("campionato_attuale"): hit["attuale"]=r["campionato_attuale"]
            if r.get("squadre"):
                sq={(q.get("categoria",""),q.get("genere","")):q for q in hit.get("squadre") or []}
                for q in r["squadre"]:
                    if isinstance(q,dict) and q.get("categoria"): sq[(q["categoria"],q.get("genere",""))]=q
                hit["squadre"]=list(sq.values())
            if isinstance(r.get("social"),dict):
                so=hit.get("social") or {}
                for kk,vv in r["social"].items():
                    if kk in ("facebook","instagram","sito") and isinstance(vv,str) and vv.startswith("http"): so[kk]=vv.strip()
                hit["social"]=so
                if r.get("social_verifica"): hit["social_verifica"]=r["social_verifica"]
            if isinstance(r.get("eventi"),list):
                ev={(e.get("data",""),e.get("evento","")):e for e in hit.get("eventi") or []}
                for e in r["eventi"]:
                    if isinstance(e,dict) and e.get("evento") and e.get("fonte"): ev[(e.get("data",""),e["evento"])]=e
                hit["eventi"]=sorted(ev.values(),key=lambda e:e.get("data",""),reverse=True)
            hit["altri_sport"]=list(dict.fromkeys(hit["altri_sport"]+[x for x in (r.get("altri_sport") or []) if x in SPORTS and x!=hit["sport"]]))
            hit["categorie"]=list(dict.fromkeys(hit["categorie"]+[str(x) for x in r.get("categorie") or []]))
            if r.get("fonte") and r["fonte"] not in hit["fonte"]: hit["fonte"]=(hit["fonte"]+"; "+r["fonte"]).strip("; ")
            merged+=1
        elif os.path.basename(os.path.dirname(path)).startswith(("social-","eventi-")):
            problems.append(f"social/eventi non abbinato: {code} {r['nome']}")
        else:
            clubs.append({"id":"","codice":code,"comune":c["nome"],"prov":c["prov"],"nome":str(r["nome"]).strip(),"sport":sp,
              "altri_sport":[x for x in (r.get("altri_sport") or []) if x in SPORTS and x!=sp],"indirizzo":r.get("indirizzo") or "",
              "fondata":r.get("fondata") or None,"categorie":[str(x) for x in r.get("categorie") or []],"storico":sorted(st,key=lambda s:s["stagione"]),
              "attuale":r.get("campionato_attuale") or "","note":r.get("note") or "","fonte":r.get("fonte") or "","squadre":[q for q in r.get("squadre") or [] if isinstance(q,dict) and q.get("categoria")]}); added+=1
cnt={}
for x in clubs:
    cnt[x["codice"]]=cnt.get(x["codice"],0)+1; x["id"]=f'{x["codice"]}-{cnt[x["codice"]]}'
print(f"patch: {merged} aggiornate, {added} nuove")

# ---- Azioni di correzione (patch/correzioni/*.json, oggetti con "azione") -------------------------------
# Applicate DOPO l'assegnazione degli id: le società che restano tengono il loro id; quelle unite o rimosse
# lasciano un "buco" nella numerazione. Vedi PATCH.md, sezione "Correzioni strutturali".
AZIONI = {"unisci", "sposta", "rinomina", "rimuovi", "cancella_social", "rimuovi_squadra", "sposta_squadra", "modifica"}
MODIFICABILI = {"nome", "indirizzo", "fondata", "note", "categorie", "attuale", "altri_sport"}
by_id = {x["id"]: x for x in clubs}
alias = {}          # id unito/rimosso -> id che lo sostituisce (None se rimosso)
def risolvi(i):
    seen = set()
    while i in alias and i not in seen:
        seen.add(i); i = alias[i]
    return i
def unisci(a, b):
    """Porta i dati di a dentro b (b vince sui campi già valorizzati)."""
    byS = {s["stagione"]: s for s in a.get("storico") or []}
    for s in b.get("storico") or []: byS[s["stagione"]] = s
    b["storico"] = sorted(byS.values(), key=lambda s: s["stagione"])
    for f in ("indirizzo", "fondata", "attuale"):
        if not b.get(f) and a.get(f): b[f] = a[f]
    if a.get("note") and a["note"] not in (b.get("note") or ""): b["note"] = ((b.get("note") or "") + " " + a["note"]).strip()
    # squadre: quelle di b restano; quelle di a con la stessa categoria+genere ma un altro campionato
    # diventano la squadra successiva (Prima -> Seconda squadra; Under 15 -> Under 15 (2ª squadra))
    sq = {(q.get("categoria", ""), q.get("genere", "")): q for q in b.get("squadre") or []}
    SEN = ["Prima squadra", "Seconda squadra", "Terza squadra", "Quarta squadra"]
    for q in a.get("squadre") or []:
        k = (q.get("categoria", ""), q.get("genere", ""))
        if k in sq and sq[k].get("campionato") == q.get("campionato"): continue
        if k in sq:
            cat = re.sub(r" \((\d)ª squadra\)$", "", k[0]); n = 2
            if cat in SEN:
                prossime = [c for c in SEN[SEN.index(cat) + 1:] if (c, k[1]) not in sq]
                nuova = prossime[0] if prossime else None
            else:
                while (f"{cat} ({n}ª squadra)", k[1]) in sq: n += 1
                nuova = f"{cat} ({n}ª squadra)"
            if not nuova: problems.append(f"unisci {a['id']}→{b['id']}: squadra {k} non spostata"); continue
            q = {**q, "categoria": nuova}; k = (nuova, k[1])
        sq[k] = q
    b["squadre"] = list(sq.values())
    so = dict(a.get("social") or {}); so.update(b.get("social") or {})
    if so: b["social"] = so
    if a.get("eventi") or b.get("eventi"):
        ev = {(e.get("data", ""), e.get("evento", "")): e for e in (a.get("eventi") or []) + (b.get("eventi") or [])}
        b["eventi"] = sorted(ev.values(), key=lambda e: e.get("data", ""), reverse=True)
    b["altri_sport"] = list(dict.fromkeys(b["altri_sport"] + [x for x in a["altri_sport"] + [a["sport"]] if x != b["sport"]]))
    b["categorie"] = list(dict.fromkeys(b["categorie"] + a["categorie"]))
    for f in (a.get("fonte") or "").split("; "):
        if f and f not in b["fonte"]: b["fonte"] = (b["fonte"] + "; " + f).strip("; ")
    b["id_vecchi"] = list(dict.fromkeys((b.get("id_vecchi") or []) + [a["id"]] + (a.get("id_vecchi") or [])))
azioni_fatte = []
for path in sorted(glob.glob(os.path.join(BASE, "patch", "correzioni", "*.json"))):
    try: rows = json.load(open(path))
    except Exception as e: problems.append(f"azioni {path}: {e}"); continue
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict) or not r.get("azione"): continue
        az = r["azione"]; dove = f"{os.path.basename(path)} {az}"
        if az not in AZIONI: problems.append(f"{dove}: azione sconosciuta"); continue
        if not r.get("motivo") or not r.get("fonte"): problems.append(f"{dove}: mancano motivo o fonte, ignorata"); continue
        i = r.get("id") or r.get("da")
        if i in alias: problems.append(f"{dove}: {i} già unita/rimossa (→ {alias[i]}), ignorata"); continue
        x = by_id.get(i)
        if not x: problems.append(f"{dove}: id {i} inesistente"); continue
        if az == "unisci":
            j = risolvi(r.get("in")); y = by_id.get(j)
            if not y or j == i: problems.append(f"{dove}: destinazione {r.get('in')} non valida"); continue
            unisci(x, y); alias[i] = j
            if r.get("nome"): y["nome"] = str(r["nome"]).strip()
        elif az == "rimuovi":
            alias[i] = None
        elif az == "sposta":
            cc = by_code.get(str(r.get("codice", "")))
            if not cc: problems.append(f"{dove}: codice {r.get('codice')} non FVG"); continue
            x["codice"], x["comune"], x["prov"] = cc["codice"], cc["nome"], cc["prov"]; done.add(cc["codice"])
            if "indirizzo" in r: x["indirizzo"] = r["indirizzo"] or ""
        elif az == "rinomina":
            if not r.get("nome"): problems.append(f"{dove}: manca il nuovo nome"); continue
            x["nome"] = str(r["nome"]).strip()
        elif az == "modifica":
            campi = r.get("campi") or {}
            fuori = [k for k in campi if k not in MODIFICABILI]
            if fuori or not campi: problems.append(f"{dove}: campi non modificabili {fuori or 'nessuno'}"); continue
            for k, v in campi.items(): x[k] = v
        elif az == "cancella_social":
            so = x.get("social") or {}
            for k in r.get("campi") or ["facebook", "instagram", "sito"]: so.pop(k, None)
            x["social"] = so
            if r.get("social_verifica"): x["social_verifica"] = r["social_verifica"]
        elif az in ("rimuovi_squadra", "sposta_squadra"):
            key_q = (r.get("categoria", ""), r.get("genere", ""))
            q = next((q for q in x.get("squadre") or [] if (q.get("categoria", ""), q.get("genere", "")) == key_q), None)
            if not q: problems.append(f"{dove}: {i} non ha la squadra {key_q}"); continue
            x["squadre"] = [z for z in x["squadre"] if z is not q]
            if az == "sposta_squadra":
                y = by_id.get(risolvi(r.get("in")))
                if not y: problems.append(f"{dove}: destinazione {r.get('in')} non valida (squadra tolta e basta)")
                else:
                    q = {**q, **{k: v for k, v in (r.get("squadra") or {}).items()}}
                    y["squadre"] = [z for z in y.get("squadre") or [] if (z.get("categoria", ""), z.get("genere", "")) != (q.get("categoria", ""), q.get("genere", ""))] + [q]
        for k in ("note_aggiunta",):
            if r.get(k): x["note"] = ((x.get("note") or "") + " " + r[k]).strip()
        azioni_fatte.append(az)
if alias:
    clubs = [x for x in clubs if x["id"] not in alias]
json.dump({k: risolvi(k) for k in sorted(alias)}, open(os.path.join(BASE, "app", "id_alias.json"), "w"), ensure_ascii=False, indent=1)
if azioni_fatte:
    print("azioni: " + ", ".join(f"{a} {azioni_fatte.count(a)}" for a in sorted(set(azioni_fatte))) + f"; id sostituiti/rimossi {len(alias)} (app/id_alias.json)")
for x in clubs:
    for q in x.get("squadre") or []:
        if q.get("campionato"): q["campionato"]=re.sub(r"\s*\(calendario:[^)]*\)","",str(q["campionato"])).strip()
json.dump(clubs, open(os.path.join(BASE, "app", "data.json"), "w"), ensure_ascii=False, separators=(",", ":"))
out = [{**c, "fatto": c["codice"] in done, "n": sum(1 for k in clubs if k["codice"] == c["codice"])} for c in comuni]
json.dump({"aggiornato": date.today().isoformat(), "comuni": out},
          open(os.path.join(BASE, "app", "comuni.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(f"comuni censiti {len(done)}/215, società {len(clubs)}")
for p in problems: print("  !", p)
