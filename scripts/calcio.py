"""Aggiornamento automatico del CALCIO e CALCIO A 5 dai Comunicati Ufficiali LND FVG (nessuna intelligenza artificiale).

Legge tutti i PDF dei Comunicati Ufficiali (Comitato Regionale e Delegazioni) pubblicati nell'archivio WordPress
di friuliveneziagiulia.lnd.it, ne estrae la sezione "RISULTATI GARE" e ricostruisce ogni girone:
  categoria (es. ECCELLENZA, UNDER 17 ALLIEVI REGIONALI), girone, giornata, casa, ospite, gol.
Classifica calcolata: 3 punti vittoria, 1 pareggio; a parità differenza reti, poi gol fatti (gli scontri diretti
non sono considerati: lo dice la nota del girone).
Ogni girone diventa "calcio-<slug>" in data/risultati.json; i nomi squadra sono abbinati alle società di
data/data.json con config/calcio_alias.json (alias certi) o per nome identico.
Uso: python scripts/calcio.py [--tutto] [--prova]
"""
import io, json, os, re, sys, time, datetime as dt, unicodedata
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
SOC = os.path.join(ROOT, "data", "data.json")
STATO = os.path.join(ROOT, "config", "calcio_stato.json")
ALIAS = os.path.join(ROOT, "config", "calcio_alias.json")
BASE = "https://friuliveneziagiulia.lnd.it"
INIZIO = "2026-08-01T00:00:00"
S = requests.Session()
S.headers["User-Agent"] = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (app non ufficiale di consultazione)")


def strip_acc(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s):
    s = strip_acc((s or "").upper()).replace("’", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", strip_acc(s.lower()))).strip("-")


def elenco_pdf():
    out, pagina = [], 1
    while True:
        r = S.get(f"{BASE}/wp-json/wp/v2/media", params={"per_page": 100, "page": pagina, "after": INIZIO,
                  "mime_type": "application/pdf", "_fields": "date,source_url"}, timeout=60)
        if r.status_code == 400:
            break
        r.raise_for_status()
        js = r.json()
        out += [x for x in js if re.search(r"(^|[/_-])cu[-_ ]?\d+|comunicato", x["source_url"].rsplit("/", 1)[-1], re.I)
                and not re.search(r"allegat", x["source_url"], re.I)]
        if len(js) < 100:
            break
        pagina += 1
        time.sleep(0.5)
    return sorted(out, key=lambda x: x["date"])


def pdf_righe(url):
    import pdfplumber
    time.sleep(0.8)
    r = S.get(url, timeout=90); r.raise_for_status()
    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        return [l.strip() for p in pdf.pages for l in (p.extract_text() or "").splitlines() if l.strip()]


RX_DELEG = re.compile(r"DELEGAZIONE\s+(?:PROVINCIALE|DISTRETTUALE|TERRITORIALE)?\s*DI\s+([A-Z]+)", re.I)
RX_DATA = re.compile(r"RISULTATI UFFICIALI GARE DEL (\d{2})/(\d{2})/(\d{4})", re.I)
RX_GIR = re.compile(r"^GIRONE\s+([A-Z0-9]{1,3})\s*-\s*(\d{1,2})\s*Giornata\s*-\s*([AR])", re.I)
RX_RIS = re.compile(r"^(?:\(\d+\)\s*)?(.+?)\s+-\s+(.+?)\s+(\d{1,2})\s*-\s*(\d{1,2})\s*$")
RX_DISP = re.compile(r"^\((\d+)\)\s*-\s*disputata il (\d{2})/(\d{2})/(\d{4})", re.I)
NON_CATEG = re.compile(r"RISULTATI|Si trascrivono|GIRONE|Pag\.|COMUNICATO|^\(|DECISIONI|GIUDICE", re.I)


def leggi_cu(url):
    """-> comitato, [(categoria, girone, giornata, AR, data, casa, ospite, gc, go, n_nota)]"""
    righe = pdf_righe(url)
    testa = " ".join(righe[:15])
    m = RX_DELEG.search(testa)
    comitato = m.group(1).title() if m else "Regionale"
    out, cat, gir, data, in_ris = [], None, None, None, False
    note_disp = {}
    for i, l in enumerate(righe):
        if l.upper().startswith("RISULTATI GARE"):
            in_ris = True; continue
        if not in_ris:
            continue
        if re.match(r"^(DECISIONI|GIUSTIZIA SPORTIVA|PROVVEDIMENTI|ERRATA CORRIGE|CALENDARIO|PROGRAMMA GARE)", l, re.I):
            in_ris = False; continue
        md = RX_DATA.search(l)
        if md:
            data = f"{md.group(3)}-{md.group(2)}-{md.group(1)}"
            # la categoria è la riga precedente (es. "UNDER 17 ALLIEVI REGIONALI")
            j = i - 1
            while j >= 0 and NON_CATEG.search(righe[j]):
                j -= 1
            cat = righe[j].strip() if j >= 0 else cat
            continue
        mg = RX_GIR.match(l)
        if mg:
            gir = (mg.group(1).upper(), int(mg.group(2)), mg.group(3).upper()); continue
        mn = RX_DISP.match(l)
        if mn:
            note_disp[mn.group(1)] = f"{mn.group(4)}-{mn.group(3)}-{mn.group(2)}"; continue
        mr = RX_RIS.match(l)
        if mr and cat and gir and data:
            nota = re.match(r"^\((\d+)\)", l)
            out.append([cat, gir[0], gir[1], gir[2], data, mr.group(1).strip(), mr.group(2).strip(),
                        int(mr.group(3)), int(mr.group(4)), nota.group(1) if nota else None])
    for r in out:  # data effettiva delle gare con nota "(1) - disputata il ..."
        if r[9] and r[9] in note_disp:
            r[4] = note_disp[r[9]]
    return comitato, out


def calcio5(cat):
    return bool(re.search(r"CALCIO A (5|CINQUE)|C5|FUTSAL", cat, re.I))


def categoria_app(cat):
    c = cat.upper()
    m = re.search(r"UNDER\s*(\d{2})", c)
    if m: return f"Under {m.group(1)}"
    if "JUNIORES" in c: return "Under 19"
    if "ALLIEVI" in c: return "Under 17"
    if "GIOVANISSIMI" in c: return "Under 15"
    return "Prima squadra"


def costruisci(key, gare, comitato, ids_di, oggi):
    cat, gir = key[1], key[2]
    squadre = sorted({g["casa"] for g in gare} | {g["ospite"] for g in gare})
    tab = {n: dict(squadra=n, g=0, v=0, n=0, p=0, gf=0, gs=0) for n in squadre}
    for g in gare:
        a, b = g["gc"], g["go"]
        for t, f, s in ((g["casa"], a, b), (g["ospite"], b, a)):
            r = tab[t]; r["g"] += 1; r["gf"] += f; r["gs"] += s
            r["v" if f > s else "n" if f == s else "p"] += 1
    rows = sorted(tab.values(), key=lambda r: (-(3 * r["v"] + r["n"]), -(r["gf"] - r["gs"]), -r["gf"], r["squadra"]))
    classifica = [{"pos": i, "squadra": r["squadra"], "id": ids_di(r["squadra"]), "punti": 3 * r["v"] + r["n"], "g": r["g"],
                   "v": r["v"], "n": r["n"], "p": r["p"], "gf": r["gf"], "gs": r["gs"]} for i, r in enumerate(rows, 1)]
    partite = [{"giornata": g["g_eff"], "data": g["data"], "casa": g["casa"], "ospite": g["ospite"],
                "id_casa": ids_di(g["casa"]), "id_ospite": ids_di(g["ospite"]), "risultato": f"{g['gc']}-{g['go']}"}
               for g in sorted(gare, key=lambda g: (g["data"], g["g_eff"]))]
    nome_cat = cat.title().replace("Under ", "Under ")
    return {"gid": "", "sport": "calcio5" if calcio5(cat) else "calcio", "girone": f"{nome_cat} — girone {gir}",
            "categoria": categoria_app(cat), "genere": "F" if re.search(r"FEMMINIL", cat, re.I) else "M",
            "stagione": "2026/27", "comitato": f"LND FVG — {'Comitato Regionale' if comitato == 'Regionale' else 'Delegazione di ' + comitato}",
            "fonte": max(g["fonte"] for g in gare), "aggiornato": max(g["pubbl"] for g in gare),
            "giornata": max(g["g_eff"] for g in gare), "calcolata": True,
            "classifica": classifica, "partite": partite}


def main():
    prova, tutto = "--prova" in sys.argv, "--tutto" in sys.argv
    oggi = dt.date.today().isoformat()
    stato = {"letti": [], "gare": []} if tutto or not os.path.exists(STATO) else json.load(open(STATO))
    letti = set(stato["letti"])
    gare = {(tuple(g["k"]), g["giornata"], norm(g["casa"]), norm(g["ospite"])): g for g in stato["gare"]}
    elenco = elenco_pdf()
    print(f"comunicati in archivio: {len(elenco)}, già letti: {len(letti & {x['source_url'] for x in elenco})}")
    for x in elenco:
        u = x["source_url"]
        if u in letti:
            continue
        try:
            comitato, righe = leggi_cu(u)
        except Exception as e:
            print(f"  ! {u}: {e}"); continue
        for cat, gir, n, ar, data, casa, osp, gc, go, _ in righe:
            k = (comitato, cat.upper(), gir)
            gare[(k, (n, ar), norm(casa), norm(osp))] = {"k": list(k), "giornata": n, "ar": ar, "data": data, "casa": casa,
                                                          "ospite": osp, "gc": gc, "go": go, "fonte": u, "pubbl": x["date"][:10]}
        letti.add(u)
        if righe:
            print(f"{u.rsplit('/', 1)[-1]} ({comitato}): {len(righe)} risultati")
    # gironi
    per_k = {}
    for g in gare.values():
        per_k.setdefault(tuple(g["k"]), []).append(g)
    # giornate di ritorno: numero andata = squadre - 1 (pari) o squadre (dispari)
    for k, gs in per_k.items():
        n_sq = len({g["casa"] for g in gs} | {g["ospite"] for g in gs})
        andata = n_sq - 1 if n_sq % 2 == 0 else n_sq
        for g in gs:
            g["g_eff"] = g["giornata"] + (andata if g.get("ar") == "R" else 0)
    soc = json.load(open(SOC))
    soc = soc if isinstance(soc, list) else soc.get("societa", [])
    calcio_soc = [s for s in soc if s.get("sport") in ("calcio", "calcio5") or "calcio" in (s.get("altri_sport") or [])]
    per_nome = {}
    for s in calcio_soc:
        for nome in [s.get("nome", "")] + (s.get("alias") or []):
            per_nome.setdefault(norm(re.sub(r"\b(A\.?S\.?D\.?|S\.?S\.?D\.?|A\.?C\.?|U\.?S\.?|S\.?R\.?L\.?|A R L|ARL)\b", " ", nome)), set()).add(s["id"])
    alias = json.load(open(ALIAS)) if os.path.exists(ALIAS) else {}
    alias_n = {norm(k): v for k, v in alias.items()}

    def ids_di(nome):
        if norm(nome) in alias_n:
            return alias_n[norm(nome)]
        c = per_nome.get(norm(re.sub(r"\b(A\.?S\.?D\.?|S\.?S\.?D\.?|A\.?C\.?|U\.?S\.?|S\.?R\.?L\.?|A R L|ARL)\b", " ", nome)), set())
        return next(iter(c)) if len(c) == 1 else None

    nuovi = []
    for k, gs in sorted(per_k.items()):
        if len(gs) < 3:
            continue
        g = costruisci(k, gs, k[0], ids_di, oggi)
        pref = "" if k[0] == "Regionale" else slugify(k[0])[:3] + "-"
        g["gid"] = f"{g['sport']}-{pref}{slugify(k[1])}-{k[2].lower()}"
        nuovi.append(g)
        print(f"  {g['gid']}: {len(g['classifica'])} squadre, {len(gs)} gare, giornata {g['giornata']}, "
              f"abbinate {sum(1 for r in g['classifica'] if r['id'])}")
    print(f"gironi ricostruiti: {len(nuovi)}")
    if prova:
        print("prova: nessun file scritto"); return
    data = json.load(open(RIS))
    vecchi = {g["gid"]: g for g in data}
    nuovi_gid = {n["gid"] for n in nuovi}
    # i gironi delle delegazioni caricati a mano (es. calcio-seconda-categoria-b) sono sostituiti da quelli automatici
    sostituiti = {g for g in vecchi if vecchi[g]["sport"] in ("calcio", "calcio5") and any(n.endswith("-" + g.split("-", 1)[1]) and n != g for n in nuovi_gid)}
    tenuti = [g for g in data if g["gid"] not in nuovi_gid and g["gid"] not in sostituiti]
    for n in nuovi:
        o = vecchi.get(n["gid"]) or next((vecchi[v] for v in sostituiti if n["gid"].endswith("-" + v.split("-", 1)[1])), None)
        if o and len(n["classifica"]) < len(o.get("classifica") or []):
            print(f"  {n['gid']}: meno squadre del precedente, tenuto il vecchio"); tenuti.append(o); continue
        tenuti.append(n)
    json.dump(tenuti, open(RIS, "w"), ensure_ascii=False, separators=(",", ":"))
    stato = {"letti": sorted(letti), "gare": list(gare.values())}
    json.dump(stato, open(STATO, "w"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
