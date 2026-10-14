// Heavy libraries load only on pages that need them: Mermaid (about 1.5 MB) for
// a page with a ```mermaid block, KaTeX for a page with a $$ formula line
// (.docs/math.js marks those). Versions stay pinned here, like in index.html.
(function () {
  var LIBS = {
    mermaid: {
      js: 'https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js',
    },
    katex: {
      css: 'https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.css',
      js: 'https://cdn.jsdelivr.net/npm/katex@0.19.0/dist/katex.min.js',
    },
  };
  var loading = {};

  // Loads a library once and resolves when its script has run.
  function load(name) {
    if (loading[name]) return loading[name];
    var lib = LIBS[name];
    loading[name] = new Promise(function (resolve, reject) {
      if (lib.css) {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = lib.css;
        if (lib.cssIntegrity) { link.integrity = lib.cssIntegrity; link.crossOrigin = 'anonymous'; }
        document.head.appendChild(link);
      }
      var s = document.createElement('script');
      s.src = lib.js;
      if (lib.integrity) { s.integrity = lib.integrity; s.crossOrigin = 'anonymous'; }
      s.onload = resolve;
      s.onerror = function () { delete loading[name]; reject(new Error('could not load ' + name)); };
      document.head.appendChild(s);
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
