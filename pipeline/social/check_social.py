"""Controlli automatici sui profili social in app/data.json. Stampa un report e salva social/report.json."""
import json, re, os, unicodedata
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, "app", "data.json")))

STOP = {"asd", "ssd", "a", "s", "d", "r", "l", "arl", "srl", "us", "gs", "ac", "pol", "polisportiva", "associazione",
        "sportiva", "dilettantistica", "societa", "di", "del", "della", "dei", "e", "the", "club", "team", "sport",
        "volley", "pallavolo", "calcio", "basket", "pallacanestro", "asdr", "apd", "sd", "cs", "fc", "ssdrl", "1"}

def toks(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return {t for t in re.split(r"[^a-z0-9]+", s) if len(t) > 2 and t not in STOP}

def handle(url):
    m = re.match(r"https?://(?:www\.|m\.|it-it\.)?(facebook|instagram)\.com/(.+?)/?$", url)
    return (m.group(1), m.group(2)) if m else (None, None)

issues = defaultdict(list)
by_url = defaultdict(list)
n = {"facebook": 0, "instagram": 0, "sito": 0, "clubs": 0}
for c in d:
    so = c.get("social") or {}
    if so: n["clubs"] += 1
    for k, url in so.items():
        n[k] += 1
        by_url[url.lower().rstrip("/")].append(c)
        if k in ("facebook", "instagram"):
            site, h = handle(url)
            if site != k:
                issues[c["id"]].append(f"{k}: URL non valido ({url})")
                continue
            if k == "facebook" and re.match(r"(groups|events|hashtag|watch|share)/", h):
                issues[c["id"]].append(f"facebook: non è una pagina ufficiale ({url})")
            if "?" in h and not h.startswith("profile.php?id="):
                issues[c["id"]].append(f"{k}: URL con parametri ({url})")
            ht = toks(h.replace(".", " ").replace("_", " "))
            nt = toks(c["nome"]) | toks(c["comune"])
            hs = re.sub(r"[^a-z0-9]", "", h.lower())
            if not (ht & nt) and not any(t in hs for t in nt if len(t) > 3) and not h.startswith("profile.php") and not re.match(r"p/|pages/|people/|\d+$", h):
                issues[c["id"]].append(f"{k}: handle '{h}' senza parole del nome o del comune")
        elif k == "sito" and not re.match(r"https?://[^/\s]+\.[a-z]{2,}", url):
            issues[c["id"]].append(f"sito: URL non valido ({url})")

shared = []
for url, cs in by_url.items():
    names = {x["nome"] for x in cs}
    if len(cs) > 1:
        shared.append({"url": url, "societa": [f'{x["nome"]} ({x["comune"]}, {x["sport"]})' for x in cs]})

rep = {"conteggi": n, "dubbi": {k: v for k, v in issues.items()}, "condivisi": shared}
json.dump(rep, open(os.path.join(BASE, "social", "report.json"), "w"), ensure_ascii=False, indent=1)
print("società con almeno un link:", n["clubs"], "| FB", n["facebook"], "| IG", n["instagram"], "| sito", n["sito"])
print("società con dubbi:", len(issues), "| link condivisi tra più società:", len(shared))
idx = {c["id"]: c for c in d}
for k, v in list(issues.items())[:60]:
    print(" -", idx[k]["nome"], f'({idx[k]["comune"]})', "→", "; ".join(v))
for s in shared[:30]:
    print(" = ", s["url"], "→", " | ".join(s["societa"]))
