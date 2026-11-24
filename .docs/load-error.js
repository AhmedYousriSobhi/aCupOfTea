// When a page's Markdown cannot be fetched, Docsify shows an empty page headed
// "0 -" (the request failed before any answer) or "503 -". Replace that with an
// honest message: ask for the same file once more and say what happened
// (it answered after all, the file is missing, the server errored, or the
// connection failed), with a Try again button. A page that does not exist keeps
// its own 404 page (notFoundPage in config.js). A first retry runs by itself.
(function () {
  function failed() {
    var h = document.querySelector('.markdown-section h1');
    return !!h && /^\s*(0|5\d\d)\s+-/.test(h.textContent);
  }

  function file() {
    var path = decodeURIComponent((location.hash || '#/').replace(/^#\/?/, '').split('?')[0]);
    if (path === '' || /\/$/.test(path)) path += 'README';
    return path + '.md';
  }

  function show() {
    if (!failed()) return;
    var f = file();
    var sec = document.querySelector('.markdown-section');
    var h = document.createElement('h1');
    h.textContent = 'This page could not be loaded';
    var p = document.createElement('p');
    p.textContent = 'Checking what went wrong...';
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'load-retry';
    b.textContent = 'Try again';
    b.addEventListener('click', function () { location.reload(); });
    sec.replaceChildren(h, p, b);
    document.title = 'Page not loaded - aCupOfTea';

    var hash = location.hash;
    var key = 'load-retry:' + hash;
    var again = false;
    try { again = !!sessionStorage.getItem(key); sessionStorage.setItem(key, '1'); } catch (e) { /* no storage */ }
    var note = function (text) { if (location.hash === hash) p.textContent = text; };

    fetch('./' + f, { cache: 'no-store' }).then(function (r) {
      if (r.ok) {
        // the file is there and answers: the first request was lost on the way
        note('The page file is on the server and answers now (' + r.status + '); the first request was lost on the way.' + (again ? '' : ' Reloading...'));
        if (!again) setTimeout(function () { if (location.hash === hash) location.reload(); }, 800);
      } else if (r.status === 404) {
        note('The page file ' + f + ' is not on the server (404). The link may be out of date.');
      } else {
        note('The server answered ' + r.status + ' for ' + f + '. Try again in a moment.');
      }
    }, function (e) {
      note('The connection failed before the server answered (' + (navigator.onLine === false ? 'the device reports it is offline' : 'the device reports it is online') +
        '; ' + (e && e.name ? e.name : 'network error') + '). The page file ' + f + ' was not reached. Try again when the connection is back.');
    });
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(show);
  });
})();
