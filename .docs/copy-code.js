// A small icon button in the top-right corner of every code block copies its
// text (replaces the docsify-copy-code plugin). Quiet until the block is
// hovered or focused, always visible on touch screens; the icon turns into a
// check mark with a short note ("Copied" / "Could not copy").
(function () {
  var COPY = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
  var DONE = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';

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
    document.querySelectorAll('.markdown-section pre[data-lang] > code').forEach(function (code) {
      var pre = code.parentNode;
      if (pre.querySelector('.code-copy') || pre.getAttribute('data-lang') === 'mermaid') return;
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'code-copy';
      b.innerHTML = COPY;
      b.title = 'Copy code';
      b.setAttribute('aria-label', 'Copy this code block');
      var timer;
      b.addEventListener('click', function () {
        copy(code.textContent.replace(/\n$/, '')).then(function () {
          b.setAttribute('data-note', 'Copied');
          b.innerHTML = DONE;
        }, function () {
          b.setAttribute('data-note', 'Could not copy');
        }).then(function () {
          clearTimeout(timer);
          timer = setTimeout(function () { b.removeAttribute('data-note'); b.innerHTML = COPY; }, 1600);
        });
      });
      pre.appendChild(b);
    });
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(add);
  });
})();
