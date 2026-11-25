"""Partite spostate: confronta i dati prima/dopo un aggiornamento e segna le partite future cambiate.

  python scripts/variazioni.py [prima.json] [dopo.json] [--prova]

Per ogni partita senza risultato di dopo.json (default data/risultati.json) cerca la stessa partita in
prima.json (default /tmp/risultati_prima.json): stesso girone e stesso numero gara ("gara"), altrimenti
stesse squadre e stessa giornata. Se la data o l'ora sono cambiate e la partita non è ancora giocata:
  "variata": "AAAA-MM-GG"   giorno in cui ce ne siamo accorti (oggi)
  "data_prec": "AAAA-MM-GG" data di prima, se è cambiata la data
  "ora_prec": "HH:MM"       ora di prima, se è cambiata solo l'ora
I segni già presenti prima vengono riportati (gli script del basket e del calcio ricostruiscono i gironi da
capo) e tolti dopo GIORNI_SEGNO giorni. Un'ora che sparisce (dato mancante) non è una variazione.
Stampa anche un rapporto: partite future prima/dopo per sport, partite spostate, controlli
(squadra due volte nella stessa giornata, partita futura con risultato).
--prova: non scrive il file, stampa soltanto.
Non fa mai fallire il workflow.
"""
import datetime as dt
import json
import os
import re
import sys
from collections import Counter

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GIORNI_SEGNO = 30  # dopo quanti giorni il segno "variata" viene tolto (l'app lo mostra per 7)


def _k(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def chiavi(gid, p):
    """Chiavi con cui riconoscere la stessa partita in due versioni dei dati (la prima è la più sicura)."""
    out = []
    if str(p.get("gara") or "").strip():
        out.append((gid, "#", str(p["gara"]).strip().lstrip("0")))
    out.append((gid, _k(p.get("casa")), _k(p.get("ospite")), str(p.get("giornata") or "")))
    return out


def indice(dati):
    idx = {}
    for g in dati:
        for p in g.get("partite", []):
            for c in chiavi(g["gid"], p):
                idx.setdefault(c, p)
    return idx


def trova(idx, gid, p):
    for c in chiavi(gid, p):
        if c in idx:
            return idx[c]
    return None


def cambiata(p0, p):
    """True se data o ora sono cambiate (un'ora che manca nella versione nuova non conta)."""
    if not p0 or p0.get("risultato") or not p0.get("data") or not p.get("data"):
        return False
    if p["data"] != p0["data"]:
        return True
    return bool(p.get("ora") and p0.get("ora") and p["ora"] != p0["ora"])


def segna(prima, dopo, oggi):
    """Aggiunge/riporta i campi variata/data_prec/ora_prec in dopo. -> elenco (girone, partita) spostate oggi."""
    idx = indice(prima)
    limite = (oggi - dt.timedelta(days=GIORNI_SEGNO)).isoformat()
    oggi_s = oggi.isoformat()
    nuove = []
    for g in dopo:
        for p in g.get("partite", []):
            p0 = trova(idx, g["gid"], p)
            if not p.get("risultato") and (p.get("data") or "") >= oggi_s and cambiata(p0, p):
                p["variata"] = oggi_s
                p.pop("data_prec", None); p.pop("ora_prec", None)
                if p["data"] != p0["data"]:
                    p["data_prec"] = p0["data"]
                else:
                    p["ora_prec"] = p0["ora"]
                nuove.append((g, p, p0))
                continue
            # riporta il segno di prima (se la partita non è cambiata di nuovo)
            if p0 and p0.get("variata") and not p.get("variata"):
                for f in ("variata", "data_prec", "ora_prec"):
                    if p0.get(f):
                        p[f] = p0[f]
            if (p.get("variata") or "9") < limite:
                for f in ("variata", "data_prec", "ora_prec"):
                    p.pop(f, None)
    return nuove


def future(dati, oggi_s):
    c = Counter()
    for g in dati:
        c[g["sport"]] += sum(1 for p in g.get("partite", []) if not p.get("risultato") and (p.get("data") or "") >= oggi_s)
    return c


def controlli(dati, oggi_s):
    """Squadre due volte nella stessa giornata (baseball escluso: doppi incontri) e partite future con risultato."""
    doppie, fut_ris = [], []
    for g in dati:
        if g["sport"] != "baseball":
            c = Counter((p.get("giornata"), _k(t)) for p in g.get("partite", []) if p.get("giornata") is not None
                        for t in (p.get("casa"), p.get("ospite")))
            doppie += [(g["gid"], gi, t) for (gi, t), n in c.items() if n > 1]
        fut_ris += [(g["gid"], p.get("casa"), p.get("ospite"), p.get("data")) for p in g.get("partite", [])
                    if p.get("risultato") and (p.get("data") or "") > oggi_s]
    return doppie, fut_ris


def main(argv):
    prova = "--prova" in argv
    argv = [a for a in argv if not a.startswith("--")]
    f_prima = argv[0] if argv else "/tmp/risultati_prima.json"
    f_dopo = argv[1] if len(argv) > 1 else os.path.join(BASE, "data", "risultati.json")
    if not os.path.exists(f_prima) or not os.path.exists(f_dopo):
        print("Variazioni: file mancante, niente da confrontare"); return
    prima = json.load(open(f_prima, encoding="utf-8"))
    dopo = json.load(open(f_dopo, encoding="utf-8"))
    oggi = dt.date.today(); oggi_s = oggi.isoformat()
    nuove = segna(prima, dopo, oggi)
    fp, fd = future(prima, oggi_s), future(dopo, oggi_s)
    print("Partite future (da oggi) prima -> dopo:")
    for s in sorted(set(fp) | set(fd)):
        print(f"  {s}: {fp.get(s, 0)} -> {fd.get(s, 0)}")
    print(f"Partite spostate rilevate in questo aggiornamento: {len(nuove)}")
    for g, p, p0 in nuove[:60]:
        print(f"  {g['gid']}: {p.get('casa')} - {p.get('ospite')}: {p0.get('data')} {p0.get('ora') or ''} -> {p.get('data')} {p.get('ora') or ''}")
    doppie, fut_ris = controlli(dopo, oggi_s)
    print(f"Controlli: squadre doppie nella stessa giornata {len(doppie)}, partite future con risultato {len(fut_ris)}")
    for x in doppie[:20]: print("  doppia:", x)
    for x in fut_ris[:20]: print("  futura con risultato:", x)
    if prova:
        print("Variazioni: prova, file non scritto"); return
    json.dump(dopo, open(f_dopo, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:  # non deve mai bloccare la pubblicazione dei risultati
        print("variazioni.py: errore", e)
    sys.exit(0)
