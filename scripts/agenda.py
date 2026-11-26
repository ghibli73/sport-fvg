"""Agenda degli eventi degli sport individuali (gare, tornei, manifestazioni) per l'app Zuìn – Sport in FVG.

  python scripts/agenda.py            -> rigenera data/agenda.json
  python scripts/agenda.py --prova    -> legge le fonti e stampa il riepilogo, senza scrivere niente
  python scripts/agenda.py --solo fidal,fisi   -> solo alcuni moduli (gli altri eventi restano come sono)
  python scripts/agenda.py --debug    -> come --prova, e stampa un estratto grezzo delle fonti che non danno eventi

Un modulo per fonte (funzioni mod_<nome>): ciascuno legge un calendario ufficiale e restituisce eventi
nel formato di data/agenda.json. Si tengono solo gli eventi tra oggi e oggi + GIORNI giorni che si svolgono
in FVG o sono organizzati da una società del FVG. Gli eventi scritti a mano stanno in config/agenda_manuale.json
e vengono sempre conservati (stesso formato; "id" facoltativo).

Formato di un evento:
  id (fnv1a di data|titolo|luogo, stabile), data AAAA-MM-GG, data_fine?, ora?, titolo, sport (chiave di
  data.json), disciplina?, livello (internazionale|nazionale|regionale|provinciale|promozionale), luogo,
  comune? (ISTAT, solo se in FVG), organizzatore? (id di data/data.json se l'abbinamento è certo, altrimenti
  il nome come scritto nella fonte; assente se la fonte non lo indica), categorie?, link (pagina ufficiale),
  fonte (URL letto), aggiornato (AAAA-MM-GG), pos? ([lat, lon] del centro del comune, per "Vicino a me"),
  origine (nome del modulo o "manuale").
Nessun dato inventato: se un campo non c'è nella fonte, resta vuoto. Nessun nome di atleti.

Sicurezza: se un modulo va in errore o non trova niente mentre prima aveva eventi futuri, si tengono
quelli già presenti in data/agenda.json (con la loro fonte) e si stampa un avviso. Esce sempre con 0,
così il workflow non si ferma per una fonte irraggiungibile.
"""
import datetime as dt
import html
import io
import json
import os
import re
import sys
import time
import unicodedata

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(BASE, "data", "agenda.json")
MANUALE = os.path.join(BASE, "config", "agenda_manuale.json")
GIORNI = 183
PAUSA = 0.8
UA = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (app non ufficiale di consultazione)")
OGGI = dt.date.fromisoformat(os.environ["AGENDA_OGGI"]) if os.environ.get("AGENDA_OGGI") else dt.date.today()
FINE = OGGI + dt.timedelta(days=GIORNI)
DEBUG = "--debug" in sys.argv

_S = None


def sessione():
    global _S
    if _S is None:
        import requests
        _S = requests.Session()
        _S.headers["User-Agent"] = UA
    return _S


def get(url, metodo="GET", **kw):
    time.sleep(PAUSA)
    r = sessione().request(metodo, url, timeout=kw.pop("timeout", 45), **kw)
    r.raise_for_status()
    return r


def grezzo(nome, testo, n=2500):
    if DEBUG:
        print(f"   [debug {nome}] {len(testo)} caratteri:\n" + testo[:n].replace("\n", " ")[:n])


# ---------------------------------------------------------------- utilità

def fnv(s):
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return "%08x" % h


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)).strip()


def pulisci(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", str(s or "")))
    return re.sub(r"\s+", " ", s).strip(" -–·")


def ev_id(e):
    return "ag-" + fnv("|".join([e.get("data", ""), e.get("titolo", ""), e.get("luogo", "")]))


def carica(p, vuoto):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return vuoto


COMUNI = carica(os.path.join(BASE, "data", "comuni.json"), {"comuni": []})["comuni"]
SOC = carica(os.path.join(BASE, "data", "data.json"), [])
CACHE = carica(os.path.join(BASE, "config", "geocodifica_cache.json"), {})
PER_NOME = {norm(c["nome"]): c for c in COMUNI}
# località, frazioni e stazioni sciistiche che compaiono nei calendari -> comune (ISTAT)
ALIAS_LUOGHI = {
    "piancavallo": "093004", "zoncolan": "030088", "sella nevea": "030025", "nevea": "030025",
    "lignano": "030049", "lignano pineta": "030049", "lignano riviera": "030049", "aprilia marittima": "030048",
    "opicina": "032006", "barcola": "032006", "grignano": "032006", "sistiana": "032001", "portopiccolo": "032001",
    "monte di buja": "030013", "camporosso": "030117", "camporosso in valcanale": "030117",
    "valbruna": "030054", "malborghetto": "030054", "forni di sotto": "030042", "pradibosco": "030081",
    "timau": "030071", "cleulis": "030071", "sauris di sopra": "030107", "sauris di sotto": "030107",
    "marina julia": "031012", "panzano": "031012", "portorosega": "031012", "isola della cona": "031020",
    "trieste porto": "032006", "pordenone fiera": "093033", "udine": "030129", "tarvisio": "030117",
    "san giorgio di nogaro": "030100", "porto nogaro": "030100", "marano": "030056", "muggia": "032003",
    "piani di luzza": "030040", "sappada": "030189", "forni avoltri": "030040", "claut": "093015",
}
PROV_SIGLE = {"UD", "PN", "GO", "TS"}


def comune_da(testo):
    """ISTAT del comune FVG nominato in un testo di località ('Buja (UD)', 'Trieste c/o ...', 'Sella Nevea')."""
    t = norm(re.sub(r"\(.*?\)", " ", str(testo or "")))
    if not t:
        return None
    if t in PER_NOME:
        return PER_NOME[t]["codice"]
    for a, cod in sorted(ALIAS_LUOGHI.items(), key=lambda x: -len(x[0])):
        if t == a or t.startswith(a + " "):
            return cod
    # nome del comune all'inizio del testo ("Trieste c o ASD Polet", "Forni di Sopra Varmost")
    best = None
    for n, c in PER_NOME.items():
        if (t == n or t.startswith(n + " ")) and (best is None or len(n) > len(best[0])):
            best = (n, c["codice"])
    return best[1] if best else None


def centro(cod):
    c = next((x for x in COMUNI if x["codice"] == cod), None)
    if not c:
        return None
    p = CACHE.get(f"{c['nome']}, Friuli-Venezia Giulia, Italia")
    return [round(p[0], 5), round(p[1], 5)] if p else None


GENERICHE = set("""asd a s d ssd sd ad as srl arl r l dilettantistica dilettantistico dilettantistiche associazione ass ne
sportiva sportivo societa soc unione gruppo g c onlus di del della dei e la il lo le aps ets coop cooperativa
sezione sez ss""".split())
ESPANDI = {"us": "unione sportiva", "sc": "sci club", "gs": "gruppo sportivo", "sk": "sk", "vc": "velo club",
           "cv": "circolo velico", "yc": "yacht club", "pol": "polisportiva", "atl": "atletica"}


def nucleo(nome):
    t = norm(nome)
    # sigle con i punti: "s.c." -> "s c" -> "sc"
    t = re.sub(r"\b(?:[a-z] )+[a-z]\b", lambda m: m.group(0).replace(" ", ""), t)
    out = []
    for w in t.split():
        w = ESPANDI.get(w, w)
        out.extend(x for x in w.split() if x not in GENERICHE)
    return out


_NUC = None


def organizzatore(nome, sport=None):
    """id della società in data.json se l'abbinamento è certo (stesso nucleo del nome, unico), altrimenti il nome."""
    global _NUC
    nome = pulisci(nome)
    if not nome or nome in ("-", "Da definire"):
        return None
    if re.search(r"\s[-/]\s", nome):  # più organizzatori insieme: nessun abbinamento automatico
        return nome
    if _NUC is None:
        _NUC = [(s, nucleo(s["nome"])) for s in SOC]
    n = nucleo(nome)
    if not n:
        return nome
    cand = [(s, k) for s, k in _NUC if not sport or s["sport"] == sport or sport in s.get("altri_sport", [])]
    pari = [s for s, k in cand if k == n]
    if len(pari) == 1:
        return pari[0]["id"]
    if len(n) >= 2:
        sn = set(n)
        cont = [s for s, k in cand if len(k) >= 2 and (sn <= set(k) or set(k) <= sn)
                and len(sn & set(k)) >= 2 and any(len(x) >= 4 and x not in ("club", "sci", "team") for x in sn & set(k))]
        if len(cont) == 1:
            return cont[0]["id"]
    return nome


def evento(**k):
    e = {x: v for x, v in k.items() if v not in (None, "", [])}
    if e.get("comune") is None and e.get("luogo") and not e["luogo"].startswith("Provincia di"):
        c = comune_da(e["luogo"])
        if c:
            e["comune"] = c
    if e.get("comune"):
        p = centro(e["comune"])
        if p:
            e["pos"] = p
    e["aggiornato"] = OGGI.isoformat()
    e["id"] = ev_id(e)
    return e


def nel_periodo(e):
    fine = e.get("data_fine") or e["data"]
    return fine >= OGGI.isoformat() and e["data"] <= FINE.isoformat()


def in_fvg(e):
    o = e.get("organizzatore")
    return bool(e.get("comune")) or bool(o and any(s["id"] == o for s in SOC))


def mesi():
    d = dt.date(OGGI.year, OGGI.month, 1)
    while d <= FINE:
        yield d.year, d.month
        d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def data_dmy(s, anno=None):
    """'10.01.2027', '05/07/2026', '28-02-2026', '06/12' (con anno) -> AAAA-MM-GG."""
    m = re.search(r"(\d{1,2})[./-](\d{1,2})(?:[./-](\d{2,4}))?", s or "")
    if not m:
        return None
    y = m.group(3) or (str(anno) if anno else None)
    if not y:
        return None
    y = int(y) + (2000 if len(y) == 2 else 0)
    try:
        return dt.date(y, int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None


# ---------------------------------------------------------------- moduli

def mod_fidal():
    """FIDAL: calendario.php, livello REG + regione FVG (tutte le gare regionali e provinciali) e livello COD
    (nazionali e internazionali di tutta Italia, filtrate sulla provincia UD/PN/GO/TS nella colonna località)."""
    out = []
    riga = re.compile(r"<tr><td>(?:<i[^>]*></i>)?</td><td><b[^>]*>([^<]+)</b></td><td><abbr title=\"([^\"]*)\">.*?</abbr></td>"
                      r"<td[^>]*><a href=\"([^\"]+)\">(.*?)</a>(.*?)</td><td[^>]*>(.*?)</td><td[^>]*>(.*?)</td>", re.S)
    for y, m in mesi():
        for liv in ("REG", "COD"):
            u = (f"https://www.fidal.it/calendario.php?anno={y}&mese={m}&livello={liv}"
                 f"&new_regione=FRIULIVENEZIAGIULIA&new_tipo=0&new_categoria=&submit=Invia")
            h = get(u).text
            rr = riga.findall(h)
            if not rr:
                grezzo(f"fidal {y}-{m} {liv}", h[h.find("<tbody"):] if "<tbody" in h else h[-3000:])
            for dd, lv, link, tit, nota, tipo, loc in rr:
                loc = pulisci(loc)
                prov = re.search(r"\(([A-Z]{2})\)", loc)
                if liv == "COD" and not (prov and prov.group(1) in PROV_SIGLE):
                    continue
                tit = pulisci(tit)
                if re.match(r"annullat", tit, re.I):
                    continue
                tit = re.sub(r"^FVG\d\d\s*-\s*", "", tit)
                dd = dd.strip()
                g = re.match(r"(\d{1,2})(?:-(\d{1,2}))?/(\d{1,2})", dd)
                if not g:
                    continue
                d0 = dt.date(y, int(g.group(3)), int(g.group(1))).isoformat()
                d1 = dt.date(y, int(g.group(3)), int(g.group(2))).isoformat() if g.group(2) else None
                lvt = lv.upper()
                livello = ("internazionale" if "INTERNAZ" in lvt else "nazionale" if "NAZ" in lvt
                           else "provinciale" if "PROVINC" in lvt else "regionale")
                tipo = pulisci(tipo).capitalize()
                out.append(evento(data=d0, data_fine=d1, titolo=tit, sport="atletica", disciplina=tipo or None,
                                  livello=livello, luogo=re.sub(r"\s*\([A-Z]{2}\)\s*$", "", loc), link=link,
                                  fonte=u, origine="fidal", _liv=liv))
    # la stessa gara compare come nazionale (COD) e come "Pagina Regionale" (REG): resta la nazionale
    cod = {(e["data"], e.get("comune"), norm(e["titolo"])[:18]) for e in out if e["_liv"] == "COD"}
    res = []
    for e in out:
        if e["_liv"] == "REG" and re.search(r"pagina regionale", e["titolo"], re.I):
            k = (e["data"], e.get("comune"), norm(re.sub(r"(?i)\s*-\s*pagina regionale", "", e["titolo"]))[:18])
            if any(k[0] == c[0] and k[1] == c[1] for c in cod):
                continue
            e["titolo"] = re.sub(r"(?i)\s*-\s*pagina regionale", "", e["titolo"])
            e["id"] = ev_id(e)
        e.pop("_liv", None)
        res.append(e)
    for e in res:
        e["titolo"] = re.sub(r"\^", "ª", e["titolo"])
        e["id"] = ev_id(e)
    return res


FISI_BASE = "https://comitati.fisi.org/friuli-venezia-giulia"


def fisi_livello(cod, tipo, tit):
    t = f"{cod} {tipo} {tit}".upper()
    if re.search(r"\b(WC|EC|FIS|NJR|NJC|CIT|I1)\b|WC_|EC_|FIS_|COPPA DEL MONDO|COPPA EUROPA", t):
        return "internazionale"
    if re.search(r"\bN1\b|CPI_|CI_|NAZ", t):
        return "nazionale"
    if re.search(r"CP_|PROVINC", t):
        return "provinciale"
    if re.search(r"PROMOZ", t):
        return "promozionale"
    return "regionale"


def mod_fisi():
    """FISI FVG: i PDF "Calendario ..." della stagione in corso, trovati con l'API media di WordPress del comitato.
    Si leggono le tabelle (pdfplumber) per intestazione: DATA, LOCALITÀ, ORGANIZZAZIONE, DENOMINAZIONE, SPEC., ..."""
    import pdfplumber
    st = OGGI.year if OGGI.month >= 7 else OGGI.year - 1
    stag = f"{st}-{st + 1}"
    stag2 = f"{st}_{st + 1}"
    L = get(f"{FISI_BASE}/wp-json/wp/v2/media?search=calendario&per_page=60&_fields=date,source_url").json()
    pdf = []
    for x in sorted(L, key=lambda x: x["date"], reverse=True):
        u = x["source_url"]
        if not u.lower().endswith(".pdf") or (stag not in u and stag2 not in u and f"{st}-{str(st + 1)[2:]}" not in u):
            continue
        chiave = re.sub(r"(-\d)?\.pdf$", "", u.rsplit("/", 1)[-1].lower())
        if chiave not in [c for c, _ in pdf]:
            pdf.append((chiave, u))  # il più recente per ogni nome (le revisioni hanno -1, -2 ...)
    print(f"   PDF FISI {stag}: {len(pdf)}")
    out = []
    for chiave, u in pdf:
        disciplina = "Sci di fondo" if "fondo" in chiave else "Sci alpinismo" if "alpinism" in chiave else \
            "Biathlon" if "biathlon" in chiave else "Salto e combinata" if "salto" in chiave else "Sci alpino"
        try:
            blob = get(u, timeout=90).content
            with pdfplumber.open(io.BytesIO(blob)) as doc:
                tabelle = [t for p in doc.pages for t in (p.extract_tables() or [])]
        except Exception as ex:  # noqa: BLE001
            print("   ! PDF illeggibile", u, ex)
            continue
        n0 = len(out)
        for t in tabelle:
            col = None
            for r in t:
                cel = [pulisci(c) for c in r]
                testa = [norm(c) for c in cel]
                if any(c.startswith("data") for c in testa) and any("localit" in c for c in testa):
                    col = {}
                    for i, c in enumerate(testa):
                        for k, pref in (("data", "data"), ("loc", "localit"), ("org", "organizz"), ("den", "denomin"),
                                        ("spec", "spec"), ("tipo", "tipo"), ("cod", "cod"), ("part", "partecip"),
                                        ("pista", "pista")):
                            if c.startswith(pref) and k not in col:
                                col[k] = i
                    continue
                if not col or "data" not in col:
                    continue
                g = lambda k: cel[col[k]] if k in col and col[k] < len(cel) else ""  # noqa: E731
                dd = g("data")
                m = re.search(r"(\d{1,2})(?:/(\d{1,2}))?\.(\d{1,2})\.(\d{4})", dd)
                if not m:
                    continue
                d0 = dt.date(int(m.group(4)), int(m.group(3)), int(m.group(1))).isoformat()
                d1 = dt.date(int(m.group(4)), int(m.group(3)), int(m.group(2))).isoformat() if m.group(2) else None
                loc = g("loc")
                if not loc or norm(loc) in ("da definire", "-"):
                    loc = loc or ""
                den = g("den")
                spec = " / ".join(dict.fromkeys(x.strip() for x in re.split(r"\s+|/", g("spec")) if x.strip() and x.strip() != "-"))
                tit = den if den and den not in ("-",) else ""
                tit = re.split(r"\s+-\s+(?:gara\s+)?valid[ao]\b", tit, flags=re.I)[0].strip()
                if re.match(r"(?i)(gara\s+)?valid[ao]\b", tit):
                    tit = ""
                cat_tit = re.sub(r"(?i)^calendario[- ]+(gare[- ]+)?sci[- ]+alpino[- ]+", "", chiave.replace("-", " "))
                cat_tit = re.sub(r"\s*\d{4}\s*\d{4}.*$", "", cat_tit).strip()
                base = f"Gara {disciplina.lower()}"
                if spec and spec != "-":
                    base += f" {spec}"
                titolo = tit or f"{base} – {loc}" if loc else (tit or base)
                if tit and spec and spec not in tit:
                    titolo = f"{tit} ({spec})"
                comune = comune_da(loc)
                org = organizzatore(g("org"), "sci")
                e = evento(data=d0, data_fine=d1, titolo=titolo, sport="sci", disciplina=disciplina,
                           livello=fisi_livello(g("cod"), g("tipo"), tit), luogo=loc or "Da definire", comune=comune,
                           organizzatore=org, categorie=g("part") or (cat_tit.title() if cat_tit else None),
                           link=u, fonte=u, origine="fisi")
                if in_fvg(e):
                    out.append(e)
        print(f"   {chiave}: {len(out) - n0} gare in FVG")
        if len(out) == n0 and tabelle:
            grezzo("fisi " + chiave, json.dumps(tabelle[:2], ensure_ascii=False))
    # la stessa gara F e M nello stesso giorno: una riga sola
    vist, res = set(), []
    for e in out:
        k = (e["data"], e["titolo"], e["luogo"])
        if k not in vist:
            vist.add(k)
            res.append(e)
    return res


def mod_fci():
    """FCI FVG: tabella "Calendario gare" (TablePress) su fcifriuli.com, una riga per gara e categoria.
    Colonne: data, settore, specialità, categoria, società organizzatrice, nome gara, località."""
    u = "https://www.fcifriuli.com/calendario-gare-ciclistiche-friuli-venezia-giulia/"
    h = get(u).text
    righe = re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S)
    grp = {}
    for r in righe:
        c = dict(re.findall(r'<td class="column-(\d+)"[^>]*>(.*?)</td>', r, re.S))
        if len(c) < 7:
            continue
        d = data_dmy(pulisci(c["1"]))
        if not d:
            continue
        sett, spec, cat, soc, nome, loc = (pulisci(c[k]) for k in "234567")
        k = (d, norm(nome), norm(loc))
        e = grp.get(k)
        if not e:
            e = grp[k] = {"data": d, "titolo": nome.title() if nome.isupper() else nome, "settore": sett,
                          "spec": spec, "soc": soc, "luogo": loc.title() if loc.isupper() else loc, "cat": []}
        if cat and cat not in e["cat"]:
            e["cat"].append(cat)
    if not grp:
        grezzo("fci", h[h.find("<table"):] if "<table" in h else h[-3000:])
    out = []
    for e in grp.values():
        cat = " ".join(e["cat"]).lower()
        livello = ("internazionale" if re.search(r"internaz|uci", cat + e["titolo"].lower()) else
                   "nazionale" if re.search(r"nazional|italian|top class", cat + e["titolo"].lower()) else
                   "promozionale" if re.search(r"giovanissim", cat) and len(e["cat"]) == 1 else "regionale")
        disc = e["spec"] or e["settore"]
        x = evento(data=e["data"], titolo=e["titolo"], sport="ciclismo", disciplina=disc, livello=livello,
                   luogo=e["luogo"], organizzatore=organizzatore(e["soc"], "ciclismo"),
                   categorie=", ".join(e["cat"]) or None, link=u, fonte=u, origine="fci")
        # località piccole (frazioni) non riconosciute: la gara è comunque nel calendario regionale FVG
        out.append(x)
    return out


def mod_fiv():
    """FIV: elenco delle regate su federvela.it/regate (righe con attributi data-*), solo XIII Zona (FVG)."""
    u = "https://federvela.it/regate/"
    h = get(u).text
    out = []
    righe = re.findall(r'<tr class="em-row"([^>]*)>', h)
    for a in righe:
        at = {k: html.unescape(v) for k, v in re.findall(r'data-(\w+)="([^"]*)"', a)}
        if at.get("zon") != "XIII":
            continue
        tit = re.sub(r"^\d{4}-\d{4}\s+", "", at.get("man", "")).strip()
        loc = at.get("loc", "")
        luogo = loc.split(" - ")[0]
        luogo = re.sub(r"\s*\([A-Z]{2}\)", "", luogo).strip() or loc
        tip = at.get("tip", "")
        livello = ("internazionale" if re.search(r"internaz|mondial|europe", tip + tit, re.I) else
                   "nazionale" if re.search(r"nazional|italian", tip + tit, re.I) else "regionale")
        out.append(evento(data=at.get("di"), data_fine=at.get("df") if at.get("df") != at.get("di") else None,
                          titolo=tit, sport="vela", disciplina=tip or None, livello=livello, luogo=luogo,
                          comune=comune_da(loc.split(" - ")[-1]) or comune_da(luogo), categorie=at.get("cla") or None,
                          link=at.get("li") or u, fonte=u, origine="fiv"))
    if not righe:
        grezzo("fiv", h[h.find("<table"):] if "<table" in h else h[-3000:])
    return [e for e in out if e.get("data")]


def mod_fisr():
    """FISR FVG (pattinaggio): calendari per provincia (IDZona 1 TS, 2 UD, 3 GO, 4 PN) dell'anno in corso e del successivo."""
    out = []
    for zona in (1, 2, 3, 4):
        for anno in sorted({OGGI.year, FINE.year}):
            u = f"https://www.fisrfvg.it/core/base_calendario_zona.php?IDZona={zona}&anno={anno}"
            h = get(u).text
            for d, loc, spec, tit in re.findall(r"<tr class='row'><td[^>]*>([^<]+)</td><td><b>(.*?)</b></td>"
                                                r"<td><i>(.*?)</i></td><td>(.*?)</td></tr>", h, re.S):
                dd = data_dmy(d)
                if not dd:
                    continue
                tit, loc, spec = pulisci(tit), pulisci(loc), pulisci(spec)
                livello = ("internazionale" if re.search(r"internaz", tit, re.I) else
                           "nazionale" if re.search(r"italian|nazional", tit, re.I) else
                           "provinciale" if re.search(r"provincial", tit, re.I) else
                           "promozionale" if re.search(r"promozional|esordien|trofeo|saggio", tit, re.I) and
                           not re.search(r"regional", tit, re.I) else "regionale")
                out.append(evento(data=dd, titolo=tit, sport="pattinaggio", disciplina=spec or None, livello=livello,
                                  luogo=loc, link="https://www.fisrfvg.it/", fonte=u, origine="fisr"))
    vist, res = set(), []
    for e in out:
        if e["id"] not in vist:
            vist.add(e["id"])
            res.append(e)
    return res


MESI_EN = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
MESI_IT = {m: i + 1 for i, m in enumerate("gen feb mar apr mag giu lug ago set ott nov dic".split())}


def mod_fijlkam():
    """FIJLKAM FVG: "Gare ed eventi" del comitato (judo, karate, lotta); si tengono quelli con sede in FVG."""
    base = "https://www.fijlkam.it"
    u = base + "/fvg/gare-ed-eventi-friuli-venezia-giulia.html"
    h = get(u).text
    out = []
    blocchi = re.split(r'<div class="eventi-item', h)[1:]
    for b in blocchi:
        cat = pulisci((re.search(r'<span class="category[^"]*">(.*?)</span>', b, re.S) or [None, ""])[1])
        dts = re.findall(r'<div class="date-day">(\d+)</div>\s*<div class="date-month">(\w+)</div>\s*<div class="date-year">(\d{4})</div>', b)
        if not dts:
            continue

        def iso(t):
            mm = MESI_EN.get(t[1][:3].lower()) or MESI_IT.get(t[1][:3].lower())
            return dt.date(int(t[2]), mm, int(t[0])).isoformat() if mm else None
        d0 = iso(dts[0])
        d1 = iso(dts[1]) if len(dts) > 1 else None
        a = re.search(r'<div class="detail-title">.*?<a href="([^"]+)">(.*?)</a>', b, re.S)
        if not a or not d0:
            continue
        loc = pulisci((re.search(r'<span class="location">(.*?)</span>', b, re.S) or [None, ""])[1])
        tit = pulisci(a.group(2))
        com = None
        for parte in re.split(r"\s*[-,–]\s*", loc):
            com = comune_da(parte)
            if com:
                break
        if not com:
            continue
        livello = ("internazionale" if re.search(r"european|open|cup|grand|internaz|world", tit, re.I) else
                   "nazionale" if re.search(r"italian|nazional|a1|a2|serie", tit, re.I) else "regionale")
        out.append(evento(data=d0, data_fine=d1 if d1 != d0 else None, titolo=tit, sport="judo",
                          disciplina=cat.title() or None, livello=livello, luogo=loc, comune=com,
                          link=base + a.group(1), fonte=u, origine="fijlkam"))
    if not blocchi:
        grezzo("fijlkam", h[-3000:])
    return out


MESI_LUNGHI = {m: i + 1 for i, m in enumerate("gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split())}


def mod_fib():
    """FIB FVG (bocce): elenco gare del comitato. Il calendario va da ottobre a settembre ("Calendario 2027" =
    stagione 2026/27): si sceglie con il modulo (POST, il filtro resta nella sessione) e si scorrono le pagine
    con ?start=100, 200... Ogni gara è un blocco: data, provincia, titolo (link), specialità, livello, società, categorie."""
    u = "https://www.federbocce.it/friuliveneziagiulia/gare.html"
    rx_data = re.compile(r"(\d{1,2})\s+(" + "|".join(MESI_LUNGHI) + r")\s+(\d{4})", re.I)
    out, viste = [], set()
    for cal in sorted({OGGI.year + (OGGI.month >= 10), FINE.year + (FINE.month >= 10)}):
        h = get(u, "POST", data={"calendario": str(cal)[2:], "mese": "", "anno": "", "provincie": "",
                                 "specialita": "all", "tipo": "", "cerca-gare": "Cerca"}).text
        for pag in range(0, 15):
            if pag:
                h = get(f"{u}?start={pag * 100}").text
            i = h.find("</form>")
            corpo = h[i:] if i >= 0 else h
            corpo = corpo[:corpo.find('<footer')] if '<footer' in corpo else corpo
            pos = [m for m in rx_data.finditer(re.sub(r"<[^>]+>", lambda t: " " * len(t.group(0)), corpo))]
            if pag == 0 and DEBUG and pos:
                print("   [debug fib blocco]", corpo[max(0, pos[0].start() - 300):pos[0].start() + 1500].replace("\n", " "))
            nuove = 0
            for k, m in enumerate(pos):
                pezzo = corpo[m.start():pos[k + 1].start() if k + 1 < len(pos) else len(corpo)]
                righe = [pulisci(x) for x in re.split(r"<[^>]+>", pezzo)]
                righe = [x for x in righe if x]
                link = re.search(r'href="([^"]+)"[^>]*>(.*?)</a>', pezzo, re.S)
                d = dt.date(int(m.group(3)), MESI_LUNGHI[m.group(2).lower()], int(m.group(1))).isoformat()
                chiave = (d, tuple(righe[:6]))
                if chiave in viste:
                    continue
                viste.add(chiave)
                nuove += 1
                out.append({"data": d, "righe": righe[1:], "link": link.group(1) if link else None,
                            "titolo": pulisci(link.group(2)) if link else None})
            if not nuove:
                if pag == 0:
                    grezzo(f"fib calendario {cal}", corpo[:4000])
                break
    res = []
    for x in out:
        r = x["righe"]
        if DEBUG and len(res) < 5:
            print("   fib righe:", x["data"], r[:8])
        liv = next((t for t in r if re.fullmatch(r"(?i)(inter)?regionale|provinciale|nazionale|internazionale", t)), "")
        spec = next((t for t in r if re.fullmatch(r"(?i)volo|raffa|petanque|boccia paralimpica", t)), "")
        tit = x["titolo"] or (r[1] if len(r) > 1 else "Gara di bocce")
        dopo = r[r.index(liv) + 1:] if liv in r else []
        soc = dopo[0] if dopo else None
        cat = dopo[1] if len(dopo) > 1 else None
        prov = r[0] if r else ""
        livello = {"internazionale": "internazionale", "nazionale": "nazionale", "provinciale": "provinciale"}.get(liv.lower(), "regionale")
        link = x["link"]
        if link and link.startswith("/"):
            link = "https://www.federbocce.it" + link
        org = organizzatore(soc, "bocce") if soc else None
        sig = {"udine": "UD", "pordenone": "PN", "gorizia": "GO", "trieste": "TS"}.get(norm(prov))
        # la fonte indica solo la provincia: il comune non si deduce (l'impianto può non essere quello della società)
        e = evento(data=x["data"], titolo=tit, sport="bocce", disciplina=spec.title() or None,
                   livello="nazionale" if liv.lower() == "interregionale" else livello,
                   luogo=f"Provincia di {prov.title()}" if sig else (prov.title() or "Friuli Venezia Giulia"),
                   comune=None, prov=sig, organizzatore=org, categorie=cat, link=link or u, fonte=u, origine="fib")
        e.pop("comune", None)
        e.pop("pos", None)
        res.append(e)
    return res


MODULI = {"fidal": mod_fidal, "fisi": mod_fisi, "fci": mod_fci, "fiv": mod_fiv, "fisr": mod_fisr,
          "fijlkam": mod_fijlkam, "fib": mod_fib}


# ---------------------------------------------------------------- principale

def manuali():
    m = carica(MANUALE, {"eventi": []})
    out = []
    for e in m.get("eventi", []):
        e = dict(e)
        e.setdefault("origine", "manuale")
        if e.get("comune") and not e.get("pos"):
            p = centro(e["comune"])
            if p:
                e["pos"] = p
        e.setdefault("aggiornato", m.get("aggiornato") or OGGI.isoformat())
        e["id"] = e.get("id") or ev_id(e)
        out.append(e)
    return out


def main():
    prova = "--prova" in sys.argv or DEBUG
    solo = None
    if "--solo" in sys.argv:
        solo = set(sys.argv[sys.argv.index("--solo") + 1].split(","))
    prima = carica(OUT, [])
    print(f"Agenda: dal {OGGI} al {FINE}; eventi già presenti {len(prima)}")
    tutti = []
    for nome, f in MODULI.items():
        vecchi = [e for e in prima if e.get("origine") == nome and nel_periodo(e)]
        if solo and nome not in solo:
            tutti += vecchi
            continue
        t0 = time.time()
        try:
            ev = [e for e in f() if e.get("data") and nel_periodo(e)]
            err = None
        except Exception as ex:  # noqa: BLE001
            ev, err = [], ex
        if err or (not ev and len(vecchi) >= 3):
            print(f"! {nome}: {'errore ' + repr(err) if err else 'nessun evento'}; tengo i {len(vecchi)} eventi già presenti")
            tutti += vecchi
        else:
            print(f"- {nome}: {len(ev)} eventi ({time.time() - t0:.0f} s)")
            tutti += ev
    man = [e for e in manuali() if nel_periodo(e)]
    print(f"- manuale: {len(man)} eventi")
    # gli eventi manuali hanno la precedenza sugli automatici con lo stesso id
    ids_man = {e["id"] for e in man}
    tutti = [e for e in tutti if e["id"] not in ids_man] + man
    vist, finale = set(), []
    for e in sorted(tutti, key=lambda e: (e["data"], e.get("ora") or "", e["titolo"])):
        if e["id"] in vist:
            continue
        vist.add(e["id"])
        finale.append(e)
    per = {}
    for e in finale:
        per[e["sport"]] = per.get(e["sport"], 0) + 1
    print("Eventi per sport:", ", ".join(f"{k} {v}" for k, v in sorted(per.items(), key=lambda x: -x[1])))
    print(f"Totale {len(finale)} (prima {len(prima)}); con comune {sum(1 for e in finale if e.get('comune'))}, "
          f"con società abbinata {sum(1 for e in finale if any(s['id'] == e.get('organizzatore') for s in SOC))}")
    if prova:
        for e in finale[:400]:
            print("  ", e["data"], e.get("data_fine", ""), "|", e["sport"], "|", e["livello"], "|", e["titolo"][:70], "|",
                  e.get("luogo", "")[:30], "|", e.get("comune", "-"), "|", str(e.get("organizzatore", "-"))[:40])
        print("--prova: nessun file scritto")
        return
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(finale, f, ensure_ascii=False, indent=0)
        f.write("\n")
    print("Scritto", OUT)


if __name__ == "__main__":
    main()
