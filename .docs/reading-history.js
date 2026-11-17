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
  // Learning paths: "Part 2 of 6" and a Next button at the end of a page, and
  // "2 of 6 read" under each path on Start here (data: .docs/generated/paths.json).
  var paths = null, pathsLoading = null;
  function loadPaths() {
    if (!pathsLoading) {
      pathsLoading = fetch('./.docs/generated/paths.json').then(function (r) { return r.ok ? r.json() : {}; })
        .catch(function () { return {}; }).then(function (d) { paths = d; return d; });
    }
    return pathsLoading;
  }
  function seriesBlock() {
    var old = document.querySelector('.markdown-section .series-next');
    if (old) old.remove();
    var r = route();
    if (!isContent(r)) return;
    loadPaths().then(function (all) {
      var e = all[r.replace(/^\//, '')], sec = document.querySelector('.markdown-section');
      if (!e || !sec || route() !== r || sec.querySelector('.series-next')) return;
      var box = document.createElement('div');
      box.className = 'series-next';
      var t = document.createElement('p');
      t.textContent = 'Part ' + e.pos + ' of ' + e.total + ' in this learning path';
      box.appendChild(t);
      if (e.next) {
        var a = document.createElement('a');
        a.className = 'next-btn';
        a.href = '#/' + e.next.path;
        a.textContent = 'Next: ' + e.next.title + ' \u2192';
        box.appendChild(a);
      } else {
        t.textContent += ' \u2014 you reached the last step.';
      }
      var before = sec.querySelector('.see-also, .page-footer, .docsify-pagination-container');
      if (before) sec.insertBefore(box, before); else sec.appendChild(box);
    });
  }
  function startProgress() {
    if (route() !== '/.docs/generated/explore/start-here') return;
    var read = load(KEY, {});
    Array.prototype.forEach.call(document.querySelectorAll('.markdown-section h3'), function (h) {
      var list = h.nextElementSibling;
      if (!list || list.tagName !== 'OL') return;
      var links = Array.prototype.slice.call(list.querySelectorAll(':scope > li > a[href^="#/"]'));
      var done = 0, next = null;
      links.forEach(function (a) {
        var k = decodeURIComponent(a.getAttribute('href').replace(/^#/, '').split('?')[0]).replace(/\.md$/, '');
        if (read[k]) done++; else if (!next) next = a;
      });
      if (!done) return;
      var p = document.createElement('p');
      p.className = 'path-progress';
      p.textContent = done + ' of ' + links.length + ' read';
      if (next) {
        p.appendChild(document.createTextNode(' \u00b7 '));
        var n = document.createElement('a');
        n.href = next.getAttribute('href');
        n.textContent = 'Next: ' + next.textContent;
        p.appendChild(n);
      }
      h.parentNode.insertBefore(p, list);
    });
  }

  // Move reading history and saved pages to another browser: a JSON file, no account.
  function exportData() {
    var data = { app: 'acupoftea', version: 1, read: load(KEY, {}), last: load(LAST, null), saved: saved() };
    var url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' }));
    var a = document.createElement('a');
    a.href = url;
    a.download = 'acupoftea-reading-data.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }
  function importData(text) {
    var d = JSON.parse(text);
    if (!d || d.app !== 'acupoftea' || typeof d.read !== 'object' || !Array.isArray(d.saved)) throw new Error('not a reading-data file');
    var read = load(KEY, {});
    Object.keys(d.read).forEach(function (k) {
      if (typeof d.read[k] === 'number' && k.charAt(0) === '/') read[k] = Math.max(read[k] || 0, d.read[k]);
    });
    save(KEY, read);
    var have = saved();
    d.saved.forEach(function (p) {
      if (p && typeof p.route === 'string' && typeof p.title === 'string' && p.route.charAt(0) === '/' &&
          !have.some(function (q) { return q.route === p.route; })) have.push({ route: p.route, title: p.title });
    });
    save(SAVED, have);
    if (d.last && typeof d.last.route === 'string' && !load(LAST, null)) save(LAST, { route: d.last.route, title: String(d.last.title || '') });
  }
  function dataButtons() {
    var menu = document.getElementById('theme-menu');
    if (!menu || menu.querySelector('.data-row')) return;
    var row = document.createElement('div');
    row.className = 'data-row';
    var note = document.createElement('span');
    row.appendChild(note);
    function btn(label, fn) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.addEventListener('click', fn);
      row.appendChild(b);
    }
    var file = document.createElement('input');
    file.type = 'file';
    file.accept = 'application/json,.json';
    file.hidden = true;
    file.addEventListener('change', function () {
      var f = file.files && file.files[0];
      if (!f) return;
      f.text().then(function (t) {
        importData(t);
        note.textContent = 'Imported';
        mark(); savedList(); saveButton(); startProgress();
      }, function () { note.textContent = 'Could not read the file'; }).catch(function () { note.textContent = 'Not a reading-data file'; });
      file.value = '';
    });
    note.textContent = 'Reading data';
    btn('Export', exportData);
    btn('Import', function () { file.click(); });
    row.appendChild(file);
    menu.appendChild(row);
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(function () {
      // the link shows the page read before this one, so refresh it first, then record this page
      resume();
      record();
      saveButton();
      savedList();
      seriesBlock();
      startProgress();
      dataButtons();
      setTimeout(dataButtons, 300); // the theme menu is built just after the first page
      mark();
      setTimeout(mark, 300); // Docsify redraws the menu after the page loads
    });
  });
})();
