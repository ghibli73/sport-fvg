"""Avvisi dei risultati con ntfy.sh (gratuito, senza account) per l'app Zuìn – Sport in FVG.

  python scripts/avvisi.py [prima.json] [dopo.json] [--prova]

Confronta data/risultati.json prima/dopo l'aggiornamento (per default /tmp/risultati_prima.json e
data/risultati.json) e, per ogni partita che ha appena ricevuto il risultato, pubblica un avviso
sull'argomento pubblico di ciascuna delle due società: https://ntfy.sh/zuin-fvg-<id società>
(caratteri non alfanumerici dell'id sostituiti da "-", come in index.html).

- titolo "Casa 3-1 Ospite", testo = nome del girone, Click -> pagina del girone, Tags "trophy";
- al massimo MAX_AVVISI per esecuzione, pausa PAUSA secondi tra un invio e l'altro;
- solo partite che prima esistevano senza risultato, oppure nuove con data negli ultimi GIORNI_NUOVE
  giorni (un girone aggiunto per la prima volta non deve mandare decine di avvisi vecchi);
- nessun avviso se la variabile SILENZIOSO è "true" (input del lancio manuale) o con --prova
  (stampa soltanto);
- partite spostate: se una partita non ancora giocata cambia data o ora e la data (nuova o vecchia) cade
  entro i prossimi GIORNI_SPOSTATE giorni, avviso "Partita spostata" alle due società (titolo
  "Partita spostata: Casa – Ospite", testo "sab 28/11 ore 14:30 (era dom 29/11 ore 14:30) · girone",
  Tags "calendar"). Stessa partita = stesso girone e numero gara, altrimenti stesse squadre e giornata
  (come in scripts/variazioni.py); stesse regole, stessa pausa e stesso limite MAX_AVVISI dei risultati
  (i risultati hanno la precedenza);
- non fa mai fallire il workflow: ogni errore viene stampato e lo script termina con codice 0.
"""
import base64
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITO = "https://ghibli73.github.io/sport-fvg/"
NTFY = "https://ntfy.sh/"
MAX_AVVISI = 200
PAUSA = 0.3
GIORNI_NUOVE = 3
GIORNI_SPOSTATE = 10  # avvisi di partita spostata solo per le partite dei prossimi 10 giorni
TEMPO_MAX = 8 * 60  # secondi: oltre si smette (il workflow deve poi salvare i dati)


def argomento(sid):
    return "zuin-fvg-" + re.sub(r"[^A-Za-z0-9]", "-", str(sid))


def _s(v):
    return "" if v is None else str(v)


def chiave(g, x):
    return (g["gid"], _s(x.get("giornata")), _s(x.get("gara")), _s(x.get("casa")), _s(x.get("ospite")))


def intestazione(v):
    """Gli header HTTP accettano solo latin-1: il testo non ASCII va codificato (RFC 2047), che ntfy decodifica."""
    try:
        v.encode("ascii")
        return v
    except UnicodeEncodeError:
        return "=?UTF-8?B?" + base64.b64encode(v.encode("utf-8")).decode("ascii") + "?="


def nuovi_risultati(prima, dopo, oggi):
    vecchie = {}
    for g in prima:
        for x in g.get("partite", []):
            vecchie[chiave(g, x)] = x
    dal = (oggi - dt.timedelta(days=GIORNI_NUOVE)).isoformat()
    out = []
    for g in dopo:
        for x in g.get("partite", []):
            if not x.get("risultato"):
                continue
            v = vecchie.get(chiave(g, x))
            if v is not None:
                if v.get("risultato"):
                    continue
            elif not (x.get("data") or "") >= dal:
                continue
            out.append((g, x))
    return out


GG = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]


def quando(data, ora):
    try:
        d = dt.date.fromisoformat(data)
        t = f"{GG[d.weekday()]} {d.day:02d}/{d.month:02d}"
    except (TypeError, ValueError):
        t = data or "data da definire"
    return t + (f" ore {ora}" if ora else "")


def partite_spostate(prima, dopo, oggi):
    """Partite non giocate con data o ora cambiata, giocate (prima o dopo lo spostamento) entro GIORNI_SPOSTATE giorni."""
    try:
        import variazioni as V
    except Exception:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import variazioni as V
    idx = V.indice(prima)
    da, a = oggi.isoformat(), (oggi + dt.timedelta(days=GIORNI_SPOSTATE)).isoformat()
    out = []
    for g in dopo:
        for x in g.get("partite", []):
            if x.get("risultato") or not (x.get("data") or "") >= da:
                continue
            v = V.trova(idx, g["gid"], x)
            if not V.cambiata(v, x):
                continue
            if da <= x["data"] <= a or da <= (v.get("data") or "") <= a:
                out.append((g, x, v))
    return out


def invia(topic, titolo, testo, click, tags="trophy"):
    req = urllib.request.Request(NTFY + topic, data=testo.encode("utf-8"), method="POST", headers={
        "Title": intestazione(titolo), "Tags": tags, "Click": click,
        "User-Agent": "Zuin-SportFVG/1.0 (" + SITO + ")"})
    for tentativo in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code == 429 and tentativo < 2:  # troppe richieste: ntfy chiede di rallentare
                time.sleep(float(e.headers.get("Retry-After") or 6))
                continue
            return e.code
        except Exception as e:
            print("  errore di rete:", e)
            return None
    return None


def main(argv):
    prova = "--prova" in argv
    argv = [a for a in argv if not a.startswith("--")]
    f_prima = argv[0] if argv else "/tmp/risultati_prima.json"
    f_dopo = argv[1] if len(argv) > 1 else os.path.join(BASE, "data", "risultati.json")
    if os.environ.get("SILENZIOSO", "").strip().lower() in ("true", "1", "si", "sì"):
        print("Avvisi: esecuzione silenziosa, nessun invio")
        return
    if not os.path.exists(f_prima):
        print("Avvisi: manca", f_prima, "- nessun invio")
        return
    prima = json.load(open(f_prima, encoding="utf-8"))
    dopo = json.load(open(f_dopo, encoding="utf-8"))
    ids = {c["id"] for c in json.load(open(os.path.join(BASE, "data", "data.json"), encoding="utf-8"))}
    partite = nuovi_risultati(prima, dopo, dt.date.today())
    coda = []
    for g, x in partite:
        titolo = f"{x['casa']} {x['risultato']} {x['ospite']}"
        for sid in dict.fromkeys([x.get("id_casa"), x.get("id_ospite")]):
            if sid and sid in ids:
                coda.append((argomento(sid), titolo, g["girone"], SITO + "#g-" + g["gid"], "trophy"))
    n_ris = len(coda)
    spostate = partite_spostate(prima, dopo, dt.date.today())
    for g, x, v in spostate:
        titolo = f"Partita spostata: {x['casa']} – {x['ospite']}"
        testo = f"{quando(x['data'], x.get('ora'))} (era {quando(v.get('data'), v.get('ora'))}) · {g['girone']}"
        for sid in dict.fromkeys([x.get("id_casa"), x.get("id_ospite")]):
            if sid and sid in ids:
                coda.append((argomento(sid), titolo, testo, SITO + "#g-" + g["gid"], "calendar"))
    print(f"Avvisi: {len(partite)} partite con risultato nuovo ({n_ris} avvisi), {len(spostate)} partite spostate "
          f"nei prossimi {GIORNI_SPOSTATE} giorni ({len(coda) - n_ris} avvisi)"
          + (f"; si inviano i primi {MAX_AVVISI}" if len(coda) > MAX_AVVISI else ""))
    inizio, ok, ko = time.time(), 0, 0
    for i, (topic, titolo, testo, click, tags) in enumerate(coda[:MAX_AVVISI]):
        if prova:
            print("  [prova]", topic, "|", titolo, "|", testo, "|", click)
            continue
        if time.time() - inizio > TEMPO_MAX:
            print(f"  tempo massimo raggiunto: inviati {ok}, saltati {len(coda[:MAX_AVVISI]) - i}")
            break
        st = invia(topic, titolo, testo, click, tags)
        if st and 200 <= st < 300:
            ok += 1
        else:
            ko += 1
            print("  non inviato:", topic, st)
        time.sleep(PAUSA)
    if not prova:
        print(f"Avvisi inviati: {ok}, non inviati: {ko}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:  # gli avvisi non devono mai bloccare la pubblicazione dei risultati
        print("avvisi.py: errore", e)
    sys.exit(0)
