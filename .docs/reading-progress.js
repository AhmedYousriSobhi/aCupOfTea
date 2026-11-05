// Long pages: a thin bar at the top shows how far you have read, and a
// back-to-top button appears after scrolling a screen and a half. Both stay
// hidden on pages shorter than two screens. Smooth scrolling is skipped for
// readers who ask for reduced motion.
(function () {
  var bar, top;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');

  function update() {
    if (!bar) return;
    var doc = document.documentElement;
    var room = doc.scrollHeight - window.innerHeight;
    var y = window.scrollY || doc.scrollTop;
    var long = room > window.innerHeight;
    bar.hidden = !long;
    bar.style.transform = 'scaleX(' + (long ? Math.min(1, y / room) : 0) + ')';
    top.hidden = !(long && y > window.innerHeight * 1.5);
  }

  function build() {
    bar = document.createElement('div');
    bar.id = 'read-progress';
    bar.setAttribute('aria-hidden', 'true');
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
