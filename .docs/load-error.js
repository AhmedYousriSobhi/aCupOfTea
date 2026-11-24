// When a page's Markdown cannot be fetched (a dropped connection on a phone or
// tablet, a server hiccup), Docsify shows an empty page headed "0 -" or "503 -".
// Replace that with a plain message and a Try again button, after one automatic retry. A page that does not
// exist keeps its own 404 page (notFoundPage in config.js).
(function () {
  function failed() {
    var h = document.querySelector('.markdown-section h1');
    return !!h && /^\s*(0|5\d\d)\s+-/.test(h.textContent);
  }

  function show() {
    if (!failed()) return;
    var sec = document.querySelector('.markdown-section');
    var h = document.createElement('h1');
    h.textContent = 'This page could not be loaded';
    var p = document.createElement('p');
    p.textContent = 'The connection dropped or the server did not answer. Your place is kept; try again in a moment.';
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'load-retry';
    b.textContent = 'Try again';
    b.addEventListener('click', function () { location.reload(); });
    sec.replaceChildren(h, p, b);
    document.title = 'Page not loaded - aCupOfTea';
    // a dropped request usually works the second time: try once by itself per page, then leave the button
    var key = 'load-retry:' + location.hash;
    try {
      if (!sessionStorage.getItem(key)) {
        sessionStorage.setItem(key, '1');
        p.textContent = 'The connection dropped. Trying again...';
        setTimeout(function () { location.reload(); }, 1200);
      }
    } catch (e) { /* no storage: the button is enough */ }
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(show);
  });
})();
