/* config.js */
try {
// Docsify settings, and the one page behaviour that is not a plugin.
// Kept in a file rather than inline in index.html: the site's
// Content-Security-Policy allows scripts from files only, so a script
// injected into a page cannot run.
window.$docsify = Object.assign(window.$docsify || {}, {
  name: 'aCupOfTea',
  repo: 'AhmedYousriSobhi/aCupOfTea',
  // basePath: '../', // Tell docsify to look for the markdown files in the parent directory
  loadSidebar: './.docs/_sidebar.md',
  loadNavbar: './.docs/_navbar.md',
  notFoundPage: './.docs/_404.md',
  relativePath: false, // Use relative paths for sidebar and navbar links
  // Below 1400px the right-hand outline is hidden, so list the page's
  // sections (h2, h3) under it in the sidebar instead.
  subMaxLevel: window.matchMedia('(max-width: 1399px)').matches ? 3 : 0,
  auto2top: true,
  plugins: [window.themeToggle, function (hook) {
    // Docsify 5's auto2top leaves the window where it was (the window, not an
    // inner box, is the scroller), so Next opened the next page mid-page:
    // start every page at its top unless the link names a section.
    hook.doneEach(function () {
      if (!/[?&]id=/.test(location.hash)) window.scrollTo(0, 0);
    });
  }],
   pagination: {
    previousText: 'Previous',
    nextText: 'Next',
    crossChapter: true,
    crossChapterText: true,
  },
  // Configure the tabs plugin
  tabs: {
    persist: true,      // stay on the same tab when refreshing
    sync: true,         // sync tabs with same label across page
    theme: 'classic',   // 'classic' or 'material'
  },
  // Add this to help Docsify match URLs to the sidebar entries
  alias: {
    '/(.*)/_sidebar.md': './.docs/_sidebar.md',
    '/(.*)/_navbar.md': './.docs/_navbar.md'
  },
});

// On phones the sidebar covers the page: close it after any page or section
// link in it is tapped (and "Surprise me"), so the reader sees the page they
// chose, not the menu. Docsify 5 leaves the menu open otherwise.
document.addEventListener('click', function (e) {
  var link = e.target.closest && e.target.closest('.sidebar-nav a[href^="#/"], #surprise-me');
  if (!link || window.innerWidth > 768) return;
  setTimeout(function () {
    var open = document.querySelector('aside.sidebar.show');
    var toggle = document.querySelector('button.sidebar-toggle');
    if (open && toggle) toggle.click();
  }, 0);
});

// Phones hide the GitHub corner (the theme button takes its place in the top
// bar), so the side menu ends with a link to the repository instead.
window.$docsify.plugins = [].concat(window.$docsify.plugins || [], function (hook) {
  hook.doneEach(function () {
    var nav = document.querySelector('.sidebar-nav');
    if (!nav || document.getElementById('menu-github')) return;
    var p = document.createElement('p');
    p.id = 'menu-github';
    var a = document.createElement('a');
    a.href = 'https://github.com/AhmedYousriSobhi/aCupOfTea';
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = 'Source on GitHub';
    p.appendChild(a);
    nav.parentNode.insertBefore(p, nav.nextSibling);
  });
});

} catch (e) { console.error("config.js", e); }
/* math.js */
try {
// Formulas. A line that is only $$...$$ is shown as a display formula with
// KaTeX (pages stay plain LaTeX, which GitHub also renders). Lines inside code
// fences are left alone, and inline $...$ is not touched, so shell snippets and
// prices never turn into maths.
(function () {
  var FENCE = /^\s*(```|~~~)/;
  var BLOCK = /^\s*\$\$(.+?)\$\$\s*$/;
  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function protect(md) {
    var fence = false;
    return md.split('\n').map(function (line) {
      if (FENCE.test(line)) { fence = !fence; return line; }
      var m = !fence && line.match(BLOCK);
      return m ? '\n<div class="math-block" data-tex="' + esc(m[1].trim()) + '"></div>\n' : line;
    }).join('\n');
  }
  function render() {
    if (typeof katex === 'undefined') return;
    Array.prototype.forEach.call(document.querySelectorAll('.math-block[data-tex]'), function (el) {
      try {
        katex.render(el.getAttribute('data-tex'), el, { displayMode: true, throwOnError: false });
      } catch (e) {
        el.textContent = el.getAttribute('data-tex');
      }
      el.removeAttribute('data-tex');
    });
  }
  // KaTeX itself is loaded by .docs/lazy-libs.js only on pages with a formula,
  // which then calls this.
  window.renderMath = render;
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.beforeEach(protect);
    hook.doneEach(render);
  });
})();

} catch (e) { console.error("math.js", e); }
/* lazy-libs.js */
try {
// Heavy libraries load only on pages that need them: Mermaid (about 1.5 MB) for
// a page with a ```mermaid block, KaTeX for a page with a $$ formula line
// (.docs/math.js marks those). Versions stay pinned here, like in index.html.
(function () {
  // [address, integrity hash]; `check_pins.py --sri --write` fills the hashes
  var LIBS = {
    mermaid: {
      js: ['https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js', 'sha384-8xUhuLNMjW/cI2Dacg3DR4WliYznvIg0LVG1stctThKD/YVrJFI9TNCFxft5NYgp'],
    },
    katex: {
      css: ['https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.css', 'sha384-3rdsX6e5mueWyoweR9NIVmtEsUkokpBT/0ALqKKIBMr9j4qhHkaIkAcGgsE6uVlp'],
      js: ['https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.js', 'sha384-QFFtAGzvvj+bfgCGxXJlNZZR1nXEZgvG8tDLCCY1F19xl20WlfTYgguB4VcNdxYk'],
    },
  };
  function attach(el, attr, pair) {
    el[attr] = pair[0];
    if (pair[1]) { el.integrity = pair[1]; el.crossOrigin = 'anonymous'; }
    document.head.appendChild(el);
  }
  var loading = {};

  // Loads a library once and resolves when its script has run.
  function load(name) {
    if (loading[name]) return loading[name];
    var lib = LIBS[name];
    loading[name] = new Promise(function (resolve, reject) {
      if (lib.css) {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        attach(link, 'href', lib.css);
      }
      var s = document.createElement('script');
      s.onload = resolve;
      s.onerror = function () { delete loading[name]; reject(new Error('could not load ' + name)); };
      attach(s, 'src', lib.js);
    });
    return loading[name];
  }
  window.lazyLibs = { load: load, LIBS: LIBS };

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    // ```mermaid blocks become <div class="mermaid"> (what docsify-mermaid did)
    hook.afterEach(function (html, next) {
      if (html.indexOf('data-lang="mermaid"') < 0) return next(html);
      var box = document.createElement('div');
      box.innerHTML = html;
      box.querySelectorAll('pre[data-lang=mermaid]').forEach(function (pre) {
        var div = document.createElement('div');
        div.className = 'mermaid';
        div.textContent = pre.textContent;
        pre.parentNode.replaceChild(div, pre);
      });
      next(box.innerHTML);
    });
    hook.doneEach(function () {
      if (document.querySelector('.markdown-section .mermaid:not([data-processed])')) {
        load('mermaid').then(function () {
          if (!window.__mermaidReady) { mermaid.initialize({ startOnLoad: false }); window.__mermaidReady = true; }
          return mermaid.run({ querySelector: '.markdown-section .mermaid:not([data-processed])' });
        }).catch(function (e) { console.warn(e.message); });
      }
      if (document.querySelector('.markdown-section .math-block[data-tex]')) {
        load('katex').then(function () { if (window.renderMath) window.renderMath(); })
          .catch(function (e) { console.warn(e.message); });
      }
    });
  });
})();

} catch (e) { console.error("lazy-libs.js", e); }
/* phone-tables.js */
try {
// Phone tables. A 2-4 column table squeezes into narrow columns on a phone, so
// each row is shown as a small card (first cell as the title, the other cells
// labelled by their column heading). Wider tables keep their grid and scroll
// sideways. The layout itself lives in the CSS in index.html (table.stack).
(function () {
  function prepare() {
    var tables = document.querySelectorAll('.markdown-section table');
    Array.prototype.forEach.call(tables, function (t) {
      var heads = Array.prototype.map.call(t.querySelectorAll('thead th'), function (h) {
        return h.textContent.trim();
      });
      if (heads.length < 2 || heads.length > 4) return;
      t.classList.add('stack');
      Array.prototype.forEach.call(t.querySelectorAll('tbody tr'), function (tr) {
        Array.prototype.forEach.call(tr.children, function (td, i) {
          if (i > 0 && heads[i]) td.setAttribute('data-label', heads[i]);
        });
      });
    });
  }
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(prepare);
  });
})();

} catch (e) { console.error("phone-tables.js", e); }
/* lazy-images.js */
try {
// Lazy images: every picture in a page except the first is marked
// loading="lazy", so a long page fetches images as the reader scrolls instead
// of all at once (matters on a phone connection). The first image stays eager
// because it is usually on screen at the start. Done on the page's HTML before
// it is inserted, so the browser never starts the early download.
(function () {
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.afterEach(function (html) {
      var seen = 0;
      return html.replace(/<img\b(?![^>]*\bloading=)/g, function (tag) {
        seen += 1;
        return seen === 1 ? tag : tag + ' loading="lazy" decoding="async"';
      });
    });
  });
})();

} catch (e) { console.error("lazy-images.js", e); }
/* page-footer.js */
try {
// Page footer: "Edit this page" (opens the file on GitHub, on dev) and, on the
// deployed site, "Last updated" from .docs/last-updated.json (written by
// stage_site.py from git history) and "Copy share link" (the page's own folder
// address, a share page written by stage_site.py whose preview shows this page's
// title and summary). The homepage, generated pages and the 404 page get no
// footer. Without the dates file (local preview) only the edit link shows.
(function () {
  var EDIT = 'https://github.com/AhmedYousriSobhi/aCupOfTea/edit/dev/';
  var dates = null;
  function loadDates() {
    if (!dates) {
      dates = fetch('./.docs/last-updated.json')
        .then(function (r) { return r.ok ? r.json() : {}; })
        .catch(function () { return {}; });
    }
    return dates;
  }
  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var t = document.createElement('textarea');
      t.value = text;
      t.setAttribute('readonly', '');
      t.style.position = 'fixed';
      t.style.opacity = '0';
      document.body.appendChild(t);
      t.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { /* not allowed */ }
      t.remove();
      if (ok) resolve(); else reject(new Error('copy refused'));
    });
  }
  // the share page of a page: its path without .md (a folder README: the folder), as a folder address
  function shareUrl(file) {
    var site = location.href.split('#')[0].replace(/index\.html$/, '');
    if (site.charAt(site.length - 1) !== '/') site = site.replace(/[^/]*$/, '');
    var dir = file.replace(/\/README\.md$/, '').replace(/\.md$/, '');
    return site + dir.split('/').map(encodeURIComponent).join('/') + '/';
  }
  function render(file) {
    loadDates().then(function (d) {
      var section = document.querySelector('.markdown-section');
      if (!section || section.querySelector('.page-footer')) return;
      var known = Object.keys(d).length > 0;
      if (known && !d[file]) return; // not a real page (the 404 page, for one)
      var foot = document.createElement('p');
      foot.className = 'page-footer';
      var a = document.createElement('a');
      a.href = EDIT + file.split('/').map(encodeURIComponent).join('/');
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = 'Edit this page';
      foot.appendChild(a);
      if (d[file]) foot.appendChild(document.createTextNode(' \u00b7 Last updated ' + d[file]));
      if (known) {
        foot.appendChild(document.createTextNode(' \u00b7 '));
        var share = document.createElement('button');
        share.type = 'button';
        share.className = 'share-link';
        share.textContent = 'Copy share link';
        var timer;
        share.addEventListener('click', function () {
          copy(shareUrl(file)).then(function () { share.textContent = 'Link copied'; },
            function () { share.textContent = 'Could not copy'; });
          clearTimeout(timer);
          timer = setTimeout(function () { share.textContent = 'Copy share link'; }, 2000);
        });
        foot.appendChild(share);
      }
      section.appendChild(foot);
    });
  }
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook, vm) {
    hook.doneEach(function () {
      var file = vm.route.file || '';
      if (!file || file === 'README.md' || file.indexOf('.docs/') === 0) return;
      render(file);
    });
  });
})();

} catch (e) { console.error("page-footer.js", e); }
/* page-outline.js */
try {
// Page outline: on wide screens a small "On this page" list (h2 and h3) sits
// to the right of the text, with the section being read highlighted. It
// replaces the abandoned docsify-plugin-toc. Narrower screens get the section
// list in the sidebar instead (subMaxLevel in index.html).
(function () {
  var MIN_WIDTH = 1400;
  var observer = null;
  function build() {
    var old = document.querySelector('aside.page-outline');
    if (old) old.remove();
    if (observer) { observer.disconnect(); observer = null; }
    if (window.innerWidth < MIN_WIDTH) return;
    var heads = document.querySelectorAll('.markdown-section h2[id], .markdown-section h3[id]');
    if (heads.length < 2) return;
    var aside = document.createElement('aside');
    aside.className = 'page-outline';
    var title = document.createElement('p');
    title.textContent = 'On this page';
    aside.appendChild(title);
    var links = {};
    Array.prototype.forEach.call(heads, function (h) {
      var a = document.createElement('a');
      a.href = '#' + location.hash.replace(/^#/, '').split('?')[0] + '?id=' + h.id;
      a.textContent = h.textContent.trim();
      a.className = h.tagName === 'H3' ? 'sub' : '';
      aside.appendChild(a);
      links[h.id] = a;
    });
    document.body.appendChild(aside);
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && links[e.target.id]) {
          Object.keys(links).forEach(function (k) { links[k].classList.remove('active'); });
          links[e.target.id].classList.add('active');
        }
      });
    }, { rootMargin: '0px 0px -75% 0px' });
    Array.prototype.forEach.call(heads, function (h) { observer.observe(h); });
  }
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(build);
  });
})();

} catch (e) { console.error("page-outline.js", e); }
/* reading-progress.js */
try {
// Long pages: a thin bar at the top shows how far you have read, and a
// back-to-top button appears after scrolling a screen and a half. Both stay
// hidden on pages shorter than two screens. Smooth scrolling is skipped for
// readers who ask for reduced motion.
(function () {
  var bar, top;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');

  function update() {
    if (!bar) return;
    var doc = document.documentElement;
    var room = doc.scrollHeight - window.innerHeight;
    var y = window.scrollY || doc.scrollTop;
    var long = room > window.innerHeight;
    bar.hidden = !long;
    bar.style.transform = 'scaleX(' + (long ? Math.min(1, y / room) : 0) + ')';
    top.hidden = !(long && y > window.innerHeight * 1.5);
  }

  function build() {
    bar = document.createElement('div');
    bar.id = 'read-progress';
    bar.setAttribute('aria-hidden', 'true');
    top = document.createElement('button');
    top.id = 'back-to-top';
    top.type = 'button';
    top.title = 'Back to top';
    top.setAttribute('aria-label', 'Back to top');
    top.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M6 15l6-6 6 6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    top.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: still.matches ? 'auto' : 'smooth' });
    });
    document.body.appendChild(bar);
    document.body.appendChild(top);
    window.addEventListener('scroll', function () { window.requestAnimationFrame(update); }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.ready(build);
    // images load late and make the page longer, so measure again shortly after
    hook.doneEach(function () { update(); setTimeout(update, 800); });
  });
})();

} catch (e) { console.error("reading-progress.js", e); }
/* surprise-me.js */
try {
// "Surprise me": a link at the top of the side menu that opens a random
// content page from the menu (not a folder index, not a generated page, not
// the page already open). Good for a coffee break, and resurfaces old pages.
(function () {
  function pages() {
    var seen = {};
    return Array.prototype.map.call(document.querySelectorAll('.sidebar-nav a[href^="#/"]'), function (a) {
      return a.getAttribute('href').split('?')[0];
    }).filter(function (h) {
      if (seen[h] || /\/README(\.md)?$|^#\/$|^#\/\.docs\//.test(h)) return false;
      seen[h] = true;
      return true;
    });
  }

  function go(e) {
    e.preventDefault();
    var here = location.hash.split('?')[0];
    var list = pages().filter(function (h) { return h !== here; });
    if (list.length) location.hash = list[Math.floor(Math.random() * list.length)].slice(1);
  }

  function add() {
    var nav = document.querySelector('.sidebar-nav');
    if (!nav || document.getElementById('surprise-me')) return;
    var a = document.createElement('a');
    a.id = 'surprise-me';
    a.href = '#/';
    a.textContent = '🎲 Surprise me';
    a.title = 'Open a random page';
    a.addEventListener('click', go);
    nav.parentNode.insertBefore(a, nav);
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(add);
  });
})();

} catch (e) { console.error("surprise-me.js", e); }
/* reading-history.js */
try {
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
      btn.textContent = on ? '★' : '☆';
      btn.setAttribute('aria-label', on ? 'Saved, click to remove' : 'Save for later');
      btn.title = on ? 'Saved: click to remove' : 'Save for later';
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
    btn.addEventListener('click', function () { toggleSaved(r, title); paint(); savedList(); });
    paint();
    // a star at the right end of the meta line under the title; pages without one get it under the title
    var meta = document.querySelector('.markdown-section .reading-time');
    if (meta) meta.appendChild(btn); else h1.parentNode.insertBefore(btn, h1.nextSibling);
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
  // Homepage: the Search button focuses the search box, and the last page read is offered again.
  function home() {
    var btn = document.querySelector('.markdown-section .home-search');
    if (btn && !btn.getAttribute('data-ready')) {
      btn.setAttribute('data-ready', '1');
      btn.addEventListener('click', function () {
        var input = document.querySelector('.srch input');
        if (input && !input.offsetParent) {
          var t = document.querySelector('button.sidebar-toggle');
          if (t) t.click();
        }
        setTimeout(function () { if (input) input.focus(); }, 150);
      });
    }
    var box = document.querySelector('.markdown-section .home-continue'), last = load(LAST, null);
    if (box && last && isContent(last.route)) {
      box.textContent = '';
      var a = document.createElement('a');
      a.href = '#' + last.route;
      a.textContent = '\u25b6 Continue: ' + last.title;
      box.appendChild(a);
      box.hidden = false;
    }
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
      home();
      seriesBlock();
      startProgress();
      dataButtons();
      setTimeout(dataButtons, 300); // the theme menu is built just after the first page
      mark();
      setTimeout(mark, 300); // Docsify redraws the menu after the page loads
    });
  });
})();

} catch (e) { console.error("reading-history.js", e); }
/* section-links.js */
try {
// A small link button after each h2/h3 heading copies the address of that
// section (#/page?id=section), so "see this part" is one tap to share.
// Shown on hover on desktop, always on touch screens; a short "Copied" note
// confirms it.
(function () {
  var ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.5 1.5"/><path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.5-1.5"/></svg>';

  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var t = document.createElement('textarea');
      t.value = text;
      t.setAttribute('readonly', '');
      t.style.position = 'fixed';
      t.style.opacity = '0';
      document.body.appendChild(t);
      t.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { /* not allowed */ }
      t.remove();
      if (ok) resolve(); else reject(new Error('copy refused'));
    });
  }

  function add() {
    var page = location.hash.split('?')[0] || '#/';
    document.querySelectorAll('.markdown-section h2[id], .markdown-section h3[id]').forEach(function (h) {
      if (h.querySelector('.section-link-copy')) return;
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'section-link-copy';
      b.innerHTML = ICON;
      b.title = 'Copy a link to this section';
      b.setAttribute('aria-label', 'Copy a link to the section ' + h.textContent.trim());
      b.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var url = location.origin + location.pathname + page + '?id=' + encodeURIComponent(h.id);
        b.setAttribute('data-url', url);
        copy(url).then(function () { b.setAttribute('data-note', 'Copied'); },
          function () { b.setAttribute('data-note', 'Could not copy'); })
          .then(function () { setTimeout(function () { b.removeAttribute('data-note'); }, 1600); });
      });
      h.appendChild(b);
    });
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(add);
  });
})();

} catch (e) { console.error("section-links.js", e); }
/* offline.js */
try {
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

} catch (e) { console.error("offline.js", e); }
/* offline-series.js */
try {
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

} catch (e) { console.error("offline-series.js", e); }
/* search.js */
try {
/* Search for the Docsify site, an overlay ("palette"): pages whose title matches, passages inside
 * pages, and code, with filters for type, level and domain. Replaces Docsify's built-in search.
 * Data: .docs/index-titles.json (loaded when the search opens) and .docs/index-body.json (text and
 * code, loaded on the first search for text); both written by stage_site.py, or for a local preview by
 * build_search_index.py --local. Every word must match (stop words are ignored). */
(function () {
  var STOP = 'a an the is are was what how why do does of to in on for and or with it this that'.split(' ');
  var index = null, loading = null, bodyLoading = null, MAX_PAGES = 8, MAX_PASSAGES = 3, MAX_CODE = 8;

  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function hay(p) { p.hay = (p.label + ' ' + p.title + ' ' + p.path.replace(/[-_\/.]/g, ' ')).toLowerCase(); return p; }

  // Titles first (small), the text of the pages on the first search for text.
  var missing = false; // no index files: a local preview that has not built them
  function getJSON(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error('missing ' + url); return r.json(); });
  }
  function build() {
    if (loading) return loading;
    loading = getJSON('./.docs/index-titles.json').then(function (pages) {
      if (!Array.isArray(pages) || !pages.length) throw new Error('empty index');
      pages.forEach(function (p) { p.secs = []; p.code = ''; hay(p); });
      return pages;
    }).catch(function () { missing = true; return []; }).then(function (pages) { index = pages; return pages; });
    return loading;
  }
  function loadBody() {
    if (bodyLoading) return bodyLoading;
    bodyLoading = build().then(function (pages) {
      if (missing) return pages;
      return getJSON('./.docs/index-body.json').then(function (bodies) {
        pages.forEach(function (p) { var b = bodies[p.path]; if (b) { p.secs = b.secs || []; p.code = b.code || ''; } });
        return pages;
      }).catch(function () { bodyLoading = null; return pages; });
    });
    return bodyLoading;
  }

  function terms(q) {
    var all = q.toLowerCase().split(/\s+/).filter(Boolean);
    var kept = all.filter(function (w) { return STOP.indexOf(w) < 0; });
    return kept.length ? kept : all;
  }
  function mark(text, ts) {
    var out = esc(text);
    ts.forEach(function (t) {
      var re = new RegExp('(' + esc(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      out = out.replace(re, '<mark>$1</mark>');
    });
    return out;
  }
  function snippet(s, ts) {
    var text = s.body, low = text.toLowerCase(), at = -1;
    ts.forEach(function (t) { var i = low.indexOf(t); if (i >= 0 && (at < 0 || i < at)) at = i; });
    if (at < 0) return s.body.slice(0, 120);
    var from = Math.max(0, at - 40);
    return (from > 0 ? '…' : '') + text.slice(from, from + 130) + (from + 130 < text.length ? '…' : '');
  }
  function href(p, id) { return '#/' + p.path.replace(/\.md$/, '') + (id ? '?id=' + id : ''); }
  function route(p) { return '/' + p.path.replace(/\.md$/, ''); }
  function nice(s) { return s.replace(/-/g, ' ').replace(/^./, function (c) { return c.toUpperCase(); }); }

  // Filters: one value per kind (type, level, domain); a page without that metadata is hidden while it is set.
  var flt = {type: '', level: '', domain: ''};
  function pageOk(p) {
    if (flt.type && [].concat(p.type || []).indexOf(flt.type) < 0) return false;
    if (flt.level && p.level !== flt.level) return false;
    if (flt.domain && (p.domains || []).indexOf(flt.domain) < 0) return false;
    return true;
  }
  function filtering() { return !!(flt.type || flt.level || flt.domain); }

  function run(q) {
    var ts = terms(q), titleHits = [], passageHits = [], codeHits = [];
    index.forEach(function (p) {
      if (!pageOk(p)) return;
      var all = function (hay) { return ts.every(function (t) { return hay.indexOf(t) >= 0; }); };
      if (all(p.hay + ' ' + (p.tags || []).join(' ').replace(/-/g, ' '))) {
        var l = p.label.toLowerCase();
        titleHits.push({p: p, rank: l === q.toLowerCase() ? 0 : l.indexOf(ts[0]) === 0 ? 1 : 2});
      }
      var found = [];
      p.secs.forEach(function (s) { if (all((s.head + ' ' + s.body).toLowerCase())) found.push(s); });
      if (found.length) {
        found.forEach(function (s) { s.score = all(s.head.toLowerCase()) ? 3 : 1; });
        found.sort(function (a, b) { return b.score - a.score; });
        passageHits.push({p: p, secs: found, score: found.reduce(function (n, s) { return n + s.score; }, 0)});
      }
      if (p.code) {
        var lines = p.code.split('\n').filter(function (ln) { return all(ln.toLowerCase()); });
        if (lines.length) codeHits.push({p: p, lines: lines});
      }
    });
    titleHits.sort(function (a, b) { return a.rank - b.rank || a.p.label.localeCompare(b.p.label); });
    passageHits.sort(function (a, b) { return b.score - a.score || a.p.label.localeCompare(b.p.label); });
    codeHits.sort(function (a, b) { return b.lines.length - a.lines.length || a.p.label.localeCompare(b.p.label); });
    return {ts: ts, titles: titleHits, passages: passageHits, code: codeHits};
  }

  function metaLine(p) {
    var bits = [];
    if (p.level) bits.push(nice(p.level));
    if (p.type) bits.push(nice([].concat(p.type)[0]));
    if (p.min) bits.push(p.min + ' min');
    return bits.join(' · ');
  }
  function pageItem(p, ts) {
    var d = p.desc ? esc(p.desc) + (p.desc.length >= 120 && !/[.!?]$/.test(p.desc) ? '…' : '') : '';
    var m = metaLine(p);
    return '<a class="sp-item" href="' + href(p) + '"><b>' + (ts ? mark(p.label, ts) : esc(p.label)) + '</b>' +
      '<span class="sp-path">' + esc(p.path.replace(/\/[^/]*$/, '') || 'home') + (m ? ' · ' + esc(m) : '') + '</span>' +
      (d ? '<span class="sp-desc">' + d + '</span>' : '') + '</a>';
  }
  function group(name, count, inner) { return '<div class="sp-group"><h3>' + name + '<span>' + count + '</span></h3>' + inner + '</div>'; }

  function render(box, q, res, all) {
    var h = '', ts = res.ts, tl = '';
    res.titles.slice(0, 10).forEach(function (x) { tl += pageItem(x.p, ts); });
    h += group('Pages', res.titles.length, tl || '<p class="sp-none">No page titles match.</p>');
    var inner = '', list = all ? res.passages : res.passages.slice(0, MAX_PAGES);
    list.forEach(function (x) {
      inner += '<div class="sp-page"><span class="sp-page-name">' + esc(x.p.label) + '</span>';
      x.secs.slice(0, MAX_PASSAGES).forEach(function (s) {
        inner += '<a class="sp-item" href="' + href(x.p, s.id) + '"><b>' + mark(s.head || x.p.label, ts) + '</b>' +
          '<span class="sp-desc">' + mark(snippet(s, ts), ts) + '</span></a>';
      });
      if (x.secs.length > MAX_PASSAGES) inner += '<span class="sp-more">+' + (x.secs.length - MAX_PASSAGES) + ' more in this page</span>';
      inner += '</div>';
    });
    if (!all && res.passages.length > MAX_PAGES)
      inner += '<button type="button" class="sp-all">Show ' + (res.passages.length - MAX_PAGES) + ' more pages</button>';
    h += group('Inside pages', res.passages.length + ' pages', inner || '<p class="sp-none">Nothing found inside pages.</p>');
    if (res.code.length) {
      var ci = '';
      res.code.slice(0, MAX_CODE).forEach(function (x) {
        ci += '<a class="sp-item" href="' + href(x.p) + '"><b>' + esc(x.p.label) + '</b>' +
          x.lines.slice(0, 2).map(function (ln) { return '<code class="sp-code">' + mark(ln.trim().slice(0, 140), ts) + '</code>'; }).join('') + '</a>';
      });
      h += group('Code', res.code.length + ' pages', ci);
    }
    box.innerHTML = h;
    var btn = box.querySelector('.sp-all');
    if (btn) btn.addEventListener('click', function () { render(box, q, res, true); });
  }

  function notBuilt(box) {
    box.innerHTML = '<p class="sp-none">The search index is not built. Run <code>python3 .docs/tools/build_search_index.py --local</code> and reload.</p>';
  }
  // Nothing typed: the page read last, recent and saved pages; with a filter set, the pages that match it.
  function readJSON(key, fb) { try { return JSON.parse(localStorage.getItem(key)) || fb; } catch (e) { return fb; } }
  function rest(box) {
    var byRoute = {}, h = '';
    index.forEach(function (p) { byRoute[route(p)] = p; });
    if (filtering()) {
      var ps = index.filter(pageOk).sort(function (a, b) { return a.label.localeCompare(b.label); });
      box.innerHTML = group('Matching pages', ps.length, ps.slice(0, 40).map(function (p) { return pageItem(p); }).join('') ||
        '<p class="sp-none">No page has this combination.</p>');
      return;
    }
    var last = readJSON('acot-last', null), read = readJSON('acot-read', {});
    var recent = Object.keys(read).sort(function (a, b) { return read[b] - read[a]; })
      .filter(function (r) { return byRoute[r] && (!last || last.route !== r); }).slice(0, 5).map(function (r) { return byRoute[r]; });
    var inner = '';
    if (last && byRoute[last.route]) inner += '<p class="sp-lead">Continue where you stopped</p>' + pageItem(byRoute[last.route]);
    if (recent.length) h += group('Recent', recent.length, recent.map(function (p) { return pageItem(p); }).join(''));
    var saved = readJSON('acot-saved', []).filter(function (s) { return byRoute[s.route]; }).slice(0, 8);
    if (saved.length) h += group('Saved', saved.length, saved.map(function (s) { return pageItem(byRoute[s.route]); }).join(''));
    box.innerHTML = inner + h +
      '<p class="sp-hint">Type to search titles, text and code. Every word must match.</p>';
  }

  var ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>';


  var pal = null, opener = null;
  function chipRow(label, key, values) {
    if (!values.length) return null;
    var row = document.createElement('div'); row.className = 'sp-row';
    var l = document.createElement('span'); l.textContent = label; row.appendChild(l);
    values.forEach(function (v) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'sp-chip';
      b.setAttribute('data-key', key); b.setAttribute('data-value', v);
      b.setAttribute('aria-pressed', 'false'); b.textContent = nice(v); row.appendChild(b);
    });
    return row;
  }
  function counted(list) {
    var n = {};
    list.forEach(function (v) { n[v] = (n[v] || 0) + 1; });
    return Object.keys(n).sort(function (a, b) { return n[b] - n[a] || a.localeCompare(b); });
  }
  function buildFilters(host) {
    host.textContent = '';
    var types = [], levels = [], domains = [];
    index.forEach(function (p) { types = types.concat(p.type || []); if (p.level) levels.push(p.level); domains = domains.concat(p.domains || []); });
    var order = ['beginner', 'intermediate', 'advanced'];
    levels = counted(levels).sort(function (a, b) { return order.indexOf(a) - order.indexOf(b); });
    [chipRow('Type', 'type', counted(types)), chipRow('Level', 'level', levels), chipRow('Domain', 'domain', counted(domains))]
      .forEach(function (r) { if (r) host.appendChild(r); });
    host.hidden = !host.children.length;
  }
  function make() {
    var d = document.createElement('div');
    d.id = 'sp'; d.hidden = true; d.setAttribute('role', 'dialog'); d.setAttribute('aria-modal', 'true'); d.setAttribute('aria-label', 'Search');
    d.innerHTML = '<div class="sp-box"><div class="sp-top">' + ICON +
      '<input id="sp-input" type="search" aria-label="Search pages, text and code" placeholder="Search pages, text and code" autocomplete="off" enterkeyhint="search">' +
      '<button type="button" class="sp-close" aria-label="Close search">Esc</button></div>' +
      '<div class="sp-filters" hidden></div><div class="sp-results" aria-live="polite"></div></div>';
    document.body.appendChild(d);
    var input = d.querySelector('#sp-input'), box = d.querySelector('.sp-results'), filters = d.querySelector('.sp-filters'), timer;
    function go() {
      var q = input.value.trim();
      if (!q) { box.innerHTML = '<p class="sp-none">Loading pages…</p>'; build().then(function () { if (!input.value.trim()) { if (missing) notBuilt(box); else rest(box); } }); return; }
      if (!index) box.innerHTML = '<p class="sp-none">Loading pages…</p>';
      build().then(function () {
        if (input.value.trim() !== q) return;
        if (missing) { notBuilt(box); return; }
        render(box, q, run(q), false); // titles now, text as soon as it has loaded
        loadBody().then(function () { if (input.value.trim() === q) render(box, q, run(q), false); });
      });
    }
    d._go = go;
    input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(go, 150); });
    filters.addEventListener('click', function (e) {
      var b = e.target.closest('.sp-chip'); if (!b) return;
      var k = b.getAttribute('data-key'), v = b.getAttribute('data-value');
      flt[k] = flt[k] === v ? '' : v;
      Array.prototype.forEach.call(filters.querySelectorAll('.sp-chip'), function (c) {
        c.setAttribute('aria-pressed', String(flt[c.getAttribute('data-key')] === c.getAttribute('data-value')));
      });
      go();
    });
    d.addEventListener('click', function (e) {
      if (e.target === d || e.target.closest('.sp-close')) close();
      else if (e.target.closest('a')) close(true);
    });
    function items() { return Array.prototype.slice.call(box.querySelectorAll('a.sp-item')); }
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.preventDefault(); close(); return; }
      if (e.key === 'Tab') { // keep focus inside the overlay
        var f = Array.prototype.slice.call(d.querySelectorAll('input,button,a[href]')).filter(function (x) { return x.offsetParent; });
        if (!f.length) return;
        var at = f.indexOf(document.activeElement);
        if (e.shiftKey && at <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
        else if (!e.shiftKey && at === f.length - 1) { e.preventDefault(); f[0].focus(); }
        return;
      }
      var list = items(), at = list.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault(); if (!list.length) return;
        var next = e.key === 'ArrowDown' ? at + 1 : at - 1;
        if (next < 0) input.focus(); else if (next < list.length) list[next].focus();
      } else if (e.key === 'Enter' && document.activeElement === input && list[0]) { e.preventDefault(); list[0].click(); }
    });
    d._filters = filters; d._input = input; d._box = box;
    return d;
  }
  function open() {
    if (!pal) pal = make();
    if (!pal.hidden) return;
    opener = document.activeElement;
    pal.hidden = false;
    document.documentElement.classList.add('sp-lock');
    pal._input.value = '';
    build().then(function () { buildFilters(pal._filters); });
    pal._go();
    pal._input.focus();
  }
  function close(keep) {
    if (!pal || pal.hidden) return;
    pal.hidden = true;
    document.documentElement.classList.remove('sp-lock');
    flt = {type: '', level: '', domain: ''};
    if (!keep && opener && opener.focus && !opener.closest('.srch')) opener.focus();
    else if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
  }
  window.acotSearch = {open: open, close: close};

  function install(hook) {
    // "/" and Ctrl/Cmd+K open the search, unless the reader is typing somewhere.
    document.addEventListener('keydown', function (e) {
      var t = e.target, typing = t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
      var combo = (e.ctrlKey || e.metaKey) && !e.altKey && e.key.toLowerCase() === 'k';
      if (!combo && (typing || e.ctrlKey || e.metaKey || e.altKey || e.key !== '/')) return;
      e.preventDefault();
      open();
    });
    hook.doneEach(function () {
      if (!document.getElementById('search-toggle')) {
        var b = document.createElement('button');
        b.id = 'search-toggle'; b.type = 'button'; b.innerHTML = ICON;
        b.setAttribute('aria-label', 'Search (press /)');
        b.addEventListener('click', open);
        document.body.appendChild(b);
      }
      var side = document.querySelector('.sidebar');
      if (!side || side.querySelector('.srch')) return;
      var box = document.createElement('div');
      box.className = 'srch';
      box.innerHTML = '<input type="search" readonly aria-label="Search" placeholder="Search pages and content" autocomplete="off">';
      side.insertBefore(box, side.querySelector('.sidebar-nav') || side.firstChild);
      // On phones Docsify closes the sidebar on any click that reaches <body>.
      box.addEventListener('click', function (e) { e.stopPropagation(); open(); });
      box.querySelector('input').addEventListener('focus', open);
    });
  }
  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = [].concat(window.$docsify.plugins || [], install);
})();

} catch (e) { console.error("search.js", e); }
