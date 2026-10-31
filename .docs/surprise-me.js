// "Surprise me": a link at the top of the side menu that opens a random
// content page from the menu (not a folder index, not a generated page, not
// the page already open). Good for a coffee break, and resurfaces old pages.
(function () {
  function pages() {
    var seen = {};
    return Array.prototype.map.call(document.querySelectorAll('.sidebar-nav a[href^="#/"]'), function (a) {
      return a.getAttribute('href').split('?')[0];
    }).filter(function (h) {
      if (seen[h] || /\/README(\.md)?$|^#\/$|^#\/\.docs\//.test(h)) return false;
      seen[h] = true;
      return true;
    });
  }

  function go(e) {
    e.preventDefault();
    var here = location.hash.split('?')[0];
    var list = pages().filter(function (h) { return h !== here; });
    if (list.length) location.hash = list[Math.floor(Math.random() * list.length)].slice(1);
  }

  function add() {
    var nav = document.querySelector('.sidebar-nav');
    if (!nav || document.getElementById('surprise-me')) return;
    var a = document.createElement('a');
    a.id = 'surprise-me';
    a.href = '#/';
    a.textContent = '🎲 Surprise me';
    a.title = 'Open a random page';
    a.addEventListener('click', go);
    nav.parentNode.insertBefore(a, nav);
  }

  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(add);
  });
})();
