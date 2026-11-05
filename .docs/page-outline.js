// Page outline: on wide screens a small "On this page" list (h2 and h3) sits
// to the right of the text, with the section being read highlighted. It
// replaces the abandoned docsify-plugin-toc. Narrower screens get the section
// list in the sidebar instead (subMaxLevel in index.html).
(function () {
  var MIN_WIDTH = 1400;
  var observer = null;
  function build() {
    var old = document.querySelector('aside.page-outline');
    if (old) old.remove();
    if (observer) { observer.disconnect(); observer = null; }
    if (window.innerWidth < MIN_WIDTH) return;
    var heads = document.querySelectorAll('.markdown-section h2[id], .markdown-section h3[id]');
    if (heads.length < 2) return;
    var aside = document.createElement('aside');
    aside.className = 'page-outline';
    var title = document.createElement('p');
    title.textContent = 'On this page';
    aside.appendChild(title);
    var links = {};
    Array.prototype.forEach.call(heads, function (h) {
      var a = document.createElement('a');
      a.href = '#' + location.hash.replace(/^#/, '').split('?')[0] + '?id=' + h.id;
      a.textContent = h.textContent.trim();
      a.className = h.tagName === 'H3' ? 'sub' : '';
      aside.appendChild(a);
      links[h.id] = a;
    });
    document.body.appendChild(aside);
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && links[e.target.id]) {
          Object.keys(links).forEach(function (k) { links[k].classList.remove('active'); });
          links[e.target.id].classList.add('active');
        }
      });
    }, { rootMargin: '0px 0px -75% 0px' });
    Array.prototype.forEach.call(heads, function (h) { observer.observe(h); });
  }
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(build);
  });
})();
