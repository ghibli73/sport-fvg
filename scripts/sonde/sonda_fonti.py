"""Sonda: verifica da GitHub Actions quali fonti ufficiali sono leggibili senza AI e stampa un estratto nel log.
Non modifica nessun dato."""
import io, re, sys, json, time
import html as html_mod
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
# "media=<sito>|<parole>[|<dopo AAAA-MM-GG>]": elenco completo dei file dell'archivio WordPress che contengono le parole
# (es. media=https://friuliveneziagiulia.fip.it|Spostamenti|2026-09-01)
for x in [x[6:] for x in prove if x.startswith("media=")]:
    base, q, *dopo = x.split("|")
    titolo(f"MEDIA {base} '{q}'")
    try:
        pagina_n, tot = 1, 0
        while pagina_n < 6:
            par = {"search": q.replace("+", " "), "per_page": 100, "page": pagina_n, "_fields": "date,source_url,title"}
            if not q: par.pop("search")
            if dopo and dopo[0]: par["after"] = dopo[0] + "T00:00:00"
            if len(dopo) > 1: par["mime_type"] = dopo[1]
            r = S.get(f"{base}/wp-json/wp/v2/media", params=par, timeout=30)
            if r.status_code == 400: break
            r.raise_for_status(); js = r.json()
            for m in js: print(m["date"], m["source_url"])
            tot += len(js)
            if len(js) < 100: break
            pagina_n += 1; time.sleep(1)
        print("totale:", tot)
    except Exception as e: print("ERRORE", e)
    time.sleep(1)
# "righe=<url PDF LND>": stampa le righe come le legge scripts/calcio.py (colonne separate) dalla sezione RISULTATI
# e, per ogni gara riconosciuta, categoria/girone/giornata assegnati dal parser: serve a controllare il parser sul CU reale
for u in [x[6:] for x in prove if x.startswith("righe=")]:
    titolo("RIGHE calcio.py " + u)
    try:
        sys.path.insert(0, "scripts"); import calcio
        righe = calcio.pdf_righe(u)
        dentro = False
        for l in righe:
            if l.upper().startswith("RISULTATI GARE"): dentro = True
            if dentro: print("   |", l)
        com, gare = calcio.leggi_cu(u)
        print("comitato:", com)
        for g in gare: print("   >", calcio.classifica_cat(g[0]), "| gir", g[1], g[2], g[3], "|", g[4], "|", g[5], "-", g[6], g[7], g[8])
    except Exception as e: print("ERRORE", e)
# "html=<url>|<regex>": i pezzi dell'HTML grezzo che corrispondono (es. i valori delle <option> di un filtro)
for x in [x[5:] for x in prove if x.startswith("html=")]:
    u, rx = x.split("|", 1)
    rx, _, lung = rx.partition("@@")  # "html=<url>|<regex>@@<caratteri>": estratti più lunghi (default 400)
    lung = int(lung or 400)
    titolo("HTML " + u + " /" + rx + "/")
    try:
        t = S.get(u, timeout=60).text
        ms = list(re.finditer(rx, t, re.I | re.S))
        print("byte:", len(t), "corrispondenze:", len(ms))
        for m in ms[:40 if lung <= 400 else 3]: print("   |", t[m.start():m.start() + lung].replace("\n", " ")[:lung])
    except Exception as e: print("ERRORE", e)
    time.sleep(1.5)
# "cerca=<url PDF o ZIP>|<regex>": nel PDF (o nei PDF dello ZIP il cui nome contiene la regex del file, dopo "@")
# stampa le righe attorno a ogni corrispondenza, es. cerca=https://.../CU-50.pdf|VARIAZIONI GARE
for x in [x[6:] for x in prove if x.startswith("cerca=")]:
    u, rx = x.split("|", 1)
    rx, _, rxf = rx.partition("@")
    titolo("CERCA " + u + " /" + rx + "/" + (" file /" + rxf + "/" if rxf else ""))
    try:
        import pdfplumber, zipfile
        dati = S.get(u, timeout=90).content
        files = [(u, dati)]
        if u.lower().endswith(".zip"):
            z = zipfile.ZipFile(io.BytesIO(dati))
            for n in z.namelist(): print("  file:", n, z.getinfo(n).file_size)
            files = [(n, z.read(n)) for n in z.namelist() if n.lower().endswith(".pdf") and (not rxf or re.search(rxf, n, re.I))]
        for n, b in files[:6]:
            with pdfplumber.open(io.BytesIO(b)) as pdf:
                lines = [l for pg in pdf.pages for l in (pg.extract_text() or "").splitlines()]
            idx = [i for i, l in enumerate(lines) if re.search(rx, l, re.I)]
            print("---", n, "righe", len(lines), "corrispondenze", len(idx))
            fatto = -1
            for i in idx[:8]:
                if i <= fatto: continue
                print("\n".join("   | " + l for l in lines[max(0, i - 2):i + 50])); print("   ..."); fatto = i + 50
    except Exception as e: print("ERRORE", e)
    time.sleep(1)
# "pagina=<url>|<regex>": testo della pagina (senza tag) a partire dalla prima corrispondenza, 5000 caratteri
for x in [x[7:] for x in prove if x.startswith("pagina=")]:
    u, rx = x.split("|", 1)
    titolo("PAGINA " + u)
    try: pagina(u, 5000, rx)
    except Exception as e: print("ERRORE", e)
    time.sleep(1.5)
# "testo=<url PDF>": testo completo (tutte le pagine, al massimo 600 righe), per confrontare a mano dati e fonte
for u in [x[6:] for x in prove if x.startswith("testo=")]:
    titolo("TESTO " + u)
    try:
        import pdfplumber
        r = S.get(u, timeout=60); r.raise_for_status()
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            lines = [l for p in pdf.pages for l in (p.extract_text() or "").splitlines()]
        print("\n".join("   | " + l for l in lines[:600]))
    except Exception as e: print("ERRORE", e)
# "opzioni=<url>": valori e testi dei menu <select> (es. filtro Società FIPAV: SId -> nome società)
# "loghi=<url>": righe di classifica FIPAV con l'ID società del logo (mngArea/Societa/img/<ID>/...)
for u in [x[8:] for x in prove if x.startswith("opzioni=")]:
    titolo("OPZIONI " + u)
    try:
        h = S.get(u, timeout=30).text
        for nome, corpo in re.findall(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', h, re.S | re.I):
            print("  menu", nome)
            for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', corpo, re.S | re.I):
                print("   |", v, "|", re.sub(r"\s+", " ", t).strip())
    except Exception as e: print("ERRORE", e)
for u in [x[6:] for x in prove if x.startswith("loghi=")]:
    titolo("LOGHI " + u)
    try:
        h = S.get(u, timeout=30).text
        for riga in re.findall(r"<tr.*?</tr>", h, re.S | re.I):
            m = re.search(r"Societa/img/(\d+)/", riga)
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", riga)).strip()
            if m or "no-image" in riga: print("   |", m.group(1) if m else "-", "|", t[:90])
    except Exception as e: print("ERRORE", e)
# "grezzo=<url>": HTML grezzo (prime 6000 battute dopo <body>, poi i link), "~" nell'URL sta per "&" (la shell del workflow non lo vuole nudo)
# "cercah=<regex>@@<url>": righe HTML grezze che contengono la regex (al massimo 60), sempre con "~" per "&"; nella regex ",," sta per "|" e "LT" per "<"
for u in [x[7:] for x in prove if x.startswith("grezzo=")]:
    u = u.replace("~", "&"); titolo("GREZZO " + u)
    try:
        r = S.get(u, timeout=40); print("HTTP", r.status_code, "byte", len(r.content), "tipo", r.headers.get("content-type"), "url finale", r.url)
        h = r.text; i = max(0, h.lower().find("<body"))
        print(h[i:i + 6000])
        links = re.findall(r'href="([^"#]+)"', h)
        print("LINK (", len(links), "):"); print("\n".join("   " + l for l in links[:150]))
    except Exception as e: print("ERRORE", e)
for x in [x[7:] for x in prove if x.startswith("cercah=")]:
    rx, u = x.split("@@", 1); u = u.replace("~", "&"); rx = rx.replace(",,", "|").replace("LT", "<"); titolo("CERCA " + rx + " IN " + u)
    try:
        h = S.get(u, timeout=40).text
        L = [l.strip() for l in re.split(r"\n|(?=<tr)|(?=<li)|(?=<div class)", h) if re.search(rx, l, re.I)]
        print("righe:", len(L)); print("\n".join("   | " + l[:400] for l in L[:60]))
    except Exception as e: print("ERRORE", e)
# "da=<regex>@@<url>": 5000 battute di HTML grezzo a partire dal primo punto che corrisponde alla regex (stessi segnaposto di cerca=)
for x in [x[3:] for x in prove if x.startswith("da=")]:
    rx, u = x.split("@@", 1); u = u.replace("~", "&"); rx = rx.replace(",,", "|").replace("LT", "<"); titolo("DA " + rx + " IN " + u)
    try:
        h = S.get(u, timeout=40).text; m = re.search(rx, h, re.I)
        print("NON trovato" if not m else h[m.start():m.start() + 5000])
    except Exception as e: print("ERRORE", e)
# "agenda=<opzioni>": esegue scripts/agenda.py in prova (le opzioni separate da virgola, es. agenda=--debug,--solo,fisi)
for x in [x[7:] for x in prove if x.startswith("agenda=")]:
    import subprocess
    titolo("AGENDA " + x)
    ops = [o for o in x.split(",") if o] or ["--prova"]
    if "--debug" not in ops and "--prova" not in ops: ops.append("--prova")
    subprocess.run([sys.executable, "scripts/agenda.py", *ops])
# "agendajson": rigenera data/agenda.json nel runner (non salva nel repository) e lo stampa tra due marcatori
if "agendajson" in prove:
    import subprocess
    titolo("AGENDA JSON")
    subprocess.run([sys.executable, "scripts/agenda.py"])
    print("@@INIZIO_AGENDA@@"); print(open("data/agenda.json", encoding="utf-8").read()); print("@@FINE_AGENDA@@")
# "date=<url>": testo della pagina attorno alle date (2026/2027 o mesi) e link a pagine evento; "~" per "&"
MESI_RX = r"(\d{1,2}(?:\s*[-–]\s*\d{1,2})?\s+(?:gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)[a-z]*\.?\s+20(?:26|27)|\d{1,2}[./]\d{1,2}[./]20(?:26|27)|20(?:26|27)-\d\d-\d\d)"
for u in [x[5:] for x in prove if x.startswith("date=")]:
    u = u.replace("~", "&"); titolo("DATE " + u)
    try:
        h = S.get(u, timeout=40).text
        t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
        t = html_mod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", t)))
        t = re.sub(r"(\s*\|\s*)+", " | ", t)
        ms = list(re.finditer(MESI_RX, t, re.I))
        print("date trovate:", len(ms))
        last = -1
        for m in ms[:40]:
            if m.start() < last: continue
            print("   >", t[max(0, m.start() - 220):m.end() + 260]); last = m.end() + 260
        ev = sorted(set(re.findall(r'href="([^"]*/even[a-z]*/[^"#?]+)"', h)))
        print("link evento:", len(ev)); print("\n".join("   " + l for l in ev[:80]))
    except Exception as e: print("ERRORE", e)
# "testo2=<regex>@@<url>": 7000 battute di testo (senza tag) a partire dalla regex (",," = "|"), "~" per "&"
for x in [x[7:] for x in prove if x.startswith("testo2=")]:
    rx, u = x.split("@@", 1); u = u.replace("~", "&"); rx = rx.replace(",,", "|"); titolo("TESTO2 " + rx + " IN " + u)
    try:
        h = S.get(u, timeout=40).text
        t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
        t = html_mod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", t))); t = re.sub(r"(\s*\|\s*)+", " | ", t)
        m = re.search(rx, t, re.I); print(t[m.start():m.start() + 7000] if m else "NON trovato")
        ev = sorted(set(re.findall(r'href="([^"]*/even[a-z]*/[^"#?]+)"', h))); print("link evento:", " ".join(ev[:120]))
    except Exception as e: print("ERRORE", e)
# "testa=<url>": intestazioni HTTP (cache-control, age, last-modified, etag...) e due richieste a distanza, per
# misurare la cache di GitHub Pages o capire se una pagina dichiara quando è cambiata
for u in [x[6:] for x in prove if x.startswith("testa=")]:
    titolo("TESTA " + u)
    try:
        for i in range(2):
            r = S.get(u, timeout=30, headers={"Cache-Control": "no-cache"} if i else {})
            print(f"  richiesta {i + 1}: HTTP", r.status_code, "byte", len(r.content))
            for k, v in r.headers.items():
                if k.lower() in ("cache-control", "age", "last-modified", "etag", "expires", "date", "x-cache", "x-cache-hits",
                                 "x-served-by", "via", "access-control-allow-origin", "content-type", "vary", "x-github-request-id",
                                 "x-fastly-request-id", "server"):
                    print("   ", k, ":", v)
            time.sleep(2)
    except Exception as e: print("ERRORE", e)
# "giri=<url>|<n>|<secondi>": legge la stessa pagina n volte a distanza di <secondi> (minimo 60) e stampa per ogni
# lettura l'ora, l'etag/last-modified e un'impronta del contenuto: dice dopo quanto un cambiamento si vede
for x in [x[5:] for x in prove if x.startswith("giri=")]:
    u, n, sec = (x.split("|") + ["3", "60"])[:3]
    titolo("GIRI " + u)
    import hashlib
    for i in range(min(int(n), 15)):
        try:
            r = S.get(u, timeout=30)
            print(time.strftime("%H:%M:%S"), r.status_code, r.headers.get("age"), r.headers.get("etag"),
                  r.headers.get("last-modified"), hashlib.md5(r.content).hexdigest()[:10], flush=True)
        except Exception as e: print("ERRORE", e)
        if i + 1 < int(n): time.sleep(max(60, int(sec)))
# "inertia=<url>[|<regex>]": pagine Inertia (es. gare.lnd.it, Quadro gare LND): stampa componente, chiavi delle props
# e il JSON compatto (o solo i pezzi attorno alla regex), più gli header X-Inertia-Version per le richieste successive
for x in [x[8:] for x in prove if x.startswith("inertia=")]:
    u, _, rx = x.partition("|")
    titolo("INERTIA " + u)
    try:
        r = S.get(u, timeout=30)
        h = r.text
        m = re.search(r'data-page="app" type="application/json">(.*?)</script>', h, re.S) or re.search(r'data-page="([^"]+)"', h)
        if not m: print("HTTP", r.status_code, "nessun data-page"); continue
        import html as _h
        js = json.loads(_h.unescape(m.group(1)))
        print("HTTP", r.status_code, "componente", js.get("component"), "url", js.get("url"), "versione", js.get("version"))
        props = js.get("props", {})
        print("props:", list(props))
        dump = json.dumps(props, ensure_ascii=False)
        if rx:
            for mm in list(re.finditer(rx, dump, re.I))[:12]:
                print("   |", dump[max(0, mm.start() - 300):mm.start() + 900])
        else:
            print(dump[:9000])
    except Exception as e: print("ERRORE", e)
    time.sleep(1.5)
for u in [x for x in prove if x.startswith("http")]:
    titolo(u)
    try:
        if u.lower().endswith(".zip"):
            import zipfile
            z = zipfile.ZipFile(io.BytesIO(S.get(u, timeout=60).content))
            for n in z.namelist(): print("  file:", n, z.getinfo(n).file_size)
            for n in [n for n in z.namelist() if n.lower().endswith(".pdf") and re.search(r"calendar", n, re.I)][:2]:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(z.read(n))) as pdf:
                    t = "\n".join((pg.extract_text() or "") for pg in pdf.pages[:2])
                print("---", n); print("\n".join("   | " + l for l in t.splitlines()[:60]))
        elif u.lower().endswith(".pdf"):
            pdf_testo(u, 90)
        else:
            pagina(u, 3000)
    except Exception as e: print("ERRORE", e)
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
