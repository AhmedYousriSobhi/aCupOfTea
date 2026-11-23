// Long pages: a thin bar at the top shows how far you have read, and a
// back-to-top button appears after scrolling a screen and a half. Both stay
// hidden on pages shorter than two screens. Smooth scrolling is skipped for
// readers who ask for reduced motion.
// The bar has two colours: green while you read the page itself, and a muted
// one for the blocks added at the end ("See also", "Mentioned in", the page
// footer), which are fine to skip. Green reaches 100% when the last line of the
// page is at the bottom of the screen, so the bar shows the real reading progress.
(function () {
  var bar, main, extra, top;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');

  // document y of the first appended block (end of the page text), or null
  function endOfText() {
    var el = document.querySelector('.markdown-section .see-also, .markdown-section .mentioned-in, .page-footer');
    return el ? el.getBoundingClientRect().top + (window.scrollY || document.documentElement.scrollTop) : null;
  }

  function update() {
    if (!bar) return;
    var doc = document.documentElement;
    var room = doc.scrollHeight - window.innerHeight;
    var y = window.scrollY || doc.scrollTop;
    var long = room > window.innerHeight;
    bar.hidden = !long;
    // scroll position at which the page text ends at the bottom of the screen
    var end = endOfText();
    var edge = end === null ? room : Math.max(0, Math.min(room, end - window.innerHeight));
    var cut = long ? edge / room : 1;
    var at = long ? Math.min(1, y / room) : 0;
    main.style.width = Math.min(at, cut) * 100 + '%';
    extra.style.left = cut * 100 + '%';
    extra.style.width = Math.max(0, at - cut) * 100 + '%';
    top.hidden = !(long && y > window.innerHeight * 1.5);
  }

  function build() {
    bar = document.createElement('div');
    bar.id = 'read-progress';
    bar.setAttribute('aria-hidden', 'true');
    main = document.createElement('span');
    main.className = 'read-main';
    extra = document.createElement('span');
    extra.className = 'read-extra';
    bar.appendChild(main);
    bar.appendChild(extra);
    top = document.createElement('button');
    top.id = 'back-to-top';
    top.type = 'button';
    top.title = 'Back to top';
    top.setAttribute('aria-label', 'Back to top');
    top.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M6 15l6-6 6 6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    top.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: still.matches ? 'auto' : 'smooth' });
    });
    document.body.appendChild(bar);
    document.body.appendChild(top);
    window.addEventListener('scroll', function () { window.requestAnimationFrame(update); }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.ready(build);
    // images load late and make the page longer, so measure again shortly after
    hook.doneEach(function () { update(); setTimeout(update, 800); });
  });
})();
