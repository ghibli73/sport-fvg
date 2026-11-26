"""Aggiornamento automatico dei gironi NAZIONALI con squadre del FVG (nessuna intelligenza artificiale).

Un modulo per fonte; ogni modulo restituisce un girone completo nel formato di data/risultati.json
(classifica ufficiale, tutte le partite della stagione con giornata, data, ora e campo) con "auto": "naz".
Moduli:
  serie_a  Lega Serie A (Udinese): API pubblica della piattaforma dati usata da www.legaseriea.it
           https://api-sdp.legaseriea.it/v1/serie-a/football/seasons/<season_id>/standings  (classifica ufficiale)
           https://api-sdp.legaseriea.it/v1/serie-a/football/seasons/<season_id>/matches    (tutte le 380 partite)
Se un modulo fallisce o i dati non passano i controlli il girone precedente resta com'è.
Uso: python scripts/nazionali.py [--prova] [--solo serie_a]
     --prova  non modifica il repository: il risultato va in /tmp/risultati_prova.json
Manuale: pipeline/agenti/nazionali.md
"""
import datetime as dt, json, os, re, sys, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
SOC = os.path.join(ROOT, "data", "data.json")
CONF = os.path.join(ROOT, "config", "nazionali.json")
PROVA = "/tmp/risultati_prova.json"
S = requests.Session()
S.headers["User-Agent"] = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (app non ufficiale di consultazione)")
S.headers["Accept"] = "application/json"


def oggi():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=1))).date().isoformat()


def get_json(url):
    for t in range(3):
        try:
            r = S.get(url, timeout=60)
            if r.status_code == 200:
                return r.json()
            print("  HTTP", r.status_code, url)
        except Exception as e:
            print("  errore", e, url)
        time.sleep(3 * (t + 1))
    raise RuntimeError("fonte non raggiungibile: " + url)


# ---------------------------------------------------------------- Serie A (Lega Serie A)
SDP = "https://api-sdp.legaseriea.it/v1/serie-a/football/seasons/"


def serie_a(cfg, ids):
    sid = cfg["season_id"]; alias = cfg.get("alias", {})
    idd = lambda nome: alias.get(nome) if alias.get(nome) in ids else None
    st = get_json(SDP + sid + "/standings")
    cl = []
    for t in st.get("teams") or []:
        v = {x["statsId"]: x.get("statsValue") for x in t.get("stats") or []}
        nome = t.get("shortName") or t.get("officialName")
        cl.append({"pos": v.get("rank"), "squadra": nome, "id": idd(nome), "punti": v.get("points"),
                   "g": v.get("matches-played"), "v": v.get("win"), "n": v.get("draw"), "p": v.get("lose"),
                   "gf": v.get("goals-for"), "gs": v.get("goals-against")})
    cl.sort(key=lambda r: r["pos"] or 99)
    ms = get_json(SDP + sid + "/matches").get("matches") or []
    pa, ultima = [], 0
    for m in ms:
        g = re.search(r"\d+", (m.get("matchSet") or {}).get("name") or "")
        loc = m.get("matchDateLocal") or ""
        casa = (m.get("home") or {}).get("shortName"); osp = (m.get("away") or {}).get("shortName")
        if not (g and casa and osp and loc[:10]):
            continue
        x = {"giornata": int(g.group()), "data": loc[:10]}
        if not m.get("isUnknownKickOffTime") and len(loc) >= 16:
            x["ora"] = loc[11:16]
        x.update({"casa": casa, "ospite": osp, "id_casa": idd(casa), "id_ospite": idd(osp), "risultato": ""})
        if m.get("status") == "FINISHED" and m.get("providerHomeScore") is not None:
            x["risultato"] = f'{m["providerHomeScore"]}-{m["providerAwayScore"]}'
            ultima = max(ultima, x["giornata"])
        elif m.get("status") not in (None, "", "FINISHED", "PRE_MATCH", "SCHEDULED", "FIXTURE"):
            x["stato"] = str(m.get("status")).lower()  # es. rinviata, in corso: nessun risultato
        if m.get("stadiumName"):
            x["campo"] = m["stadiumName"] + (", " + m["cityName"] if m.get("cityName") else "")
        pa.append(x)
    pa.sort(key=lambda x: (x["giornata"], x["data"], x.get("ora", "")))
    if len(cl) != 20 or len(pa) < 300:
        raise RuntimeError(f"Serie A: dati incompleti (squadre {len(cl)}, partite {len(pa)})")
    return {"gid": cfg["gid"], "sport": "calcio", "girone": "Serie A — girone unico", "categoria": "Prima squadra",
            "genere": "M", "stagione": cfg["stagione"], "comitato": "Lega Serie A (nazionale)",
            "fonte": "https://www.legaseriea.it/serie-a/classifica (dati: " + SDP + sid + "/standings e /matches)",
            "aggiornato": oggi(), "giornata": ultima, "calcolata": False, "classifica": cl, "partite": pa, "auto": "naz"}


# ---------------------------------------------------------------- SuperLega (Lega Pallavolo Serie A)
import html as _html
LV = "https://www.legavolley.it"
MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]


def _txt(h):
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def get_html(url):
    for t in range(3):
        try:
            r = S.get(url, timeout=60, headers={"Accept": "text/html"})
            if r.status_code == 200: return r.text
            print("  HTTP", r.status_code, url)
        except Exception as e:
            print("  errore", e, url)
        time.sleep(3 * (t + 1))
    raise RuntimeError("fonte non raggiungibile: " + url)


def legavolley(cfg, ids):
    """Classifica e calendario completo dalle pagine ufficiali di legavolley.it (HTML statico).
    Dal calendario si prendono solo giornata, data, ora, squadre, risultato in set e impianto (mai gli arbitri)."""
    cid = cfg["id_campionato"]; alias = cfg.get("alias", {})
    idd = lambda nome: alias.get(nome) if alias.get(nome) in ids else None
    h = get_html(f"{LV}/classifica/?IdCampionato={cid}")
    cl = []
    for row in re.findall(r'<tr id="EvenRow">(.*?)</tr>', h, re.S):
        m = re.search(r'<span class="pos">(\d+)</span>(.*?)</td>', row, re.S)
        if not m: continue
        celle = [_txt(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)][1:]
        n = [int(c) if c.isdigit() else None for c in celle]
        nome = _txt(m.group(2))
        cl.append({"pos": int(m.group(1)), "squadra": nome, "id": idd(nome), "punti": n[0], "g": n[1], "v": n[2], "p": n[3],
                   "set_v": n[10], "set_p": n[11]})
    h = get_html(f"{LV}/calendario/?IdCampionato={cid}")
    pa, gior, base, max_and, ultima, data_g = [], None, 0, 0, 0, None
    for blocco in re.split(r"(?=<span>\d+\S*\s+Giornata\s+(?:Andata|Ritorno))|(?=<tr class=\"tab-gara\")", h):
        m = re.match(r"<span>(\d+)\S*\s+Giornata\s+(Andata|Ritorno)", blocco)
        if m:
            k = int(m.group(1))
            if m.group(2) == "Andata": max_and = max(max_and, k); gior = k
            else: gior = max_and + k
            hd = re.search(r"(\d{1,2}) (\w+) (\d{4})", _txt(blocco[:300]))
            data_g = f"{hd.group(3)}-{MESI.index(hd.group(2).lower()[:3]) + 1:02d}-{int(hd.group(1)):02d}" if hd and hd.group(2).lower()[:3] in MESI else None
            continue
        if not blocco.startswith('<tr class="tab-gara"') or gior is None: continue
        td = re.findall(r"<td[^>]*>(.*?)</td>", blocco, re.S)
        if len(td) < 7: continue
        dm = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", _txt(td[1])); om = re.search(r"(\d\d):(\d\d)", _txt(td[1]))
        casa, ris, osp = _txt(td[2]), _txt(td[3]), _txt(td[4])
        if not ((dm or data_g) and casa and osp): continue
        x = {"giornata": gior, "data": f"{dm.group(3)}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}" if dm else data_g}
        if om and dm: x["ora"] = om.group(0)
        x.update({"casa": casa, "ospite": osp, "id_casa": idd(casa), "id_ospite": idd(osp), "risultato": ""})
        if re.fullmatch(r"[0-3]-[0-3]", ris) and ris not in ("0-0",):
            x["risultato"] = ris; ultima = max(ultima, gior)
        campo = re.sub(r"\s*<br\s*/?>\s*", ", ", td[6]); campo = _txt(campo)
        if campo: x["campo"] = campo
        pa.append(x)
    cnt = {}
    for x in pa: cnt.setdefault(x["giornata"], [0, 0]); cnt[x["giornata"]][0] += 1; cnt[x["giornata"]][1] += bool(x["risultato"])
    ultima = max([k for k, (n, r) in cnt.items() if r * 2 >= n] or [0])  # giornata: non contano gli anticipi isolati
    n_sq = cfg.get("squadre", len(cl))
    if len(cl) != n_sq or len(pa) < n_sq * (n_sq - 1) // 2 * 0.95:
        raise RuntimeError(f"{cfg['gid']}: dati incompleti (squadre {len(cl)}, partite {len(pa)})")
    return {"gid": cfg["gid"], "sport": "pallavolo", "girone": cfg["girone"], "categoria": "Prima squadra",
            "genere": cfg.get("genere", "M"), "stagione": cfg["stagione"], "comitato": "Lega Pallavolo Serie A (nazionale)",
            "fonte": f"{LV}/classifica/?IdCampionato={cid} e {LV}/calendario/?IdCampionato={cid}",
            "aggiornato": oggi(), "giornata": ultima, "calcolata": False, "classifica": cl, "partite": pa, "auto": "naz"}


MODULI = {"serie_a": serie_a, "superlega": legavolley}


def controlli(g):
    """Nessuna squadra due volte nella stessa giornata; nessuna partita futura con risultato."""
    vis, err, d0 = {}, [], oggi()
    for x in g["partite"]:
        for s in (x["casa"], x["ospite"]):
            k = (x["giornata"], s)
            if k in vis: err.append(f"{s} due volte nella giornata {x['giornata']}")
            vis[k] = 1
        if x.get("risultato") and x["data"] > d0: err.append(f"partita futura con risultato: {x['casa']}-{x['ospite']} {x['data']}")
    return err


def main():
    prova = "--prova" in sys.argv
    solo = sys.argv[sys.argv.index("--solo") + 1].split(",") if "--solo" in sys.argv else list(MODULI)
    conf = json.load(open(CONF, encoding="utf-8"))
    ids = {c["id"] for c in json.load(open(SOC, encoding="utf-8"))}
    ris = json.load(open(RIS, encoding="utf-8"))
    for nome in solo:
        print("==", nome)
        try:
            g = MODULI[nome](conf[nome], ids)
        except Exception as e:
            print("  ! modulo non aggiornato:", e); continue
        err = controlli(g)
        if err:
            print("  ! controlli non superati, girone non aggiornato:"); print("\n".join("    " + e for e in err[:20])); continue
        prima = next((x for x in ris if x["gid"] == g["gid"]), None)
        if prima and len(g["classifica"]) < len(prima.get("classifica") or []):
            print("  ! meno squadre di prima: girone non aggiornato"); continue
        ris = [x for x in ris if x["gid"] != g["gid"]] + [g]
        fut = sum(1 for x in g["partite"] if not x["risultato"])
        print(f"  {g['gid']}: {len(g['classifica'])} squadre, {len(g['partite'])} partite ({fut} da giocare), giornata {g['giornata']}")
        fvg = [r for r in g["classifica"] if r["id"]]
        for r in fvg: print(f"    FVG {r['squadra']} ({r['id']}): {r['pos']}° con {r['punti']} punti")
    # id delle squadre FVG nei gironi "agente" (aggiornati a mano): li rimettiamo a ogni esecuzione
    for gid, al in conf.get("alias_gironi", {}).items():
        g = next((x for x in ris if x["gid"] == gid), None)
        if not g or not isinstance(al, dict): continue
        ok = lambda n: al.get(n) if al.get(n) in ids else None
        for r in g.get("classifica") or []:
            r["id"] = r.get("id") or ok(r["squadra"])
        for x in g.get("partite") or []:
            x["id_casa"] = x.get("id_casa") or ok(x["casa"]); x["id_ospite"] = x.get("id_ospite") or ok(x["ospite"])
    ris.sort(key=lambda g: (g["sport"], g.get("categoria") != "Prima squadra", g["girone"]))
    out = PROVA if prova else RIS
    json.dump(ris, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("scritto", out)


if __name__ == "__main__":
    main()
