"""Aggiornamento automatico della PALLAVOLO dai portali FIPAV (piattaforma PowerSPORT), senza intelligenza artificiale.

Per ogni girone di config/pallavolo.json:
  1. legge la classifica ufficiale:  https://<host>/classifica.aspx?CId=<cid>
  2. legge le gare dalla pagina risultati del comitato (risultati-classifiche.aspx?...&DataDa=<lunedì>&PId=<pid>),
     una pagina per settimana, tenendo le gare della sezione del girone:
       - normale (ogni ora nel fine settimana): settimana scorsa, corrente e prossima;
       - --completo (una volta al giorno, di notte): dalla settimana scorsa in avanti finché le pagine
         restituiscono gare (si smette dopo SETTIMANE_VUOTE settimane vuote di fila, al massimo MAX_SETTIMANE),
         così ogni girone ha il calendario completo pubblicato con data, ora e impianto aggiornati;
  3. unisce le gare lette a quelle già presenti in data/risultati.json per NUMERO GARA (campo "gara"; per le
     gare salvate prima che il numero fosse registrato, per squadre): una gara spostata cambia data, ora e
     impianto ma resta nella sua giornata. Poi aggiorna classifica, giornata e data.

Protezioni: se una classifica letta ha meno squadre di quella esistente, o la lettura fallisce, il girone resta com'era.
Uso:  python scripts/volley.py            (aggiorna data/risultati.json)
      python scripts/volley.py --dump     (salva anche le pagine scaricate in debug/ per controllare il parser)
      python scripts/volley.py --solo <slug>
      python scripts/volley.py --completo (calendario completo: tutte le settimane con gare)
      python scripts/volley.py --prova    (non tocca data/risultati.json: scrive /tmp/risultati_prova.json)
      python scripts/volley.py --rapido   (giro rapido delle fasce di gara, vedi pipeline/agenti/tempo-reale.md: solo le
                                           pagine settimanali dei risultati, settimana corrente e, il lunedì e il martedì,
                                           la precedente; la classifica si rilegge solo nei gironi con risultati nuovi)
Classifica provvisoria: se la classifica ufficiale non conta ancora tutte le gare con risultato (il portale aggiorna la
classifica dopo i risultati), le gare mancanti vengono sommate alla classifica ufficiale (3-0/3-1: 3 punti, 3-2: 2 e 1)
e il girone riceve "classifica_provvisoria": true, finché la classifica ufficiale non le conta.
"""
import json, os, re, sys, time, datetime as dt
import requests
from abbinamenti import applica_comuni  # scripts/abbinamenti.py
from bs4 import BeautifulSoup
import tempo_reale as TR  # scripts/tempo_reale.py

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
CFG = os.path.join(ROOT, "config", "pallavolo.json")
DEBUG = os.path.join(ROOT, "debug")
UA = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (+https://github.com/; app non ufficiale di consultazione)")
PAUSA = 1.5  # secondi tra le richieste: siamo ospiti dei portali federali
MAX_SETTIMANE = 30   # lettura completa: al massimo 30 settimane dopo quella corrente
SETTIMANE_VUOTE = 3  # ... e ci si ferma dopo 3 settimane di fila senza gare (la pausa di Natale dura meno)
PROVA = "/tmp/risultati_prova.json"
S = requests.Session()
S.headers["User-Agent"] = UA
_cache = {}


def get(url, dump=False):
    if url in _cache:
        return _cache[url]
    time.sleep(PAUSA)
    r = S.get(url, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    _cache[url] = r.text
    if dump:
        os.makedirs(DEBUG, exist_ok=True)
        name = re.sub(r"[^a-zA-Z0-9]+", "_", url)[-120:] + ".html"
        open(os.path.join(DEBUG, name), "w", encoding="utf-8").write(r.text)
    return r.text


def norm(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def key(s):
    return re.sub(r"[^a-z0-9]", "", norm(s).lower())


def cells(tr):
    return [norm(td.get_text(" ")) for td in tr.find_all(["td", "th"])]


def parse_classifica(html):
    """Righe: posizione, squadra, poi numeri (punti, giocate, vinte, perse, set vinti, set persi, ...)."""
    soup = BeautifulSoup(html, "html.parser")
    best = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            c = [x for x in cells(tr) if x != ""]
            if len(c) < 5 or not re.fullmatch(r"\d{1,2}", c[0]):
                continue
            name_i = next((i for i in range(1, len(c)) if not re.fullmatch(r"[\d.,:]+", c[i])), None)
            if name_i is None:
                continue
            nums = [x for x in c[name_i + 1:] if re.fullmatch(r"-?\d+", x)]
            if len(nums) < 4:
                continue
            n = list(map(int, nums))
            r = {"pos": int(c[0]), "squadra": c[name_i], "punti": n[0], "g": n[1], "v": n[2], "p": n[3]}
            if len(n) >= 6:
                r["set_v"], r["set_p"] = n[4], n[5]
            rows.append(r)
        if len(rows) > len(best):
            best = rows
    # controllo di coerenza: posizioni 1..N e partite vinte+perse = giocate
    ok = [r for r in best if r["v"] + r["p"] == r["g"]]
    if len(ok) < max(2, int(0.8 * len(best))):
        return []
    return best


RX_DATA = re.compile(r"(\d{2})/(\d{2})/(\d{2,4})(?:\s+(\d{1,2}[:.]\d{2}))?")
RX_RIS = re.compile(r"^(\d)\s*-\s*(\d)$")
RX_PARZ = re.compile(r"\d{1,2}-\d{1,2}")


RX_CID = re.compile(r"classifica\.aspx\?CId=(\d+)", re.I)


def parse_gare(html):
    """La pagina risultati è una tabella unica divisa in sezioni, una per girone:
    riga titolo (con i link classifica.aspx?CId=... se il girone ha classifica; le Coppe non li hanno),
    riga intestazione "Gara | G | Data / ora | Squadra casa | Squadra ospite | Risul. | Dettagli",
    poi una riga per gara: numero, giornata, data/ora, casa, ospite, risultato, parziali, impianto."""
    soup = BeautifulSoup(html, "html.parser")
    pos = lambda t: (t.sourceline or 0, t.sourcepos or 0)
    links = [(pos(a), RX_CID.search(a["href"]).group(1)) for a in soup.find_all("a", href=True) if RX_CID.search(a["href"])]
    gare, cid, camp, ultima_gara = [], None, "", (0, 0)
    for tr in soup.find_all("tr"):
        c = [x for x in cells(tr) if x != ""]
        if not c:
            continue
        di = next((i for i, x in enumerate(c) if RX_DATA.search(x)), None)
        if di is None:
            if c[0].lower().startswith("gara"):
                # intestazione di una sezione: il girone è il link "classifica" più vicino che sta tra
                # l'ultima gara della sezione precedente e questa intestazione; nessun link = Coppa/altro
                tra = [x for p, x in links if ultima_gara < p < pos(tr)]
                cid = tra[-1] if tra else None
            else:
                camp = " ".join(c)[:120]
            continue
        ultima_gara = pos(tr)
        pre = [x for x in c[:di] if re.fullmatch(r"\d{1,5}", x)]
        rest = c[di + 1:]
        ri = next((i for i, x in enumerate(rest) if RX_RIS.match(x)), None)
        teams = [x for x in (rest[:ri] if ri is not None else rest) if not RX_PARZ.fullmatch(x) and not re.fullmatch(r"[\d\s:.-]*", x)]
        if len(teams) < 2:
            continue
        d = RX_DATA.search(c[di])
        y = d.group(3); y = ("20" + y) if len(y) == 2 else y
        g = {"num": pre[0] if pre else "", "giornata": int(pre[1]) if len(pre) > 1 else None, "cid": cid,
             "data": f"{y}-{d.group(2)}-{d.group(1)}", "ora": (d.group(4) or "").replace(".", ":"),
             "casa": teams[0], "ospite": teams[1], "risultato": "", "parziali": "", "campo": "", "campionato": camp}
        after = rest[ri + 1:] if ri is not None else rest[2:]
        if ri is not None:
            m = RX_RIS.match(rest[ri]); g["risultato"] = f"{m.group(1)}-{m.group(2)}"
        parz = [x for x in after if RX_PARZ.search(x) and re.fullmatch(r"[\d\s,;-]+", x)]
        if parz:
            g["parziali"] = ", ".join(RX_PARZ.findall(" ".join(parz)))
        campo = [x for x in after if not re.fullmatch(r"[\d\s,;:-]+", x)]
        if campo:
            g["campo"] = campo[-1]
        gare.append(g)
    return gare


def lunedi(d):
    return d - dt.timedelta(days=d.weekday())


def url_settimana(cfg, lun):
    data = lun.strftime("%d%%2f%m%%2f%Y")
    q = f"DataDa={data}&StatoGara=&CId=&SId=&PId={cfg['pid']}&btFiltro=CERCA"
    if cfg.get("comitato_id"):
        q = f"ComitatoId={cfg['comitato_id']}&" + q
    return f"https://{cfg['host']}/risultati-classifiche.aspx?{q}"


_comitati = {}


def gare_comitato(cfg, oggi, dump, completo):
    """Tutte le gare (di tutti i campionati) delle pagine settimanali del comitato: le pagine sono le stesse per
    tutti i gironi dello stesso comitato, quindi si leggono una volta sola."""
    chiave = (cfg["host"], cfg.get("comitato_id"), cfg["pid"])
    if chiave in _comitati:
        return _comitati[chiave]
    out, vuote, lette = [], 0, 0
    if completo == "rapido":
        settimane = (-1, 0) if oggi.weekday() <= 1 else (0,)  # al massimo 2 pagine per comitato
    else:
        settimane = range(-1, MAX_SETTIMANE + 1) if completo else (-1, 0, 1)
    for k in settimane:
        try:
            gare = parse_gare(get(url_settimana(cfg, lunedi(oggi) + dt.timedelta(days=7 * k)), dump))
            lette += 1
        except Exception as e:
            print(f"   ! pagina gare ({k:+d} sett.): {e}")
            continue
        out += gare
        vuote = 0 if gare else vuote + 1
        if completo is True and k > 1 and vuote >= SETTIMANE_VUOTE:
            break
    print(f"   [{cfg['host']} {cfg['pid']}] pagine lette {lette}, gare {len(out)}")
    _comitati[chiave] = out
    return out


def classifica_provvisoria(g):
    """Se la classifica ufficiale conta meno gare di quelle con risultato, somma le gare mancanti (le più recenti) e
    segna "classifica_provvisoria". Lo fa solo se i conti tornano squadra per squadra; altrimenti lascia l'ufficiale."""
    g.pop("classifica_provvisoria", None)
    cl = g.get("classifica") or []
    giocate = [p for p in g.get("partite") or [] if RX_RIS.match(p.get("risultato") or "")]
    k_manc = len(giocate) - sum(r.get("g") or 0 for r in cl) // 2
    if k_manc <= 0 or not cl:
        return 0
    manca = {key(r["squadra"]): -(r.get("g") or 0) for r in cl}
    for p in giocate:
        for t in (key(p["casa"]), key(p["ospite"])):
            if t not in manca:
                return 0
            manca[t] += 1
    if any(v < 0 for v in manca.values()) or sum(manca.values()) != 2 * k_manc:
        return 0
    scelte = []
    for p in sorted(giocate, key=lambda m: (m.get("data") or "", m.get("ora") or ""), reverse=True):
        a, b = key(p["casa"]), key(p["ospite"])
        if manca[a] > 0 and manca[b] > 0:
            scelte.append(p); manca[a] -= 1; manca[b] -= 1
        if len(scelte) == k_manc:
            break
    if len(scelte) != k_manc or any(manca.values()):
        return 0
    for p in scelte:
        TR.somma_partita(g, p, p["risultato"])
    TR.riordina(g)
    g["classifica_provvisoria"] = True
    return k_manc


def aggiorna(g, cfg, oggi, dump, completo=False):
    rapido = completo == "rapido"
    alias = {key(k): v for k, v in (cfg.get("alias") or {}).items()}
    if rapido:
        # giro rapido: prima le gare, la classifica solo se ci sono risultati nuovi
        cl = None
        nomi = {key(r["squadra"]) for r in g.get("classifica") or []}
        if not nomi:
            return "ok: girone senza classifica, saltato nel giro rapido"
    else:
        cl = parse_classifica(get(f"https://{cfg['host']}/classifica.aspx?CId={cfg['cid']}", dump))
        if not cl:
            return "classifica non letta: girone invariato"
        if len(cl) < len(g.get("classifica") or []):
            return f"classifica con meno squadre ({len(cl)} < {len(g['classifica'])}): girone invariato"
        nomi = {key(r["squadra"]) for r in cl}
        for r in cl:
            r["id"] = alias.get(key(r["squadra"]))
    # gare delle settimane lette (vedi gare_comitato)
    nuove = []
    if cfg.get("pid"):
        for x in gare_comitato(cfg, oggi, dump, completo):
            # solo le gare della sezione di questo girone (le stesse squadre giocano anche in Coppa)
            # sezioni senza link "classifica" (es. Under 12 Misto Udine): riconosciute dal titolo, campo "sezione" (regex)
            sez = cfg.get("sezione")
            if x["cid"] != str(cfg["cid"]) and not (sez and x["cid"] is None and re.search(sez, x.get("campionato") or "", re.I)):
                continue
            if key(x["casa"]) in nomi and key(x["ospite"]) in nomi:
                nuove.append(x)
    old = g.get("partite") or []
    idx = {(key(m["casa"]), key(m["ospite"])): m for m in old}
    per_num = {str(m["gara"]): m for m in old if m.get("gara")}
    giorn_max = max([m.get("giornata") or 0 for m in old] + [0])
    settimane = {}
    ris_nuovi = 0
    for x in sorted(nuove, key=lambda m: (m["data"], m["ora"])):
        k2 = (key(x["casa"]), key(x["ospite"]))
        # prima per numero gara (una gara spostata resta la stessa gara), poi per squadre
        m = per_num.get(x["num"]) if x["num"] else None
        if m is None:
            m = idx.get(k2)
            # stesse squadre ma altro numero gara: è un'altra gara (gironi con più di andata e ritorno)
            if m is not None and m.get("gara") and x["num"] and str(m["gara"]) != x["num"]:
                m = None
        if m is None:
            if x["giornata"]:
                m = {"giornata": x["giornata"]}
            else:
                w = lunedi(dt.date.fromisoformat(x["data"]))
                if w not in settimane:
                    settimane[w] = giorn_max + len(settimane) + 1
                m = {"giornata": settimane[w]}
            old.append(m); idx.setdefault(k2, m)
            if x["num"]:
                per_num[x["num"]] = m
        elif x["giornata"]:
            m["giornata"] = x["giornata"]  # la giornata scritta dal portale prevale su quella ricostruita
        if x["num"]:
            m["gara"] = x["num"]
        if x["risultato"] and x["risultato"] != m.get("risultato"):
            ris_nuovi += 1
        m.update({"data": x["data"], "ora": x["ora"], "casa": x["casa"], "ospite": x["ospite"],
                  "id_casa": alias.get(k2[0]), "id_ospite": alias.get(k2[1]),
                  "risultato": x["risultato"] or m.get("risultato", ""), "parziali": x["parziali"] or m.get("parziali", ""),
                  "campo": x["campo"] or m.get("campo", "")})
    if rapido:
        if not ris_nuovi:
            return "ok: nessun risultato nuovo"
        try:
            cl = parse_classifica(get(f"https://{cfg['host']}/classifica.aspx?CId={cfg['cid']}", dump))
        except Exception as e:
            print(f"   ! classifica {cfg['slug']}: {e}"); cl = None
        if not cl or len(cl) < len(g.get("classifica") or []):
            # classifica non letta: si tiene la precedente (ufficiale, senza le somme provvisorie di prima)
            cl = g.get("classifica_ufficiale") or g.get("classifica") or []
            cl = [dict(r) for r in cl]
        for r in cl:
            r["id"] = alias.get(key(r["squadra"]), r.get("id"))
    g["classifica"] = cl
    g["partite"] = sorted(old, key=lambda m: (m.get("giornata") or 0, m.get("data") or "", m.get("ora") or ""))
    giocate = [m.get("giornata") or 0 for m in g["partite"] if m.get("risultato")]
    g["giornata"] = max(giocate) if giocate else g.get("giornata")
    g["aggiornato"] = oggi.isoformat()
    g["calcolata"] = False
    g["classifica_ufficiale"] = [dict(r) for r in cl]
    somme = classifica_provvisoria(g)
    if not somme:
        g.pop("classifica_ufficiale", None)  # serve solo quando la classifica in app è provvisoria
    return f"ok: {len(cl)} squadre, {len(nuove)} gare lette, {ris_nuovi} risultati nuovi" + (f", classifica provvisoria (+{somme} gare)" if somme else "")


def main():
    dump = "--dump" in sys.argv
    completo, prova = "--completo" in sys.argv, "--prova" in sys.argv
    if "--rapido" in sys.argv:
        completo = "rapido"
    solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    oggi = dt.date.today()
    data = json.load(open(RIS))
    by = {g["gid"]: g for g in data}
    cfgs = json.load(open(CFG))["gironi"]
    errori = 0
    for cfg in cfgs:
        if not cfg.get("attivo", True) or (solo and cfg["slug"] != solo):
            continue
        gid = "pallavolo-" + cfg["slug"]
        g = by.get(gid)
        if g is None:
            g = {"gid": gid, "sport": "pallavolo", "girone": cfg["girone"], "categoria": cfg["categoria"], "genere": cfg["genere"],
                 "stagione": cfg["stagione"], "comitato": cfg["comitato"], "classifica": [], "partite": [], "calcolata": False}
        g["fonte"] = f"https://{cfg['host']}/classifica.aspx?CId={cfg['cid']}"
        try:
            esito = aggiorna(g, cfg, oggi, dump, completo)
        except Exception as e:
            esito = f"errore: {e}"
        if esito.startswith("ok") and gid not in by:
            data.append(g); by[gid] = g
        if not esito.startswith("ok"):
            errori += 1
        print(f"{cfg['slug']}: {esito}")
    applica_comuni(data)  # comune delle squadre senza id (config/squadre_comune.json)
    json.dump(data, open(PROVA if prova else RIS, "w"), ensure_ascii=False, separators=(",", ":"))
    if prova:
        print("prova: data/risultati.json non modificato, risultato in", PROVA)
    print(f"gironi con problemi: {errori} su {len(cfgs)}")
    # il workflow fallisce solo se non è stato letto quasi nulla (probabile cambio del portale)
    sys.exit(2 if cfgs and errori > 0.5 * len(cfgs) else 0)


if __name__ == "__main__":
    main()
