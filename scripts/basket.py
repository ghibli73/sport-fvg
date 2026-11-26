"""Aggiornamento automatico del BASKET dai documenti ufficiali FIP (nessuna intelligenza artificiale).

Per ogni girone in config/basket/<slug>.json (calendario + abbinamenti squadra -> società):
  1. completa il calendario leggendo il PDF "Calendario Definitivo" del girone (campo id_fonte), se è un PDF;
  2. legge le "Omologazione gare" pubblicate dal Comitato (archivio WordPress del sito FIP regionale) non ancora lette
     e assegna i punteggi per numero gara;
  3. ricalcola la classifica (2 punti a vittoria; a parità differenza canestri, poi punti fatti) e scrive il girone
     in data/risultati.json con tutte le gare giocate e TUTTE le gare in calendario ancora da giocare.
Calendario aggiornato (spostamenti, anticipi, cambi di campo, recuperi): vedi pipeline/agenti/calendari.md
  4. calendari riemessi: ogni PDF "Calendario" dell'archivio non ancora letto viene confrontato con i gironi (stessi
     numeri gara e squadre) e, se è di un girone, ne aggiorna per numero gara data, ora e campo delle gare non giocate;
  5. portale risultati FIP (fip.it/risultati, una pagina per giornata con data, ora, numero gara e campo di gioco):
     per i gironi abbinati in config/basket_fip.json legge le giornate con gare non giocate entro FIP_GIORNI giorni
     (tutte con --completo) e aggiorna per numero gara data, ora e campo. L'abbinamento girone FIP -> slug viene
     cercato in automatico (--scopri-fip, oppure da solo una volta alla settimana) confrontando i numeri gara.
Le omologazioni lette sono ricordate in config/basket_stato.json, così ogni esecuzione legge solo le nuove.
  6. giro rapido (--rapido, nelle fasce di gara: pipeline/agenti/tempo-reale.md): per i gironi abbinati legge sul portale
     FIP le pagine delle giornate con gare finite da poco e senza omologazione, prende i punteggi (referto elettronico)
     e li salva in config/live.json; in app compaiono con "non_omologato": true finché l'omologazione del Giudice non li
     conferma (se omologazione e portale non coincidono vale l'omologazione).
Uso: python scripts/basket.py [--tutto] [--solo <slug>] [--prova] [--completo] [--scopri-fip] [--rapido]
     --tutto  rilegge tutte le omologazioni della stagione;  --prova  non scrive config né data/risultati.json
     (il risultato va in /tmp/risultati_prova.json);  --completo  legge sul portale FIP tutte le giornate future.
"""
import io, json, os, re, sys, time, glob, datetime as dt
import requests
from abbinamenti import applica_comuni  # scripts/abbinamenti.py
import tempo_reale as TR  # scripts/tempo_reale.py

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DIR = os.path.join(ROOT, "config", "basket")
STATO = os.path.join(ROOT, "config", "basket_stato.json")
RIS = os.path.join(ROOT, "data", "risultati.json")
ARCHIVI = {  # comitato -> (archivio media WordPress, filtro sul nome del file)
    "fvg": ("https://friuliveneziagiulia.fip.it", None),
    "veneto": ("https://veneto.fip.it", r"Interregionale"),  # dal Veneto solo la B Interregionale (girone con squadre FVG)
}
INIZIO = "2026-08-15T00:00:00"
FIP_CFG = os.path.join(ROOT, "config", "basket_fip.json")
FIP_URL = "https://fip.it/risultati/"
FIP_PAUSA = 1.5    # secondi tra le pagine del portale FIP
FIP_GIORNI = 14    # lettura normale: giornate con gare non giocate fino a 14 giorni da oggi (e i recuperi)
PROVA = "/tmp/risultati_prova.json"
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
    righe = righe_calendario(url)
    return abbina_calendario(righe, gare_note)


_righe_cal = {}


def righe_calendario(url):
    """Righe del PDF del calendario (tipo, dati), lette una volta sola per URL."""
    if url in _righe_cal:
        return _righe_cal[url]
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
    _righe_cal[url] = righe
    return righe


def abbina_calendario(righe, gare_note):
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
        # tutte le gare non giocate restano: calendario completo (anche i recuperi delle giornate passate)
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


# ---------------------------------------------------------------- calendari riemessi
def elenco_calendari(base):
    """PDF "Calendario" dell'archivio media del Comitato (data, url), dal più vecchio."""
    out, pagina = [], 1
    while True:
        r = S.get(f"{base}/wp-json/wp/v2/media", params={"search": "Calendario", "per_page": 100, "page": pagina,
                  "after": INIZIO, "_fields": "date,source_url"}, timeout=60)
        if r.status_code == 400:
            break
        r.raise_for_status()
        js = r.json()
        out += [x for x in js if x["source_url"].lower().endswith(".pdf")]
        if len(js) < 100:
            break
        pagina += 1
    return sorted(out, key=lambda x: x["date"])


def aggiorna_da_calendario(s, cal, fonte):
    """Gare del calendario (riemesso) -> per numero gara aggiorna data, ora e campo delle gare non giocate.
    -> numero di gare cambiate."""
    per_num = {g[0]: g for g in s["gare"]}
    cambiate = 0
    for c in cal:
        g = per_num.get(c[0])
        if not g or (g[7] and not pari(g[7])) or not c[4] or not c[5]:
            continue
        if g[4] != c[4] or g[5] != c[5]:
            continue  # stesso numero ma altre squadre: non è la stessa gara
        nuovo = (c[2], c[3], c[6] if c[6] and "," in c[6] else g[6])
        if (g[2], g[3], g[6]) != nuovo:
            print(f"  gara {g[0]} ({s['slug']}): {g[2]} {g[3]} {g[6]} -> {nuovo[0]} {nuovo[1]} {nuovo[2]} [{fonte.rsplit('/', 1)[-1]}]")
            g[2], g[3], g[6] = nuovo
            cambiate += 1
    return cambiate


# ---------------------------------------------------------------- portale risultati FIP
MESI = {m: i for i, m in enumerate(["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
                                     "settembre", "ottobre", "novembre", "dicembre"], 1)}
RX_FIP = re.compile(r"(\d{1,2}) (" + "|".join(MESI) + r") (\d{4}) (\d{1,2}[:.]\d{2}) (\d{3,7}) .*?Squadra di casa (.+?) "
                    r"Squadra ospite (.+?) Campo di gioco (.+?) (?:Arbitri|\d\W{0,2} Arbitro|Designazione)", re.I)
_fip_t = [0.0]


def fip_get(params):
    attesa = FIP_PAUSA - (time.time() - _fip_t[0])
    if attesa > 0:
        time.sleep(attesa)
    r = S.get(FIP_URL, params=params, timeout=60)
    _fip_t[0] = time.time()
    r.raise_for_status()
    return r.text


def fip_testo(html):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&#039;", "'").replace("&amp;", "&").replace("&quot;", '"')
    t = re.sub(r"[ЇїЄє]", "'", t)  # virgolette tipografiche lette con la codifica sbagliata dal portale
    return re.sub(r"\s+", " ", t)


def fip_campo(c):
    """Es. "PALESTRA 'M.ERVATTI', Località Borgo Grotta Gigante 34010 SGONICO ( TS)" -> "Palestra 'M.Ervatti', Sgonico"."""
    nome = re.split(r"\s*,\s*", c.strip(), 1)[0].strip(" ,")
    m = re.search(r"\d{5}\s+(.+?)\s*\(\s*[A-Z]{2}\s*\)\s*$", c)
    return f"{nome.title()}, {m.group(1).title()}" if m else nome.title()


def fip_gare(html):
    """Gare di una pagina giornata del portale FIP -> [(numero, casa, ospite, data, ora, campo)]."""
    out = []
    for m in RX_FIP.finditer(fip_testo(html)):
        d = f"{m.group(3)}-{MESI[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
        if d[5:] == "06-30":
            d = None  # 30 giugno = data segnaposto del portale per le gare rinviate "da definire"
        out.append((int(m.group(5)), m.group(6).strip(), m.group(7).strip(), d, m.group(4).replace(".", ":").zfill(5),
                    fip_campo(m.group(8))))
    return out


def fip_link(html):
    """Parametri dei link alle giornate presenti nella pagina: {(fase, girone): {(ar, giornata), ...}}."""
    out = {}
    for q in re.findall(r"codice_fase=(\d+)&(?:amp;)?codice_girone=(\d+)&(?:amp;)?codice_ar=(\d)&(?:amp;)?giornata=(\d+)", html):
        out.setdefault((q[0], q[1]), set()).add((int(q[2]), int(q[3])))
    return out


REGIONI = {"ABR", "BAS", "CAL", "CAM", "EMR", "FVG", "LAZ", "LIG", "LOM", "MAR", "MOL", "PMN", "PUG", "SAR", "SIC", "TOS",
           "TAA", "UMB", "VDA", "VEN", "NAZ"}
NON_GIRONI = {"ES", "ESO", "TAQ", "TAQB", "TAQS", "OPENM", "OPENF", "A1/F", "A2/F", "B/F"}  # minibasket, open, nazionali


def fip_campionati(html):
    """Campionati dell'elenco a tendina (senza regioni, comitati, minibasket e campionati nazionali)."""
    out = {}
    for v, nome in re.findall(r'<option value="([A-Z0-9]{1,6}(?:/[A-Z]{1,2})?)"\s*>\s*([^<]{3,120}?)\s*</option>', html):
        nome = re.sub(r"\s+", " ", nome)
        if v in REGIONI or v in NON_GIRONI or re.match(r"R[A-Z]{2}$", v) or nome.upper().startswith(("COMITATO", "NAZIONALE")):
            continue
        out.setdefault(v, nome)
    return out


def scopri_fip(specs, cfg):
    """Abbina i gironi del portale FIP (comitato FVG) ai gironi di config/basket: per ogni campionato e girone legge
    la 1ª giornata di andata e confronta i numeri gara con quelli del calendario (almeno 3 numeri e le squadre)."""
    base = {"group": "campionati-regionali", "regione_codice": "RFR", "comitato_codice": "RFR"}
    per_num = {}
    for s in specs.values():
        for g in s["gare"]:
            per_num.setdefault(g[0], []).append((s, g))
    trovati = 0
    for sesso in ("M", "F"):
        try:
            camp = fip_campionati(fip_get({**base, "sesso": sesso}))
        except Exception as e:
            print(f"FIP: elenco campionati {sesso} non letto ({e})"); continue
        for codice, nome in camp.items():
            try:
                html = fip_get({**base, "sesso": sesso, "codice_campionato": codice})
            except Exception as e:
                print(f"FIP {codice}: {e}"); continue
            link = fip_link(html)
            # altri gironi dello stesso campionato: numeri a 5-6 cifre nelle voci dei menu (stessa fase del primo)
            fase0 = next(iter(link))[0] if link else "1"
            for gir in set(re.findall(r'value="(\d{5,6})"', html)) - {g for _, g in link}:
                link[(fase0, gir)] = set()
            # gli altri gironi dello stesso campionato hanno quasi sempre codici vicini (DR1 Est 85168, Ovest 85169):
            # la pagina predefinita mostra solo il primo, quindi si provano i codici fino a 3 prima e dopo
            gia = {p.get("codice_girone") for p in cfg["gironi"].values()}
            for _, gir in list(link):
                for d in (-3, -2, -1, 1, 2, 3):
                    c = str(int(gir) + d)
                    if c not in gia and (fase0, c) not in link:
                        link[(fase0, c)] = set()
            for (fase, gir), giornate in link.items():
                p = {**base, "sesso": sesso, "codice_campionato": codice, "codice_fase": fase, "codice_girone": gir}
                andata = max([g for ar, g in giornate if ar == 1] or [0])
                gare = []
                for ar, n in ((0, 1), (1, andata), (1, 1)):
                    if not n:
                        continue
                    try:
                        h = fip_get({**p, "codice_ar": ar, "giornata": n})
                    except Exception as e:
                        print(f"FIP {codice} {gir}: {e}"); break
                    gare = fip_gare(h)
                    if not andata:
                        andata = max([g for a, g in fip_link(h).get((fase, gir), set()) if a == 1] or [0])
                    if gare:
                        break
                voti = {}
                for num, casa, osp, *_ in gare:
                    t = set(toks(casa + " " + osp)) - VUOTE
                    for s, g in per_num.get(num, []):
                        if t & (set(toks(g[4] + " " + g[5])) - VUOTE):
                            voti[s["slug"]] = voti.get(s["slug"], 0) + 1
                if voti:
                    slug, n = max(voti.items(), key=lambda x: x[1])
                    if n >= min(3, len(gare)) and andata and n >= cfg["gironi"].get(slug, {}).get("uguali", 0):
                        cfg["gironi"][slug] = {**p, "andata": andata, "nome": nome.strip(), "uguali": n}
                        trovati += 1
                        print(f"FIP: {slug} = {nome.strip()} (campionato {codice}, fase {fase}, girone {gir}, {n} gare uguali)")
    cfg["scoperta"] = dt.date.today().isoformat()
    print(f"FIP: gironi abbinati {trovati}; senza abbinamento: {sorted(set(specs) - set(cfg['gironi']))}")


def fip_punteggi(html):
    """Punteggi di una pagina giornata: {numero gara: (punti casa, punti ospite, omologata sul portale)}.
    Il testo è "CASA 80 OSPITE 71 20 Novembre 2026 21:15 000225 [Gara omologata ...] Info Squadra di casa CASA ...":
    i nomi letti dopo "Squadra di casa"/"Squadra ospite" servono a riconoscere i due numeri prima della data."""
    t = fip_testo(html)
    out = {}
    for m in RX_FIP.finditer(t):
        casa, osp = m.group(6).strip(), m.group(7).strip()
        prima = t[max(0, m.start() - 300):m.start()]
        r = re.search(re.escape(casa) + r"\s+(\d{1,3})\s+" + re.escape(osp) + r"\s+(\d{1,3})\s*$", prima)
        if not r:
            continue
        a, b = int(r.group(1)), int(r.group(2))
        if a == b:
            continue  # nessun pareggio nel basket: 0-0 = da giocare
        out[int(m.group(5))] = (a, b, bool(re.search(r"omologat", m.group(0)[:200], re.I)))
    return out


def risultati_fip(specs, cfg, live, oggi):
    """Giro rapido: punteggi delle gare finite (inizio + 105 minuti) negli ultimi 3 giorni e non ancora omologate.
    -> (pagine lette, risultati nuovi)."""
    da = (dt.date.fromisoformat(oggi) - dt.timedelta(days=3)).isoformat()
    pagine = nuovi = 0
    for slug, p in sorted(cfg.get("gironi", {}).items()):
        s = specs.get(slug)
        if not s or not p.get("andata"):
            continue
        voci = live.setdefault("gironi", {}).setdefault("basket-" + slug, {})
        attese = [g for g in s["gare"] if (not g[7] or pari(g[7])) and da <= (g[2] or "") <= oggi
                  and TR.finita(g[2], g[3], 105) and f"gara:{g[0]}" not in voci]
        per_num = {g[0]: g for g in s["gare"]}
        for gio in sorted({g[1] for g in attese}):
            ar, n = (1, gio) if gio <= p["andata"] else (0, gio - p["andata"])
            q = {k: v for k, v in p.items() if k not in ("andata", "nome", "uguali")}
            try:
                html = fip_get({**q, "codice_ar": ar, "giornata": n}); pagine += 1
            except Exception as e:
                print(f"  ! FIP {slug} giornata {gio}: {e}"); continue
            punti = fip_punteggi(html)
            for num, (a, b, omo) in punti.items():
                g = per_num.get(num)
                if not g or g not in attese:
                    continue
                voci[f"gara:{num}"] = {"r": f"{a}-{b}", "data": g[2], "omologata_portale": omo,
                                       "letto": TR.adesso().isoformat(timespec="minutes"),
                                       "fonte": f"{FIP_URL}?codice_campionato={q.get('codice_campionato')}&codice_girone={q.get('codice_girone')}"}
                nuovi += 1
                print(f"  {slug} gara {num}: {g[4]} - {g[5]} {a}-{b} (da omologare)")
        if not voci:
            live["gironi"].pop("basket-" + slug, None)
    print(f"FIP risultati: pagine lette {pagine}, risultati nuovi {nuovi}")
    return pagine, nuovi


def rapido(specs, prova, oggi):
    """--rapido: solo risultati del portale FIP -> config/live.json -> data/risultati.json (nessun PDF)."""
    fip = json.load(open(FIP_CFG)) if os.path.exists(FIP_CFG) else {"gironi": {}}
    live = TR.carica_live()
    data = json.load(open(RIS))
    conf, div = TR.pulisci(data, live, oggi)
    print(f"provvisori confermati dalle omologazioni: {conf}, diversi: {div}")
    risultati_fip(specs, fip, live, oggi)
    n = TR.applica(data, live, solo_sport={"basket"})
    print(f"partite aggiornate in app: {n}")
    if prova:
        json.dump(data, open(PROVA, "w"), ensure_ascii=False, separators=(",", ":"))
        print("prova: config/live.json e data/risultati.json non modificati, risultato in", PROVA); return
    TR.salva_live(live)
    json.dump(data, open(RIS, "w"), ensure_ascii=False, separators=(",", ":"))


def variazioni_fip(specs, cfg, oggi, completo):
    """Per i gironi abbinati legge le giornate con gare non giocate (entro FIP_GIORNI giorni, o tutte con
    --completo, più i recuperi) e aggiorna per numero gara data, ora e campo. -> gare cambiate."""
    fino = (dt.date.fromisoformat(oggi) + dt.timedelta(days=FIP_GIORNI)).isoformat()
    cambiate = pagine = 0
    for slug, p in sorted(cfg.get("gironi", {}).items()):
        s = specs.get(slug)
        if not s or not p.get("andata"):
            continue
        aperte = sorted({g[1] for g in s["gare"] if (not g[7] or pari(g[7])) and (completo or (g[2] or "") <= fino)})
        per_num = {g[0]: g for g in s["gare"]}
        for gio in aperte:
            ar, n = (1, gio) if gio <= p["andata"] else (0, gio - p["andata"])
            q = {k: v for k, v in p.items() if k not in ("andata", "nome", "uguali")}
            try:
                gare = fip_gare(fip_get({**q, "codice_ar": ar, "giornata": n}))
                pagine += 1
            except Exception as e:
                print(f"  ! FIP {slug} giornata {gio}: {e}"); continue
            for num, casa, osp, data, ora, campo in gare:
                g = per_num.get(num)
                if not g or (g[7] and not pari(g[7])):
                    continue
                if not (set(toks(casa)) - VUOTE) & (set(toks(g[4])) - VUOTE):
                    continue  # stesso numero, altra squadra di casa: non è la stessa gara
                if not data:
                    continue  # rinviata a data da definire: resta la data del calendario
                if (g[2], g[3]) != (data, ora) or (campo and campo != g[6]):
                    if (g[2], g[3]) != (data, ora):
                        print(f"  gara {num} ({slug}): {g[2]} {g[3]} -> {data} {ora}" + (f" campo {campo}" if campo != g[6] else ""))
                        cambiate += 1
                    g[2], g[3] = data, ora
                    if campo:
                        g[6] = campo
    print(f"FIP: pagine lette {pagine}, gare spostate {cambiate}")
    return cambiate


def main():
    prova, tutto, completo = "--prova" in sys.argv, "--tutto" in sys.argv, "--completo" in sys.argv
    solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    oggi = dt.date.today().isoformat()
    specs = {}
    for f in sorted(glob.glob(os.path.join(CFG_DIR, "*.json"))):
        s = json.load(open(f))
        if solo and s["slug"] != solo:
            continue
        s["_file"] = f
        specs[s["slug"]] = s
    if "--rapido" in sys.argv:
        return rapido(specs, prova, oggi)
    stato = json.load(open(STATO)) if os.path.exists(STATO) and not tutto else {"omologazioni_lette": [], "calendari_letti": []}
    prima_fut = sum(1 for s in specs.values() for g in s["gare"] if not g[7] and (g[2] or "") >= oggi)

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

    # 1b. calendari riemessi (anche con un nome diverso): stessi numeri gara e squadre di un girone
    try:
        nuovi_cal = [x for x in elenco_calendari(ARCHIVI["fvg"][0]) if x["source_url"] not in stato["calendari_letti"]]
    except Exception as e:
        nuovi_cal = []; print(f"calendari riemessi: archivio non letto ({e})")
    for x in nuovi_cal:
        u = x["source_url"]
        usato = False
        for s in specs.values():
            try:
                cal = leggi_calendario(u, s["gare"])
            except Exception as e:
                print(f"  ! {u.rsplit('/', 1)[-1]}: {e}"); break
            per_num = {g[0]: g for g in s["gare"]}
            # è il calendario di questo girone se quasi tutte le gare hanno numero e squadre uguali
            buone = [c for c in cal if c[4] and per_num.get(c[0]) and per_num[c[0]][4:6] == c[4:6]]
            if len(buone) < 0.8 * max(1, len(cal)) or len(buone) < 3:
                continue
            n = aggiorna_da_calendario(s, cal, u)
            print(f"{s['slug']}: calendario {u.rsplit('/', 1)[-1]} ({len(buone)} gare, {n} cambiate)")
            if u != s.get("id_fonte"):
                s["id_fonte"] = u
            usato = True
        if not usato:
            print(f"calendario {u.rsplit('/', 1)[-1]}: nessun girone corrispondente")
        stato["calendari_letti"].append(u)

    # 1c. portale risultati FIP: date, ore e campi aggiornati delle gare non giocate
    fip = json.load(open(FIP_CFG)) if os.path.exists(FIP_CFG) else {"gironi": {}}
    fip.setdefault("gironi", {})
    if "--scopri-fip" in sys.argv or not fip.get("scoperta") or \
            (dt.date.fromisoformat(oggi) - dt.date.fromisoformat(fip["scoperta"])).days >= 7 and set(specs) - set(fip["gironi"]):
        try:
            scopri_fip(specs, fip)
        except Exception as e:
            print(f"FIP: ricerca dei gironi non riuscita ({e})")
    try:
        variazioni_fip(specs, fip, oggi, completo)
    except Exception as e:
        print(f"FIP: lettura non riuscita ({e})")

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
    dopo_fut = sum(1 for s in specs.values() for g in s["gare"] if not g[7] and (g[2] or "") >= oggi)
    print(f"gare future in calendario (config): {prima_fut} -> {dopo_fut}")
    # 3. scrittura (in prova solo /tmp/risultati_prova.json: config e stato restano com'erano)
    data = json.load(open(RIS))
    by = {g["gid"]: i for i, g in enumerate(data)}
    for s in specs.values():
        f = s.pop("_file")
        if not prova:
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
    # risultati del portale FIP non ancora omologati (giro rapido): restano finché l'omologazione non arriva
    print("provvisori (non omologati) applicati:", TR.applica(data, solo_sport={"basket"}))
    if prova:
        json.dump(data, open(PROVA, "w"), ensure_ascii=False, separators=(",", ":"))
        if "--scopri-fip" in sys.argv:
            print("@@FIP@@" + json.dumps(fip, ensure_ascii=False) + "@@FIP@@")
        print("prova: config e data/risultati.json non modificati, risultato in", PROVA); return
    json.dump(data, open(RIS, "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump(stato, open(STATO, "w"), ensure_ascii=False, indent=0)
    json.dump(fip, open(FIP_CFG, "w"), ensure_ascii=False, indent=1)
    print(f"gironi aggiornati da nuove omologazioni: {len(aggiornate)} su {len(specs)}")


if __name__ == "__main__":
    main()
