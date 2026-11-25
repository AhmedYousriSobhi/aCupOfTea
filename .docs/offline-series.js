// "Save this series for offline": at the end of a page that sits in a folder of
// 3 to 80 pages (a series), a button fetches every page of that folder and their
// pictures. The service worker (offline.js, sw.js) keeps what is fetched, so the
// whole series opens again with no network. Only shown when a service worker
// controls the page (the deployed site, not a local preview). Nothing is sent
// anywhere; the browser keeps the copies.
(function () {
  var MIN = 3, MAX = 80, listing = null;
  function route() {
    return decodeURIComponent(location.hash.replace(/^#/, '').split('?')[0]);
  }
  function folderOf(r) {
    if (!r || r === '/' || r.indexOf('/.docs/') === 0) return '';
    var f = /\/$/.test(r) ? r.replace(/\/$/, '') : r.replace(/\/[^/]*$/, '');
    return (/README$/.test(f) ? f.replace(/\/README$/, '') : f).replace(/^\//, '');
  }
  function pages() {
    if (!listing) {
      listing = fetch('./.docs/_sidebar.md').then(function (r) { return r.ok ? r.text() : ''; }).then(function (t) {
        var out = [];
        t.replace(/\]\(([^)\s]+\.md)\)/g, function (_, p) { p = p.replace(/^\//, ''); if (!/^https?:/.test(p) && out.indexOf(p) < 0) out.push(p); });
        return out;
      }).catch(function () { return []; });
    }
    return listing;
  }
  function pictures(md, page) {
    var dir = '/' + page.replace(/[^/]*$/, ''), found = [];
    md.replace(/!\[[^\]\n]*\]\(\s*([^()\s'"<>]+)/g, function (_, src) {
      if (/^([a-z][a-z0-9+.-]*:|\/\/)/i.test(src)) return;
      var p = src.split(/[?#]/)[0];
      try { p = decodeURI(p); } catch (e) { /* keep as written */ }
      var a = (p.charAt(0) === '/' ? p : dir + p).split('/'), stack = [];
      a.forEach(function (s) { if (s === '..') stack.pop(); else if (s && s !== '.') stack.push(s); });
      var full = '/' + stack.join('/');
      if (found.indexOf(full) < 0) found.push(full);
    });
    return found;
  }
  function save(list, status, btn) {
    var done = 0, pics = 0, queue = list.slice(), failed = 0;
    btn.disabled = true;
    function next() {
      var p = queue.shift();
      if (!p) return Promise.resolve();
      return fetch('./' + p).then(function (r) {
        if (!r.ok) { failed++; return ''; }
        return r.text();
      }).then(function (md) {
        var imgs = pictures(md, p);
        return Promise.all(imgs.map(function (i) {
          return fetch('.' + i).then(function (r) { if (r.ok) pics++; else failed++; }).catch(function () { failed++; });
        }));
      }).catch(function () { failed++; }).then(function () {
        done++;
        status.textContent = 'Saving ' + done + ' of ' + list.length + '…';
        return next();
      });
    }
    status.textContent = 'Saving 0 of ' + list.length + '…';
    return Promise.all([next(), next(), next()]).then(function () {
      btn.disabled = false;
      status.textContent = failed ? 'Saved with ' + failed + ' file(s) missing; try again online.'
        : 'Saved ' + list.length + ' pages and ' + pics + ' pictures. They open without a network.';
    });
  }
  function show() {
    var old = document.querySelector('.markdown-section .offline-series');
    if (old) old.remove();
    var f = folderOf(route()), host = document.querySelector('.markdown-section');
    if (!f || !host || !navigator.serviceWorker || !navigator.serviceWorker.controller) return;
    pages().then(function (all) {
      var list = all.filter(function (p) { return p.indexOf(f + '/') === 0; });
      if (list.length < MIN || list.length > MAX || folderOf(route()) !== f || document.querySelector('.markdown-section .offline-series')) return;
      var box = document.createElement('div');
      box.className = 'offline-series';
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = 'Save this series for offline (' + list.length + ' pages)';
      var s = document.createElement('span');
      s.className = 'offline-status';
      s.setAttribute('role', 'status');
      b.addEventListener('click', function () { save(list, s, b); });
      box.appendChild(b);
      box.appendChild(s);
      host.appendChild(box);
    });
  }
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) { hook.doneEach(show); });
})();
