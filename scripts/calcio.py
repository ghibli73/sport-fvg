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


def compatto(s):
    return norm(s).replace(" ", "")


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
    """Testo riga per riga; nelle pagine a due colonne (es. girone A a sinistra, girone B a destra) le due colonne
    vengono lette una dopo l'altra, mentre i titoli a tutta larghezza restano al loro posto."""
    import pdfplumber
    time.sleep(0.8)
    r = S.get(url, timeout=90); r.raise_for_status()
    out = []
    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        for page in pdf.pages:
            mid = page.width / 2
            linee = {}
            for w in page.extract_words(use_text_flow=False, keep_blank_chars=False):
                linee.setdefault(round(w["top"] / 2.5), []).append(w)
            L, R = [], []
            def flush():
                out.extend(L); out.extend(R); L.clear(); R.clear()
            for k in sorted(linee):
                ws = sorted(linee[k], key=lambda w: w["x0"])
                attraversa = any(w["x0"] < mid - 2 and w["x1"] > mid + 2 for w in ws)
                sx = [w["text"] for w in ws if w["x1"] <= mid + 2]
                dx = [w["text"] for w in ws if w["x0"] >= mid - 2]
                if attraversa:
                    flush(); out.append(" ".join(w["text"] for w in ws))
                else:
                    if sx: L.append(" ".join(sx))
                    if dx: R.append(" ".join(dx))
            flush()
    return [l.strip() for l in out if l.strip()]


RX_DELEG = re.compile(r"DELEGAZION[EI][^\n]{0,50}?(UDINE|PORDENONE|TRIESTE|GORIZIA|TOLMEZZO)", re.I)
PREF_FILE = {"ts": "Trieste", "pn": "Pordenone", "go": "Gorizia", "ud": "Udine", "tol": "Tolmezzo"}
RX_DATA = re.compile(r"RISULTATI UFFICIALI GARE DEL (\d{2})/(\d{2})/(\d{4})", re.I)
RX_GIR = re.compile(r"^GIRONE\s+([A-Z0-9]{1,3})\s*-\s*(\d{1,2})\s*Giornata\s*-\s*([AR])", re.I)
RX_RIS = re.compile(r"^(?:\(\d+\)\s*)?(.+?)\s+-\s+(.+?)\s+(\d{1,2})\s*-\s*(\d{1,2})\s*$")
RX_DISP = re.compile(r"^\((\d+)\)\s*-\s*disputata il (\d{2})/(\d{2})/(\d{4})", re.I)
RX_CAT_OK = re.compile(r"ECCELLENZA|PROMOZIONE|PRIMACATEGORIA|SECONDACATEGORIA|TERZACATEGORIA|UNDER\d\d|JUNIORES|ALLIEVI|GIOVANISSIMI|CALCIOA(5|CINQUE)|SERIEC[12]|SERIED|FEMMINILE|AMATORI")
RX_CAT_NO = re.compile(r"COPPA|TORNEO|TROFEO|MEMORIAL|FASEFINALE|SPAREGGI|PLAYOFF|PLAYOUT")
NON_CATEG = re.compile(r"RISULTATI|Si trascrivono|GIRONE|Pag\.|COMUNICATO|^\(|DECISIONI|GIUDICE", re.I)


def leggi_cu(url):
    """-> comitato, [(categoria, girone, giornata, AR, data, casa, ospite, gc, go, n_nota)]"""
    righe = pdf_righe(url)
    testa = " ".join(righe[:40])
    m = RX_DELEG.search(testa)
    f = url.rsplit("/", 1)[-1].lower()
    pf = re.match(r"^(ts|pn|go|ud|tol)[_-]", f)
    comitato = PREF_FILE[pf.group(1)] if pf else m.group(1).title() if m else "Regionale"
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
            j, cat = i - 1, None
            while j >= 0 and i - j <= 3:
                comp = re.sub(r"[^A-Z0-9]", "", strip_acc(righe[j].upper()))
                if RX_CAT_OK.search(comp):
                    cat = None if RX_CAT_NO.search(comp) else canon_cat(righe[j])
                    break
                j -= 1
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


def canon_cat(l):
    """Ricompone le parole spezzate dal PDF: confronta il testo senza spazi con un elenco di parole note."""
    comp = re.sub(r"[^A-Z0-9]", "", strip_acc(l.upper()))
    parole = ["ECCELLENZA", "PROMOZIONE", "PRIMA", "SECONDA", "TERZA", "CATEGORIA", "UNDER", "JUNIORES", "ALLIEVI",
              "GIOVANISSIMI", "REGIONALI", "REGIONALE", "PROVINCIALI", "PROVINCIALE", "CALCIO", "CINQUE", "FEMMINILE",
              "SERIE", "AMATORI", "CAMPIONATO", "PROV", "TRIESTE", "UDINE", "PORDENONE", "GORIZIA", "TOLMEZZO", "ELITE", "FASCIA"]
    out, i = [], 0
    while i < len(comp):
        for p in sorted(parole, key=len, reverse=True):
            if comp.startswith(p, i):
                out.append(p); i += len(p); break
        else:
            m = re.match(r"\d+|[A-Z]", comp[i:])
            if out and re.fullmatch(r"[A-Z]", m.group(0)) and not re.fullmatch(r"\d+", out[-1]) and out[-1] not in parole:
                out[-1] += m.group(0)
            else:
                out.append(m.group(0))
            i += len(m.group(0))
    t = " ".join(out)
    t = re.sub(r"\bUNDER (\d\d)\b", r"UNDER \1", re.sub(r"UNDER(\d\d)", r"UNDER \1", t))
    t = re.sub(r"\bCALCIO A (5|CINQUE)\b", "CALCIO A 5", t.replace("CALCIO A5", "CALCIO A 5"))
    t = re.sub(r"\bU (\d\d)\b", r"U\1", t)
    return t


def classifica_cat(cat):
    """Nome standard della categoria (stessa chiave anche se il comunicato la scrive in modi diversi), o None."""
    c = " " + cat.upper() + " "
    fem = " femminile" if "FEMMINIL" in c else ""
    if re.search(r"CALCIO A 5|CINQUE|FUTSAL", c):
        m = re.search(r"SERIE (C1|C2|D)", c)
        base = f"Calcio a 5 Serie {m.group(1)}" if m else "Calcio a 5 regionale"
        eta = re.search(r"\bU(?:NDER)?\s?(\d\d)\b", c)
        return base + (f" Under {eta.group(1)}" if eta else "") + fem
    for parola, nome in (("ECCELLENZA", "Eccellenza"), ("PROMOZIONE", "Promozione"), ("PRIMA CATEGORIA", "Prima Categoria"),
                         ("SECONDA CATEGORIA", "Seconda Categoria"), ("TERZA CATEGORIA", "Terza Categoria")):
        if parola in c and not re.search(r"\bU(?:NDER)?\s?\d\d\b|JUNIORES|ALLIEVI|GIOVANISSIMI", c):
            return nome + fem
    eta = re.search(r"\bU(?:NDER)?\s?(\d\d)\b", c)
    eta = eta.group(1) if eta else "19" if "JUNIORES" in c else "17" if "ALLIEVI" in c else "15" if "GIOVANISSIMI" in c else None
    if not eta:
        return ("Serie C femminile" if "SERIE C" in c and fem else None)
    ambito = " élite" if "ELITE" in c else " regionali" if "REGIONAL" in c else " provinciali" if re.search(r"PROVINCIAL|PROV ", c) else ""
    return f"Under {eta}{ambito}{fem}"


def calcio5(cat):
    return bool(re.search(r"CALCIO A (5|CINQUE)|C5|FUTSAL", cat, re.I))


def categoria_app(cat):
    c = cat.upper()
    m = re.search(r"\bU(?:NDER)?\s*(\d{2})\b", c)
    if m: return f"Under {m.group(1)}"
    if "JUNIORES" in c: return "Under 19"
    if "ALLIEVI" in c: return "Under 17"
    if "GIOVANISSIMI" in c: return "Under 15"
    return "Prima squadra"


def unifica_nomi(gare):
    from collections import Counter
    c = Counter()
    for g in gare:
        c[g["casa"]] += 1; c[g["ospite"]] += 1
    scelto = {}
    tolti = lambda x: re.sub(r"^(ASD|SSD|AC|US|USD|APD|POL|ACD)|(ASD|SSD|ARL|SRL|SSDARL|AC)$", "", x)
    forme = {}
    for nome, _ in c.most_common():
        k = compatto(nome)
        # varianti dello stesso nome: con/senza sigla societaria, o una che è l'inizio dell'altra
        uguale = next((f for f in forme if tolti(f) == tolti(k) or (len(k) >= 6 and len(f) >= 6 and (f.startswith(k) or k.startswith(f)))), None)
        if uguale:
            scelto[k] = forme[uguale]
        else:
            forme[k] = nome; scelto[k] = nome
    for g in gare:
        g["casa"] = scelto[compatto(g["casa"])]; g["ospite"] = scelto[compatto(g["ospite"])]


def costruisci(key, gare, comitato, ids_di, oggi):
    cat, gir = key[1], key[2]
    unifica_nomi(gare)
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
    return {"gid": "", "sport": "calcio5" if calcio5(cat) else "calcio", "girone": f"{cat} — girone {gir}",
            "categoria": categoria_app(cat), "genere": "F" if "femminile" in cat else "M",
            "stagione": "2026/27", "comitato": f"LND FVG — {'Comitato Regionale' if comitato == 'Regionale' else 'Delegazione di ' + comitato}",
            "fonte": max(g["fonte"] for g in gare), "aggiornato": max(g["pubbl"] for g in gare),
            "giornata": max(g["g_eff"] for g in gare), "calcolata": True,
            "classifica": classifica, "partite": partite}


def main():
    prova, tutto = "--prova" in sys.argv, "--tutto" in sys.argv
    oggi = dt.date.today().isoformat()
    stato = {"letti": [], "gare": []} if tutto or not os.path.exists(STATO) else json.load(open(STATO))
    letti = set(stato["letti"])
    gare = {(tuple(g["k"]), (g["giornata"], g.get("ar")), compatto(g["casa"]), compatto(g["ospite"])): g for g in stato["gare"]}
    # punto di partenza: le gare già presenti nell'app (l'archivio online non contiene tutti i comunicati vecchi)
    if not stato["gare"]:
        for g in json.load(open(RIS)):
            if g["sport"] not in ("calcio", "calcio5"):
                continue
            m = re.match(r"(.+?) — girone ([A-Z0-9]+)$", g["girone"])
            if not m:
                continue
            com = "Regionale" if "Regionale" in g["comitato"] else g["comitato"].rsplit(" ", 1)[-1]
            k = [com, classifica_cat(canon_cat(m.group(1))), m.group(2)]
            for p in g["partite"]:
                if not re.fullmatch(r"\d+-\d+", p.get("risultato") or ""):
                    continue
                a, b = map(int, p["risultato"].split("-"))
                gare[(tuple(k), (p["giornata"], "A"), compatto(p["casa"]), compatto(p["ospite"]))] = {
                    "k": k, "giornata": p["giornata"], "ar": "A", "data": p.get("data") or "", "casa": p["casa"],
                    "ospite": p["ospite"], "gc": a, "go": b, "fonte": g["fonte"], "pubbl": g["aggiornato"]}
        print(f"gare di partenza dai dati attuali: {len(gare)}")
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
            cs = classifica_cat(cat)
            if not cs:
                continue
            if cs.startswith("Under") and not re.search(r"regionali|provinciali|élite", cs):
                cs = cs.replace(f"Under {cs.split()[1]}", f"Under {cs.split()[1]} " + ("regionali" if comitato == "Regionale" else "provinciali"), 1)
            k = (comitato, cs, gir)
            gare[(k, (n, ar), compatto(casa), compatto(osp))] = {"k": list(k), "giornata": n, "ar": ar, "data": data, "casa": casa,
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
    alias_n = {compatto(k): v for k, v in alias.items()}

    def ids_di(nome):
        if compatto(nome) in alias_n:
            return alias_n[compatto(nome)]
        c = per_nome.get(norm(re.sub(r"\b(A\.?S\.?D\.?|S\.?S\.?D\.?|A\.?C\.?|U\.?S\.?|S\.?R\.?L\.?|A R L|ARL)\b", " ", nome)), set())
        return next(iter(c)) if len(c) == 1 else None

    nuovi = []
    from collections import Counter
    for k, gs in sorted(per_k.items()):
        if k[0] == "Regionale" and "provinciali" in k[1]:
            print(f"  scartato {k}: categoria provinciale senza delegazione riconosciuta"); continue
        n_sq = len({compatto(g["casa"]) for g in gs} | {compatto(g["ospite"]) for g in gs})
        doppie = [x for x, c in Counter((g["g_eff"], compatto(t)) for g in gs for t in (g["casa"], g["ospite"])).items() if c > 1]
        if len(gs) < 4 or n_sq < 4 or n_sq > 22 or doppie:
            print(f"  scartato {k}: {n_sq} squadre, {len(gs)} gare, {len(doppie)} squadre doppie nella stessa giornata"); continue
        g = costruisci(k, gs, k[0], ids_di, oggi)
        pref = "" if k[0] == "Regionale" else slugify(k[0])[:3] + "-"
        g["gid"] = f"{g['sport']}-{pref}{slugify(k[1])}-{k[2].lower()}"
        nuovi.append(g)
        if "--diag" in sys.argv:
            print("     ", " | ".join(r["squadra"] for r in g["classifica"]))
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
