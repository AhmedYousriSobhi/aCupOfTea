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
  function decorate() {
    Array.prototype.forEach.call(groups(), function (li) {
      var sub = li.querySelector(':scope > ul:not(.app-sub-sidebar)');
      if (!sub) return;
      li.classList.add('group');
      var holdsActive = !!li.querySelector('li.active');
      li.classList.toggle('collapsed', !(holdsActive || open[label(li)]));
    });
  }
  document.addEventListener('click', function (e) {
    var li = e.target.closest && e.target.closest('.sidebar-nav li.group');
    if (!li || e.target.closest('li.group > ul')) return;
    if (e.target.closest('a[href]')) return;
    li.classList.toggle('collapsed');
    open[label(li)] = !li.classList.contains('collapsed');
  });
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.doneEach(decorate);
  });
})();
