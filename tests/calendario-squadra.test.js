#!/usr/bin/env node
// Controllo del calendario della squadra (1.20.0): le chiavi calcolate in app (calChiave, blocco CALSQ-CHIAVI di
// index.html) devono coincidere con i file data/ics/squadra/<gid>--<chiave>.ics scritti da scripts/ics.py, così il
// pulsante "Abbonati al calendario" punta sempre a un file esistente. Esce con 1 se manca un file o ce n'è uno in più.
// Uso: node tests/calendario-squadra.test.js   (dopo python scripts/ics.py)
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const a = html.indexOf('/* CALSQ-CHIAVI-INIZIO */'), b = html.indexOf('/* CALSQ-CHIAVI-FINE */');
if (a < 0 || b < 0) { console.error('Blocco CALSQ-CHIAVI non trovato in index.html'); process.exit(2); }
const api = new Function(html.slice(a, b) + '\nreturn {calSlug, calNomi, calChiave};')();
const G = JSON.parse(fs.readFileSync(path.join(root, 'data/risultati.json'), 'utf8'));
const dir = path.join(root, 'data/ics/squadra');
const files = new Set(fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.ics')) : []);
const attesi = new Set(); let mancanti = [];
const ok = d => /^\d{4}-\d\d-\d\d$/.test(d || '');
for (const g of G) {
  const N = api.calNomi(g);
  for (const [n, id] of N.m) {
    const k = api.calChiave(g, id, n);
    const me = k.startsWith('n-') ? x => x.casa === n || x.ospite === n : x => x.id_casa === k || x.id_ospite === k;
    if (!g.partite.some(x => ok(x.data) && me(x))) continue;
    const f = `${g.gid}--${k}.ics`; attesi.add(f);
    if (!files.has(f)) mancanti.push(f);
  }
}
const extra = [...files].filter(f => !attesi.has(f));
console.log(`Squadre con partite: ${attesi.size} · file: ${files.size} · mancanti: ${mancanti.length} · in più: ${extra.length}`);
mancanti.slice(0, 10).forEach(f => console.log('  manca', f)); extra.slice(0, 10).forEach(f => console.log('  in più', f));
process.exit(mancanti.length || extra.length ? 1 : 0);
