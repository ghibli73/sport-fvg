// Service worker: app shell in cache, dati sempre dalla rete se disponibile (così i risultati sono freschi), cache come riserva offline.
const SHELL = 'sportfvg-shell-v26';
const DATA = 'sportfvg-data';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png'].map(u => new Request(u, {cache: 'reload'})))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== DATA).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // risorse di altri siti (Leaflet da unpkg, tessere OpenStreetMap, conteggio visite): mai in cache, le gestisce il browser
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  // widget.js (per i siti esterni): mai in cache, deve aggiornarsi subito; data/widget/ resta network-first come tutto data/.
  // Sui siti terzi il service worker non è attivo; qui vale per widget.html e per l'app: lo gestisce il browser.
  if (url.pathname.endsWith('/widget.js')) return;
  if (url.pathname.includes('/data/')) {
    // chiave senza parametri: data/stato.json?t=... e data/risultati.json?v=<impronta> (1.13.1) tengono una sola copia
    const key = url.origin + url.pathname;
    e.respondWith(fetch(e.request).then(r => { if (r.ok) { const c = r.clone(); caches.open(DATA).then(x => x.put(key, c)); } return r; })
      .catch(() => caches.match(key)));
  } else {
    e.respondWith(caches.match(e.request).then(m => m || fetch(e.request)));
  }
});
