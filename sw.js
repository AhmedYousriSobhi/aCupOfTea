// Service worker template: read offline. stage_site.py writes it to sw.js at
// the root of the staged site (a worker only controls pages in its own folder
// and below), filling in VERSION (the git commit, or a timestamp) and SHELL
// (index.html, the scripts it loads, the menu files, the search index). Every
// deploy gets a new VERSION, so a new cache; old ones are deleted on activate.
//
//   same-origin GET (pages, .md, .json, .js, css, images): network first, the
//     copy in the cache when the network fails; every good answer is cached,
//     so each page read once can be read again offline;
//   cdn.jsdelivr.net (pinned, immutable versions): cache first;
//   anything else: not touched.
'use strict';
var VERSION = "90052e0e34f8";
var SHELL = ["./", "index.html", ".docs/_sidebar.md", ".docs/_navbar.md", ".docs/_404.md", "README.md", ".docs/search-index.json", ".docs/last-updated.json", ".docs/icons/favicon.svg", ".docs/icons/favicon-32.png", ".docs/icons/apple-touch-icon.png", ".docs/icons/site.webmanifest", "https://cdn.jsdelivr.net/npm/docsify@5.0.0/dist/themes/core.min.css", "https://cdn.jsdelivr.net/npm/docsify@5.0.0/dist/themes/addons/vue.min.css", "https://cdn.jsdelivr.net/npm/docsify@5.0.0/dist/themes/addons/core-dark.min.css", ".docs/theme-toggle.js", ".docs/config.js", ".docs/math.js", ".docs/lazy-libs.js", ".docs/phone-tables.js", ".docs/lazy-images.js", ".docs/page-footer.js", ".docs/page-outline.js", ".docs/reading-progress.js", ".docs/surprise-me.js", ".docs/reading-history.js", ".docs/section-links.js", ".docs/offline.js", ".docs/search.js", "https://cdn.jsdelivr.net/npm/docsify@5.0.0/dist/docsify.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-bash.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-python.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-powershell.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-yaml.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-c.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-ini.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.30.0/components/prism-sql.min.js", "https://cdn.jsdelivr.net/npm/docsify@5.0.0/dist/plugins/zoom-image.min.js", ".docs/image-viewer.js", "https://cdn.jsdelivr.net/npm/docsify@5.0.0/dist/plugins/front-matter.min.js", ".docs/copy-code.js", "https://cdn.jsdelivr.net/npm/docsify-tabs@1.6.3/dist/docsify-tabs.min.js", ".docs/sidebar-groups.js", "https://cdn.jsdelivr.net/npm/docsify-pagination@2.10.1/dist/docsify-pagination.min.js", "https://cdn.jsdelivr.net/npm/docsify-plugin-flexible-alerts@1.3.0/dist/docsify-plugin-flexible-alerts.min.js"];
var PREFIX = 'acupoftea-';
var CACHE = PREFIX + VERSION;
var CDN = 'https://cdn.jsdelivr.net/';
var SCOPE = self.registration.scope;

var OFFLINE_PAGE = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">' +
  '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Offline</title></head>' +
  '<body style="max-width:640px;margin:15vh auto;padding:0 16px;font:17px/1.6 sans-serif;color:#34495e">' +
  '<h1 style="font-size:1.6em">You are offline</h1><p>This page has not been read on this device yet, ' +
  'so there is no saved copy. Pages you have opened before still work; try again when you are back online.</p>' +
  '</body></html>';

function keep(cache, req, res) {
  if (res && res.ok && res.status !== 206 && (res.type === 'basic' || res.type === 'cors')) {
    cache.put(req, res.clone()).catch(function () {});
  }
  return res;
}

self.addEventListener('install', function (event) {
  event.waitUntil(caches.open(CACHE).then(function (cache) {
    // one by one: a missing file must not stop the others (or the install)
    return Promise.all(SHELL.map(function (url) {
      var abs = new URL(url, SCOPE).href;
      var req = abs.indexOf(CDN) === 0
        ? new Request(abs, { mode: 'cors', credentials: 'omit' })
        : new Request(abs, { cache: 'reload' });
      return fetch(req).then(function (res) { keep(cache, abs, res); }).catch(function () {});
    }));
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (event) {
  // only this site's caches: other sites on the same github.io origin keep theirs
  event.waitUntil(caches.keys().then(function (names) {
    return Promise.all(names.filter(function (n) { return n.indexOf(PREFIX) === 0 && n !== CACHE; })
      .map(function (n) { return caches.delete(n); }));
  }).then(function () { return self.clients.claim(); }));
});

function offlineAnswer(req) {
  if (req.mode === 'navigate') {
    return new Response(OFFLINE_PAGE, { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }
  return Response.error();
}

function networkFirst(req) {
  return caches.open(CACHE).then(function (cache) {
    return fetch(req).then(function (res) { return keep(cache, req, res); }).catch(function () {
      return cache.match(req, { ignoreSearch: req.mode === 'navigate' }).then(function (hit) {
        if (hit) return hit;
        if (req.mode !== 'navigate') return offlineAnswer(req);
        // hash routing: every page of the site is index.html
        return cache.match(new URL('index.html', SCOPE).href).then(function (shell) {
          return shell || cache.match(SCOPE).then(function (root) { return root || offlineAnswer(req); });
        });
      });
    });
  });
}

function cacheFirst(req) {
  return caches.open(CACHE).then(function (cache) {
    return cache.match(req).then(function (hit) {
      // fetch(req) keeps the page's CORS mode, so integrity (SRI) checks still pass
      return hit || fetch(req).then(function (res) { return keep(cache, req, res); });
    });
  });
}

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET' || req.headers.has('range')) return;
  if (req.url.indexOf(SCOPE) === 0) event.respondWith(networkFirst(req));
  else if (req.url.indexOf(CDN) === 0) event.respondWith(cacheFirst(req));
});
