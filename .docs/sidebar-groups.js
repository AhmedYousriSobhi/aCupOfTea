// Sidebar groups: the folders in the menu open and close with a tap, and the
// group that holds the page being read starts open. It replaces the abandoned
// docsify-sidebar-collapse. The open groups are remembered while you browse,
// because Docsify redraws the menu on every page.
(function () {
  var open = {};
  function label(li) {
    var head = li.firstElementChild;
    return head ? head.textContent.trim() : '';
  }
  function groups() {
    return document.querySelectorAll('.sidebar-nav li');
  }
  // The page being read, as a sidebar link: matched by route, not by the
  // "active" class, which Docsify sets late (and not for pages reached from the
  // search results or a link inside another page).
  function currentLink() {
    var path = decodeURIComponent(location.hash.replace(/^#/, '').split('?')[0]).replace(/\.md$/, '');
    var wanted = [path, path.replace(/\/$/, '') + '/README'];
    var links = document.querySelectorAll('.sidebar-nav a.page-link, .sidebar-nav a[href^="#/"]');
    for (var i = 0; i < links.length; i++) {
      var h = decodeURIComponent((links[i].getAttribute('href') || '').replace(/^#/, '').split('?')[0]).replace(/\.md$/, '');
      if (wanted.indexOf(h) !== -1) return links[i];
    }
    return null;
  }
  function decorate() {
    var here = currentLink();
    // mark the page being read ourselves (Docsify's own "active" mark comes late or not at all)
    Array.prototype.forEach.call(document.querySelectorAll('.sidebar-nav a.here'), function (a) {
      if (a !== here) a.classList.remove('here');
    });
    if (here) here.classList.add('here');
    Array.prototype.forEach.call(groups(), function (li) {
      var sub = li.querySelector(':scope > ul:not(.app-sub-sidebar)');
      if (!sub) return;
      li.classList.add('group');
      var holdsActive = !!li.querySelector('li.active') || (!!here && li.contains(here));
      li.classList.toggle('collapsed', !(holdsActive || open[label(li)]));
    });
    return here;
  }
  // Show where the page is: open its folders and bring its entry into view.
  function reveal() {
    var here = decorate();
    var side = document.querySelector('aside.sidebar');
    if (here && side && side.scrollHeight > side.clientHeight) {
      var box = here.getBoundingClientRect(), sb = side.getBoundingClientRect();
      if (box.top < sb.top + 60 || box.bottom > sb.bottom - 20) {
        side.scrollTop += box.top - sb.top - sb.height / 3;
      }
    }
  }
  // opening the menu (on a phone it was closed when the page changed) brings the entry into view again
  function watchSidebar() {
    var side = document.querySelector('aside.sidebar');
    if (!side || side.__groupsWatched) return;
    side.__groupsWatched = true;
    new MutationObserver(function () { if (side.classList.contains('show')) setTimeout(reveal, 260); })
      .observe(side, { attributes: true, attributeFilter: ['class'] });
  }
  window.addEventListener('hashchange', function () {
    setTimeout(reveal, 50);
    setTimeout(reveal, 400); // Docsify redraws the menu after the page loads
  });
  document.addEventListener('click', function (e) {
    var li = e.target.closest && e.target.closest('.sidebar-nav li.group');
    if (!li) return;
    // a click inside this folder's own list belongs to its entries; a folder's label inside another folder's list still toggles
    var list = e.target.closest('ul');
    if (list && li.contains(list)) return;
    if (e.target.closest('a[href]')) return;
    li.classList.toggle('collapsed');
    open[label(li)] = !li.classList.contains('collapsed');
  });
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(function () { watchSidebar(); reveal(); setTimeout(reveal, 300); });
  });
})();
