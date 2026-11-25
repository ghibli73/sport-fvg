"""Controllo qualità dei dati di Sport in FVG (solo libreria standard).

Uso:
    python scripts/test_dati.py                  # report testuale completo
    python scripts/test_dati.py --json out.json  # salva anche il report in JSON
    python scripts/test_dati.py --oggi 2026-11-25 --max 30

Legge data/data.json, data/risultati.json, data/comuni.json (percorsi modificabili con
--data, --risultati, --comuni). Esce con codice 1 se trova problemi di gravità "alta".

Controlli (gravità tra parentesi):
  A. Società
     doppioni_nome        (alta)  stesso comune + sport con nomi simili
     doppioni_social      (alta)  stesso profilo facebook/instagram su più società
     doppioni_indirizzo   (media) stesso comune + sport + indirizzo
     indirizzo_altro_comune (media) l'indirizzo termina con il nome di un altro comune FVG
     cap_incoerente       (bassa) CAP dell'indirizzo non compatibile con la provincia
     social_malformato    (media) URL social/sito non normalizzati o non validi
     social_polisportiva  (bassa) stesso profilo su società di sport diversi (sezioni di una polisportiva?)
     sito_condiviso       (bassa) stesso sito web su più società (spesso polisportive: da guardare)
     squadra_senza_campionato (media)
     squadra_stagione     (media) stagione diversa da 2026/27
     categoria_non_standard (bassa)
     comune_senza_societa (bassa)
     squadra_sport        (media) campionato/fonte di uno sport diverso da quello della società
     squadra_genere       (media) genere della squadra diverso da quello scritto nel campionato
     prima_squadra_doppia (alta)  la società risulta in due campionati di prima squadra dello stesso genere
     livello_incoerente   (media) seconda squadra in un campionato di livello superiore alla prima
     id_doppio_girone     (bassa) lo stesso id dato a due squadre con nomi diversi nello stesso girone
     id_alias_usato       (alta)  id unito/rimosso (data/id_alias.json) ancora usato nei risultati
  B. Risultati
     id_mancante          (media) squadre senza id nelle classifiche
     id_inesistente       (alta)  id in risultati.json che non esiste in data.json
     giocate_incoerenti   (alta)  partite con risultato != somma giocate classifica / 2
     giornata_doppia      (alta)  una squadra due volte nella stessa giornata
     girone_fermo         (media) "aggiornato" più vecchio di 7 giorni
     girone_stagione      (media) stagione del girone diversa da 2026/27
"""
import argparse
import difflib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGIONE = "2026/27"
GRAVITA = {
    "doppioni_nome": "alta", "doppioni_social": "alta", "id_inesistente": "alta",
    "giocate_incoerenti": "alta", "giornata_doppia": "alta",
    "doppioni_indirizzo": "bassa", "indirizzo_altro_comune": "media", "social_malformato": "media",
    "squadra_senza_campionato": "media", "squadra_stagione": "media", "id_mancante": "media",
    "girone_fermo": "media", "girone_stagione": "media",
    "cap_incoerente": "bassa", "sito_condiviso": "bassa", "social_polisportiva": "bassa", "categoria_non_standard": "bassa",
    "comune_senza_societa": "bassa",
    "squadra_sport": "media", "squadra_genere": "media", "prima_squadra_doppia": "alta",
    "livello_incoerente": "media", "id_alias_usato": "alta", "id_doppio_girone": "bassa",
}
ORDINE = {"alta": 0, "media": 1, "bassa": 2}

STOP = {"asd", "ssd", "as", "a", "s", "d", "pol", "polisportiva", "associazione", "sportiva", "sportivo",
        "dilettantistica", "dilettantistico", "societa", "rl", "arl", "srl", "us", "gs", "ac", "sd", "apd",
        "asdr", "scsd", "aps", "ssdrl", "volley", "pallavolo", "calcio", "basket", "pallacanestro", "di", "del",
        "della", "dei", "e", "il", "la", "lo", "club", "team", "ad", "cs", "uc", "ssdarl", "sc", "ct", "fc"}

CATEGORIA_OK = re.compile(
    r"^(Under (6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|23)|Juniores|Prima squadra|Seconda squadra|"
    r"Terza squadra|Quarta squadra)( \((2|3|4|5)ª squadra\))?$")
FB_OK = re.compile(r"^https://www\.facebook\.com/([^?#\s]+|profile\.php\?id=\d+)$")
IG_OK = re.compile(r"^https://www\.instagram\.com/[A-Za-z0-9._]+/$")
SITO_OK = re.compile(r"^https?://[^\s/]+\.[a-z]{2,}(/\S*)?$", re.I)
PUNTEGGIO = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def chiave_nome(n):
    n = re.sub(r"\b([a-z])\.(?=[a-z]\.)", r"\1", str(n).lower())  # A.S.D. -> asd
    return " ".join(w for w in norm(n.replace(".", "")).split() if w not in STOP)


def norm_url(u):
    u = str(u or "").strip().lower().split("?")[0].split("#")[0]
    u = re.sub(r"^https?://(www\.|m\.|it-it\.|it\.)?", "", u)
    return u.rstrip("/")


SPORT_PAROLE = {"atletica", "judo", "karate", "nuoto", "tennis", "padel", "ciclismo", "scherma", "ginnastica",
                "danza", "sci", "vela", "canottaggio", "canoa", "bocce", "tiro", "equitazione", "rugby", "hockey",
                "baseball", "softball", "pattinaggio", "c", "5", "calcetto", "futsal", "nuoto", "podismo", "skating"}


def simili(a, b, comune=""):
    """Nomi simili dopo aver tolto forme societarie, nome del comune e nome dello sport."""
    via = set(norm(comune).split()) | SPORT_PAROLE
    ka = " ".join(w for w in chiave_nome(a).split() if w not in via)
    kb = " ".join(w for w in chiave_nome(b).split() if w not in via)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    ta, tb = set(ka.split()), set(kb.split())
    piccolo, grande = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(piccolo) >= 2 and piccolo <= grande:
        return True
    return difflib.SequenceMatcher(None, ka, kb).ratio() >= 0.88


def cap_ok(cap, prov):
    c = int(cap)
    if prov == "UD":
        return 33010 <= c <= 33069 or c == 33100 or c == 32047  # 33061 Rivignano Teor, 32047 Sappada
    if prov == "PN":
        return 33070 <= c <= 33099 or c == 33170
    if prov == "GO":
        return 34070 <= c <= 34079 or c == 34170
    if prov == "TS":
        return 34010 <= c <= 34018 or 34100 <= c <= 34151
    return True


def controlla_societa(data, comuni, out):
    nomi_comuni = {norm(c["nome"]): c for c in comuni}
    per_cs = defaultdict(list)
    for x in data:
        per_cs[(x["codice"], x["sport"])].append(x)

    # doppioni per nome e per indirizzo (stesso comune + sport)
    for (cod, sp), lst in per_cs.items():
        per_ind = defaultdict(list)
        for x in lst:
            ind = norm(x.get("indirizzo"))
            if ind and len(ind) > 8:
                per_ind[ind].append(x)
        for ind, gruppo in per_ind.items():
            if len(gruppo) > 1:
                elenco = "; ".join(f"{x['id']} «{x['nome']}»" for x in gruppo)
                out.append(("doppioni_indirizzo", f"{gruppo[0]['comune']}, {sp}: «{gruppo[0]['indirizzo']}» → {elenco}"))
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = lst[i], lst[j]
                if simili(a["nome"], b["nome"], a["comune"]):
                    out.append(("doppioni_nome", f"{a['id']} «{a['nome']}» ~ {b['id']} «{b['nome']}» ({a['comune']}, {sp})"))

    # social e siti condivisi / malformati
    uso = defaultdict(list)
    for x in data:
        so = x.get("social") or {}
        for k, v in so.items():
            if k == "facebook" and not FB_OK.match(v or ""):
                out.append(("social_malformato", f"{x['id']} «{x['nome']}» facebook: {v}"))
            elif k == "instagram" and not IG_OK.match(v or ""):
                out.append(("social_malformato", f"{x['id']} «{x['nome']}» instagram: {v}"))
            elif k == "sito" and not SITO_OK.match(v or ""):
                out.append(("social_malformato", f"{x['id']} «{x['nome']}» sito: {v}"))
            elif k not in ("facebook", "instagram", "sito"):
                out.append(("social_malformato", f"{x['id']} «{x['nome']}» chiave sconosciuta {k}: {v}"))
            if v:
                uso[(k, norm_url(v))].append(x)
    for (k, u), lst in sorted(uso.items()):
        if len(lst) > 1:
            elenco = "; ".join(f"{x['id']} «{x['nome']}» ({x['comune']}, {x['sport']})" for x in lst)
            stesso_sport = len({x["sport"] for x in lst}) < len(lst)
            tipo = "sito_condiviso" if k == "sito" else ("doppioni_social" if stesso_sport else "social_polisportiva")
            out.append((tipo, f"{k} {u} → {elenco}"))

    # indirizzo che cita un altro comune / CAP incoerente
    for x in data:
        ind = str(x.get("indirizzo") or "")
        if not ind:
            continue
        coda = ind.split(",")[-1]
        coda = re.sub(r"\(\s*[A-Z]{2}\s*\)", "", coda)
        coda = re.sub(r"\b\d{5}\b", "", coda)
        coda = re.sub(r"\b(UD|PN|GO|TS)\b", "", coda)
        cn = norm(coda)
        proprio = norm(x["comune"])
        if cn and cn != proprio and cn in nomi_comuni and proprio not in norm(ind):
            out.append(("indirizzo_altro_comune", f"{x['id']} «{x['nome']}» ({x['comune']}): «{ind}» → {nomi_comuni[cn]['nome']}"))
        for cap in re.findall(r"\b(3[234]\d{3})\b", ind):
            if not cap_ok(cap, x["prov"]):
                out.append(("cap_incoerente", f"{x['id']} «{x['nome']}» ({x['comune']}, {x['prov']}): CAP {cap} in «{ind}»"))

    # squadre
    for x in data:
        for q in x.get("squadre") or []:
            etichetta = f"{x['id']} «{x['nome']}» {q.get('categoria')} {q.get('genere', '')}"
            if not str(q.get("campionato") or "").strip():
                out.append(("squadra_senza_campionato", etichetta))
            # il Campionato Carnico si gioca nell'anno solare (stagione "2026"): ammesso
            # Campionato Carnico e baseball/softball si giocano nell'anno solare (stagione "2026"): ammessi
            carnico = ("carnico" in str(q.get("campionato", "")).lower() or x["sport"] == "baseball") and q.get("stagione") == "2026"
            if q.get("stagione") != STAGIONE and not carnico:
                out.append(("squadra_stagione", f"{etichetta}: stagione «{q.get('stagione')}»"))
            if not CATEGORIA_OK.match(str(q.get("categoria") or "")):
                out.append(("categoria_non_standard", f"{etichetta}: «{q.get('categoria')}»"))

    # comuni senza società
    presenti = {x["codice"] for x in data}
    for c in comuni:
        if c["codice"] not in presenti:
            out.append(("comune_senza_societa", f"{c['codice']} {c['nome']} ({c['prov']}, {c.get('pop', '?')} ab.)"))


# --- Squadre: sport, genere, livello -------------------------------------------------------------------
# Indizi forti di uno sport nel nome del campionato o nella fonte (id_fonte). Servono a scoprire squadre
# attribuite alla società sbagliata (es. una squadra di basket su una società di calcio).
SPORT_INDIZI = [
    ("pallamano", re.compile(r"federhandball|pallamano", re.I)),
    ("baseball", re.compile(r"\bfibs\.it\b|baseball|softball", re.I)),
    ("rugby", re.compile(r"federugby|rugby", re.I)),
    ("pallavolo", re.compile(r"\bfipav\b|federvolley|portalefipav|\b(prima|seconda|terza) divisione\b|\bct (udine|pordenone|trieste)", re.I)),
    ("basket", re.compile(r"\bfip\.it\b|divisione regionale|\bdr[123]\b|\b(maschile|femminile|under \d\d|u\d\d)\b[^;]*\b(gold|silver)\b|\blba\b", re.I)),
    ("calcio5", re.compile(r"calcio a 5|\bc5\b|futsal", re.I)),
    ("calcio", re.compile(r"\blnd\.it\b|\b(prima|seconda|terza) categoria\b|\ballievi\b|\bgiovanissimi\b|\bjuniores\b|\bpromozione\b|campionato carnico", re.I)),
]
SPORT_AFFINI = {"calcio": {"calcio5"}, "calcio5": {"calcio"}}
SENIOR = re.compile(r"^(Prima|Seconda|Terza|Quarta) squadra")
ORDINE_SQUADRA = {"Prima": 1, "Seconda": 2, "Terza": 3, "Quarta": 4}
# livello del campionato (più basso = più alto in classifica); None se non riconosciuto
LIVELLI = {
    "calcio": [(r"serie d\b", 0), (r"eccellenza", 1), (r"promozione", 2), (r"prima categoria", 3),
               (r"seconda categoria", 4), (r"terza categoria", 5)],
    "basket": [(r"serie a2|\ba2\b", 1), (r"serie a\b|\blba\b", 0), (r"serie b", 2), (r"serie c", 3),
               (r"divisione regionale 1|\bdr1\b", 4), (r"divisione regionale 2|\bdr2\b", 5), (r"divisione regionale 3|\bdr3\b", 6)],
    "pallavolo": [(r"serie a1|\ba1\b", 0), (r"serie a2|\ba2\b", 1), (r"serie a3|\ba3\b", 2), (r"serie b1", 3), (r"serie b2", 4),
                  (r"serie b\b", 3), (r"serie c\b", 5), (r"serie d\b", 6), (r"prima divisione", 7), (r"seconda divisione", 8),
                  (r"terza divisione", 9)],
}


def livello(sport, campionato):
    t = str(campionato or "").lower()
    for pat, lv in LIVELLI.get(sport, []):
        if re.search(pat, t):
            return lv
    return None


def campionati(q):
    """Una voce può elencare più campionati separati da ';' (es. Eccellenza; Regionale)."""
    return [c.strip(" )") for c in str(q.get("campionato") or "").split(";") if c.strip(" )")]


def controlla_squadre(data, ris, out):
    for x in data:
        ammessi = {x["sport"], *x.get("altri_sport", []), *SPORT_AFFINI.get(x["sport"], set())}
        senior = defaultdict(dict)
        for q in x.get("squadre") or []:
            et = f"{x['id']} «{x['nome']}» ({x['sport']}) {q.get('categoria')} {q.get('genere', '')}"
            testo = f"{q.get('campionato', '')} {q.get('id_fonte', '')}"
            for sp, rx in SPORT_INDIZI:
                if rx.search(testo):
                    if sp not in ammessi and not (sp == "calcio" and x["sport"] in ("calcio5",)):
                        out.append(("squadra_sport", f"{et}: «{q.get('campionato')}» sembra {sp}"))
                    break
            camp = str(q.get("campionato") or "").lower()
            g = q.get("genere")
            if g == "M" and re.search(r"\bfemminil", camp) or g == "F" and re.search(r"\bmaschil", camp):
                out.append(("squadra_genere", f"{et}: «{q.get('campionato')}»"))
            m = SENIOR.match(str(q.get("categoria") or ""))
            if m:
                cs = campionati(q)
                if m.group(1) == "Prima" and len(cs) > 1:
                    out.append(("prima_squadra_doppia", f"{et}: più campionati nella stessa voce «{q.get('campionato')}»"))
                senior[g][ORDINE_SQUADRA[m.group(1)]] = (q, livello(x["sport"], q.get("campionato")))
        for g, per_n in senior.items():
            if 1 in per_n and per_n[1][1] is not None:
                for n, (q, lv) in per_n.items():
                    if n > 1 and lv is not None and lv < per_n[1][1]:
                        out.append(("livello_incoerente", f"{x['id']} «{x['nome']}» {g}: {q['categoria']} in «{q['campionato']}» "
                                    f"è sopra la prima squadra «{per_n[1][0]['campionato']}»"))

    # dai risultati: la stessa società in più gironi senior dello stesso genere di quante squadre senior ha
    by_id = {x["id"]: x for x in data}
    gironi = defaultdict(set)
    for gr in ris:
        ids = {r.get("id") for r in gr.get("classifica") or [] if r.get("id")}
        nomi = defaultdict(set)
        for r in gr.get("classifica") or []:
            if r.get("id"):
                nomi[r["id"]].add(r.get("squadra"))
        for i, ns in nomi.items():
            if len(ns) > 1:
                out.append(("id_doppio_girone", f"{gr.get('gid')}: {i} per {', '.join(sorted(map(str, ns)))}"))
        for i in ids if SENIOR.match(str(gr.get("categoria") or "")) else ():
            gironi[(i, gr.get("genere"), gr.get("sport"))].add(gr.get("gid"))
        for i in ids:
            x = by_id.get(i)
            if x and gr.get("sport") not in {x["sport"], *x.get("altri_sport", []), *SPORT_AFFINI.get(x["sport"], set())}:
                out.append(("squadra_sport", f"{i} «{x['nome']}» ({x['sport']}) è in classifica in {gr.get('gid')} ({gr.get('sport')})"))
    for (i, g, _sp), gids in sorted(gironi.items()):
        x = by_id.get(i)
        if not x or len(gids) < 2:
            continue
        n = sum(1 for q in x.get("squadre") or [] if SENIOR.match(str(q.get("categoria") or "")) and q.get("genere") == g)
        # gironi che sono fasi diverse dello stesso campionato (es. regular season/play-off) contano una volta
        base = {re.sub(r"-(girone-)?[a-z0-9]$|-(playoff|playout|poule).*$", "", gid) for gid in gids}
        if len(gids) > max(n, 1) and len(base) > 1:
            out.append(("prima_squadra_doppia", f"{i} «{x['nome']}» genere {g}: in {len(gids)} gironi senior ({', '.join(sorted(gids))}) "
                        f"ma {n} squadre senior in data.json"))


def controlla_alias(ris, alias, out):
    for g in ris:
        usati = {r.get("id") for r in g.get("classifica") or []}
        usati |= {p.get(k) for p in g.get("partite") or [] for k in ("id_casa", "id_ospite")}
        for i in sorted(u for u in usati if u in alias):
            out.append(("id_alias_usato", f"{g.get('gid')}: {i} → {alias[i]}"))


def controlla_risultati(ris, data, oggi, out):
    ids = {x["id"] for x in data}
    for g in ris:
        gid = g.get("gid")
        if g.get("stagione") != STAGIONE:
            out.append(("girone_stagione", f"{gid}: stagione «{g.get('stagione')}»"))
        for r in g.get("classifica") or []:
            if not r.get("id"):
                out.append(("id_mancante", f"{gid}: «{r.get('squadra')}»"))
            elif r["id"] not in ids:
                out.append(("id_inesistente", f"{gid} classifica: «{r.get('squadra')}» → {r['id']}"))
        for p in g.get("partite") or []:
            for lato in ("casa", "ospite"):
                i = p.get("id_" + lato)
                if i and i not in ids:
                    out.append(("id_inesistente", f"{gid} partita {p.get('gara', '')} {lato}: «{p.get(lato)}» → {i}"))
        # partite giocate = somma giocate / 2
        giocate = sum(1 for p in g.get("partite") or [] if PUNTEGGIO.match(str(p.get("risultato") or "")))
        somma = sum(int(r.get("g") or 0) for r in g.get("classifica") or [])
        if somma and (somma % 2 == 1 or giocate != somma // 2):
            out.append(("giocate_incoerenti", f"{gid}: {giocate} partite con risultato, somma giocate in classifica {somma} (attese {somma / 2:g})"))
        # una squadra due volte nella stessa giornata
        per_g = defaultdict(list)
        for p in g.get("partite") or []:
            if p.get("giornata") in (None, ""):
                continue
            for lato in ("casa", "ospite"):
                per_g[p["giornata"]].append(norm(p.get(lato)))
        for gi, sq in sorted(per_g.items(), key=lambda t: str(t[0])):
            doppie = sorted({s for s in sq if s and sq.count(s) > 1})
            if doppie:
                out.append(("giornata_doppia", f"{gid} giornata {gi}: {', '.join(doppie)}"))
        # girone fermo
        try:
            agg = datetime.strptime(str(g.get("aggiornato"))[:10], "%Y-%m-%d").date()
            if (oggi - agg).days > 7:
                out.append(("girone_fermo", f"{gid}: aggiornato {agg.isoformat()} ({(oggi - agg).days} giorni fa)"))
        except ValueError:
            out.append(("girone_fermo", f"{gid}: data «aggiornato» non valida ({g.get('aggiornato')})"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "data.json"))
    ap.add_argument("--risultati", default=os.path.join(ROOT, "data", "risultati.json"))
    ap.add_argument("--comuni", default=os.path.join(ROOT, "data", "comuni.json"))
    ap.add_argument("--oggi", default=date.today().isoformat(), help="data di riferimento AAAA-MM-GG")
    ap.add_argument("--max", type=int, default=0, help="righe massime per tipo (0 = tutte)")
    ap.add_argument("--json", help="salva il report anche in questo file JSON")
    a = ap.parse_args()

    data = json.load(open(a.data, encoding="utf-8"))
    ris = json.load(open(a.risultati, encoding="utf-8"))
    com = json.load(open(a.comuni, encoding="utf-8"))
    comuni = com["comuni"] if isinstance(com, dict) else com
    oggi = datetime.strptime(a.oggi, "%Y-%m-%d").date()

    alias_p = os.path.join(os.path.dirname(a.data), "id_alias.json")
    alias = json.load(open(alias_p, encoding="utf-8")) if os.path.exists(alias_p) else {}

    out = []
    controlla_societa(data, comuni, out)
    controlla_squadre(data, ris, out)
    controlla_risultati(ris, data, oggi, out)
    controlla_alias(ris, alias, out)

    per_tipo = defaultdict(list)
    for tipo, msg in out:
        per_tipo[tipo].append(msg)
    tipi = sorted(GRAVITA, key=lambda t: (ORDINE[GRAVITA[t]], t))
    print(f"Report controllo dati — {oggi.isoformat()} — {len(data)} società, {len(ris)} gironi, {len(comuni)} comuni")
    print("\nRiepilogo:")
    for t in tipi:
        print(f"  [{GRAVITA[t]:5}] {t:26} {len(per_tipo.get(t, []))}")
    for t in tipi:
        righe = per_tipo.get(t, [])
        if not righe:
            continue
        print(f"\n== {t} ({GRAVITA[t]}): {len(righe)}")
        for r in righe[: a.max or None]:
            print("  -", r)
        if a.max and len(righe) > a.max:
            print(f"  … altre {len(righe) - a.max}")
    if a.json:
        json.dump({"oggi": oggi.isoformat(), "gravita": GRAVITA, "problemi": {t: per_tipo.get(t, []) for t in tipi}},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    alti = sum(len(per_tipo.get(t, [])) for t in tipi if GRAVITA[t] == "alta")
    sys.exit(1 if alti else 0)


if __name__ == "__main__":
    main()
