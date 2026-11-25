"""Sonda: verifica da GitHub Actions quali fonti ufficiali sono leggibili senza AI e stampa un estratto nel log.
Non modifica nessun dato."""
import io, re, sys, json, time
import requests
S = requests.Session(); S.headers["User-Agent"] = "SportFVG/1.0 (app non ufficiale; sonda fonti)"

def titolo(t): print("\n" + "=" * 8, t, "=" * 8, flush=True)

def pdf_testo(url, righe=80, cerca=None):
    import pdfplumber
    r = S.get(url, timeout=60); r.raise_for_status()
    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        print("pagine:", len(pdf.pages))
        testo = "\n".join((p.extract_text() or "") for p in pdf.pages[:12])
    lines = testo.splitlines()
    if cerca:
        idx = [i for i, l in enumerate(lines) if re.search(cerca, l, re.I)]
        print("righe con", cerca, ":", len(idx))
        for i in idx[:3]:
            print("\n".join("   | " + l for l in lines[max(0, i - 2):i + 25]))
            print("   ...")
    else:
        print("\n".join("   | " + l for l in lines[:righe]))

def media(base, q, n=5):
    u = f"{base}/wp-json/wp/v2/media?search={q}&per_page={n}&_fields=date,source_url"
    r = S.get(u, timeout=30); r.raise_for_status()
    return r.json()

def pagina(url, n=1500, cerca=None):
    r = S.get(url, timeout=30)
    print("HTTP", r.status_code, "byte", len(r.content), "tipo", r.headers.get("content-type"))
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", r.text, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t); t = re.sub(r"\s+", " ", t)
    if cerca:
        m = re.search(cerca, t, re.I); print("trovato" if m else "NON trovato", cerca)
        if m: print("   ", t[max(0, m.start() - 200):m.start() + n])
    else:
        print("   ", t[:n])

prove = sys.argv[1:] or ["basket", "calcio", "minori"]
if "basket" in prove:
    titolo("FIP FVG - ultime omologazioni")
    try:
        L = media("https://friuliveneziagiulia.fip.it", "Omologazione", 6)
        for x in L: print(x["date"], x["source_url"])
        for x in L[:2]:
            titolo("PDF " + x["source_url"].rsplit("/", 1)[-1]); pdf_testo(x["source_url"], 70)
    except Exception as e: print("ERRORE", e)
if "calcio" in prove:
    titolo("LND FVG - ultimi comunicati")
    try:
        L = media("https://friuliveneziagiulia.lnd.it", "CU", 8)
        for x in L: print(x["date"], x["source_url"])
        pdfs = [x["source_url"] for x in L if x["source_url"].lower().endswith(".pdf")]
        for u in pdfs[:2]:
            titolo("PDF " + u.rsplit("/", 1)[-1]); pdf_testo(u, cerca=r"CLASSIFICA|RISULTATI")
    except Exception as e: print("ERRORE", e)
if "minori" in prove:
    for nome, url, cerca in [
        ("FITeT portale", "https://portale.fitet.org/risultati/campionati/", r"Friuli|Serie"),
        ("Federnuoto pallanuoto", "https://www.federnuoto.it/home/pallanuoto/campionati.html", r"Serie A1|Classifica"),
        ("FIR rugby", "https://www.federugby.it/", r"Serie|Classifica"),
        ("FIGH pallamano", "https://www.figh.it/", r"Serie|Classifica"),
        ("FISR hockey", "https://www.fisr.it/hockey-pista.html", r"Serie|Classifica"),
        ("Lega Volley", "https://www.legavolley.it/classifica/", r"Classifica|Prata"),
        ("Lega Volley Femminile", "https://www.legavolleyfemminile.it/classifica/", r"Talmassons|Classifica"),
        ("Lega Basket A", "https://www.legabasket.it/lba/standings", r"Trieste|Classifica"),
        ("LNP basket", "https://www.legapallacanestro.com/serie-a2/classifica", r"Classifica|Cividale"),
        ("FIBS baseball", "https://www.fibs.it/", r"Serie|Classifica"),
        ("FIB bocce", "https://www.federbocce.it/", r"Serie|Campionat"),
        ("FIPAV nazionale serie B", "https://www.federvolley.it/campionati-serie-b", r"Girone|Classifica"),
    ]:
        titolo(nome + " " + url)
        try: pagina(url, 600, cerca)
        except Exception as e: print("ERRORE", e)
        time.sleep(1)
