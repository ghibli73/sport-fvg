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
  --dettagli  dati della gara dal Quadro gare (config/calcio_dettagli.json, pipeline/agenti/formato-risultati.md): per
            ogni girone abbinato le giornate dagli ultimi 4 giorni ai prossimi 7 (al massimo DETT_PAGINE pagine, ogni
            giornata al più ogni DETT_ORE ore): data e campo del calendario quando la gara è anticipata/posticipata o cambia
            campo (campo "change" ufficializzato), rinvii e altri esiti particolari, punti di penalizzazione in classifica.
            Le stesse informazioni si raccolgono anche dalle pagine lette dal giro rapido. Mai un rinvio diventa risultato.
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
DETT = os.path.join(ROOT, "config", "calcio_dettagli.json")
DETT_PAGINE = 24   # pagine al massimo per esecuzione di --dettagli
DETT_ORE = 10      # una giornata già letta da meno di 10 ore non si rilegge
DETT_PRIMA, DETT_DOPO = 4, 7  # giornate con date da 4 giorni fa a 7 giorni da oggi
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
    # gironi dell'app senza abbinamento a questa scoperta: un girone nuovo (es. i provinciali di Pordenone appena letti)
    # non è in questo elenco e fa ripetere la scoperta al prossimo aggiorna-calcio senza aspettare 7 giorni
    cfg["senza_abbinamento"] = sorted(set(nostri) - set(cfg["gironi"]))
    if completa:
        cfg["scoperta"] = dt.date.today().isoformat()
    else:
        cfg["scoperta_parziale"] = dt.date.today().isoformat()
    print(f"gironi abbinati {len(cfg['gironi'])}; senza abbinamento: {sorted(set(nostri) - set(cfg['gironi']))}")


# ------------------------------------------------------------------ dati della gara (config/calcio_dettagli.json)
# Esiti del Quadro gare tradotti in etichette fisse (mai il testo libero della fonte, che potrebbe contenere nomi).
# "Da Giudice sportivo" è l'esito di TUTTE le gare giocate in attesa del Comunicato (lo copre già "provvisorio"):
# non è un esito particolare e non viene salvato.
ESITI = [(r"rinviat|da recuperare|rinvio", "rinviata"), (r"sospes", "sospesa"), (r"non disputat|impraticab|non effettuat", "non disputata"),
         (r"da ripetere|ripetizione", "da ripetere"), (r"tavolino|forfait|rinuncia", "a tavolino"), (r"annullat", "annullata")]
SENZA_RISULTATO = {"rinviata", "sospesa", "non disputata", "da ripetere", "annullata"}


def carica_dett():
    return json.load(open(DETT)) if os.path.exists(DETT) else {"gironi": {}, "penalita": {}, "letture": {}}


def salva_dett(det):
    json.dump(det, open(DETT, "w"), ensure_ascii=False, indent=1, sort_keys=True)


def esito_di(m):
    testo = " ".join(str(m.get(k) or "") for k in ("outcome", "publicNote")) + " " + " ".join(map(str, m.get("flags") or []))
    for rx, lab in ESITI:
        if re.search(rx, testo, re.I):
            return lab
    return ""


def raccogli(props, g, gio, det, oggi):
    """Dalle partite e dalla classifica di una pagina del Quadro gare salva in det i dati della gara del girone g
    (giornata gio dell'app). Per ogni partita la voce viene riscritta o tolta: vale l'ultima lettura. -> voci scritte."""
    nomi = [r["squadra"] for r in g.get("classifica") or []]
    voci = det.setdefault("gironi", {}).setdefault(g["gid"], {})
    scritte = 0
    for m in props.get("matches") or []:
        if m.get("isRest"):
            continue
        casa, osp = abbina_nome(m.get("home"), nomi), abbina_nome(m.get("away"), nomi)
        if not casa or not osp or casa == osp:
            continue
        kk = f"{TR.k(casa)}|{TR.k(osp)}|{gio}"
        v = {}
        ch = m.get("change") or {}
        d = m.get("date") or ""
        if ch and str(ch.get("status") or "").upper() == "UFF":  # solo variazioni ufficializzate
            od = ch.get("originalDate") or ""
            if od and d and od != d and od > "1900":
                v["data_cal"] = od
                v["data"] = d
                if m.get("time"):
                    v["ora"] = m["time"][:5]
            of, f = (ch.get("originalField") or "").strip(), (m.get("field") or "").strip()
            if of and f and of.upper() != f.upper():
                v["campo_cal"] = of.title()
                v["campo"] = f.title()
        e = esito_di(m)
        if e:
            v["esito"] = e
        if v:
            v["letto"] = oggi
            voci[kk] = v; scritte += 1
        else:
            voci.pop(kk, None)
    if not voci:
        det["gironi"].pop(g["gid"], None)
    st = props.get("standings")
    if isinstance(st, dict):
        st = st.get("standings")
    if isinstance(st, list) and st:
        pen = {}
        for r in st:
            try:
                n = int(r.get("penalties") or 0)
            except (TypeError, ValueError):
                n = 0
            nome = abbina_nome(r.get("team"), nomi)
            if n > 0 and nome:
                pen[nome] = n
        if pen:
            det.setdefault("penalita", {})[g["gid"]] = pen
        else:
            det.setdefault("penalita", {}).pop(g["gid"], None)
    return scritte


def applica_dettagli(data, det=None):
    """Applica config/calcio_dettagli.json a data/risultati.json (idempotente; si può chiamare dopo calcio.py, che
    ricostruisce i gironi da capo). -> (partite con dati, squadre penalizzate)."""
    det = det if det is not None else carica_dett()
    n_p = n_s = 0
    for g in data:
        if g.get("sport") not in ("calcio", "calcio5"):
            continue
        voci = (det.get("gironi") or {}).get(g["gid"]) or {}
        for p in g.get("partite") or []:
            for f in ("data_cal", "campo_cal", "esito", "rinviata"):  # nel calcio "rinviata" viene solo da qui
                p.pop(f, None)
            v = voci.get(f"{TR.k(p['casa'])}|{TR.k(p['ospite'])}|{p.get('giornata')}")
            if not v:
                continue
            fatto = False
            if v.get("data_cal"):
                if not p.get("risultato") and v.get("data"):
                    p["data"] = v["data"]  # data ufficializzata dal Quadro gare (anticipo/posticipo)
                    if v.get("ora"):
                        p["ora"] = v["ora"]
                if v["data_cal"] != p.get("data"):
                    p["data_cal"] = v["data_cal"]; fatto = True
            if v.get("campo_cal"):
                p["campo_cal"] = v["campo_cal"]
                if v.get("campo"):
                    p["campo"] = v["campo"]
                fatto = True
            e = v.get("esito")
            if e and (e not in SENZA_RISULTATO or not p.get("risultato")):
                p["esito"] = e; fatto = True
                if e in SENZA_RISULTATO and not p.get("risultato"):
                    p["rinviata"] = True  # mai un risultato: resta senza punteggio
            n_p += fatto
        pen = (det.get("penalita") or {}).get(g["gid"]) or {}
        cambiata = False
        for r in g.get("classifica") or []:
            prima, ora = r.get("penalita") or 0, pen.get(r["squadra"], 0)
            if prima != ora:
                r["punti"] = (r.get("punti") or 0) - (ora - prima); cambiata = True
            if ora:
                r["penalita"] = ora; n_s += 1
            else:
                r.pop("penalita", None)
        if cambiata:
            TR.riordina(g)
        if pen:
            g["nota_penalita"] = "Classifica con i punti di penalizzazione indicati dalla LND (Quadro gare): " + \
                ", ".join(f"{s} -{n}" for s, n in sorted(pen.items())) + "."
        else:
            g.pop("nota_penalita", None)
    return n_p, n_s


def dettagli(data, cfg, det, oggi):
    """--dettagli: legge le giornate vicine di ogni girone abbinato (vedi DETT_*). -> pagine lette."""
    o = dt.date.fromisoformat(oggi)
    da, a = (o - dt.timedelta(days=DETT_PRIMA)).isoformat(), (o + dt.timedelta(days=DETT_DOPO)).isoformat()
    by = {g["gid"]: g for g in data}
    letture = det.setdefault("letture", {})
    ora = TR.adesso()
    lista = []
    for gid, p in sorted((cfg.get("gironi") or {}).items()):
        g = by.get(gid)
        if not g:
            continue
        n_sq = len(g.get("classifica") or [])
        andata = n_sq - 1 if n_sq % 2 == 0 else n_sq
        for num, leg, ini, fine in p.get("giornate") or []:
            if not fine:
                continue
            if not ini or ini < "1900":
                ini = (dt.date.fromisoformat(fine) - dt.timedelta(days=6)).isoformat()
            if fine < da or ini > a:
                continue
            chiave = f"{gid}|{num}|{leg}"
            ultima = letture.get(chiave, "")
            try:
                if ultima and ora - dt.datetime.fromisoformat(ultima) < dt.timedelta(hours=DETT_ORE):
                    continue
            except ValueError:
                pass
            gio = num + (andata if leg == "second" else 0)
            lista.append((ultima, gid, num, leg, gio))
    lista.sort()
    print(f"dati della gara: giornate da leggere {len(lista)}, in questa esecuzione al massimo {DETT_PAGINE}")
    pagine = scritte = 0
    for ultima, gid, num, leg, gio in lista[:DETT_PAGINE]:
        p = cfg["gironi"][gid]
        try:
            props = pagina({"campionato": p["campionato"], "girone": p["girone"], "giornata": num, "leg": leg})
        except Rallentato as e:
            print(f"  ! {gid} giornata {num} {leg}: {e}: lettura interrotta"); break
        except Exception as e:
            print(f"  ! {gid} giornata {num} {leg}: {e}"); continue
        pagine += 1
        cm = props.get("currentMatchday") or {}
        if cm.get("number") != num or cm.get("leg") != leg:
            continue
        letture[f"{gid}|{num}|{leg}"] = ora.isoformat(timespec="minutes")
        scritte += raccogli(props, by[gid], gio, det, oggi)
    # letture vecchie (giornate passate) dimenticate
    limite = (o - dt.timedelta(days=30)).isoformat()
    for k in list(letture):
        if letture[k][:10] < limite:
            del letture[k]
    print(f"dati della gara: pagine lette {pagine}, partite con dati {scritte}")
    return pagine


VERIFICA = {"uguali": 0, "diversi": 0}


def leggi(data, cfg, live, oggi, verifica=False, det=None):
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
            if det is not None and not verifica:
                raccogli(props, g, n + (andata if leg == "second" else 0), det, oggi)  # dati della gara, senza pagine in più
            per = {(TR.k(x["casa"]), TR.k(x["ospite"])): x for x in g["partite"] if x.get("giornata") in gg}
            for m in props.get("matches") or []:
                if m.get("isRest") or m.get("isLive") or not m.get("isPlayed"):
                    continue
                # gare rinviate, sospese, non disputate o da ripetere: il Quadro gare le mostra con 0-0, non sono risultati
                if re.search(r"rinviat|sospes|non disputat|da recuperare|da ripetere|annullat|impraticab", str(m.get("outcome") or "") + " " + str(m.get("resultState") or ""), re.I):
                    continue
                if m.get("homeGoals") is None or m.get("awayGoals") is None:
                    continue
                # 0-0 con una nota qualsiasi (es. "Da Giudice sportivo", "Non disputata per mancanza arbitro" scritta in
                # altro modo, le lettere "F"/"P"/"V.D." dei CU provinciali): non è un pareggio sicuro, si aspetta il CU
                if int(m["homeGoals"]) == 0 and int(m["awayGoals"]) == 0 and str(m.get("outcome") or "").strip():
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
    senza = nostri - set(cfg.get("gironi") or {})
    serve = (vecchia and senza) or cfg.get("scoperta_parziale", "") > cfg.get("scoperta", "") \
        or bool(senza - set(cfg.get("senza_abbinamento") or []))  # gironi nuovi dall'ultima scoperta
    if "--scopri" in sys.argv or not cfg.get("gironi") or ("--solo-scoperta" in sys.argv and serve):
        try:
            scopri(data, cfg)
        except Exception as e:
            print(f"scoperta dei gironi non riuscita ({e})")
    if "--solo-scoperta" in sys.argv:
        if prova:
            print("@@LND@@" + json.dumps(cfg, ensure_ascii=False) + "@@LND@@"); return
        json.dump(cfg, open(CFG, "w"), ensure_ascii=False, indent=1); return
    det = carica_dett()
    if "--dettagli" in sys.argv:
        if prova and os.path.exists(PROVA):
            data = json.load(open(PROVA))  # in prova si continua dal risultato di calcio.py --prova
        try:
            dettagli(data, cfg, det, oggi)
        except Exception as e:
            print(f"dati della gara: lettura non riuscita ({e})")
        n_p, n_s = applica_dettagli(data, det)
        print(f"dati della gara applicati: partite {n_p}, squadre penalizzate {n_s}")
        if prova:
            json.dump(data, open(PROVA, "w"), ensure_ascii=False, separators=(",", ":"))
            print("prova: config e data/risultati.json non modificati, risultato in", PROVA); return
        salva_dett(det)
        json.dump(data, open(RIS, "w"), ensure_ascii=False, separators=(",", ":")); return
    live = TR.carica_live()
    conf, div = TR.pulisci(data, live, oggi)
    print(f"provvisori confermati dal Comunicato: {conf}, diversi: {div}")
    if "--verifica" in sys.argv:
        leggi(data, cfg, live, oggi, verifica=True)
        print(f"verifica Quadro gare / Comunicati (ultimi 7 giorni): {VERIFICA}, pagine lette {LETTE[0]}"); return
    try:
        n = leggi(data, cfg, live, oggi, det=det)
    except Exception as e:
        n = 0; print(f"Quadro gare: lettura non riuscita ({e})")
    print(f"Quadro gare LND: pagine lette {LETTE[0]}, risultati nuovi {n}")
    print("partite aggiornate in app:", TR.applica(data, live, solo_sport={"calcio", "calcio5"}))
    print("dati della gara applicati (partite, squadre penalizzate):", applica_dettagli(data, det))
    if prova:
        json.dump(data, open(PROVA, "w"), ensure_ascii=False, separators=(",", ":"))
        if "--scopri" in sys.argv:
            print("@@LND@@" + json.dumps(cfg, ensure_ascii=False) + "@@LND@@")
        print("prova: config e data/risultati.json non modificati, risultato in", PROVA); return
    json.dump(cfg, open(CFG, "w"), ensure_ascii=False, indent=1)
    TR.salva_live(live)
    salva_dett(det)
    json.dump(data, open(RIS, "w"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
