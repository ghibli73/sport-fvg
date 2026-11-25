/* Zuìn – Sport in FVG · widget dei risultati per i siti di società, comitati e giornali.
   Uso: <script src="https://ghibli73.github.io/sport-fvg/widget.js" data-societa="<id>" async></script>
   oppure data-girone="<gid>"; opzioni data-tema="chiaro|scuro|auto", data-squadre="<n massimo>".
   JavaScript puro, Shadow DOM, nessun cookie, nessun tracciamento. Manuale: pipeline/agenti/widget.md */
(function () {
  'use strict';
  var W = window.ZuinWidget;
  if (W && W.scan) { W.scan(); return; }
  var me = document.currentScript;
  var BASE = 'https://ghibli73.github.io/sport-fvg/';
  try { if (me && me.src) BASE = new URL('.', me.src).href; } catch (e) {}
  var CACHE = {}, SHEET = null;
  var GG = ['dom', 'lun', 'mar', 'mer', 'gio', 'ven', 'sab'];
  var SP = { calcio: 'Calcio', calcio5: 'Calcio a 5', pallavolo: 'Pallavolo', basket: 'Basket', rugby: 'Rugby', pallamano: 'Pallamano', hockey: 'Hockey', baseball: 'Baseball', bocce: 'Bocce', pallanuoto: 'Pallanuoto' };
  var ESL = { v: 'Vinta', p: 'Persa', n: 'Pari' };

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function dt(s, wd) {
    var p = String(s || '').split('-'); if (p.length !== 3) return esc(s || '');
    var t = +p[2] + '/' + (+p[1]);
    if (wd) { var d = new Date(+p[0], +p[1] - 1, +p[2]); if (!isNaN(d)) t = GG[d.getDay()] + ' ' + t; }
    return t;
  }
  function dtl(s) { var p = String(s || '').split('-'); return p.length === 3 ? +p[2] + '/' + (+p[1]) + '/' + p[0] : esc(s || ''); }
  function fid(s) { return String(s).replace(/[^A-Za-z0-9._-]/g, '_'); }

  function load(path) {
    var u = BASE + 'data/widget/' + path;
    if (!CACHE[u]) {
      var ctl = typeof AbortController === 'function' ? new AbortController() : null;
      var to = setTimeout(function () { if (ctl) ctl.abort(); }, 12000);
      CACHE[u] = fetch(u, { cache: 'no-cache', credentials: 'omit', signal: ctl ? ctl.signal : undefined })
        .then(function (r) { clearTimeout(to); if (!r.ok) throw new Error(r.status); return r.json(); })
        .catch(function (e) { clearTimeout(to); delete CACHE[u]; throw e; });
    }
    return CACHE[u];
  }

  var CSS = ':host{all:initial!important;display:block!important;width:100%!important;max-width:600px!important;margin:0 0 16px!important;box-sizing:border-box!important}' +
    '*{box-sizing:border-box;min-width:0}' +
    '.w{--bg:#fff;--ink:#0f1c33;--mute:#5a6780;--line:#dde3ee;--soft:#eef2f8;--acc:#123a6b;container-type:inline-size;font:15px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:14px;overflow:hidden;text-align:left;letter-spacing:normal;word-spacing:normal;text-transform:none;font-style:normal;font-weight:400;-webkit-text-size-adjust:100%}' +
    '.w.scuro{--bg:#121e34;--ink:#e8eef8;--mute:#a9b8cf;--line:#2a3b5c;--soft:#1a2a47;--acc:#f2b705}' +
    '@media(prefers-color-scheme:dark){.w.auto{--bg:#121e34;--ink:#e8eef8;--mute:#a9b8cf;--line:#2a3b5c;--soft:#1a2a47;--acc:#f2b705}}' +
    'a{color:var(--acc);text-decoration:underline;text-underline-offset:2px}a:focus-visible{outline:3px solid #f2b705;outline-offset:2px;border-radius:4px}' +
    '.hd{display:flex;align-items:center;gap:10px;background:#123a6b;color:#fff;padding:10px 14px}' +
    '.hd img{width:28px;height:28px;border-radius:8px;flex:none;display:block}' +
    '.hd b{display:block;font-size:17px;line-height:1.2;font-weight:800;overflow-wrap:anywhere}.hd small{display:block;font-size:13px;color:#d3deee}' +
    '.sq{padding:12px 14px;border-top:1px solid var(--line)}.sq:first-of-type{border-top:0}' +
    '.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}' +
    '.cat{display:block;font-size:13px;font-weight:600;color:var(--mute)}' +
    '.gir{display:block;font-weight:700;font-size:15px;line-height:1.25;color:var(--ink);text-decoration:none;overflow-wrap:anywhere}.gir:hover{text-decoration:underline}' +
    '.ps{text-align:right;flex:none}.ps b{display:block;font-size:28px;line-height:1;font-weight:800;color:var(--acc)}.ps span{font-size:13px;color:var(--mute);white-space:nowrap}' +
    '.ln{display:flex;align-items:center;gap:8px;margin-top:8px;font-size:14px;line-height:1.3}' +
    '.lb{flex:none;width:4.9em;font-size:12px;font-weight:700;color:var(--mute);text-transform:uppercase;letter-spacing:.3px}' +
    '.es{display:inline-grid;place-items:center;min-width:24px;height:24px;padding:0 4px;border-radius:6px;font-weight:800;font-size:13px;flex:none}' +
    '.es.v{background:#d6f5df;color:#0b5a2b}.es.p{background:#fde0d6;color:#8a2a0a}.es.n{background:#e3e8f0;color:#33415c}' +
    '.rs{font-weight:800;white-space:nowrap;font-variant-numeric:tabular-nums}.me{font-weight:700}.tx{overflow-wrap:anywhere}' +
    '.cp{display:block;color:var(--mute);font-size:13px}.cpi{color:var(--mute);font-size:13px;white-space:nowrap}' +
    '.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    'table{width:100%;border-collapse:collapse;font-size:14px}th{font-size:12px;font-weight:600;color:var(--mute);text-align:right;padding:8px 6px 4px;border-bottom:1px solid var(--line)}' +
    'td{padding:7px 6px;border-bottom:1px solid var(--line);text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}' +
    'th.n,td.n{text-align:left;white-space:normal;overflow-wrap:anywhere;width:100%}td.n{font-weight:600}td.p{color:var(--mute);font-weight:700;width:2em;text-align:center}td.pt{font-weight:800}' +
    'tbody tr:last-child td{border-bottom:0}.tb{padding:2px 8px 4px}' +
    '.gt{padding:10px 14px 2px;font-size:13px;font-weight:700;color:var(--mute);text-transform:uppercase;letter-spacing:.3px;border-top:1px solid var(--line)}' +
    '.mt{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:8px;align-items:center;padding:7px 14px;font-size:14px;line-height:1.25}' +
    '.mt .h{text-align:right;overflow-wrap:anywhere}.mt .a{overflow-wrap:anywhere}.mt .r{background:var(--soft);border-radius:6px;padding:2px 6px;text-align:center;font-weight:800;white-space:nowrap;min-width:3.4em}.mt .r.f{background:none;font-weight:600;font-size:13px;color:var(--mute)}' +
    '.more{padding:8px 14px 0;font-size:14px}' +
    '.ft{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:0 12px;padding:4px 14px;border-top:1px solid var(--line);background:var(--soft);font-size:13px;color:var(--mute)}' +
    '.ft a{display:inline-flex;align-items:center;min-height:44px;font-weight:700}' +
    '.er{padding:12px 14px;font-size:14px;color:var(--mute)}' +
    '@container (max-width:380px){.hx{display:none}.lb{width:auto}.ln{flex-wrap:wrap;gap:4px 8px}.ln .tx{flex-basis:100%}.ps b{font-size:24px}.mt{grid-template-columns:minmax(0,1fr) auto;gap:2px 8px}.mt .h{text-align:left}.mt .r{grid-row:1/3;grid-column:2}.mt .a{grid-column:1}}';

  function head(t, s) {
    return '<div class="hd"><img src="' + BASE + 'icons/icon-192.png" alt="" width="28" height="28"><div><b>' + esc(t) + '</b>' + (s ? '<small>' + esc(s) + '</small>' : '') + '</div></div>';
  }
  function foot(hash, agg) {
    return '<div class="ft"><a href="' + BASE + '#' + esc(hash) + '" target="_blank" rel="noopener">Risultati da Zuìn · Sport in FVG</a>' +
      (agg ? '<span>Aggiornato al ' + dtl(agg) + '</span>' : '') + '</div>';
  }
  function nome(n, bold) { return bold ? '<span class="me">' + esc(n) + '</span>' : esc(n); }

  function vSocieta(d, o) {
    var L = d.squadre || [], max = o.max || 5, S = L.slice(0, max);
    var h = head(d.nome, [d.comune, L.length > 1 ? L.length + ' squadre' : ''].filter(Boolean).join(' · '));
    h += S.map(function (s) {
      var u = s.ultima, p = s.prossima, x = '<div class="sq"><div class="top"><div><span class="cat">' + esc([s.categoria, SP[s.sport] || ''].filter(Boolean).join(' · ')) + '</span>' +
        '<a class="gir" href="' + BASE + '#g-' + encodeURIComponent(s.gid) + '" target="_blank" rel="noopener">' + esc(s.girone) + '</a></div>';
      if (s.pos != null) x += '<div class="ps"><b>' + esc(s.pos) + '°</b><span>' + (s.punti != null ? esc(s.punti) + ' pt' : '') + (s.n ? (s.punti != null ? ' · ' : '') + 'su ' + esc(s.n) : '') + '</span></div>';
      x += '</div>';
      if (u) x += '<div class="ln"><span class="lb">Ultima</span>' + (u.esito ? '<span class="es ' + u.esito + '"><span aria-hidden="true">' + u.esito.toUpperCase() + '</span><span class="vh">' + ESL[u.esito] + ':</span></span>' : '') +
        '<span class="tx">' + nome(u.casa, u.in_casa) + ' <span class="rs">' + esc(u.risultato) + '</span> ' + nome(u.ospite, !u.in_casa) + (u.data ? ' <span class="cpi">· ' + dt(u.data) + '</span>' : '') + '</span></div>';
      if (p) x += '<div class="ln"><span class="lb">Prossima</span><span class="tx"><b>' + dt(p.data, 1) + (p.ora ? ' · ' + esc(p.ora) : '') + '</b> ' + (p.in_casa ? 'in casa con ' : 'in trasferta con ') + esc(p.avversario) +
        (p.campo ? '<span class="cp">' + esc(p.campo) + '</span>' : '') + '</span></div>';
      if (!u && !p) x += '<div class="ln"><span class="cp">Nessuna partita disponibile</span></div>';
      return x + '</div>';
    }).join('');
    if (L.length > max) h += '<div class="more"><a href="' + BASE + '#s-' + encodeURIComponent(d.id) + '" target="_blank" rel="noopener">Altre ' + (L.length - max) + ' squadre su Zuìn</a></div>';
    return h + foot('s-' + d.id, d.aggiornato);
  }

  function righe(ps, fut) {
    return ps.map(function (m) {
      var r = fut ? '<span class="r f">' + (m.data ? dt(m.data, 1) : '') + (m.ora ? '<br>' + esc(m.ora) : '') + '</span>' : '<span class="r">' + esc(m.risultato) + '</span>';
      return '<div class="mt"><span class="h">' + esc(m.casa) + '</span>' + r + '<span class="a">' + esc(m.ospite) + '</span></div>';
    }).join('');
  }

  function vGirone(d, o) {
    var cl = d.classifica || [], max = o.max || 20, hasG = cl.some(function (r) { return r.g != null; }), hasP = cl.some(function (r) { return r.punti != null; });
    var h = head(d.girone, [d.categoria, SP[d.sport] || '', d.comitato].filter(Boolean).join(' · '));
    if (cl.length) {
      h += '<div class="tb"><table><caption class="vh">Classifica</caption><thead><tr><th scope="col"><span class="vh">Posizione</span>#</th><th scope="col" class="n">Squadra</th>' + (hasP ? '<th scope="col">Pt</th>' : '') + (hasG ? '<th scope="col" class="hx">G</th>' : '') + '</tr></thead><tbody>' +
        cl.slice(0, max).map(function (r) {
          return '<tr><td class="p">' + esc(r.pos) + '</td><td class="n">' + esc(r.squadra) + '</td>' + (hasP ? '<td class="pt">' + esc(r.punti == null ? '' : r.punti) + '</td>' : '') + (hasG ? '<td class="hx">' + esc(r.g == null ? '' : r.g) + '</td>' : '') + '</tr>';
        }).join('') + '</tbody></table></div>';
      if (cl.length > max) h += '<div class="more"><a href="' + BASE + '#g-' + encodeURIComponent(d.gid) + '" target="_blank" rel="noopener">Classifica completa (' + cl.length + ' squadre)</a></div>';
    }
    var u = d.ultima, p = d.prossima, k = u || p, fut = !u;
    if (k && k.partite && k.partite.length) {
      h += '<div class="gt">' + (fut ? 'Prossima giornata' : 'Ultima giornata') + (k.giornata != null ? ' · ' + esc(k.giornata) + 'ª' : '') + '</div>' + righe(k.partite, fut);
    }
    if (!cl.length && !k) h += '<div class="er">Classifica e partite non ancora disponibili.</div>';
    return h + foot('g-' + d.gid, d.aggiornato);
  }

  function tema(t) { return t === 'scuro' ? 'scuro' : t === 'auto' ? 'auto' : 'chiaro'; }

  function mount(host, o) {
    o = o || {};
    var root;
    try { root = host.shadowRoot || host.attachShadow({ mode: 'open' }); } catch (e) { return; }
    var cls = 'w ' + tema(o.tema);
    var max = parseInt(o.squadre, 10); o.max = max > 0 ? Math.min(max, 40) : 0;
    var lab = o.girone ? 'Classifica e risultati da Zuìn' : 'Risultati della società da Zuìn';
    var css = '<style>' + CSS + '</style>';
    try { if (!SHEET) { SHEET = new CSSStyleSheet(); SHEET.replaceSync(CSS); } root.adoptedStyleSheets = [SHEET]; css = ''; } catch (e) {}
    root.innerHTML = css + '<section class="' + cls + '" role="group" aria-label="' + lab + '" aria-busy="true"><div class="er">Carico i risultati…</div></section>';
    var box = root.querySelector('section');
    var path = o.girone ? 'g/' + fid(o.girone) + '.json' : o.societa ? 's/' + fid(o.societa) + '.json' : '';
    var hash = o.girone ? 'g-' + o.girone : o.societa ? 's-' + o.societa : '';
    if (!path) { box.innerHTML = '<div class="er">Widget Zuìn: manca data-societa o data-girone.</div>'; box.removeAttribute('aria-busy'); return; }
    return load(path).then(function (d) {
      box.innerHTML = o.girone ? vGirone(d, o) : vSocieta(d, o);
    }).catch(function () {
      box.innerHTML = '<div class="er">Risultati non disponibili in questo momento.</div>' + foot(hash, '');
    }).then(function () { box.removeAttribute('aria-busy'); });
  }

  function scan() {
    var L = document.querySelectorAll('script[data-societa],script[data-girone]');
    for (var i = 0; i < L.length; i++) {
      var s = L[i];
      if (s.getAttribute('data-zuin') || !/widget\.js(\?|#|$)/.test(s.src || '')) continue;
      s.setAttribute('data-zuin', '1');
      try {
        var host = document.createElement('div');
        host.className = 'zuin-widget';
        s.parentNode.insertBefore(host, s.nextSibling);
        mount(host, { societa: s.getAttribute('data-societa'), girone: s.getAttribute('data-girone'), tema: s.getAttribute('data-tema'), squadre: s.getAttribute('data-squadre') });
      } catch (e) {}
    }
  }

  window.ZuinWidget = { v: 1, base: BASE, mount: mount, scan: scan };
  scan();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan);
})();
