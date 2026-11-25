"""Aggiornamento automatico del BASKET dai documenti ufficiali FIP (nessuna intelligenza artificiale).

Per ogni girone in config/basket/<slug>.json (calendario + abbinamenti squadra -> società):
  1. completa il calendario leggendo il PDF "Calendario Definitivo" del girone (campo id_fonte), se è un PDF;
  2. legge le "Omologazione gare" pubblicate dal Comitato (archivio WordPress del sito FIP regionale) non ancora lette
     e assegna i punteggi per numero gara;
  3. ricalcola la classifica (2 punti a vittoria; a parità differenza canestri, poi punti fatti) e scrive il girone
     in data/risultati.json con tutte le gare giocate e la giornata successiva.
Le omologazioni lette sono ricordate in config/basket_stato.json, così ogni esecuzione legge solo le nuove.
Uso: python scripts/basket.py [--tutto] [--solo <slug>] [--prova]
     --tutto  rilegge tutte le omologazioni della stagione;  --prova  non scrive nulla, stampa solo cosa farebbe.
"""
import io, json, os, re, sys, time, glob, datetime as dt
import requests
from abbinamenti import applica_comuni  # scripts/abbinamenti.py

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DIR = os.path.join(ROOT, "config", "basket")
STATO = os.path.join(ROOT, "config", "basket_stato.json")
RIS = os.path.join(ROOT, "data", "risultati.json")
ARCHIVI = {  # comitato -> (archivio media WordPress, filtro sul nome del file)
    "fvg": ("https://friuliveneziagiulia.fip.it", None),
    "veneto": ("https://veneto.fip.it", r"Interregionale"),  # dal Veneto solo la B Interregionale (girone con squadre FVG)
}
INIZIO = "2026-08-15T00:00:00"
S = requests.Session()
S.headers["User-Agent"] = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (app non ufficiale di consultazione)")
PAUSA = 1.0


def get(url, **kw):
    time.sleep(PAUSA)
    r = S.get(url, timeout=60, **kw)
    r.raise_for_status()
    return r


def pdf_righe(url):
    import pdfplumber
    with pdfplumber.open(io.BytesIO(get(url).content)) as pdf:
        return [l.strip() for p in pdf.pages for l in (p.extract_text() or "").splitlines() if l.strip()]


def norm(s):
    s = (s or "").upper().replace("’", "'").replace("''", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9' ]", " ", s)).strip()


def toks(s):
    return [t for t in norm(s).replace("'", " ").split() if t]


# ---------------------------------------------------------------- calendario
RX_CAL = re.compile(r"^(\d{1,5}) (.+?) (Lun|Mar|Mer|Gio|Ven|Sab|Dom) (\d{2})/(\d{2})/(\d{4}) (\d{1,2}[:.]\d{2})\s*$")
RX_GIORN = re.compile(r"^(\d{1,2}) Giornata di (andata|ritorno)", re.I)
RX_CAMPO = re.compile(r" - \(([A-Z' ]+)\)\s*$|^\(?[A-Z' ]+\)$")


def dividi_squadre(testo, squadre):
    """testo = 'SQUADRA A SQUADRA B' (eventualmente con le parti a capo in coda): trova la coppia di nomi noti."""
    t = toks(testo)
    nomi = {n: toks(n) for n in squadre}
    best = None
    for a, ta in nomi.items():
        for b, tb in nomi.items():
            if a == b:
                continue
            # i nomi possono essere spezzati: prima riga = inizio A + inizio B, righe seguenti = resto A + resto B
            for i in range(1, len(ta) + 1):
                for j in range(1, len(tb) + 1):
                    if t == ta[:i] + tb[:j] + ta[i:] + tb[j:] or t == ta[:i] + tb[:j] + ta[i:] + tb[j:]:
                        sc = len(ta) + len(tb)
                        if best is None or sc > best[0]:
                            best = (sc, a, b)
    return (best[1], best[2]) if best else (None, None)


def leggi_calendario(url, gare_note):
    """Legge il PDF del calendario usando la posizione delle parole: colonne Gara | Squadra A | Squadra B | Giorno/Data/Ora.
    I nomi del PDF sono poi tradotti nei nomi della config grazie alle gare già note (stesso numero gara)."""
    import pdfplumber
    righe = []  # (tipo, dati)
    with pdfplumber.open(io.BytesIO(get(url).content)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
            xa = xb = xg = None
            for i, w in enumerate(words):
                if w["text"] == "Squadra" and i + 1 < len(words) and words[i + 1]["text"] in ("A", "B"):
                    if words[i + 1]["text"] == "A": xa = w["x0"] - 2
                    else: xb = w["x0"] - 2
                if w["text"] == "Giorno": xg = w["x0"] - 2
            if xa is None or xb is None or xg is None:
                continue
            linee = {}
            for w in words:
                linee.setdefault(round(w["top"] / 3), []).append(w)
            for k in sorted(linee):
                ws = sorted(linee[k], key=lambda w: w["x0"])
                testo = " ".join(w["text"] for w in ws)
                if RX_GIORN.match(testo):
                    righe.append(("G", testo)); continue
                if re.search(r" - .*\(|^\(?[A-Z' ]+\)$", testo):
                    righe.append(("C", testo)); continue
                A = " ".join(w["text"] for w in ws if xa <= w["x0"] < xb)
                B = " ".join(w["text"] for w in ws if xb <= w["x0"] < xg)
                pre = [w["text"] for w in ws if w["x0"] < xa]
                dopo = " ".join(w["text"] for w in ws if w["x0"] >= xg)
                m = re.search(r"(\d{2})/(\d{2})/(\d{4})\s+(\d{1,2}[:.]\d{2})", dopo)
                if pre and re.fullmatch(r"\d{1,5}", pre[0]) and m:
                    righe.append(("P", (int(pre[0]), A, B, f"{m.group(3)}-{m.group(2)}-{m.group(1)}", m.group(4).replace(".", ":").zfill(5))))
                elif (A or B) and not pre and not dopo:
                    righe.append(("X", (A, B)))
    gare, gio, andata_max = [], None, 0
    for tipo, d in righe:
        if tipo == "G":
            m = RX_GIORN.match(d); n = int(m.group(1))
            if m.group(2).lower() == "andata": gio = n; andata_max = max(andata_max, n)
            else: gio = ("R", n)
        elif tipo == "P" and gio is not None:
            gare.append([d[0], gio, d[3], d[4], d[1], d[2], ""])
        elif tipo == "X" and gare and not gare[-1][6]:
            gare[-1][4] = (gare[-1][4] + " " + d[0]).strip(); gare[-1][5] = (gare[-1][5] + " " + d[1]).strip()
        elif tipo == "C" and gare:
            gare[-1][6] = (gare[-1][6] + " " + d).strip()
    for g in gare:
        if isinstance(g[1], tuple): g[1] = andata_max + g[1][1]
        g[6] = sistema_campo(g[6])
    # nomi PDF -> nomi della config, dalle gare con lo stesso numero
    note = {g[0]: g for g in gare_note}
    alias = {}
    for g in gare:
        k = note.get(g[0])
        if k and k[4] and k[5]:
            alias.setdefault(norm(g[4]), k[4]); alias.setdefault(norm(g[5]), k[5])
    for g in gare:
        g[4] = alias.get(norm(g[4])); g[5] = alias.get(norm(g[5]))
    return gare


def sistema_campo(c):
    # "PALASPORT - Piazzale Lancieri d'Aosta - CERVIGNANO DEL FRIULI - (UDINE)" -> "Palasport, Cervignano del Friuli"
    p = [x.strip() for x in re.split(r"\s+-\s+", c) if x.strip()]
    if len(p) >= 3:
        return f"{p[0].title()}, {p[-2].title()}"
    return c.title()


# ---------------------------------------------------------------- omologazioni
RX_OMO = re.compile(r"^(\d{1,5}) (.+?) (\d{1,3}) ?- ?(\d{1,3})\s*$")


VUOTE = {"BASKET", "PALL", "PALLACANESTRO", "ASD", "A", "S", "D", "U", "US", "USD", "POL", "SSD", "SD", "SS", "ED", "E", "DI",
         "DEL", "LIBERTAS", "TRIESTE", "UDINE", "PORDENONE", "GORIZIA", "BC", "CLUB", "SRL", "SNC", "NEXT", "GEN", "ROSA", "NERA"}


CONTA = {"uguali": 0, "nuovi": 0, "diversi": 0, "scartate": 0}


def elenco_omologazioni(base, filtro=None):
    out, pagina = [], 1
    while True:
        r = S.get(f"{base}/wp-json/wp/v2/media", params={"search": "Omologazione", "per_page": 100, "page": pagina,
                  "after": INIZIO, "_fields": "date,source_url"}, timeout=60)
        if r.status_code == 400:
            break
        r.raise_for_status()
        js = r.json()
        out += [x for x in js if x["source_url"].lower().endswith(".pdf") and (not filtro or re.search(filtro, x["source_url"], re.I))]
        if len(js) < 100:
            break
        pagina += 1
    return sorted(out, key=lambda x: x["date"])


RX_GIOCATA = re.compile(r"giocata il (\d{2})/(\d{2})/(\d{4})", re.I)


def leggi_omologazione(url):
    """-> [(numero gara, testo squadre, punti A, punti B, data effettiva o None)].
    La riga sotto la gara può dire "giocata il 09/11/2026": è la data vera (anticipi, posticipi, inversioni di campo).
    Le righe "0 - 0" (es. sezione "RIPETIZIONE GARE ... Motivo della ripetizione") non sono un risultato: nel basket
    non esiste il pareggio, quindi una riga con punteggi uguali viene ignorata."""
    ris, righe = [], pdf_righe(url)
    for i, l in enumerate(righe):
        m = RX_OMO.match(l)
        if not m:
            continue
        a, b = int(m.group(3)), int(m.group(4))
        if a == b:
            continue
        d = RX_GIOCATA.search(righe[i + 1]) if i + 1 < len(righe) else None
        ris.append((int(m.group(1)), m.group(2), a, b, f"{d.group(3)}-{d.group(2)}-{d.group(1)}" if d else None))
    return ris


def pari(ris):
    """True per un punteggio con i due numeri uguali (es. "0-0" di una gara da ripetere): non è un risultato."""
    m = re.fullmatch(r"(\d+)-(\d+)", ris or "")
    return bool(m) and m.group(1) == m.group(2)


# ---------------------------------------------------------------- girone
def costruisci(spec, oggi):
    ids = spec.get("ids", {})
    tab = {n: dict(squadra=n, g=0, v=0, p=0, f=0, s=0) for n in spec["squadre"]}
    giocate_per_g = {}
    for num, gio, data, ora, casa, osp, campo, ris in spec["gare"]:
        giocate_per_g.setdefault(gio, [0, 0])[1] += 1
        if not ris or pari(ris) or casa not in tab or osp not in tab:
            continue
        giocate_per_g[gio][0] += 1
        a, b = map(int, ris.split("-"))
        for t, fa, su in ((casa, a, b), (osp, b, a)):
            r = tab[t]; r["g"] += 1; r["f"] += fa; r["s"] += su
            r["v" if fa > su else "p"] += 1
    rows = sorted(tab.values(), key=lambda r: (-r["v"], -(r["f"] - r["s"]), -r["f"], r["squadra"]))
    classifica = []
    for i, r in enumerate(rows, 1):
        e = {"pos": i, "squadra": r["squadra"]}
        if ids.get(r["squadra"]): e["id"] = ids[r["squadra"]]
        e.update(punti=2 * r["v"], g=r["g"], v=r["v"], p=r["p"], f=r["f"], s=r["s"])
        classifica.append(e)
    # ultima giornata = la più alta con almeno metà delle gare giocate
    ultima = max([g for g, (gi, tot) in giocate_per_g.items() if gi * 2 >= tot] or [0])
    partite = []
    for num, gio, data, ora, casa, osp, campo, ris in sorted(spec["gare"], key=lambda g: (g[1], g[2] or "", g[3] or "", g[0])):
        if not ris and gio > ultima + 1:
            continue
        if not ris and gio <= ultima and (data or "") >= oggi:
            pass  # recupero già in calendario: lo teniamo
        p = {"giornata": gio, "gara": num}
        if data: p["data"] = data
        if ora: p["ora"] = ora
        p.update(casa=casa, ospite=osp)
        if ids.get(casa): p["id_casa"] = ids[casa]
        if ids.get(osp): p["id_ospite"] = ids[osp]
        p["risultato"] = "" if pari(ris) else (ris or "")
        if campo: p["campo"] = campo
        partite.append(p)
    for r in classifica: r.setdefault("id", None)
    for p in partite: p.setdefault("id_casa", None); p.setdefault("id_ospite", None)
    partite.sort(key=lambda m: (m.get("data") or "9999", m.get("ora") or ""))
    out = {"gid": "basket-" + spec["slug"], "sport": "basket", "girone": spec["girone"], "categoria": spec["categoria"],
           "genere": spec["genere"], "stagione": "2026/27", "comitato": spec.get("comitato", "FIP CR Friuli Venezia Giulia"),
           "fonte": spec["fonte"], "aggiornato": spec["aggiornato"], "giornata": ultima, "calcolata": True,
           "classifica": classifica, "partite": partite}
    return out


def main():
    prova, tutto = "--prova" in sys.argv, "--tutto" in sys.argv
    solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    oggi = dt.date.today().isoformat()
    specs = {}
    for f in sorted(glob.glob(os.path.join(CFG_DIR, "*.json"))):
        s = json.load(open(f))
        if solo and s["slug"] != solo:
            continue
        s["_file"] = f
        specs[s["slug"]] = s
    stato = json.load(open(STATO)) if os.path.exists(STATO) and not tutto else {"omologazioni_lette": [], "calendari_letti": []}

    # 1. calendari completi (una volta per girone)
    for s in specs.values():
        u = s.get("id_fonte", "")
        if not u.lower().endswith(".pdf") or u in stato["calendari_letti"]:
            continue
        try:
            cal = leggi_calendario(u, s["gare"])
        except Exception as e:
            print(f"{s['slug']}: calendario non letto ({e})"); continue
        note = [g for g in cal if not g[4]]
        if len(note) > 0.1 * max(1, len(cal)) or len(cal) < len(s["gare"]):
            print(f"{s['slug']}: calendario letto male ({len(cal)} gare, {len(note)} senza squadre): ignorato")
            continue
        per_num = {g[0]: g for g in s["gare"]}
        nuove = 0
        for g in cal:
            if g[0] in per_num:
                old = per_num[g[0]]
                if not old[6] and g[6]: old[6] = g[6]
                continue
            if not g[4]:
                continue
            s["gare"].append(g + [""]); nuove += 1
        stato["calendari_letti"].append(u)
        print(f"{s['slug']}: calendario completo, {len(cal)} gare ({nuove} aggiunte)")

    # 2. omologazioni nuove
    per_num = {}
    for s in specs.values():
        for g in s["gare"]:
            per_num.setdefault(g[0], []).append((s, g))
    aggiornate = set()
    for comitato, (base, filtro) in ARCHIVI.items():
        try:
            elenco = elenco_omologazioni(base, filtro)
        except Exception as e:
            print(f"archivio {comitato}: non letto ({e})"); continue
        for x in elenco:
            u = x["source_url"]
            if u in stato["omologazioni_lette"]:
                continue
            try:
                righe = leggi_omologazione(u)
            except Exception as e:
                print(f"  ! {u}: {e}"); continue
            usate = 0
            for num, testo, a, b, giocata in righe:
                # i numeri gara si ripetono tra campionati e comitati: la gara va accettata solo se nella riga
                # compaiono parole distintive di ENTRAMBE le squadre del calendario
                t = set(toks(testo))
                cand = [(s, g) for s, g in per_num.get(num, []) if t & (set(toks(g[4])) - VUOTE) and t & (set(toks(g[5])) - VUOTE)]
                if len(cand) != 1:
                    CONTA["scartate"] += 1
                    continue
                s, g = cand[0]
                if pari(g[7]):
                    g[7] = ""  # un vecchio "0-0" (gara da ripetere) non blocca il risultato vero
                if giocata and g[2] != giocata:
                    print(f"  gara {num} ({s['slug']}): giocata il {giocata} (calendario {g[2]})")
                    g[2] = giocata
                nuovo = f"{a}-{b}"
                CONTA["uguali" if g[7] == nuovo else "nuovi" if not g[7] else "diversi"] += 1
                if g[7] and g[7] != nuovo:
                    print(f"  ! gara {num} ({s['slug']}): risultato già presente {g[7]}, letto {nuovo}: lasciato com'era")
                    continue
                g[7] = nuovo
                d = x["date"][:10]
                if d > s.get("aggiornato", ""):
                    s["aggiornato"] = d; s["fonte"] = u
                aggiornate.add(s["slug"]); usate += 1
            stato["omologazioni_lette"].append(u)
            print(f"{u.rsplit('/', 1)[-1]}: {usate} risultati su {len(righe)} righe")

    print("confronto con i risultati già presenti:", CONTA)
    if prova:
        print("prova: nessun file scritto"); return
    # 3. scrittura
    data = json.load(open(RIS))
    by = {g["gid"]: i for i, g in enumerate(data)}
    for s in specs.values():
        f = s.pop("_file")
        json.dump(s, open(f, "w"), ensure_ascii=False, indent=0)
        g = costruisci(s, oggi)
        if g["gid"] in by:
            old = data[by[g["gid"]]]
            if len(g["classifica"]) < len(old.get("classifica") or []):
                print(f"{s['slug']}: meno squadre del precedente, non aggiornato"); continue
            data[by[g["gid"]]] = g
        else:
            data.append(g)
    applica_comuni(data)  # comune delle squadre senza id (config/squadre_comune.json)
    json.dump(data, open(RIS, "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump(stato, open(STATO, "w"), ensure_ascii=False, indent=0)
    print(f"gironi aggiornati da nuove omologazioni: {len(aggiornate)} su {len(specs)}")


if __name__ == "__main__":
    main()
