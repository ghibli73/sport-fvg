"""Funzioni comuni per i risultati "in tempo reale" (manuale: pipeline/agenti/tempo-reale.md).

- fasce di gara (ora italiana): sabato 15-23:30, domenica 15-21:30, lunedì-venerdì 20-23:30;
- risultati provvisori di basket (portale fip.it/risultati, prima dell'omologazione) e calcio (Quadro gare LND, prima del
  Comunicato Ufficiale), salvati in config/live.json e applicati a data/risultati.json con un segno:
    basket  -> "non_omologato": true     calcio -> "provvisorio": true
  la classifica del girone viene aggiornata per differenza (si aggiunge la sola partita) e il girone riceve
  "classifica_provvisoria": true; quando arriva il risultato ufficiale il segno sparisce da solo (lo script dello sport
  ricostruisce il girone dalle fonti ufficiali e applica solo i provvisori che non hanno ancora un risultato ufficiale);
- data/stato.json: ora dell'ultimo aggiornamento e impronta di data/risultati.json (l'app la legge ogni pochi minuti e
  scarica i 2,4 MB dei risultati solo quando l'impronta cambia).
Uso da riga di comando:
  python scripts/tempo_reale.py fascia           -> esce con 0 se ora siamo in una fascia di gara (1 se no)
  python scripts/tempo_reale.py stato <sport>    -> riscrive data/stato.json se data/risultati.json è cambiato
  python scripts/tempo_reale.py applica          -> applica config/live.json a data/risultati.json
"""
import datetime as dt, hashlib, json, os, re, sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIS = os.path.join(ROOT, "data", "risultati.json")
STATO = os.path.join(ROOT, "data", "stato.json")
LIVE = os.path.join(ROOT, "config", "live.json")
ROMA = ZoneInfo("Europe/Rome")
# (giorno della settimana: 0 = lunedì) -> (inizio, fine) in ora italiana
FASCE = {5: ("15:00", "23:30"), 6: ("15:00", "21:30"), **{d: ("20:00", "23:30") for d in range(5)}}
GIORNI_LIVE = 21  # un provvisorio non confermato dopo 3 settimane viene tolto (gara sospesa, annullata...)


def adesso():
    return dt.datetime.now(ROMA)


def in_fascia(t=None, margine=0):
    """True se t (ora italiana) cade in una fascia di gara; margine in minuti dopo la fine (per le ultime gare)."""
    t = t or adesso()
    a, b = FASCE[t.weekday()]
    hm = t.strftime("%H:%M")
    fine = (dt.datetime.combine(t.date(), dt.time.fromisoformat(b)) + dt.timedelta(minutes=margine)).strftime("%H:%M")
    return a <= hm <= fine


def finita(data, ora, durata_min, t=None):
    """True se una gara del giorno `data` alle `ora` è (probabilmente) finita: inizio + durata <= adesso."""
    t = t or adesso()
    if not data:
        return False
    try:
        inizio = dt.datetime.combine(dt.date.fromisoformat(data), dt.time.fromisoformat((ora or "12:00")[:5]), ROMA)
    except ValueError:
        return False
    return inizio + dt.timedelta(minutes=durata_min) <= t


# ------------------------------------------------------------------ classifiche per differenza
def _num(s):
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", s or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def k(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def delta(sport, ris, segno=1):
    """-> ({campi casa}, {campi ospite}) da sommare alle righe di classifica (segno -1 = togliere)."""
    ab = _num(ris)
    if not ab:
        return None
    a, b = ab
    if sport == "pallavolo":
        if max(a, b) != 3 or a == b:
            return None
        pa, pb = (3, 0) if a == 3 and b <= 1 else (2, 1) if a == 3 else (0, 3) if a <= 1 else (1, 2)
        c = {"punti": pa, "g": 1, "v": int(a > b), "p": int(a < b), "set_v": a, "set_p": b}
        o = {"punti": pb, "g": 1, "v": int(b > a), "p": int(b < a), "set_v": b, "set_p": a}
    elif sport == "basket":
        if a == b:
            return None
        c = {"punti": 2 * int(a > b), "g": 1, "v": int(a > b), "p": int(a < b), "f": a, "s": b}
        o = {"punti": 2 * int(b > a), "g": 1, "v": int(b > a), "p": int(b < a), "f": b, "s": a}
    else:  # calcio, calcio a 5
        c = {"punti": 3 if a > b else 1 if a == b else 0, "g": 1, "v": int(a > b), "n": int(a == b), "p": int(a < b), "gf": a, "gs": b}
        o = {"punti": 3 if b > a else 1 if a == b else 0, "g": 1, "v": int(b > a), "n": int(a == b), "p": int(b < a), "gf": b, "gs": a}
    if segno < 0:
        c = {x: -y for x, y in c.items()}; o = {x: -y for x, y in o.items()}
    return c, o


def riordina(g):
    sp = g.get("sport")
    if sp == "pallavolo":
        chiave = lambda r: (-(r.get("punti") or 0), -(r.get("v") or 0), -((r.get("set_v") or 0) / max(1, r.get("set_p") or 0)))
    elif sp == "basket":
        chiave = lambda r: (-(r.get("v") or 0), -((r.get("f") or 0) - (r.get("s") or 0)), -(r.get("f") or 0))
    else:
        chiave = lambda r: (-(r.get("punti") or 0), -((r.get("gf") or 0) - (r.get("gs") or 0)), -(r.get("gf") or 0))
    g["classifica"].sort(key=chiave)  # sort stabile: a parità resta l'ordine ufficiale
    for i, r in enumerate(g["classifica"], 1):
        r["pos"] = i


def somma_partita(g, p, ris, segno=1):
    """Aggiunge (o toglie) una partita alla classifica del girone. -> True se entrambe le squadre sono in classifica."""
    d = delta(g.get("sport"), ris, segno)
    if not d:
        return False
    righe = {k(r["squadra"]): r for r in g.get("classifica") or []}
    rc, ro = righe.get(k(p["casa"])), righe.get(k(p["ospite"]))
    if not rc or not ro:
        return False
    for r, dd in ((rc, d[0]), (ro, d[1])):
        for campo, v in dd.items():
            if campo in r or campo in ("punti", "g", "v", "p"):
                r[campo] = (r.get(campo) or 0) + v
    return True


# ------------------------------------------------------------------ provvisori (config/live.json)
SEGNO = {"basket": "non_omologato", "calcio": "provvisorio", "calcio5": "provvisorio"}


def carica_live():
    return json.load(open(LIVE)) if os.path.exists(LIVE) else {"gironi": {}}


def salva_live(live):
    json.dump(live, open(LIVE, "w"), ensure_ascii=False, indent=1, sort_keys=True)


def chiave_partita(p):
    return f"gara:{p['gara']}" if p.get("gara") else f"{k(p['casa'])}|{k(p['ospite'])}|{p.get('giornata')}"


def applica(data, live=None, solo_sport=None):
    """Applica i provvisori di config/live.json alle partite ancora senza risultato ufficiale. Idempotente:
    una partita già segnata come provvisoria con lo stesso punteggio resta com'è; se il punteggio è cambiato
    la classifica viene corretta. -> numero di partite cambiate."""
    live = live if live is not None else carica_live()
    cambiate = 0
    by = {g["gid"]: g for g in data}
    for gid, voci in (live.get("gironi") or {}).items():
        g = by.get(gid)
        if not g or (solo_sport and g.get("sport") not in solo_sport):
            continue
        segno = SEGNO.get(g.get("sport"), "provvisorio")
        per = {chiave_partita(p): p for p in g.get("partite") or []}
        for kk, v in voci.items():
            p = per.get(kk)
            if p is None and v.get("nuova"):
                # partita che il calendario dell'app non ha (es. girone senza calendario): si aggiunge solo se nessuna
                # delle due squadre gioca già in quella giornata
                n = v["nuova"]
                if any(x.get("giornata") == n.get("giornata") and {k(x["casa"]), k(x["ospite"])} & {k(n["casa"]), k(n["ospite"])}
                       for x in g.get("partite") or []):
                    continue
                p = dict(n, risultato="")
                g["partite"].append(p); per[kk] = p
            if p is None:
                continue
            if p.get("risultato") and not p.get(segno):
                continue  # c'è già il risultato ufficiale: vale quello
            if p.get(segno) and p.get("risultato") == v["r"]:
                continue
            if p.get(segno) and p.get("risultato"):
                somma_partita(g, p, p["risultato"], -1)
            p["risultato"] = v["r"]
            p[segno] = True
            if v.get("parziali"):
                p["parziali"] = v["parziali"]
            if somma_partita(g, p, v["r"]):
                g["classifica_provvisoria"] = True
            cambiate += 1
        if any(p.get(segno) for p in g.get("partite") or []):
            g["classifica_provvisoria"] = True
            riordina(g)
            gio = [p.get("giornata") or 0 for p in g["partite"] if p.get("risultato")]
            if gio:
                g["giornata"] = max(g.get("giornata") or 0, max(gio))
            g["partite"].sort(key=lambda m: (m.get("data") or "9999", m.get("ora") or ""))
    return cambiate


def pulisci(data, live, oggi):
    """Toglie da config/live.json i provvisori che hanno già il risultato ufficiale (e quelli troppo vecchi).
    Stampa le differenze tra provvisorio e ufficiale (vale l'ufficiale). -> (confermati, diversi)."""
    by = {g["gid"]: g for g in data}
    conf = div = 0
    limite = (dt.date.fromisoformat(oggi) - dt.timedelta(days=GIORNI_LIVE)).isoformat()
    for gid in list((live.get("gironi") or {})):
        g = by.get(gid)
        voci = live["gironi"][gid]
        if not g:
            del live["gironi"][gid]; continue
        segno = SEGNO.get(g.get("sport"), "provvisorio")
        per = {chiave_partita(p): p for p in g.get("partite") or []}
        for kk in list(voci):
            p = per.get(kk); v = voci[kk]
            if p and p.get("risultato") and not p.get(segno):
                if p["risultato"] == v["r"]:
                    conf += 1
                else:
                    div += 1
                    print(f"  {gid} {p['casa']} - {p['ospite']}: provvisorio {v['r']}, ufficiale {p['risultato']} (vale l'ufficiale)")
                del voci[kk]
            elif (v.get("data") or "9999") < limite:
                del voci[kk]
        if not voci:
            del live["gironi"][gid]
    return conf, div


# ------------------------------------------------------------------ data/stato.json
def impronta(path=RIS):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()[:12]


def scrivi_stato(sport):
    """Aggiorna data/stato.json solo se l'impronta di data/risultati.json è cambiata. -> True se scritto."""
    st = json.load(open(STATO)) if os.path.exists(STATO) else {}
    imp = impronta()
    if st.get("versione") == imp:
        return False
    ora = adesso().isoformat(timespec="seconds")
    st.update({"versione": imp, "aggiornato": ora})
    st.setdefault("sport", {})
    for s in sport:
        st["sport"][s] = ora
    st["fasce"] = {"sab": "15:00-23:30", "dom": "15:00-21:30", "lun-ven": "20:00-23:30"}
    json.dump(st, open(STATO, "w"), ensure_ascii=False, indent=1)
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fascia":
        ok = in_fascia(margine=int(os.environ.get("MARGINE", "15")))
        print("in fascia di gara" if ok else "fuori fascia", adesso().strftime("%a %H:%M"))
        sys.exit(0 if ok else 1)
    if cmd == "stato":
        print("data/stato.json", "aggiornato" if scrivi_stato(sys.argv[2:]) else "invariato")
    elif cmd == "applica":
        d = json.load(open(RIS)); n = applica(d)
        json.dump(d, open(RIS, "w"), ensure_ascii=False, separators=(",", ":")); print("provvisori applicati:", n)
    else:
        print(__doc__)
