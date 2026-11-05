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
