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
