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
