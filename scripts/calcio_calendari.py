"""Calendari ufficiali e variazioni del CALCIO (LND FVG) per scripts/calcio.py.

Fonti (archivio WordPress di friuliveneziagiulia.lnd.it, vedi pipeline/agenti/calendari.md):
  - calendari ufficiali in formato LND ("* ECCELLENZA GIRONE: A *", blocchi "ANDATA: 6/09/26 ! 1 G I O R N A T A !
    RITORNO: 10/01/27", "ORE...: 15:30", righe "I CASA - OSPITE I", poi "ELENCO CAMPI DA GIOCO"): PDF con
    "calendar" nel nome (es. CU-12-CALENDARI-UFFICIALI-20262027.pdf) e PDF con "calendar" dentro gli ZIP degli
    allegati dei Comunicati (letti senza scaricare tutto lo ZIP: indice e singolo file con richieste Range);
  - "MODIFICHE AL PROGRAMMA GARE" dei Comunicati Ufficiali (Recupero Gare, Variazioni Gare, Altre Variazioni,
    Ripetizione Gara) e "IL SABATO DEL NOSTRO CALCIO" (anticipi al sabato del Comitato Regionale).
Le funzioni ricevono il modulo calcio (C) per usare le stesse normalizzazioni dei nomi (norm, compatto, chiave,
canon_cat, classifica_cat).
Stato in config/calcio_calendari.json: file già letti, calendari estratti, variazioni lette.
"""
import datetime as dt
import io
import json
import os
import re
import time
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATO_CAL = os.path.join(ROOT, "config", "calcio_calendari.json")
GIORNI_MODIFICHE = 35  # alla prima esecuzione si rileggono le variazioni dei comunicati degli ultimi 35 giorni
PAUSA = 1.5        # secondi tra un file e l'altro (il sito LND risponde con pagine d'errore se si chiede troppo in fretta)
MAX_ZIP = 15       # ZIP nuovi letti per esecuzione (gli altri alla prossima)
MAX_CU_VAR = 25    # comunicati nuovi letti per le variazioni per esecuzione


class Bloccato(Exception):
    """Il sito ha risposto con qualcosa che non è il file chiesto: per oggi basta."""

DELEG = [(r"TRIESTE|-TS-|\bTS\b", "Trieste"), (r"UDINE|-UD-|\bUD\b", "Udine"), (r"PORDENONE|-PN-|\bPN\b", "Pordenone"),
         (r"GORIZIA|-GO-|\bGO\b", "Gorizia"), (r"TOLMEZZO|CARNIC", "Tolmezzo")]


def stato_vuoto():
    return {"calendari_letti": [], "zip_letti": [], "calendari": [], "modifiche_lette": [], "modifiche": []}


def carica():
    if os.path.exists(STATO_CAL):
        s = json.load(open(STATO_CAL))
        for k, v in stato_vuoto().items():
            s.setdefault(k, v)
        return s
    return stato_vuoto()


def salva(stato):
    json.dump(stato, open(STATO_CAL, "w"), ensure_ascii=False, separators=(",", ":"))


def data_iso(d):
    g, m, a = re.split(r"[/.]", d.strip())
    a = ("20" + a) if len(a) == 2 else a
    return f"{a}-{int(m):02d}-{int(g):02d}"


def ora_ok(o):
    m = re.fullmatch(r"(\d{1,2})[:.](\d{2})", (o or "").strip())
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m and int(m.group(1)) < 24 else None


def comitato_di(testo, fonte=""):
    f = fonte.rsplit("/", 1)[-1].upper()
    for rx, nome in DELEG:
        if re.search(rx, testo.upper()):
            return nome
    pf = re.match(r"^(ALL_)?(TS|PN|GO|UD|TOL)[_-]", f)
    if pf:
        return {"TS": "Trieste", "PN": "Pordenone", "GO": "Gorizia", "UD": "Udine", "TOL": "Tolmezzo"}[pf.group(2)]
    for rx, nome in DELEG[:1] + DELEG[2:]:
        if re.search(rx, f):
            return nome
    return "Regionale"


def categoria(C, testo, comitato):
    """Titolo del calendario o della sezione -> nome standard di calcio.py (o None se non è un campionato gestito)."""
    comp = re.sub(r"[^A-Z0-9]", "", C.strip_acc(testo.upper()))
    if not C.RX_CAT_OK.search(comp) or C.RX_CAT_NO.search(comp) or C.RX_CAT_ALTRO.search(comp):
        return None
    cs = C.classifica_cat(C.canon_cat(testo))
    if cs and cs.startswith("Under") and not re.search(r"regionali|provinciali|élite", cs):
        cs = cs.replace(f"Under {cs.split()[1]}", f"Under {cs.split()[1]} " + ("regionali" if comitato == "Regionale" else "provinciali"), 1)
    return cs


# ---------------------------------------------------------------- lettura di PDF e ZIP
class FileRemoto(io.RawIOBase):
    """File remoto leggibile a pezzi con HTTP Range (per aprire uno ZIP leggendo solo indice e file voluti)."""

    def __init__(self, S, url):
        self.S, self.url, self.pos = S, url, 0
        r = S.head(url, timeout=60, allow_redirects=True)
        r.raise_for_status()
        if r.headers.get("Accept-Ranges", "").lower() != "bytes" or not r.headers.get("Content-Length"):
            raise IOError("Range non supportato")
        self.size = int(r.headers["Content-Length"])
        self.blocchi = {}

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = max(0, min(n, self.size - self.pos))
        if not n:
            return b""
        k = (self.pos, n)
        if k not in self.blocchi:
            time.sleep(1.0)
            r = self.S.get(self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"}, timeout=90)
            if r.status_code != 206:
                raise IOError("Range non supportato")
            self.blocchi = {k: r.content}
        b = self.blocchi[k]
        self.pos += len(b)
        return b

    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d
        return len(d)


def pdf_da_zip(S, url, filtro=r"calendar"):
    """[(nome, byte)] dei PDF dello ZIP il cui nome corrisponde al filtro."""
    try:
        z = zipfile.ZipFile(io.BufferedReader(FileRemoto(S, url), buffer_size=65536))
    except zipfile.BadZipFile:
        raise Bloccato("risposta non ZIP")
    except Exception:
        time.sleep(PAUSA)
        r = S.get(url, timeout=120); r.raise_for_status()
        if not r.content.startswith(b"PK"):
            raise Bloccato("risposta non ZIP")
        z = zipfile.ZipFile(io.BytesIO(r.content))
    out = []
    for n in z.namelist():
        base = n.rsplit("/", 1)[-1]
        if base.lower().endswith(".pdf") and not base.startswith("._") and re.search(filtro, base, re.I):
            out.append((n, z.read(n)))
    return out


def righe_testo(dati):
    """Righe del PDF così come le scrive pdfplumber (tutta la larghezza della pagina)."""
    import pdfplumber
    if not dati.lstrip()[:5].startswith(b"%PDF"):
        raise Bloccato("risposta non PDF")
    with pdfplumber.open(io.BytesIO(dati)) as pdf:
        return [l.rstrip() for p in pdf.pages for l in (p.extract_text() or "").splitlines() if l.strip()]


# ---------------------------------------------------------------- calendari in formato LND
RX_TIT = re.compile(r"^\W*\*\s*(.+?)\s+GIRONE:\s*([A-Z0-9]{1,3})\s*\*")
RX_AND = re.compile(r"ANDATA:\s*(\d{1,2}/\d{1,2}/\d{2,4})")
RX_RIT = re.compile(r"RITORNO:\s*(\d{1,2}/\d{1,2}/\d{2,4})")
RX_GIO = re.compile(r"(\d{1,2})\s*G\s*I\s*O\s*R\s*N\s*A\s*T\s*A")
RX_ORE = re.compile(r"ORE\.*:\s*(\d{1,2}[:.]\d{2})")
RX_CAMPI = re.compile(r"E\s*L\s*E\s*N\s*C\s*O\s+C\s*A\s*M\s*P\s*I")


def celle(l):
    """'I A - B I I C - D I' oppure '| A - B | | C - D |' -> ['A - B', 'C - D']."""
    t = re.sub(r"^\s*[I|]\s+|\s+[I|]\s*$", "", l.strip())
    return [c.strip() for c in re.split(r"\s+[I|!]\s+[I|!]\s+", t) if c.strip()]


def dividi_coppia(testo, squadre, C):
    """'CASA - OSPITE' (i nomi possono contenere ' - ') -> (casa, ospite) usando i nomi del girone."""
    parti = re.split(r"\s+-\s+|\s+-(?=\S)|(?<=\S)-\s+", testo)
    noti = {C.compatto(x) for x in squadre}
    scelte = []
    for i in range(1, len(parti)):
        a, b = " - ".join(parti[:i]).strip(), " - ".join(parti[i:]).strip()
        scelte.append(((C.compatto(a) in noti) + (C.compatto(b) in noti), -abs(len(a) - len(b)), a, b))
    if not scelte:
        return None, None
    best = max(scelte)
    return best[2], best[3]


def leggi_calendario_lnd(righe, fonte, C):
    """-> gironi [{"titolo", "girone", "comitato", "categoria", "squadre", "campi", "partite": [[gio, casa, osp, data, ora]]}]"""
    gironi, cur, blocco, in_campi = [], None, None, False
    for l in righe:
        mt = RX_TIT.match(l)
        if mt:
            com = comitato_di(mt.group(1), fonte)
            cur = {"titolo": mt.group(1).strip(), "girone": mt.group(2), "comitato": com,
                   "categoria": categoria(C, mt.group(1), com), "grezze": [], "campi": {}, "fonte": fonte}
            gironi.append(cur); blocco = None; in_campi = False
            continue
        if cur is None:
            continue
        if RX_CAMPI.search(l):
            in_campi = True; continue
        if in_campi:
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            if len(c) >= 4 and c[0] and not c[0].upper().startswith(("SOCIETA", "COMITATO", "-")) and re.fullmatch(r"\d{3,6}", c[1] or ""):
                den, ora, ind = c[2], (c[3] if len(c) > 3 else ""), (c[4] if len(c) > 4 else "")
                campo = ", ".join(x for x in (re.sub(r"\s+", " ", den).title(), re.sub(r"\s+", " ", ind).title()) if x)
                cur["campi"][c[0]] = {"campo": campo, "ora": ora_ok(ora)}
            continue
        a, r = RX_AND.findall(l), RX_RIT.findall(l)
        if a and r and len(a) == len(r):
            blocco = {"andata": a, "ritorno": r, "gio": RX_GIO.findall(l), "ore": []}
            continue
        if blocco is not None and RX_ORE.search(l):
            o = RX_ORE.findall(l)
            blocco["ore"] = [(o[2 * i] if 2 * i < len(o) else None, o[2 * i + 1] if 2 * i + 1 < len(o) else None) for i in range(len(blocco["andata"]))]
            if not blocco["gio"]:
                blocco["gio"] = RX_GIO.findall(l)
            continue
        if blocco is None or re.match(r"^\W*[.I|][-.]{10,}", l.strip()) or "------" in l:
            continue
        cs = celle(l)
        if not cs or len(cs) > len(blocco["andata"]) or not all(" - " in c or "-" in c for c in cs):
            continue
        for i, c in enumerate(cs):
            if i >= len(blocco["gio"]) or re.match(r"riposa", c, re.I):
                continue
            ore = blocco["ore"][i] if i < len(blocco["ore"]) else (None, None)
            cur["grezze"].append((int(blocco["gio"][i]), c, data_iso(blocco["andata"][i]), ora_ok(ore[0]),
                                  data_iso(blocco["ritorno"][i]), ora_ok(ore[1])))
    out = []
    for g in gironi:
        squadre = list(g["campi"])
        partite = []
        n_sq = len(g["campi"])
        # giornate di andata = squadre - 1 (pari) o squadre (dispari); senza elenco campi, la giornata più alta letta
        n_and = (n_sq - 1 if n_sq % 2 == 0 else n_sq) if n_sq >= 4 else max([x[0] for x in g["grezze"]] or [0])
        for gio, testo, da, oa, dr, orr in g["grezze"]:
            casa, osp = dividi_coppia(testo, squadre, C)
            if not casa or not osp:
                continue
            oc = (g["campi"].get(casa) or {}).get("ora")
            oo = (g["campi"].get(osp) or {}).get("ora")
            partite.append([gio, casa, osp, da, oc or oa])
            partite.append([gio + n_and, osp, casa, dr, oo or orr])
        if not squadre:
            squadre = sorted({p[1] for p in partite} | {p[2] for p in partite})
        if g["categoria"] and len(partite) >= 4:
            out.append({k: g[k] for k in ("titolo", "girone", "comitato", "categoria", "campi", "fonte")} |
                       {"squadre": squadre, "andata": n_and, "partite": partite})
    return out


# ---------------------------------------------------------------- variazioni dei Comunicati
RX_MOD_INIZIO = re.compile(r"^\s*MODIFICHE AL PROGRAMMA GARE\s*$", re.I)
RX_MOD_FINE = re.compile(r"^\s*(RISULTATI GARE|GIUSTIZIA SPORTIVA|DECISIONI|ERRATA CORRIGE|CLASSIFICHE)\s*$", re.I)
RX_REG = re.compile(r"^([A-Z0-9]{1,2})\s+(\d{1,2})\s+([AR])\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{1,2}[:.]\d{2})\s*(.*)$")
RX_DEL = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(\d{1,2})\s+([AR])\s+(.+?)\s+(?:(\d{2}/\d{2}/\d{4})\s+)?(\d{1,3}[:.]\d{1,2})"
                    r"(?:\s+(\d{1,2}[:.]\d{2}))?\s*(.*)$")
RX_DEL_DATA = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(\d{1,2})\s+([AR])\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s*$")
RX_GIRONE = re.compile(r"^GIRONE\s+([A-Z0-9]{1,3})\s*$", re.I)
RX_TAB = re.compile(r"^(N°|Gior\.?|Girone Squadra|Data Gara|Recupero Gare|Variazioni Gare|Altre Variazioni|Ripetizione Gara|"
                    r"Pag\.|Anticip|Posticip|DATA DA|DESTINARSI)", re.I)
RX_SAB_G = re.compile(r"(\d{1,2})\s*GIORNATA\s+(ANDATA|RITORNO)\s+SABATO\s+(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})", re.I)
RX_SAB = re.compile(r"^(?:(ECC|PR|1C(?:\s+[A-Z])?|2C(?:\s+[A-Z])?)\s+)?(.+?)\s*[–-]{1,2}\s*(.+?)\s+(\d{1,2}:\d{2})\b")
SIGLE = {"ECC": "Eccellenza", "PR": "Promozione", "1C": "Prima Categoria", "2C": "Seconda Categoria"}


def leggi_modifiche(righe, fonte, pubbl, comitato, C):
    """Righe del Comunicato -> variazioni [{categoria, girone, giornata, ar, squadre|casa/ospite, data, ora, campo, ...}]"""
    out, dentro, cat, gir = [], False, None, None
    for i, l in enumerate(righe):
        l = l.strip()
        if RX_MOD_INIZIO.match(l):
            dentro, cat, gir = True, None, None; continue
        if dentro and RX_MOD_FINE.match(l):
            dentro = False; continue
        if not dentro:
            continue
        mg = RX_GIRONE.match(l)
        if mg:
            gir = mg.group(1).upper(); continue
        m = RX_REG.match(l)
        if m and cat:
            campo = m.group(7).strip()
            if not campo:  # il nome del campo va a capo sopra e sotto la riga
                vic = [x.strip() for x in (righe[i - 1] if i else "", righe[i + 1] if i + 1 < len(righe) else "")
                       if x.strip() and not RX_TAB.match(x.strip()) and not RX_REG.match(x.strip()) and not categoria(C, x, comitato)]
                campo = " ".join(vic)
            out.append({"categoria": cat, "girone": m.group(1), "giornata": int(m.group(2)), "ar": m.group(3),
                        "squadre": m.group(4), "data": data_iso(m.group(5)), "ora": ora_ok(m.group(6)),
                        "campo": campo.title(), "comitato": comitato, "fonte": fonte, "pubbl": pubbl})
            continue
        m = RX_DEL.match(l)
        if m and cat:
            out.append({"categoria": cat, "girone": gir, "giornata": int(m.group(2)), "ar": m.group(3), "squadre": m.group(4),
                        "data": data_iso(m.group(1)), "ora": ora_ok(m.group(6)),
                        "campo": m.group(8).strip().title() if m.group(8) and not re.match(r"^\d", m.group(8)) else "",
                        "comitato": comitato, "fonte": fonte, "pubbl": pubbl})
            continue
        m = RX_DEL_DATA.match(l)
        if m and cat:  # nuova data senza ora
            out.append({"categoria": cat, "girone": gir, "giornata": int(m.group(2)), "ar": m.group(3), "squadre": m.group(4),
                        "data": data_iso(m.group(1)), "ora": None, "campo": "", "comitato": comitato, "fonte": fonte, "pubbl": pubbl})
            continue
        if not RX_TAB.match(l) and l.isupper() and len(l) < 70:
            c = categoria(C, l, comitato)
            if c or re.search(r"CAMPIONATO|CATEGORIA|UNDER|COPPA|TORNEO|ESORDIENTI|PULCINI|JUNIORES|ALLIEVI|GIOVANISSIMI", l, re.I):
                cat, gir = c, None
    # "IL SABATO DEL NOSTRO CALCIO" (Comitato Regionale): anticipi al sabato con l'ora
    data = gio = None; cat = None
    for l in righe:
        l = l.strip()
        mg = RX_SAB_G.search(l)
        if mg:
            gio, ar = int(mg.group(1)), "A" if mg.group(2).upper() == "ANDATA" else "R"
            data = f"{mg.group(5)}-{int(mg.group(4)):02d}-{int(mg.group(3)):02d}"; cat = None
            continue
        if data is None:
            continue
        m = RX_SAB.match(l)
        if not m:
            if l and not l.startswith("Pag.") and not re.search(r"\d{1,2}:\d{2}", l):
                data = None  # fine dell'elenco
            continue
        if m.group(1):
            sig = m.group(1).split()
            cat = (SIGLE.get(sig[0]), sig[1] if len(sig) > 1 else None)
        if not cat or not cat[0]:
            continue
        out.append({"categoria": cat[0], "girone": cat[1], "giornata": gio, "ar": ar, "casa": m.group(2).strip(),
                    "ospite": m.group(3).strip(" -–"), "data": data, "ora": ora_ok(m.group(4)), "campo": "",
                    "comitato": "Regionale", "fonte": fonte, "pubbl": pubbl})
    return out


# ---------------------------------------------------------------- abbinamento dei nomi
def simile(a, b, C):
    """Punteggio di somiglianza tra due nomi di squadra (0 = diversi)."""
    ka, kb = C.chiave(a), C.chiave(b)
    if not ka or not kb:
        return 0
    if ka == kb:
        return 100
    if ka.startswith(kb) or kb.startswith(ka):
        return 80 if min(len(ka), len(kb)) >= 5 else 0
    ta = set(C.norm(a).split()) - {"ASD", "SSD", "AC", "US", "USD", "APD", "POL", "ACD", "CALCIO", "A", "S", "D", "FC", "SQ", "B"}
    tb = set(C.norm(b).split()) - {"ASD", "SSD", "AC", "US", "USD", "APD", "POL", "ACD", "CALCIO", "A", "S", "D", "FC", "SQ", "B"}
    if not ta or not tb:
        return 0
    j = len(ta & tb) / len(ta | tb)
    return int(60 * j) if j >= 0.5 else 0


def mappa_nomi(nomi_cal, nomi_gir, C):
    """Nome del calendario -> nome del girone (solo abbinamenti sicuri: punteggio migliore e unico)."""
    out = {}
    for n in nomi_cal:
        sc = sorted(((simile(n, g, C), g) for g in nomi_gir), reverse=True)
        if sc and sc[0][0] and (len(sc) == 1 or sc[0][0] > sc[1][0]):
            out[n] = sc[0][1]
    # "sq.B" e simili: due nomi del calendario non possono finire sulla stessa squadra
    usati = {}
    for n, g in list(out.items()):
        usati.setdefault(g, []).append(n)
    for g, ns in usati.items():
        if len(ns) > 1:
            for n in ns:
                if C.chiave(n) != C.chiave(g):
                    out.pop(n)
    return out


def dividi_squadre(testo, nomi, C):
    """'RORAI PORCIA AZZANESE' (due nomi senza separatore) -> (casa, ospite) tra i nomi del girone."""
    tk = C.norm(testo).split()
    best = None
    for i in range(1, len(tk)):
        a, b = " ".join(tk[:i]), " ".join(tk[i:])
        sa = max(((simile(a, n, C), n) for n in nomi), default=(0, None))
        sb = max(((simile(b, n, C), n) for n in nomi), default=(0, None))
        if sa[0] and sb[0] and sa[1] != sb[1]:
            sc = sa[0] + sb[0]
            if best is None or sc > best[0]:
                best = (sc, sa[1], sb[1])
    return (best[1], best[2]) if best else (None, None)


# ---------------------------------------------------------------- lettura delle fonti
def elenco_media(C, cerca, mime=None, dopo=None):
    out, pagina = [], 1
    while True:
        par = {"search": cerca, "per_page": 100, "page": pagina, "after": dopo or C.INIZIO, "_fields": "date,source_url"}
        if mime:
            par["mime_type"] = mime
        r = C.S.get(f"{C.BASE}/wp-json/wp/v2/media", params=par, timeout=60)
        if r.status_code == 400:
            break
        r.raise_for_status()
        js = r.json()
        out += js
        if len(js) < 100:
            break
        pagina += 1
        time.sleep(PAUSA)
    return sorted(out, key=lambda x: x["date"])


def aggiungi_calendari(stato, gironi, pubbl):
    """Un calendario più recente dello stesso girone sostituisce quello vecchio (calendari riemessi/aggiornati)."""
    for g in gironi:
        g["pubbl"] = pubbl
        chiave = (g["comitato"], g["categoria"], g["girone"])
        stato["calendari"] = [x for x in stato["calendari"]
                              if (x["comitato"], x["categoria"], x["girone"]) != chiave or x.get("pubbl", "") > pubbl]
        if not any((x["comitato"], x["categoria"], x["girone"]) == chiave for x in stato["calendari"]):
            stato["calendari"].append(g)
            print(f"  calendario {g['comitato']} | {g['categoria']} | girone {g['girone']}: {len(g['squadre'])} squadre, "
                  f"{len(g['partite'])} partite ({g['fonte'].rsplit('/', 1)[-1]})")


def leggi_fonti(C, elenco_cu, stato, oggi):
    """Calendari nuovi (PDF e ZIP dell'archivio) e variazioni dei comunicati non ancora letti."""
    # 1. calendari: PDF con "calendar" nel nome, poi ZIP degli allegati (solo i PDF "calendar..." al loro interno)
    try:
        pdf = [x for x in elenco_media(C, "calendar") if x["source_url"].lower().endswith(".pdf")]
        zips = [x for x in elenco_media(C, "allegat", "application/zip") + elenco_media(C, "calendar", "application/zip")]
    except Exception as e:
        print(f"calendari: archivio non letto ({e})"); pdf, zips = [], []
    bloccato = False
    for x in pdf:
        u = x["source_url"]
        if u in stato["calendari_letti"] or bloccato:
            continue
        try:
            time.sleep(PAUSA)
            r = C.S.get(u, timeout=120); r.raise_for_status()
            aggiungi_calendari(stato, leggi_calendario_lnd(righe_testo(r.content), u, C), x["date"][:10])
            stato["calendari_letti"].append(u)
        except Bloccato as e:
            print(f"  ! calendario {u}: {e}: il sito non risponde bene, il resto alla prossima esecuzione"); bloccato = True
        except Exception as e:
            print(f"  ! calendario {u}: {e}")
    visti = set()
    for x in zips:
        u = x["source_url"]
        if u in stato["zip_letti"] or u in visti or bloccato or len(visti) >= MAX_ZIP:
            continue
        visti.add(u)
        try:
            for nome, dati in pdf_da_zip(C.S, u):
                fonte = u + "#" + nome.rsplit("/", 1)[-1]
                aggiungi_calendari(stato, leggi_calendario_lnd(righe_testo(dati), fonte, C), x["date"][:10])
            stato["zip_letti"].append(u)
        except Bloccato as e:
            print(f"  ! zip {u}: {e}: il sito non risponde bene, il resto alla prossima esecuzione"); bloccato = True
        except Exception as e:
            print(f"  ! zip {u}: {e}")
    # 2. variazioni dei comunicati (alla prima esecuzione: quelli degli ultimi GIORNI_MODIFICHE giorni)
    dal = (dt.date.fromisoformat(oggi) - dt.timedelta(days=GIORNI_MODIFICHE)).isoformat()
    nuove = lette = 0
    for x in sorted(elenco_cu, key=lambda x: x["date"], reverse=True):  # prima i più recenti
        u = x["source_url"]
        if u in stato["modifiche_lette"] or x["date"][:10] < dal or bloccato or lette >= MAX_CU_VAR:
            continue
        lette += 1
        try:
            righe = righe_testo(C.scarica(u))
            mod = leggi_modifiche(righe, u, x["date"][:10], C.comitato_cu(u, righe), C)
            stato["modifiche"] += mod; nuove += len(mod)
            stato["modifiche_lette"].append(u)
        except Bloccato as e:
            print(f"  ! variazioni {u}: {e}: il sito non risponde bene, il resto alla prossima esecuzione"); bloccato = True
        except Exception as e:
            print(f"  ! variazioni {u}: {e}")
    limite = (dt.date.fromisoformat(oggi) - dt.timedelta(days=60)).isoformat()
    stato["modifiche"] = [m for m in stato["modifiche"] if (m.get("data") or "") >= limite]
    print(f"calendari in memoria: {len(stato['calendari'])}; variazioni nuove: {nuove}, in memoria: {len(stato['modifiche'])}")


# ---------------------------------------------------------------- partite future di un girone
def futuri(C, k, nomi, giocate, andata, stato, oggi):
    """Partite future del girone k=(comitato, categoria, girone): calendario ufficiale + variazioni in ordine di
    pubblicazione. nomi = squadre del girone (come nei risultati), giocate = coppie (casa, ospite) compatte già
    giocate. -> ([partite], n. variazioni applicate)"""
    cal = [c for c in stato["calendari"] if (c["comitato"], c["categoria"], c["girone"]) == tuple(k)]
    voci, mappa = {}, {}
    if cal:
        c = max(cal, key=lambda x: x.get("pubbl", ""))
        mappa = mappa_nomi(c["squadre"], nomi, C)
        if len(mappa) < 0.6 * len(c["squadre"]):
            print(f"  {k}: calendario scartato, squadre riconosciute {len(mappa)} su {len(c['squadre'])}")
            mappa = None
        else:
            for gio, casa, osp, data, ora in c["partite"]:
                ca, os_ = mappa.get(casa, casa), mappa.get(osp, osp)
                if (C.compatto(ca), C.compatto(os_)) in giocate:
                    continue
                campo = (c["campi"].get(casa) or {}).get("campo", "")
                voci[(C.compatto(ca), C.compatto(os_))] = {"giornata": gio, "data": data, "ora": ora or "", "casa": ca,
                                                           "ospite": os_, "campo": campo}
    tutti = list(nomi) + [v for v in (mappa or {}).values()]
    applicate = 0
    for m in sorted(stato["modifiche"], key=lambda m: m.get("pubbl", "")):
        if m["comitato"] != k[0] or m["categoria"] != k[1] or (m.get("girone") and m["girone"] != k[2]):
            continue
        if m.get("squadre"):
            ca, os_ = dividi_squadre(m["squadre"], tutti, C)
        else:
            sa = max(((simile(m["casa"], n, C), n) for n in tutti), default=(0, None))
            sb = max(((simile(m["ospite"], n, C), n) for n in tutti), default=(0, None))
            soglia = 60 if not m.get("girone") else 1
            ca, os_ = (sa[1], sb[1]) if sa[0] >= soglia and sb[0] >= soglia and sa[1] != sb[1] else (None, None)
        if not ca or not os_:
            continue
        kk = (C.compatto(ca), C.compatto(os_))
        if kk in giocate:
            continue
        v = voci.get(kk)
        if v is None:  # recupero di una gara non in calendario (o calendario non disponibile)
            v = voci[kk] = {"giornata": m["giornata"] + (andata if m.get("ar") == "R" else 0), "data": "", "ora": "",
                            "casa": ca, "ospite": os_, "campo": ""}
        v["data"] = m["data"]
        if m.get("ora"):
            v["ora"] = m["ora"]
        if m.get("campo"):
            v["campo"] = m["campo"]
        v["fonte_var"] = m["fonte"]
        applicate += 1
    out = [v for v in voci.values() if (v.get("data") or "") >= oggi]
    return sorted(out, key=lambda v: (v["giornata"], v["data"], v["ora"])), applicate
