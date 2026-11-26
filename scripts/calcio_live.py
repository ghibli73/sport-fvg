"""Risultati del CALCIO prima del Comunicato Ufficiale, dal "Quadro gare" della LND (https://gare.lnd.it, servizio
pubblico ufficiale della Lega Nazionale Dilettanti, lo stesso che il sito LND FVG mostra in "Risultati e classifiche").
Manuale: pipeline/agenti/tempo-reale.md.

Ogni pagina di girone (https://gare.lnd.it/?cr=07&campionato=<codice>&girone=<codice>&giornata=<n>&leg=first|second)
contiene nei dati della pagina (Inertia, attributo data-page) le partite della giornata con gol, "isPlayed", "isLive",
"resultState" e "outcome" (es. "Da Giudice sportivo"). Nessuna chiave: è la pagina pubblica.

  --scopri  abbina i gironi dell'app (gid calcio-*) ai gironi del Quadro gare confrontando le squadre (config/calcio_lnd.json);
            da solo una volta alla settimana o se mancano gironi;
  (normale) per i gironi abbinati legge le giornate con partite finite da poco (inizio + 115 minuti, ultimi 3 giorni) e
            senza risultato del Comunicato, salva i gol in config/live.json e li applica a data/risultati.json con
            "provvisorio": true (la classifica calcolata dell'app li somma e il girone ha "classifica_provvisoria");
            il risultato del Comunicato Ufficiale li sostituisce (scripts/calcio.py), e se è diverso vale il Comunicato.
  --solo-scoperta  solo la scoperta, se serve (gironi senza abbinamento da più di 7 giorni o scoperta interrotta): la
            chiama aggiorna-calcio.yml, fuori dalle fasce di gara
  --prova   non scrive config né data/risultati.json (risultato in /tmp/risultati_prova.json)
Ritmo: 3 s tra le pagine (con 1,5 s il servizio dopo circa 25 pagine risponde con pagine vuote); al massimo MAX_PAGINE
pagine per esecuzione; alla prima risposta vuota o d'errore la lettura si ferma e riprende al giro successivo.
"""
import datetime as dt, html as H, json, os, re, sys, time
import requests
import tempo_reale as TR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
CFG = os.path.join(ROOT, "config", "calcio_lnd.json")
BASE = "https://gare.lnd.it/"
CR = "07"  # Comitato Regionale Friuli Venezia Giulia
PAUSA = 3.0      # il Quadro gare rallenta dopo circa 25 pagine lette a 1,5 s: qui 3 s tra le pagine
MAX_PAGINE = 40
DURATA = 115  # minuti dall'inizio prima di cercare il risultato
PROVA = "/tmp/risultati_prova.json"
SALTA = re.compile(r"COPPA|ESORDIENTI|PULCINI|TORNEO|FASE|SUPERCOPPA|PRIMI CALCI|PICCOLI", re.I)
S = requests.Session()
S.headers["User-Agent"] = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (app non ufficiale di consultazione)")
_t = [0.0]
GIORNATE = {}
LETTE = [0]


def pagina(params):
    attesa = PAUSA - (time.time() - _t[0])
    if attesa > 0:
        time.sleep(attesa)
    r = S.get(BASE, params={"cr": CR, **params}, timeout=40)
    _t[0] = time.time(); LETTE[0] += 1
    r.raise_for_status()
    m = re.search(r'data-page="app" type="application/json">(.*?)</script>', r.text, re.S) or re.search(r'data-page="([^"]+)"', r.text)
    if not m:
        raise ValueError("pagina senza dati (data-page)")
    props = json.loads(H.unescape(m.group(1))).get("props", {})
    if props.get("step") == "error" or (params.get("campionato") and not props.get("matchdays") and not props.get("standings")):
        raise Rallentato(f"risposta vuota o d'errore ({props.get('step')}: {str(props.get('message') or '')[:120]})")
    return props


class Rallentato(Exception):
    """Il Quadro gare non dà dati (troppe richieste o errore): ci si ferma fino al giro successivo."""


def chiave(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper())
    s = re.sub(r"\b(ASD|SSD|A S D|S S D|AC|US|USD|APD|POL|ACD|ARL|SRL|SSDARL|CALCIO|FC|SQ)\b", " ", s)
    return re.sub(r"\s+", "", s)


def parole(s):
    return {w for w in re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper()).split() if len(w) > 2} - {"ASD", "SSD", "CALCIO", "USD", "APD", "POL"}


def abbina_nome(nome, nomi):
    """Nome del Quadro gare -> nome dell'app nello stesso girone (uguale senza sigle, o unico per parole in comune)."""
    c = chiave(nome)
    for n in nomi:
        if chiave(n) == c:
            return n
    sq_b = bool(re.search(r"\bSQ\.?\s*B\b", nome, re.I))
    cand = [n for n in nomi if parole(nome) & parole(n) and bool(re.search(r"\bSQ\.?\s*B\b", n, re.I)) == sq_b]
    if len(cand) == 1:
        return cand[0]
    best = sorted(cand, key=lambda n: -len(parole(nome) & parole(n)))
    if len(best) >= 2 and len(parole(nome) & parole(best[0])) > len(parole(nome) & parole(best[1])):
        return best[0]
    return None


def squadre_props(props):
    st = props.get("standings")
    if isinstance(st, dict):
        st = st.get("standings")
    nomi = [r.get("team", "") for r in st or [] if isinstance(r, dict)]
    for m in props.get("matches") or []:
        nomi += [m.get("home", ""), m.get("away", "")]
    return {n.upper() for n in nomi if n}


def scopri(data, cfg):
    props = pagina({})
    gironi = [(c["code"], gr["code"], f"{c['name']} {gr['name']}", c.get("delegationLabel"))
              for c in props.get("championships") or [] for gr in c.get("groups") or [] if not SALTA.search(c.get("name", ""))]
    print(f"Quadro gare: {len(gironi)} gironi di campionato nel Comitato {CR}")
    nostri = {g["gid"]: {r["squadra"] for r in g.get("classifica") or []} for g in data if g.get("sport") in ("calcio", "calcio5")}
    # solo i gironi del Quadro gare non ancora abbinati e solo per i gironi dell'app senza abbinamento
    gia = {(v["campionato"], v["girone"]) for v in (cfg.get("gironi") or {}).values()}
    nostri = {gid: n for gid, n in nostri.items() if gid not in (cfg.get("gironi") or {})}
    gironi = [x for x in gironi if (x[0], x[1]) not in gia]
    completa = True
    voti = {}
    for camp, gir, nome, deleg in gironi:
        if LETTE[0] >= MAX_PAGINE * 2:
            print("  limite di pagine raggiunto: il resto alla prossima scoperta"); break
        try:
            pr = pagina({"campionato": camp, "girone": gir})
        except Rallentato as e:
            print(f"  ! {camp}/{gir}: {e}: scoperta interrotta, riprende al prossimo giro"); completa = False; break
        except Exception as e:
            print(f"  ! {camp}/{gir}: {e}"); continue
        sq = squadre_props(pr)
        GIORNATE[(camp, gir)] = [[m.get("number"), m.get("leg"), m.get("startDate"), m.get("endDate")] for m in pr.get("matchdays") or []]
        migliore = (0, "")
        for gid, nomi in nostri.items():
            if not nomi:
                continue
            ok = sum(1 for n in sq if abbina_nome(n, nomi))
            migliore = max(migliore, (ok, gid))
            if ok >= max(4, 0.6 * len(nomi)):
                voti.setdefault(gid, []).append((ok, camp, gir, nome, deleg))
        print(f"    {camp}/{gir} {nome.strip()[:40]}: {len(sq)} squadre, giornate {len(GIORNATE[(camp, gir)])}, più simile {migliore[1]} ({migliore[0]})")
    cfg.setdefault("gironi", {})
    scelti = {}
    for gid, vv in voti.items():
        vv.sort(reverse=True)
        if len(vv) > 1 and vv[0][0] == vv[1][0]:
            print(f"  {gid}: abbinamento ambiguo {vv[:2]}"); continue
        scelti.setdefault(vv[0][1:3], []).append((gid, vv[0]))
    eta = lambda t: (re.search(r"under[- ](\d+)", t, re.I) or [None, None])[1]
    for (camp, gir), lista in scelti.items():
        if len(lista) > 1:
            # due gironi dell'app con le stesse squadre (es. U14 e U15 della stessa Delegazione): vale la categoria
            giusti = [x for x in lista if eta(x[0]) and eta(x[0]) == eta(x[1][3])]
            print(f"  {camp}/{gir} somiglia a {[x[0] for x in lista]}: " + (f"tenuto {giusti[0][0]}" if len(giusti) == 1 else "nessuno tenuto"))
            lista = giusti if len(giusti) == 1 else []
            for x in scelti[(camp, gir)]:
                if x not in lista:
                    cfg["gironi"].pop(x[0], None)
        for gid, (ok, camp, gir, nome, deleg) in lista:
            cfg["gironi"][gid] = {"campionato": camp, "girone": gir, "nome": nome.strip(), "delegazione": deleg, "uguali": ok,
                                  "giornate": GIORNATE.get((camp, gir), [])}
            print(f"  {gid} = {nome.strip()} ({deleg}, campionato {camp}, girone {gir}, {ok} squadre uguali)")
    if completa:
        cfg["scoperta"] = dt.date.today().isoformat()
    else:
        cfg["scoperta_parziale"] = dt.date.today().isoformat()
    print(f"gironi abbinati {len(cfg['gironi'])}; senza abbinamento: {sorted(set(nostri) - set(cfg['gironi']))}")


VERIFICA = {"uguali": 0, "diversi": 0}


def leggi(data, cfg, live, oggi, verifica=False):
    """-> risultati nuovi. Solo i gironi con partite finite da poco e senza risultato ufficiale.
    verifica=True: rilegge le partite degli ultimi 7 giorni GIÀ nel Comunicato e confronta i gol (non scrive nulla)."""
    da = (dt.date.fromisoformat(oggi) - dt.timedelta(days=7 if verifica else 3)).isoformat()
    by = {g["gid"]: g for g in data}
    nuovi = 0
    for gid, p in sorted((cfg.get("gironi") or {}).items()):
        g = by.get(gid)
        if not g:
            continue
        voci = live.setdefault("gironi", {}).setdefault(gid, {})
        n_sq = len(g.get("classifica") or [])
        andata = n_sq - 1 if n_sq % 2 == 0 else n_sq
        attese = [x for x in g.get("partite") or [] if (verifica == bool(x.get("risultato")) and not x.get("provvisorio")) and da <= (x.get("data") or "") <= oggi
                  and TR.finita(x.get("data"), x.get("ora") or "14:30", DURATA) and TR.chiave_partita(x) not in voci]
        def pagina_di(x):
            """(numero, leg) della giornata del Quadro gare: dalla data (giornate salvate alla scoperta), se no dal numero."""
            d = x.get("data") or ""
            cand = []
            for num, leg, a, b in p.get("giornate") or []:
                if not b:
                    continue
                if not a or a < "1900":  # inizio sconosciuto ("0001-01-01"): la settimana prima della fine
                    a = (dt.date.fromisoformat(b) - dt.timedelta(days=6)).isoformat()
                if a <= d <= b:
                    cand.append((b, num, leg))
            if cand:
                _, num, leg = min(cand)
                return num, leg
            gio = x.get("giornata")
            return (("first", gio) if gio <= andata else ("second", gio - andata))[::-1] if gio else None
        pagine = {}
        for x in attese:
            pg = pagina_di(x)
            if pg:
                pagine.setdefault(pg, set()).add(x.get("giornata"))
        # girone senza calendario in app (nessuna partita futura nota): la giornata è quella dopo l'ultima giocata
        if not g.get("partite") or not any(not x.get("risultato") for x in g["partite"]):
            ultima = max([x.get("giornata") or 0 for x in g.get("partite") or []] + [0])
            if dt.date.fromisoformat(oggi).weekday() in (5, 6, 0):
                for num, leg, a, b in p.get("giornate") or []:
                    if b and (a or "") <= oggi and da <= b <= oggi:
                        pagine.setdefault((num, leg), set()).add(ultima + 1)
        nomi = [r["squadra"] for r in g.get("classifica") or []]
        ids = {r["squadra"]: r.get("id") for r in g.get("classifica") or []}
        for (n, leg), gg in sorted(pagine.items(), key=lambda z: (z[0][1] != "first", z[0][0])):
            gio = max(gg)
            if LETTE[0] >= MAX_PAGINE:
                print("  limite di pagine raggiunto"); return nuovi
            try:
                props = pagina({"campionato": p["campionato"], "girone": p["girone"], "giornata": n, "leg": leg})
            except Rallentato as e:
                print(f"  ! {gid} giornata {n} {leg}: {e}: lettura interrotta fino al prossimo giro"); return nuovi
            except Exception as e:
                print(f"  ! {gid} giornata {gio}: {e}"); continue
            cm = props.get("currentMatchday") or {}
            if cm.get("number") != n or cm.get("leg") != leg:
                print(f"  ! {gid}: il Quadro gare ha risposto con la giornata {cm.get('number')} {cm.get('leg')}, attesa {n} {leg}")
                continue
            per = {(TR.k(x["casa"]), TR.k(x["ospite"])): x for x in g["partite"] if x.get("giornata") in gg}
            for m in props.get("matches") or []:
                if m.get("isRest") or m.get("isLive") or not m.get("isPlayed"):
                    continue
                # gare rinviate, sospese, non disputate o da ripetere: il Quadro gare le mostra con 0-0, non sono risultati
                if re.search(r"rinviat|sospes|non disputat|da recuperare|da ripetere|annullat|impraticab", str(m.get("outcome") or "") + " " + str(m.get("resultState") or ""), re.I):
                    continue
                if m.get("homeGoals") is None or m.get("awayGoals") is None:
                    continue
                casa, osp = abbina_nome(m.get("home"), nomi), abbina_nome(m.get("away"), nomi)
                if not casa or not osp or casa == osp:
                    continue
                x = per.get((TR.k(casa), TR.k(osp)))
                if verifica:
                    if x is not None and x.get("risultato"):
                        r = f"{int(m['homeGoals'])}-{int(m['awayGoals'])}"
                        VERIFICA["uguali" if r == x["risultato"] else "diversi"] += 1
                        if r != x["risultato"]:
                            print(f"  DIVERSO {gid} g{x.get('giornata')}: {casa} - {osp} Quadro gare {r}, Comunicato {x['risultato']}")
                    continue
                if x is not None and x.get("risultato"):
                    continue  # c'è già (ufficiale o provvisorio)
                d = m.get("date") or (x or {}).get("data")
                if not d or d > oggi or not TR.finita(d, (m.get("time") or "14:30")[:5], DURATA):
                    continue
                voce = {"r": f"{int(m['homeGoals'])}-{int(m['awayGoals'])}", "data": d, "stato": m.get("resultState"),
                        "esito": m.get("outcome") or "", "letto": TR.adesso().isoformat(timespec="minutes"),
                        "fonte": f"{BASE}?cr={CR}&campionato={p['campionato']}&girone={p['girone']}&giornata={n}&leg={leg}"}
                if x is None:
                    x = {"giornata": gio, "data": d, "ora": (m.get("time") or "")[:5], "casa": casa, "ospite": osp,
                         "id_casa": ids.get(casa), "id_ospite": ids.get(osp)}
                    if m.get("field"):
                        x["campo"] = m["field"].title()
                    voce["nuova"] = x
                kk = TR.chiave_partita(x)
                if kk in voci:
                    continue
                voci[kk] = voce; nuovi += 1
                print(f"  {gid} g{gio}: {casa} - {osp} {voce['r']} (provvisorio; {voce['esito'] or 'stato ' + str(voce['stato'])})")
        if not voci:
            live["gironi"].pop(gid, None)
    return nuovi


def main():
    prova = "--prova" in sys.argv
    oggi = dt.date.today().isoformat()
    data = json.load(open(RIS))
    cfg = json.load(open(CFG)) if os.path.exists(CFG) else {"gironi": {}}
    nostri = {g["gid"] for g in data if g.get("sport") in ("calcio", "calcio5")}
    vecchia = not cfg.get("scoperta") or (dt.date.fromisoformat(oggi) - dt.date.fromisoformat(cfg["scoperta"])).days >= 7
    # la scoperta (circa 40 pagine) si fa nel workflow del calcio, fuori dalle fasce di gara (--solo-scoperta);
    # il giro rapido la fa solo se non c'è ancora nessun abbinamento
    serve = (vecchia and nostri - set(cfg.get("gironi") or {})) or cfg.get("scoperta_parziale", "") > cfg.get("scoperta", "")
    if "--scopri" in sys.argv or not cfg.get("gironi") or ("--solo-scoperta" in sys.argv and serve):
        try:
            scopri(data, cfg)
        except Exception as e:
            print(f"scoperta dei gironi non riuscita ({e})")
    if "--solo-scoperta" in sys.argv:
        if prova:
            print("@@LND@@" + json.dumps(cfg, ensure_ascii=False) + "@@LND@@"); return
        json.dump(cfg, open(CFG, "w"), ensure_ascii=False, indent=1); return
    live = TR.carica_live()
    conf, div = TR.pulisci(data, live, oggi)
    print(f"provvisori confermati dal Comunicato: {conf}, diversi: {div}")
    if "--verifica" in sys.argv:
        leggi(data, cfg, live, oggi, verifica=True)
        print(f"verifica Quadro gare / Comunicati (ultimi 7 giorni): {VERIFICA}, pagine lette {LETTE[0]}"); return
    try:
        n = leggi(data, cfg, live, oggi)
    except Exception as e:
        n = 0; print(f"Quadro gare: lettura non riuscita ({e})")
    print(f"Quadro gare LND: pagine lette {LETTE[0]}, risultati nuovi {n}")
    print("partite aggiornate in app:", TR.applica(data, live, solo_sport={"calcio", "calcio5"}))
    if prova:
        json.dump(data, open(PROVA, "w"), ensure_ascii=False, separators=(",", ":"))
        if "--scopri" in sys.argv:
            print("@@LND@@" + json.dumps(cfg, ensure_ascii=False) + "@@LND@@")
        print("prova: config e data/risultati.json non modificati, risultato in", PROVA); return
    json.dump(cfg, open(CFG, "w"), ensure_ascii=False, indent=1)
    TR.salva_live(live)
    json.dump(data, open(RIS, "w"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
