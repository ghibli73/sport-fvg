// Service worker: app shell in cache, dati sempre dalla rete se disponibile (così i risultati sono freschi), cache come riserva offline.
const SHELL = 'sportfvg-shell-v4';
const DATA = 'sportfvg-data';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png'])).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== SHELL && k !== DATA).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.includes('/data/')) {
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(DATA).then(x => x.put(e.request, c)); return r; })
      .catch(() => caches.match(e.request)));
  } else {
    e.respondWith(caches.match(e.request).then(m => m || fetch(e.request)));
  }
});
