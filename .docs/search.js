/* Two-group search for the Docsify site: pages whose title matches, then
 * passages inside pages that match. Replaces Docsify's built-in search.
 * It reads the pages listed in the generated sidebar, so new pages are
 * searchable automatically. Every word must match (stop words are ignored). */
(function () {
  var STOP = 'a an the is are was what how why do does of to in on for and or with it this that'.split(' ');
  var index = null, loading = null, MAX_PAGES = 8, MAX_PASSAGES = 3;

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
        if (!/^https?:/.test(path) && !seen[path]) { seen[path] = 1; pages.push({label: label, path: path}); }
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
  }
  function hay(p) { p.hay = (p.label + ' ' + p.title + ' ' + p.path.replace(/[-_\/.]/g, ' ')).toLowerCase(); return p; }
  // The deployed site ships one prebuilt file (see .docs/tools/build_search_index.py).
  // A local preview has none, so fall back to reading every page.
  function prebuilt() {
    return fetch('./.docs/search-index.json').then(function (r) {
      if (!r.ok) throw new Error('no prebuilt index');
      return r.json();
    }).then(function (pages) {
      if (!Array.isArray(pages) || !pages.length) throw new Error('empty prebuilt index');
      return pages.map(hay);
    });
  }
  function build() {
    if (loading) return loading;
    loading = prebuilt().catch(crawl).then(function (pages) { index = pages; return pages; });
    return loading;
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
    return (from > 0 ? '\u2026' : '') + text.slice(from, from + 130) + (from + 130 < text.length ? '\u2026' : '');
  }
  function href(p, id) { return '#/' + p.path.replace(/\.md$/, '') + (id ? '?id=' + id : ''); }

  function run(q) {
    var ts = terms(q), titleHits = [], passageHits = [];
    index.forEach(function (p) {
      var all = function (hay) { return ts.every(function (t) { return hay.indexOf(t) >= 0; }); };
      if (all(p.hay)) {
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
    });
    titleHits.sort(function (a, b) { return a.rank - b.rank || a.p.label.localeCompare(b.p.label); });
    passageHits.sort(function (a, b) { return b.score - a.score || a.p.label.localeCompare(b.p.label); });
    return {ts: ts, titles: titleHits, passages: passageHits};
  }
  function render(panel, q, res, all) {
    var h = '';
    h += '<div class="srch-group"><h3>Pages<span>' + res.titles.length + '</span></h3>';
    if (!res.titles.length) h += '<p class="srch-none">No page titles match.</p>';
    res.titles.slice(0, 10).forEach(function (x) {
      h += '<a class="srch-item" href="' + href(x.p) + '"><b>' + mark(x.p.label, res.ts) + '</b>' +
           '<span class="srch-path">' + esc(x.p.path.replace(/\/[^/]*$/, '') || 'home') + '</span>' +
           (x.p.desc ? '<span class="srch-desc">' + esc(x.p.desc) + '\u2026</span>' : '') + '</a>';
    });
    h += '</div><div class="srch-group"><h3>Inside pages<span>' + res.passages.length + ' pages</span></h3>';
    if (!res.passages.length) h += '<p class="srch-none">Nothing found inside pages.</p>';
    var list = all ? res.passages : res.passages.slice(0, MAX_PAGES);
    list.forEach(function (x) {
      h += '<div class="srch-page"><span class="srch-page-name">' + esc(x.p.label) + '</span>';
      x.secs.slice(0, MAX_PASSAGES).forEach(function (s) {
        h += '<a class="srch-item" href="' + href(x.p, s.id) + '"><b>' + mark(s.head || x.p.label, res.ts) + '</b>' +
             '<span class="srch-desc">' + mark(snippet(s, res.ts), res.ts) + '</span></a>';
      });
      if (x.secs.length > MAX_PASSAGES) h += '<span class="srch-more">+' + (x.secs.length - MAX_PASSAGES) + ' more in this page</span>';
      h += '</div>';
    });
    if (!all && res.passages.length > MAX_PAGES)
      h += '<button type="button" class="srch-all">Show ' + (res.passages.length - MAX_PAGES) + ' more pages</button>';
    h += '</div>';
    panel.innerHTML = h;
    var btn = panel.querySelector('.srch-all');
    if (btn) btn.addEventListener('click', function () { render(panel, q, res, true); });
  }

  var ICON = "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2.2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-3.5-3.5'/%3E%3C/svg%3E\")";
  var css = '.srch{padding:.4rem 15px .6rem}' +
    '.srch input{box-sizing:border-box;width:100%;margin:0;padding:.65rem .8rem .65rem 2.4rem;font:inherit;font-size:16px;' +
      'color:inherit;background:rgba(128,128,128,.1) ' + ICON + ' no-repeat .8rem 50%;' +
      'border:1px solid rgba(128,128,128,.3);border-radius:.7rem;outline:none;-webkit-appearance:none;appearance:none}' +
    '.srch input::placeholder{color:inherit;opacity:.55}' +
    '.srch input:focus{border-color:var(--theme-color,#42b983);box-shadow:0 0 0 3px rgba(66,185,131,.2)}' +
    '.srch-panel{display:none;max-height:calc(100vh - 9rem);overflow:auto;margin-top:.5rem;text-align:left;-webkit-overflow-scrolling:touch}' +
    '.srch-panel.show{display:block}' +
    '.srch-group h3{display:flex;justify-content:space-between;font-size:.7rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin:1rem 0 .35rem;opacity:.7}' +
    '.srch-group h3 span{font-weight:400}' +
    '.srch-item{display:block;padding:.5rem .6rem;margin:0 -.6rem;border-radius:.5rem;color:inherit;text-decoration:none}' +
    '.srch-item:hover,.srch-item:focus{background:rgba(128,128,128,.14)}' +
    '.srch-item b{display:block;font-weight:600;line-height:1.3;color:var(--theme-color,#42b983)}' +
    '.srch-path,.srch-desc,.srch-more,.srch-none{display:block;font-size:.8rem;line-height:1.45;opacity:.78;overflow-wrap:anywhere}' +
    '.srch-path{font-size:.72rem;opacity:.55;margin-top:.1rem}' +
    '.srch-none{padding:.3rem 0;font-style:italic}' +
    '.srch-page-name{display:block;font-size:.72rem;font-weight:600;opacity:.6;margin:.8rem 0 .15rem;overflow-wrap:anywhere}' +
    '.srch-more{padding-left:.6rem;opacity:.55}' +
    '.srch-all{width:100%;margin:.7rem 0;padding:.55rem;font:inherit;font-size:.85rem;color:inherit;cursor:pointer;background:rgba(128,128,128,.1);border:1px solid rgba(128,128,128,.3);border-radius:.6rem}' +
    '.srch mark,.srch-panel mark{background:rgba(201,166,107,.4);color:inherit;border-radius:2px;padding:0 1px}' +
    '.sidebar.srch-open .sidebar-nav{display:none}';

  function install(hook) {
    hook.mounted(function () {
      var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    });
    hook.doneEach(function () {
      var side = document.querySelector('.sidebar');
      if (!side || side.querySelector('.srch')) return;
      var box = document.createElement('div');
      box.className = 'srch';
      box.innerHTML = '<input type="search" aria-label="Search" placeholder="Search pages and content" autocomplete="off" enterkeyhint="search"><div class="srch-panel"></div>';
      side.insertBefore(box, side.querySelector('.sidebar-nav') || side.firstChild);
      var input = box.querySelector('input'), panel = box.querySelector('.srch-panel'), timer;
      function go() {
        var q = input.value.trim();
        if (!q) { panel.classList.remove('show'); side.classList.remove('srch-open'); panel.innerHTML = ''; return; }
        panel.classList.add('show'); side.classList.add('srch-open');
        if (!index) panel.innerHTML = '<p class="srch-none">Loading pages\u2026</p>';
        build().then(function () { if (input.value.trim() === q) render(panel, q, run(q), false); });
      }
      // On phones Docsify closes the sidebar on any click that reaches <body>;
      // keep taps on the search box here, but let result links through so
      // choosing a result still closes the sidebar.
      box.addEventListener('click', function (e) { if (!e.target.closest('a')) e.stopPropagation(); });
      input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(go, 150); });
      input.addEventListener('focus', function () { build(); });
      input.addEventListener('keydown', function (e) { if (e.key === 'Escape') { input.value = ''; go(); } });
      panel.addEventListener('click', function (e) { if (e.target.closest('a')) { input.value = ''; panel.classList.remove('show'); side.classList.remove('srch-open'); panel.innerHTML = ''; } });
    });
  }
  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = [].concat(window.$docsify.plugins || [], install);
})();
