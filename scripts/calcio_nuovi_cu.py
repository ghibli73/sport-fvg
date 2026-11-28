"""Controllo leggero per il giro rapido: ci sono Comunicati Ufficiali LND FVG nuovi da leggere?

Una sola richiesta all'archivio media WordPress di friuliveneziagiulia.lnd.it (PDF degli ultimi GIORNI giorni, solo data e
indirizzo), confrontata con i comunicati già letti in config/calcio_stato.json. Esce con:
  0 = sì, c'è almeno un CU nuovo (non letto e pubblicato dopo --dopo): il giro rapido avvia "Aggiorna calcio";
  1 = no (o archivio non raggiungibile: nessun avvio, si riprova al giro successivo).
Solo libreria standard (nessun pip install nel giro rapido).
Uso: python scripts/calcio_nuovi_cu.py [--dopo AAAA-MM-GGTHH:MM:SSZ]
     --dopo  ora (UTC) di avvio dell'ultima esecuzione di "Aggiorna calcio": i CU pubblicati prima li ha già visti
             (se non li ha letti per un errore non si riavvia ogni 15 minuti: ci pensa l'esecuzione programmata)
"""
import datetime as dt, json, os, re, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATO = os.path.join(ROOT, "config", "calcio_stato.json")
BASE = "https://friuliveneziagiulia.lnd.it"
GIORNI = 4
UA = os.environ.get("SPORTFVG_UA", "SportFVG/1.0 (app non ufficiale di consultazione)")
# nome file di un Comunicato Ufficiale: "CU-50.pdf", "go_cu_25_2026_-_2027.pdf", "ts_cu_42_...", "CU_09.pdf",
# "Comunicato-Ufficiale-nr-21-...", e quelli della Delegazione di Pordenone "2026-C.U.-N.-40-Delegazione-PN-2026-2027.pdf"
# (stessa regola di scripts/calcio.py, che la importa da qui)
RX_FILE_CU = re.compile(r"(^|[/_-])c\.?u\.?[-_ ]?(?:n(?:r|°)?\.?[-_ ]?)?\d+|comunicato", re.I)


def e_cu(url):
    nome = url.rsplit("/", 1)[-1]
    return bool(RX_FILE_CU.search(nome)) and not re.search(r"allegat", url, re.I) and nome.lower().endswith(".pdf")


def main():
    dopo = sys.argv[sys.argv.index("--dopo") + 1] if "--dopo" in sys.argv else ""
    dopo = dopo.replace("Z", "")[:19]
    da = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=GIORNI)).strftime("%Y-%m-%dT00:00:00")
    q = urllib.parse.urlencode({"after": da, "mime_type": "application/pdf", "per_page": 50, "_fields": "date_gmt,source_url"})
    try:
        req = urllib.request.Request(f"{BASE}/wp-json/wp/v2/media?{q}", headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            js = json.load(r)
    except Exception as e:
        print(f"archivio LND non letto ({e}): nessun avvio"); return 1
    letti = set(json.load(open(STATO)).get("letti", [])) if os.path.exists(STATO) else set()
    nuovi = [x for x in js if e_cu(x.get("source_url", "")) and x["source_url"] not in letti
             and (not dopo or (x.get("date_gmt") or "") > dopo)]
    print(f"PDF negli ultimi {GIORNI} giorni: {len(js)}; CU nuovi da leggere: {len(nuovi)}"
          + (f" (pubblicati dopo {dopo} UTC)" if dopo else ""))
    for x in nuovi:
        print("  ", x.get("date_gmt"), x["source_url"].rsplit("/", 1)[-1])
    return 0 if nuovi else 1


if __name__ == "__main__":
    sys.exit(main())
