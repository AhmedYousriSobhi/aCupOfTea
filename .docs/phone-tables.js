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
