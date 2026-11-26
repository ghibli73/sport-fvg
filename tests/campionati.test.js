#!/usr/bin/env node
// Controllo della barra dei campionati (1.16.0): ogni girone di data/risultati.json deve finire in un campionato.
// Legge il blocco CAMP-INIZIO … CAMP-FINE di index.html (solo funzioni pure) e stampa il rapporto per sport:
// campionati in ordine di barra, numero di gironi, generi e zone. Esce con 1 se qualche girone finisce in "Altro".
// Uso: node tests/campionati.test.js [data/risultati.json]
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const a = html.indexOf('/* CAMP-INIZIO'), b = html.indexOf('/* CAMP-FINE */');
if (a < 0 || b < 0) { console.error('Blocco CAMP-INIZIO/CAMP-FINE non trovato in index.html'); process.exit(2); }
const api = new Function(html.slice(a, b) + '\nreturn {CAMP, campDi, campZone, campLista, ZONE, GENERI};')();
const G = JSON.parse(fs.readFileSync(process.argv[2] || path.join(root, 'data/risultati.json'), 'utf8'));
const ZN = Object.fromEntries(api.ZONE);
let altri = [], tot = 0;
for (const sp of [...new Set(G.map(g => g.sport))].sort()) {
  const L = G.filter(g => g.sport === sp), cs = api.campLista(L);
  console.log(`\n${sp} — ${L.length} gironi, ${cs.length} campionati${api.CAMP[sp] ? '' : ' (nessuna tabella: solo regole generiche)'}${cs.length < 2 ? ' → nessuna barra' : ''}`);
  for (const { e, gs } of cs) {
    tot += gs.length;
    const gen = [...new Set(gs.map(g => g.genere))].join('/');
    const zone = [...new Set(gs.flatMap(api.campZone))].map(z => ZN[z]).join(', ');
    console.log(`  ${String(e.l).padEnd(16)} ${String(gs.length).padStart(3)}  ${gen.padEnd(8)} ${zone}${api.CAMP[sp] && !api.CAMP[sp].some(x => x.k === e.k) ? '  [voce generica]' : ''}`);
    if (e.k === 'altro') altri.push(...gs);
  }
}
console.log(`\nTotale: ${tot}/${G.length} gironi assegnati; in "Altro": ${altri.length}`);
altri.forEach(g => console.log(`  ALTRO ${g.gid} — ${g.girone} (${g.categoria})`));
if (tot !== G.length) { console.error('Conteggio non coerente'); process.exit(1); }
process.exit(altri.length ? 1 : 0);
