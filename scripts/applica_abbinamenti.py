"""Applica subito a data/risultati.json gli abbinamenti salvati:
  1. id delle società da config/abbinamenti_prove.json (solo dove l'id manca; un id esistente non viene mai cambiato);
  2. comune (ISTAT) delle squadre ancora senza id da config/squadre_comune.json.
Gli stessi abbinamenti sono anche negli alias degli script (config/pallavolo.json, config/basket/*.json, config/calcio_alias.json),
così restano ai prossimi aggiornamenti automatici. Uso: python scripts/applica_abbinamenti.py [--prova]
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from abbinamenti import ROOT, applica_id, applica_comuni

RIS = os.path.join(ROOT, "data", "risultati.json")


def main():
    data = json.load(open(RIS, encoding="utf-8"))
    n_id = applica_id(data)
    n_com = applica_comuni(data)
    print(f"id aggiunti (righe di classifica + lati di partita): {n_id}; comuni scritti: {n_com}")
    if "--prova" in sys.argv:
        print("prova: nessun file scritto"); return
    json.dump(data, open(RIS, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
