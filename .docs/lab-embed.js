// Embedded labs: a link written as [text](/folder/labs/name.html#embed ':ignore') becomes an inline
// frame under the text, so the reader uses the lab without leaving the page. The link stays in a
// caption ("Open full screen"), and GitHub or a reader without scripts still sees the plain link.
//
// Security, in layers (see the policy in index.html):
//  - only a path of the form <folders>/labs/<name>.html is ever framed (allowlist below), resolved
//    against this site's own address, so no other URL can become a frame;
//  - the frame is sandboxed with allow-scripts only (no allow-same-origin): the lab gets an opaque
//    origin and cannot read this page, its storage or its cookies, and it cannot navigate the top
//    page, open popups or submit forms;
//  - the lab page carries its own strict policy (no inline scripts, nothing but its own files);
//  - messages are accepted only from a frame this script created, with origin "null" (a sandboxed
//    frame), and the one number in them (the height) is clamped. Nothing from a message is ever put
//    into the page as HTML.
(function () {
  'use strict';
  var PATH = /^[a-z0-9][a-z0-9\/-]*\/labs\/[a-z0-9-]+\.html$/;
  var MIN = 240, MAX = 3000;
  var live = [];

  function siteBase() { return location.href.split('#')[0].split('?')[0].replace(/[^/]*$/, ''); }
  function mode() { return document.documentElement.getAttribute('data-mode') === 'dark' ? 'dark' : 'light'; }

  // the lab's address when the link is an allowed one, else null
  function labUrl(a) {
    var m = /^\/?([^?#]+\.html)#embed$/.exec(a.getAttribute('href') || '');
    if (!m || !PATH.test(m[1])) return null;
    var u = new URL(siteBase() + m[1]);
    return u.origin === location.origin ? u : null;
  }

  function build(url, label) {
    var fig = document.createElement('figure');
    fig.className = 'lab-embed';
    var f = document.createElement('iframe');
    f.setAttribute('sandbox', 'allow-scripts'); // before src, so the frame is never loaded unsandboxed
    f.setAttribute('referrerpolicy', 'no-referrer');
    f.setAttribute('loading', 'lazy');
    f.setAttribute('title', label + ' (interactive lab)');
    f.style.height = '520px';
    f.src = url.href + '?embed=1&theme=' + mode();
    var cap = document.createElement('figcaption');
    var open = document.createElement('a');
    open.href = url.href;
    open.target = '_blank';
    open.rel = 'noopener noreferrer';
    open.textContent = 'Open full screen';
    cap.appendChild(document.createTextNode(label + ' · '));
    cap.appendChild(open);
    fig.appendChild(f);
    fig.appendChild(cap);
    live.push(f);
    return fig;
  }

  function scan() {
    live = live.filter(function (f) { return f.isConnected; });
    var section = document.querySelector('.markdown-section');
    if (!section) return;
    fixLinks(section);
    Array.prototype.forEach.call(section.querySelectorAll('a[href$="#embed"]'), function (a) {
      if (a.getAttribute('data-embedded')) return;
      var url = labUrl(a);
      if (!url) return;
      a.setAttribute('data-embedded', '1');
      var fig = build(url, a.textContent.trim() || 'Lab');
      var block = a.closest('p, li') || a;
      if (block !== a && block.textContent.trim() === a.textContent.trim()) block.replaceWith(fig);
      else block.after(fig);
    });
  }

  // a plain link to a lab page (":ignore" keeps it root-absolute, which misses the site's folder
  // on GitHub Pages): point it at the same allowed address under this site and open it in a new tab
  function fixLinks(section) {
    Array.prototype.forEach.call(section.querySelectorAll('a[href$=".html"]'), function (a) {
      var m = /^\/([^?#]+\.html)$/.exec(a.getAttribute('href') || '');
      if (!m || !PATH.test(m[1])) return;
      a.setAttribute('href', siteBase() + m[1]);
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'noopener noreferrer');
    });
  }

  window.addEventListener('message', function (e) {
    var d = e.data;
    if (e.origin !== 'null' || !d || typeof d !== 'object' || d.type !== 'lab-height') return;
    live.forEach(function (f) {
      if (e.source !== f.contentWindow) return;
      var h = Number(d.h);
      if (isFinite(h)) f.style.height = Math.min(MAX, Math.max(MIN, Math.ceil(h))) + 'px';
    });
  });

  // keep the frames in step with the site's theme (the sandboxed origin "null" can only be reached with "*")
  if (window.MutationObserver) {
    new MutationObserver(function () {
      live.forEach(function (f) { if (f.contentWindow) f.contentWindow.postMessage({ type: 'lab-theme', theme: mode() }, '*'); });
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-mode'] });
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) { hook.doneEach(scan); });
})();
