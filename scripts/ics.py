"""Calendari .ics delle società per l'abbonamento (webcal) dall'app Zuìn – Sport in FVG.

  python scripts/ics.py            -> scrive data/ics/<id_società>.ics per ogni società con partite

Ogni file contiene le partite delle squadre della società presenti in data/risultati.json:
quelle giocate negli ultimi GIORNI_PASSATI giorni (con il risultato nel titolo) e tutte quelle future.
Formato e UID sono gli stessi del pulsante "Aggiungi al calendario" in index.html (fnv1a su
gid|giornata|gara|casa|ospite), così un evento scaricato e uno dell'abbonamento non si duplicano.
DTSTAMP = data di aggiornamento del girone: i file cambiano solo quando cambiano i dati.
I file di società che non hanno più partite vengono tolti.
"""
import datetime as dt
import json
import os
import re
import sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITO = "https://ghibli73.github.io/sport-fvg/"
GIORNI_PASSATI = 30
TZ = ["BEGIN:VTIMEZONE", "TZID:Europe/Rome", "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0100", "TZOFFSETTO:+0200",
      "TZNAME:CEST", "DTSTART:19700329T020000", "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
      "BEGIN:STANDARD", "TZOFFSETFROM:+0200", "TZOFFSETTO:+0100", "TZNAME:CET", "DTSTART:19701025T030000",
      "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD", "END:VTIMEZONE"]


def fnv(s):
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return "%08x" % h


def _s(v):
    return "" if v is None else str(v)


def uid(g, x):
    chiave = "|".join([g["gid"], _s(x.get("giornata")), _s(x.get("gara")), _s(x.get("casa")), _s(x.get("ospite"))])
    return f"{g['gid']}-{fnv(chiave)}@zuin-fvg"


def testo(s):
    return _s(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r\n", "\\n").replace("\n", "\\n")


def piega(riga):
    parti, cur, n, lim = [], "", 0, 75
    for ch in riga:
        b = len(ch.encode("utf-8"))
        if n + b > lim:
            parti.append(cur)
            cur, n, lim = "", 0, 74
        cur += ch
        n += b
    parti.append(cur)
    return "\r\n ".join(parti)


def evento(g, x):
    y, m, d = (int(v) for v in x["data"].split("-"))
    o = re.fullmatch(r"(\d{1,2}):(\d\d)", x.get("ora") or "")
    if o:
        s = dt.datetime(y, m, d, int(o[1]), int(o[2]))
        a = "DTSTART;TZID=Europe/Rome:" + s.strftime("%Y%m%dT%H%M%S")
        b = "DTEND;TZID=Europe/Rome:" + (s + dt.timedelta(hours=2)).strftime("%Y%m%dT%H%M%S")
    else:
        s = dt.date(y, m, d)
        a = "DTSTART;VALUE=DATE:" + s.strftime("%Y%m%d")
        b = "DTEND;VALUE=DATE:" + (s + dt.timedelta(days=1)).strftime("%Y%m%d")
    ris = x.get("risultato")
    titolo = f"{x['casa']}{' ' + ris + ' ' if ris else ' – '}{x['ospite']} ({g['girone']})"
    descr = "\n".join(v for v in [g["girone"], f"{x['giornata']}ª giornata" if x.get("giornata") is not None else "",
                                  "Dati non ufficiali: fa fede la federazione. " + SITO + "#g-" + g["gid"]] if v)
    agg = (g.get("aggiornato") or dt.date.today().isoformat()).replace("-", "")
    righe = ["BEGIN:VEVENT", "UID:" + uid(g, x), "DTSTAMP:" + agg + "T000000Z", a, b, "SUMMARY:" + testo(titolo)]
    if x.get("campo"):
        righe.append("LOCATION:" + testo(x["campo"]))
    righe += ["DESCRIPTION:" + testo(descr), "URL:" + SITO + "#g-" + g["gid"], "END:VEVENT"]
    return righe


def calendario(nome, eventi):
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Zuin Sport in FVG//IT", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", "X-WR-CALNAME:" + testo(nome), "X-WR-TIMEZONE:Europe/Rome",
             "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"] + TZ
    for e in eventi:
        righe += e
    righe.append("END:VCALENDAR")
    return "\r\n".join(piega(r) for r in righe) + "\r\n"


def main():
    oggi = dt.date.today()
    dal = (oggi - dt.timedelta(days=GIORNI_PASSATI)).isoformat()
    gironi = json.load(open(os.path.join(BASE, "data", "risultati.json"), encoding="utf-8"))
    nomi = {c["id"]: c["nome"] for c in json.load(open(os.path.join(BASE, "data", "data.json"), encoding="utf-8"))}
    per_soc = {}
    for g in gironi:
        for x in g.get("partite", []):
            for sid in {x.get("id_casa"), x.get("id_ospite")} - {None, ""}:
                lista = per_soc.setdefault(sid, [])
                d = x.get("data") or ""
                if not re.fullmatch(r"\d{4}-\d\d-\d\d", d):
                    continue
                if (x.get("risultato") and d >= dal) or (not x.get("risultato") and d >= oggi.isoformat()):
                    lista.append((d, x.get("ora") or "", g, x))
    cartella = os.path.join(BASE, "data", "ics")
    os.makedirs(cartella, exist_ok=True)
    scritti, eventi_tot = set(), 0
    for sid, lista in sorted(per_soc.items()):
        if sid not in nomi:
            continue
        lista.sort(key=lambda t: (t[0], t[1]))
        nome = f"{sid}.ics"
        txt = calendario("Zuìn · " + nomi[sid], [evento(g, x) for _, _, g, x in lista])
        p = os.path.join(cartella, nome)
        vecchio = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else None
        if vecchio != txt:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(txt)
        scritti.add(nome)
        eventi_tot += len(lista)
    tolti = 0
    for f in os.listdir(cartella):
        if f.endswith(".ics") and f not in scritti:
            os.remove(os.path.join(cartella, f))
            tolti += 1
    print(f"Calendari: {len(scritti)} società, {eventi_tot} eventi, {tolti} file tolti")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # il calendario non deve mai bloccare la pubblicazione dei risultati
        print("ics.py: errore", e, file=sys.stderr)
        sys.exit(0)
