// Reading history and saved pages: pages already opened get a check in the side
// menu, a "Continue" link under "Surprise me" returns to the last page read, and
// a "Save for later" button under the title collects pages in a "Saved" list in
// the menu. It lives only in this browser (localStorage); without storage
// nothing is kept.
(function () {
  var KEY = 'acot-read', LAST = 'acot-last', SAVED = 'acot-saved';
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
      nav.parentNode.insertBefore(link, document.getElementById('saved-pages') || nav);
    }
    link.href = '#' + last.route;
    link.textContent = '▶ Continue: ' + last.title;
    link.title = 'Open the last page you read';
  }
  function saved() { return load(SAVED, []); }
  function isSaved(r) { return saved().some(function (p) { return p.route === r; }); }
  function toggleSaved(r, title) {
    var list = saved();
    var kept = list.filter(function (p) { return p.route !== r; });
    if (kept.length === list.length) kept.push({ route: r, title: title });
    save(SAVED, kept);
  }
  // "Save for later" under the page title
  function saveButton() {
    var old = document.querySelector('.markdown-section .save-page');
    if (old) old.remove();
    var r = route(), h1 = document.querySelector('.markdown-section h1');
    if (!isContent(r) || !h1) return;
    var title = h1.textContent.trim();
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'save-page';
    function paint() {
      var on = isSaved(r);
      btn.textContent = on ? '★ Saved' : '☆ Save for later';
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
    btn.addEventListener('click', function () { toggleSaved(r, title); paint(); savedList(); });
    paint();
    h1.parentNode.insertBefore(btn, h1.nextSibling);
  }
  // "Saved (N)" list in the side menu, hidden when empty
  function savedList() {
    var list = saved(), box = document.getElementById('saved-pages');
    if (!list.length) {
      if (box) box.remove();
      return;
    }
    var nav = document.querySelector('.sidebar-nav');
    if (!nav) return;
    var wasOpen = !!(box && box.open);
    if (!box) {
      box = document.createElement('details');
      box.id = 'saved-pages';
      nav.parentNode.insertBefore(box, nav);
    }
    box.textContent = '';
    var sum = document.createElement('summary');
    sum.textContent = '★ Saved (' + list.length + ')';
    box.appendChild(sum);
    var ul = document.createElement('ul');
    list.forEach(function (p) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = '#' + p.route;
      a.textContent = p.title;
      var x = document.createElement('button');
      x.type = 'button';
      x.textContent = '×';
      x.setAttribute('aria-label', 'Remove ' + p.title + ' from Saved');
      x.addEventListener('click', function () {
        toggleSaved(p.route, p.title);
        savedList();
        saveButton();
      });
      li.appendChild(a);
      li.appendChild(x);
      ul.appendChild(li);
    });
    box.appendChild(ul);
    box.open = wasOpen;
  }
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(function () {
      // the link shows the page read before this one, so refresh it first, then record this page
      resume();
      record();
      saveButton();
      savedList();
      mark();
      setTimeout(mark, 300); // Docsify redraws the menu after the page loads
    });
  });
})();
