"""Aggiornamento automatico del CALCIO e CALCIO A 5 dai Comunicati Ufficiali LND FVG (nessuna intelligenza artificiale).

Legge tutti i PDF dei Comunicati Ufficiali (Comitato Regionale e Delegazioni) pubblicati nell'archivio WordPress
di friuliveneziagiulia.lnd.it, ne estrae la sezione "RISULTATI GARE" e ricostruisce ogni girone:
  categoria (es. ECCELLENZA, UNDER 17 ALLIEVI REGIONALI), girone, giornata, casa, ospite, gol.
Classifica calcolata: 3 punti vittoria, 1 pareggio; a parità differenza reti, poi gol fatti (gli scontri diretti
non sono considerati: lo dice la nota del girone).
Ogni girone diventa "calcio-<slug>" in data/risultati.json; i nomi squadra sono abbinati alle società di
data/data.json con config/calcio_alias.json (alias certi) o per nome identico.
Calendario: le partite future (giornata, data, ora, campo) vengono dai calendari ufficiali LND e dalle
"MODIFICHE AL PROGRAMMA GARE" dei comunicati: vedi scripts/calcio_calendari.py e pipeline/agenti/calendari.md.
Uso: python scripts/calcio.py [--tutto] [--prova] [--diag]
     --prova  non scrive config né data/risultati.json: il risultato va in /tmp/risultati_prova.json
"""
import io, json, os, re, sys, time, datetime as dt, unicodedata
import requests
from abbinamenti import applica_comuni  # scripts/abbinamenti.py
import calcio_calendari as CAL
import tempo_reale as TR  # scripts/tempo_reale.py

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
SOC = os.path.join(ROOT, "data", "data.json")
STATO = os.path.join(ROOT, "config", "calcio_stato.json")
ALIAS = os.path.join(ROOT, "config", "calcio_alias.json")
BASE = "https://friuliveneziagiulia.lnd.it"
INIZIO = "2026-08-01T00:00:00"
PROVA = "/tmp/risultati_prova.json"
S = requests.Session()
S.headers["User-Agent"] = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (app non ufficiale di consultazione)")


def strip_acc(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s):
    s = strip_acc((s or "").upper()).replace("’", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def compatto(s):
    return norm(s).replace(" ", "")


def chiave(s):
    """Nome per la chiave di una gara: senza spazi né sigla societaria iniziale/finale, così la stessa gara letta
    con "POLISPORTIVA TAMAI" o "POLISPORTIVA TAMAI ASD" (o con un nome già unificato nello stato) è una sola."""
    return re.sub(r"^(ASD|SSD|AC|US|USD|APD|POL|ACD)|(ASD|SSD|ARL|SRL|SSDARL|AC)$", "", compatto(s))


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


_pdf = {}


def scarica(url):
    """Byte del PDF, scaricato una volta sola per esecuzione (serve sia ai risultati sia alle variazioni)."""
    if url not in _pdf:
        time.sleep(1.2)
        r = S.get(url, timeout=90); r.raise_for_status()
        _pdf.clear()  # basta ricordare l'ultimo
        _pdf[url] = r.content
    return _pdf[url]


def comitato_cu(url, righe):
    testa = " ".join(righe[:40])
    m = RX_DELEG.search(testa)
    pf = re.match(r"^(ts|pn|go|ud|tol)[_-]", url.rsplit("/", 1)[-1].lower())
    return PREF_FILE[pf.group(1)] if pf else m.group(1).title() if m else "Regionale"


def pdf_righe(url):
    """Testo riga per riga; nelle pagine a due colonne (es. girone A a sinistra, girone B a destra) le due colonne
    vengono lette una dopo l'altra, mentre i titoli a tutta larghezza restano al loro posto."""
    import pdfplumber
    out = []
    with pdfplumber.open(io.BytesIO(scarica(url))) as pdf:
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
# "GARE DEL 15/11/2026" ma anche "GARE DEL L'8/11/2026" / "DELL'8/11/2026" (giorno con una cifra)
RX_DATA = re.compile(r"RISULTATI UFFICIALI GARE DEL\S*\s*(?:L\s*['’]\s*)?(\d{1,2})/(\d{1,2})/(\d{4})", re.I)
RX_GIR = re.compile(r"^GIRONE\s+([A-Z0-9]{1,3})\s*-\s*(\d{1,2})\s*Giornata\s*-\s*([AR])", re.I)
RX_RIS = re.compile(r"^(?:\(\d+\)\s*)?(.+?\s+-\s+.+?)\s+(\d{1,2})\s*-\s*(\d{1,2})\s*$")
NOTI = set()  # nomi squadra già conosciuti (forma compatta), per dividere "A - B - C" nel punto giusto


def dividi(testo):
    parti = re.split(r"\s+-\s+", testo)
    scelte = []
    for i in range(1, len(parti)):
        a, b = " - ".join(parti[:i]), " - ".join(parti[i:])
        scelte.append(((compatto(a) in NOTI) + (compatto(b) in NOTI), -abs(len(a) - len(b)), a, b))
    sc = max(scelte)
    return sc[2].strip(), sc[3].strip()
RX_DISP = re.compile(r"^\((\d+)\)\s*-\s*disputata il (\d{2})/(\d{2})/(\d{4})", re.I)
RX_CAT_OK = re.compile(r"ECCELLENZA|PROMOZIONE|PRIMACATEGORIA|SECONDACATEGORIA|TERZACATEGORIA|UNDER\d\d|JUNIORES|ALLIEVI|GIOVANISSIMI|CALCIOA(5|CINQUE)|SERIEC[12]|SERIED|FEMMINILE|AMATORI")
RX_CAT_NO = re.compile(r"COPPA|TORNEO|TROFEO|MEMORIAL|FASEFINALE|SPAREGGI|PLAYOFF|PLAYOUT")
# titoli di attività che non sono campionati gestiti dall'app: chiudono la categoria precedente
RX_CAT_ALTRO = re.compile(r"ESORDIENTI|PULCINI|PICCOLIAMICI|PRIMICALCI|AMICHEVOL")
NON_CATEG = re.compile(r"RISULTATI|Si trascrivono|GIRONE|Pag\.|COMUNICATO|^\(|DECISIONI|GIUDICE", re.I)


def leggi_cu(url):
    """-> comitato, [(categoria, girone, giornata, AR, data, casa, ospite, gc, go, n_nota)]"""
    righe = pdf_righe(url)
    comitato = comitato_cu(url, righe)
    out, cat, gir, data, in_ris = [], None, None, None, False
    note_disp = {}  # id(riga) -> nota già applicata
    for i, l in enumerate(righe):
        if l.upper().startswith("RISULTATI GARE"):
            in_ris = True; continue
        if not in_ris:
            continue
        if re.match(r"^(DECISIONI|GIUSTIZIA SPORTIVA|PROVVEDIMENTI|ERRATA CORRIGE|CALENDARIO|PROGRAMMA GARE)", l, re.I):
            in_ris = False; continue
        md = RX_DATA.search(l)
        if md:
            data = f"{md.group(3)}-{int(md.group(2)):02d}-{int(md.group(1)):02d}"
            gir = None  # ogni blocco di data ha la sua riga "GIRONE ..."; mai riusare il girone del blocco precedente
            # la categoria è la riga precedente (es. "UNDER 17 ALLIEVI REGIONALI"). Se nelle 3 righe prima non c'è
            # nessun titolo, è un secondo blocco di data della stessa categoria (es. recuperi della giornata
            # precedente seguiti dalla giornata corrente): la categoria resta quella del blocco prima.
            j, trovata = i - 1, False
            while j >= 0 and i - j <= 3:
                comp = re.sub(r"[^A-Z0-9]", "", strip_acc(righe[j].upper()))
                if RX_CAT_OK.search(comp):
                    cat = None if RX_CAT_NO.search(comp) else canon_cat(righe[j]); trovata = True
                    break
                if RX_CAT_NO.search(comp) or RX_CAT_ALTRO.search(comp):
                    cat = None; trovata = True
                    break
                j -= 1
            if not trovata:
                # si continua la categoria precedente solo se subito prima c'era un blocco di gare
                vicino = righe[max(0, i - 5):i]
                if not any(RX_GIR.match(x) or RX_RIS.match(x) or RX_DISP.match(x) for x in vicino):
                    cat = None
            continue
        mg = RX_GIR.match(l)
        if mg:
            gir = (mg.group(1).upper(), int(mg.group(2)), mg.group(3).upper()); continue
        mn = RX_DISP.match(l)
        if mn:
            # la nota "(1) - disputata il ..." vale per le gare del SUO blocco, scritte subito prima: i numeri
            # delle note ripartono da (1) in ogni blocco, quindi non si può usare un'unica tabella per tutto il CU
            for r in out:
                if r[9] == mn.group(1) and r[9] not in note_disp.get(id(r), ()):
                    r[4] = f"{mn.group(4)}-{mn.group(3)}-{mn.group(2)}"; note_disp[id(r)] = (r[9],)
            continue
        mr = RX_RIS.match(l)
        if mr and cat and gir and data:
            nota = re.match(r"^\((\d+)\)", l)
            casa, osp = dividi(mr.group(1))
            out.append([cat, gir[0], gir[1], gir[2], data, casa, osp,
                        int(mr.group(2)), int(mr.group(3)), nota.group(1) if nota else None])
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
        uguale = next((f for f in forme if tolti(f) == tolti(k)), None)
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
    prima = min(g["g_eff"] for g in gare)
    giorn = sorted({g["g_eff"] for g in gare})
    mancano = [n for n in range(1, max(giorn) + 1) if n not in giorn]
    nota = ""
    if prima > 1 or mancano:
        nota = (f"risultati disponibili dalla giornata {prima}" if prima > 1 else "") + \
               (("; " if prima > 1 else "") + "mancano le giornate " + ", ".join(map(str, [n for n in mancano if n >= prima])) if [n for n in mancano if n >= prima] else "") + \
               ". I comunicati più vecchi non sono nell'archivio online della LND."
    out_nota = {"nota_parziale": nota} if nota else {}
    return {**out_nota, "gid": "", "sport": "calcio5" if calcio5(cat) else "calcio", "girone": f"{cat} — girone {gir}",
            "categoria": categoria_app(cat), "genere": "F" if "femminile" in cat else "M",
            "stagione": "2026/27", "comitato": f"LND FVG — {'Comitato Regionale' if comitato == 'Regionale' else 'Delegazione di ' + comitato}",
            "fonte": max(g["fonte"] for g in gare), "aggiornato": max(g["pubbl"] for g in gare),
            "giornata": max(g["g_eff"] for g in gare), "calcolata": True,
            "classifica": classifica, "partite": partite, "auto": "lnd"}


def aggiungi_futuri(g, k, n_sq, cal_stato, ids_di, oggi):
    """Aggiunge al girone costruito le partite future del calendario ufficiale, con le variazioni dei comunicati.
    Una partita futura che metterebbe una squadra due volte nella stessa giornata viene scartata."""
    from collections import Counter
    nomi = [r["squadra"] for r in g["classifica"]]
    giocate = {(compatto(p["casa"]), compatto(p["ospite"])) for p in g["partite"] if p.get("risultato")}
    andata = n_sq - 1 if n_sq % 2 == 0 else n_sq
    try:
        fut, var = CAL.futuri(sys.modules[__name__], k, nomi, giocate, andata, cal_stato, oggi)
    except Exception as e:
        print(f"  {g['gid']}: calendario non applicato ({e})"); return
    occupate = Counter((p["giornata"], compatto(t)) for p in g["partite"] for t in (p["casa"], p["ospite"]))
    aggiunte = scartate = 0
    for v in fut:
        if occupate[(v["giornata"], compatto(v["casa"]))] or occupate[(v["giornata"], compatto(v["ospite"]))]:
            scartate += 1; continue
        occupate[(v["giornata"], compatto(v["casa"]))] += 1; occupate[(v["giornata"], compatto(v["ospite"]))] += 1
        p = {"giornata": v["giornata"], "data": v["data"]}
        if v.get("ora"): p["ora"] = v["ora"]
        p.update(casa=v["casa"], ospite=v["ospite"], id_casa=ids_di(v["casa"]), id_ospite=ids_di(v["ospite"]), risultato="")
        if v.get("campo"): p["campo"] = v["campo"]
        g["partite"].append(p); aggiunte += 1
    if aggiunte or var:
        print(f"  {g['gid']}: partite future {aggiunte}" + (f", scartate {scartate}" if scartate else "") + f", variazioni applicate {var}")


def main():
    prova, tutto = "--prova" in sys.argv, "--tutto" in sys.argv
    oggi = dt.date.today().isoformat()
    stato = {"letti": [], "gare": []} if tutto or not os.path.exists(STATO) else json.load(open(STATO))
    letti = set(stato["letti"])
    gare = {(tuple(g["k"]), (g["giornata"], g.get("ar")), chiave(g["casa"]), chiave(g["ospite"])): g for g in stato["gare"]}
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
                if not re.fullmatch(r"\d+-\d+", p.get("risultato") or "") or p.get("provvisorio"):
                    continue  # i risultati provvisori (Quadro gare LND) non sono una fonte del Comunicato
                a, b = map(int, p["risultato"].split("-"))
                gare[(tuple(k), (p["giornata"], "A"), chiave(p["casa"]), chiave(p["ospite"]))] = {
                    "k": k, "giornata": p["giornata"], "ar": "A", "data": p.get("data") or "", "casa": p["casa"],
                    "ospite": p["ospite"], "gc": a, "go": b, "fonte": g["fonte"], "pubbl": g["aggiornato"]}
        print(f"gare di partenza dai dati attuali: {len(gare)}")
    for g in gare.values():
        NOTI.add(compatto(g["casa"])); NOTI.add(compatto(g["ospite"]))
    NOTI.update(compatto(k) for k in (json.load(open(ALIAS)) if os.path.exists(ALIAS) else {}))
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
            gare[(k, (n, ar), chiave(casa), chiave(osp))] = {"k": list(k), "giornata": n, "ar": ar, "data": data, "casa": casa,
                                                          "ospite": osp, "gc": gc, "go": go, "fonte": u, "pubbl": x["date"][:10]}
        letti.add(u)
        if righe:
            print(f"{u.rsplit('/', 1)[-1]} ({comitato}): {len(righe)} risultati")
    # calendari ufficiali e variazioni (scripts/calcio_calendari.py)
    cal_stato = CAL.carica()
    try:
        CAL.leggi_fonti(sys.modules[__name__], elenco, cal_stato, oggi)
    except Exception as e:
        print(f"calendari/variazioni: lettura non riuscita ({e})")
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
        # copie: unifica_nomi cambia i nomi solo nel girone costruito, non nelle gare salvate in calcio_stato.json
        # (altrimenti una scelta sbagliata, es. "CAMPANELLE" -> "CAMPANELLE sq.B", resterebbe per sempre nello stato)
        g = costruisci(k, [dict(x) for x in gs], k[0], ids_di, oggi)
        if any(c > 1 for c in Counter((p["giornata"], t) for p in g["partite"] for t in (p["casa"], p["ospite"])).values()):
            print(f"  scartato {k}: squadre doppie nella stessa giornata dopo l'unificazione dei nomi"); continue
        pref = "" if k[0] == "Regionale" else slugify(k[0])[:3] + "-"
        g["gid"] = f"{g['sport']}-{pref}{slugify(k[1])}-{k[2].lower()}"
        aggiungi_futuri(g, k, n_sq, cal_stato, ids_di, oggi)
        nuovi.append(g)
        if "--diag" in sys.argv:
            print("     ", " | ".join(r["squadra"] for r in g["classifica"]))
        print(f"  {g['gid']}: {len(g['classifica'])} squadre, {len(gs)} gare, giornata {g['giornata']}, "
              f"abbinate {sum(1 for r in g['classifica'] if r['id'])}")
    print(f"gironi ricostruiti: {len(nuovi)}; partite future da calendari e variazioni: "
          f"{sum(1 for g in nuovi for p in g['partite'] if not p.get('risultato'))} in "
          f"{sum(1 for g in nuovi if any(not p.get('risultato') for p in g['partite']))} gironi")
    data = json.load(open(RIS))
    vecchi = {g["gid"]: g for g in data}
    nuovi_gid = {n["gid"] for n in nuovi}
    # i gironi delle delegazioni caricati a mano (es. calcio-seconda-categoria-b) sono sostituiti da quelli automatici
    sostituiti = {g for g in vecchi if vecchi[g]["sport"] in ("calcio", "calcio5") and any(n.endswith("-" + g.split("-", 1)[1]) and n != g for n in nuovi_gid)}
    # un girone creato in automatico che oggi non supera più i controlli viene tolto
    tenuti = [g for g in data if g["gid"] not in nuovi_gid and g["gid"] not in sostituiti and g.get("auto") != "lnd"]
    for n in nuovi:
        o = vecchi.get(n["gid"]) or next((vecchi[v] for v in sostituiti if n["gid"].endswith("-" + v.split("-", 1)[1])), None)
        if o and len(n["classifica"]) < len(o.get("classifica") or []):
            print(f"  {n['gid']}: meno squadre del precedente, tenuto il vecchio"); tenuti.append(o); continue
        if o and not any(not p.get("risultato") for p in n["partite"]):
            # senza calendario ufficiale letto restano le gare future già note (giornata successiva)
            n["partite"] += [p for p in o.get("partite", []) if not p.get("risultato") and (p.get("giornata") or 0) > n["giornata"]]
        tenuti.append(n)
    applica_comuni(tenuti)  # comune delle squadre senza id (config/squadre_comune.json)
    # risultati del Quadro gare LND non ancora nel Comunicato (giro rapido): restano "provvisorio" finché il CU non li riporta
    print("provvisori applicati:", TR.applica(tenuti, solo_sport={"calcio", "calcio5"}))
    if prova:
        json.dump(tenuti, open(PROVA, "w"), ensure_ascii=False, separators=(",", ":"))
        print("prova: config e data/risultati.json non modificati, risultato in", PROVA); return
    json.dump(tenuti, open(RIS, "w"), ensure_ascii=False, separators=(",", ":"))
    CAL.salva(cal_stato)
    stato = {"letti": sorted(letti), "gare": list(gare.values())}
    json.dump(stato, open(STATO, "w"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
