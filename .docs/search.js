/* Search for the Docsify site, an overlay ("palette"): pages whose title matches, passages inside
 * pages, and code, with filters for type, level and domain. Replaces Docsify's built-in search.
 * Data: .docs/index-titles.json (loaded when the search opens) and .docs/index-body.json (text and
 * code, loaded on the first search for text); both written by stage_site.py. Without them (a local
 * preview) it reads every page in the sidebar. Every word must match (stop words are ignored). */
(function () {
  var STOP = 'a an the is are was what how why do does of to in on for and or with it this that'.split(' ');
  var index = null, loading = null, bodyLoading = null, MAX_PAGES = 8, MAX_PASSAGES = 3, MAX_CODE = 8;

  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function slug(h) {
    var s = h.replace(/<[^>]+>/g, '').toLowerCase().replace(/'/g, '39').trim()
      .replace(/[^\p{L}\p{N}\s_-]/gu, '').replace(/\s+/g, '-');
    return /^\d/.test(s) ? '_' + s : s;
  }
  function plain(s) {
    return s.replace(/!\[[^\]]*\]\([^)]*\)/g, ' ').replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
      .replace(/[`*_>|#]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function crawl() {
    return fetch(typeof window.$docsify.loadSidebar === 'string' ? window.$docsify.loadSidebar : './.docs/_sidebar.md').then(function (r) { return r.text(); }).then(function (side) {
      var pages = [], seen = {};
      side.replace(/\[([^\]]+)\]\(([^)\s]+\.md)\)/g, function (_, label, path) {
        path = path.replace(/^\/+/, '');
        if (!/^https?:/.test(path) && !seen[path]) { seen[path] = 1; pages.push({label: label.replace(/\*\*/g, '').trim(), path: path}); }
      });
      if (!seen['README.md']) pages.unshift({label: 'Home', path: 'README.md'});
      return Promise.all(pages.map(function (p) {
        return fetch('./' + p.path).then(function (r) { return r.ok ? r.text() : ''; }).catch(function () { return ''; })
          .then(function (t) {
            t = t.replace(/^\uFEFF?---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(\r?\n|$)/, '').replace(/<!-- related-block -->[\s\S]*?<\/div>/g, ' ').replace(/```[\s\S]*?```/g, ' ');
            var lines = t.split(/\r?\n/), secs = [], cur = {head: '', id: '', text: []}, h1 = '';
            lines.forEach(function (ln) {
              var m = /^(#{1,3}) +(.+?)\s*#*\s*$/.exec(ln);
              if (m) {
                secs.push(cur);
                if (m[1] === '#' && !h1) h1 = m[2];
                cur = {head: m[2], id: slug(m[2]), text: []};
              } else cur.text.push(ln);
            });
            secs.push(cur);
            p.title = plain(h1 || p.label);
            p.desc = '';
            p.secs = secs.map(function (s) { return {head: plain(s.head), id: s.id, body: plain(s.text.join(' '))}; })
              .filter(function (s) { return (s.head || s.body) && !/^table of contents?$/i.test(s.head); });
            var first = p.secs.filter(function (s) { return s.body.length > 40; })[0];
            if (first) p.desc = first.body.slice(0, 120);
            return hay(p);
          });
      }));
    });
  }  function hay(p) { p.hay = (p.label + ' ' + p.title + ' ' + p.path.replace(/[-_\/.]/g, ' ')).toLowerCase(); return p; }

  // Titles first (small), the text of the pages on the first search for text.
  var crawled = false;
  function getJSON(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error('missing ' + url); return r.json(); });
  }
  function build() {
    if (loading) return loading;
    loading = getJSON('./.docs/index-titles.json').then(function (pages) {
      if (!Array.isArray(pages) || !pages.length) throw new Error('empty index');
      pages.forEach(function (p) { p.secs = []; p.code = ''; hay(p); });
      return pages;
    }).catch(function () { crawled = true; return crawl(); }).then(function (pages) { index = pages; return pages; });
    return loading;
  }
  function loadBody() {
    if (bodyLoading) return bodyLoading;
    bodyLoading = build().then(function (pages) {
      if (crawled) return pages;
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
      if (!q) { box.innerHTML = '<p class="sp-none">Loading pages…</p>'; build().then(function () { if (!input.value.trim()) rest(box); }); return; }
      if (!index) box.innerHTML = '<p class="sp-none">Loading pages…</p>';
      build().then(function () {
        if (input.value.trim() !== q) return;
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
