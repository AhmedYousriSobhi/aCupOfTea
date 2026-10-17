// Reading history: pages already opened are dimmed in the side menu, and a
// "Continue" link under "Surprise me" returns to the last page read. It lives
// only in this browser (localStorage); without storage nothing is marked.
(function () {
  var KEY = 'acot-read', LAST = 'acot-last';
  function load(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch (e) { return fallback; }
  }
  function save(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* private window or blocked storage */ }
  }
  function route() {
    return decodeURIComponent(location.hash.replace(/^#/, '').split('?')[0]).replace(/\.md$/, '');
  }
  function isContent(r) {
    return r && r !== '/' && r.indexOf('/.docs/') !== 0;
  }
  function record() {
    var r = route(), h1 = document.querySelector('.markdown-section h1');
    if (!isContent(r) || !h1) return;
    var read = load(KEY, {});
    read[r] = Date.now();
    save(KEY, read);
    save(LAST, { route: r, title: h1.textContent.trim() });
  }
  function mark() {
    var read = load(KEY, {});
    Array.prototype.forEach.call(document.querySelectorAll('.sidebar-nav li:not(.group) > a.page-link[href^="#/"]'), function (a) {
      if (a.closest('.app-sub-sidebar')) return; // the page's own sections are not pages
      var h = decodeURIComponent(a.getAttribute('href').replace(/^#/, '').split('?')[0]).replace(/\.md$/, '');
      a.classList.toggle('read', !!read[h]);
    });
  }
  function resume() {
    var last = load(LAST, null), link = document.getElementById('continue-reading');
    if (!last || last.route === route()) {
      if (link) link.remove();
      return;
    }
    var nav = document.querySelector('.sidebar-nav');
    if (!nav) return;
    if (!link) {
      link = document.createElement('a');
      link.id = 'continue-reading';
      nav.parentNode.insertBefore(link, nav);
    }
    link.href = '#' + last.route;
    link.textContent = '▶ Continue: ' + last.title;
    link.title = 'Open the last page you read';
  }
  function update() { mark(); resume(); }
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(function () {
      // the link shows the page read before this one, so refresh it first, then record this page
      resume();
      record();
      mark();
      setTimeout(mark, 300); // Docsify redraws the menu after the page loads
    });
  });
})();
