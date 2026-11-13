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
