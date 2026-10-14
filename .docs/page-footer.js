// Page footer: "Edit this page" (opens the file on GitHub, on dev) and, on the
// deployed site, "Last updated" from .docs/last-updated.json (written by
// stage_site.py from git history). The homepage, generated pages and the 404
// page get no footer. Without the dates file (local preview) only the edit
// link shows.
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
