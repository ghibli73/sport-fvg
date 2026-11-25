# Pipeline delle società (data/data.json)

Copia di lavoro dell'ambiente in cui vengono costruiti gli elenchi delle società.
- `raw/<ISTAT>.json`: dati di partenza per comune; `patch/<cartella>/<ISTAT>.json`: integrazioni e correzioni (regole in PATCH.md, schema in SCHEMA.md; azioni strutturali in patch/correzioni/azioni-*.json).
- `python3 build.py` (da questa cartella) produce `app/data.json`: copiarlo in `../data/data.json`. Dopo un'unione di società lanciare `python3 ../scripts/rimappa_id.py`.
- `agenti/`: manuali degli agenti (copia di quelli nel progetto claude.ai "Sport FvG").
- `social/`: lotti e istruzioni dell'agente social.
