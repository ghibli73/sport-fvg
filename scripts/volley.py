"""Aggiornamento automatico della PALLAVOLO dai portali FIPAV (piattaforma PowerSPORT), senza intelligenza artificiale.

Per ogni girone di config/pallavolo.json:
  1. legge la classifica ufficiale:  https://<host>/classifica.aspx?CId=<cid>
  2. legge le gare della settimana scorsa, di quella corrente e della prossima dalla pagina risultati del comitato
     (risultati-classifiche.aspx?...&DataDa=<lunedì>&PId=<pid>), tenendo le gare tra squadre del girone;
  3. unisce le gare nuove a quelle già presenti in data/risultati.json e aggiorna classifica, giornata e data.

Protezioni: se una classifica letta ha meno squadre di quella esistente, o la lettura fallisce, il girone resta com'era.
Uso:  python scripts/volley.py            (aggiorna data/risultati.json)
      python scripts/volley.py --dump     (salva anche le pagine scaricate in debug/ per controllare il parser)
      python scripts/volley.py --solo <slug>
"""
import json, os, re, sys, time, datetime as dt
import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
CFG = os.path.join(ROOT, "config", "pallavolo.json")
DEBUG = os.path.join(ROOT, "debug")
UA = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (+https://github.com/; app non ufficiale di consultazione)")
PAUSA = 1.5  # secondi tra le richieste: siamo ospiti dei portali federali
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


RX_ALTRO = re.compile(r"coppa|supercoppa|trofeo|torneo|amichevol|memorial|final|play.?off|play.?out", re.I)
RX_DATA = re.compile(r"(\d{2})/(\d{2})/(\d{2,4})(?:\s+(\d{1,2}[:.]\d{2}))?")
RX_RIS = re.compile(r"^(\d)\s*-\s*(\d)$")
RX_PARZ = re.compile(r"\d{1,2}-\d{1,2}")


def parse_gare(html):
    """Ogni riga gara della pagina risultati: numero, data/ora, casa, ospite, risultato (se giocata), parziali, impianto.
    Le etichette di campionato sono righe con una sola cella di testo che precedono le gare."""
    soup = BeautifulSoup(html, "html.parser")
    gare, camp = [], ""
    for tr in soup.find_all("tr"):
        c = [x for x in cells(tr) if x != ""]
        if not c:
            continue
        if len(c) == 1 and not RX_DATA.search(c[0]):
            camp = c[0]
            continue
        di = next((i for i, x in enumerate(c) if RX_DATA.search(x)), None)
        if di is None:
            continue
        num = next((x for x in c[:di] if re.fullmatch(r"\d{1,5}", x)), "")
        rest = c[di + 1:]
        ri = next((i for i, x in enumerate(rest) if RX_RIS.match(x)), None)
        teams = [x for x in (rest[:ri] if ri is not None else rest) if not RX_PARZ.fullmatch(x) and not re.fullmatch(r"[\d\s:.-]*", x)]
        if len(teams) < 2:
            continue
        d = RX_DATA.search(c[di])
        y = d.group(3); y = ("20" + y) if len(y) == 2 else y
        g = {"num": num, "data": f"{y}-{d.group(2)}-{d.group(1)}", "ora": (d.group(4) or "").replace(".", ":"),
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


def aggiorna(g, cfg, oggi, dump):
    cl = parse_classifica(get(f"https://{cfg['host']}/classifica.aspx?CId={cfg['cid']}", dump))
    if not cl:
        return "classifica non letta: girone invariato"
    if len(cl) < len(g.get("classifica") or []):
        return f"classifica con meno squadre ({len(cl)} < {len(g['classifica'])}): girone invariato"
    alias = {key(k): v for k, v in (cfg.get("alias") or {}).items()}
    nomi = {key(r["squadra"]) for r in cl}
    for r in cl:
        r["id"] = alias.get(key(r["squadra"]))
    # gare: settimana scorsa, corrente, prossima
    nuove = []
    if cfg.get("pid"):
        for k in (-7, 0, 7):
            try:
                for x in parse_gare(get(url_settimana(cfg, lunedi(oggi) + dt.timedelta(days=k)), dump)):
                    # stesse squadre possono incontrarsi anche in Coppa: si tengono solo le gare del campionato giusto
                    if RX_ALTRO.search(x["campionato"]) and not RX_ALTRO.search(cfg["girone"] + " " + cfg["categoria"]):
                        continue
                    if key(x["casa"]) in nomi and key(x["ospite"]) in nomi:
                        nuove.append(x)
            except Exception as e:
                print(f"   ! pagina gare ({k:+d}gg): {e}")
    old = g.get("partite") or []
    idx = {(key(m["casa"]), key(m["ospite"])): m for m in old}
    giorn_max = max([m.get("giornata") or 0 for m in old] + [0])
    settimane = {}
    for x in sorted(nuove, key=lambda m: (m["data"], m["ora"])):
        k2 = (key(x["casa"]), key(x["ospite"]))
        m = idx.get(k2)
        if m is None:
            w = lunedi(dt.date.fromisoformat(x["data"]))
            if w not in settimane:
                settimane[w] = giorn_max + len(settimane) + 1
            m = {"giornata": settimane[w]}
            old.append(m); idx[k2] = m
        m.update({"data": x["data"], "ora": x["ora"], "casa": x["casa"], "ospite": x["ospite"],
                  "id_casa": alias.get(k2[0]), "id_ospite": alias.get(k2[1]),
                  "risultato": x["risultato"] or m.get("risultato", ""), "parziali": x["parziali"] or m.get("parziali", ""),
                  "campo": x["campo"] or m.get("campo", "")})
    g["classifica"] = cl
    g["partite"] = sorted(old, key=lambda m: (m.get("giornata") or 0, m.get("data") or "", m.get("ora") or ""))
    giocate = [m.get("giornata") or 0 for m in g["partite"] if m.get("risultato")]
    g["giornata"] = max(giocate) if giocate else g.get("giornata")
    g["aggiornato"] = oggi.isoformat()
    g["calcolata"] = False
    return f"ok: {len(cl)} squadre, {len(nuove)} gare lette"


def main():
    dump = "--dump" in sys.argv
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
            esito = aggiorna(g, cfg, oggi, dump)
        except Exception as e:
            esito = f"errore: {e}"
        if esito.startswith("ok") and gid not in by:
            data.append(g); by[gid] = g
        if not esito.startswith("ok"):
            errori += 1
        print(f"{cfg['slug']}: {esito}")
    json.dump(data, open(RIS, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"gironi con problemi: {errori} su {len(cfgs)}")
    # il workflow fallisce solo se non è stato letto quasi nulla (probabile cambio del portale)
    sys.exit(2 if cfgs and errori > 0.5 * len(cfgs) else 0)


if __name__ == "__main__":
    main()
