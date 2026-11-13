// Read offline: registers the service worker (sw.js at the site root, written
// by stage_site.py from .docs/sw-template.js), which keeps a copy of every
// page you open. Only on https or localhost (browsers allow workers nowhere
// else) and only when sw.js exists: a local `docsify serve` of the repo has
// none, so nothing is registered there. Any failure is silent.
(function () {
  if (!('serviceWorker' in navigator)) return;
  var h = location.hostname;
  if (location.protocol !== 'https:' && h !== 'localhost' && h !== '127.0.0.1' && h !== '[::1]') return;
  window.addEventListener('load', function () {
    fetch('./sw.js', { method: 'HEAD', cache: 'no-store' }).then(function (r) {
      if (r.ok) return navigator.serviceWorker.register('./sw.js');
    }).catch(function () {});
  });
})();
