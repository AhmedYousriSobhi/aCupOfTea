// Themes. A button at the top of the page opens a small list: Auto (follow the
// device), Light, Sepia, Dark, Midnight and Black. The choice is remembered in
// the browser; with none yet, the device setting picks Light or Dark.
// Docsify 5 ships a dark stylesheet (#dark-css in index.html); this script
// switches it on for the dark themes. Each theme's colours live in index.html
// under html[data-theme="..."]; data-mode ("light" or "dark") marks the family
// so rules shared by all dark themes (code colour, diagrams) stay in one place.
// Loaded in <head> so the right theme is on screen from the first paint.
(function () {
  var KEY = 'aCupOfTea-theme';
  var root = document.documentElement;
  var THEMES = [
    { id: 'light',    label: 'Light',    mode: 'light', bg: '#ffffff', fg: '#34495e' },
    { id: 'sepia',    label: 'Sepia',    mode: 'light', bg: '#f4ecd8', fg: '#3b2f20' },
    { id: 'dark',     label: 'Dark',     mode: 'dark',  bg: '#16181c', fg: '#d3d6da' },
    { id: 'midnight', label: 'Midnight', mode: 'dark',  bg: '#091a28', fg: '#c4ccd3' },
    { id: 'black',    label: 'Black',    mode: 'dark',  bg: '#000000', fg: '#d4d4d4' }
  ];
  var ICON = '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 3v18" /><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/></svg>';

  function find(id) {
    for (var i = 0; i < THEMES.length; i++) if (THEMES[i].id === id) return THEMES[i];
    return null;
  }
  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function save(id) {
    try { if (id) localStorage.setItem(KEY, id); else localStorage.removeItem(KEY); } catch (e) { /* private mode: still switches */ }
  }
  function systemDark() {
    return !!(window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
  }
  function chosen() {
    var s = stored();
    return find(s) ? s : 'auto';
  }
  function resolve(choice) {
    if (choice === 'auto') return systemDark() ? 'dark' : 'light';
    return choice;
  }
  function apply() {
    var theme = find(resolve(chosen()));
    root.setAttribute('data-theme', theme.id);
    root.setAttribute('data-mode', theme.mode);
    var css = document.getElementById('dark-css');
    if (css) css.disabled = theme.mode !== 'dark';
    var items = document.querySelectorAll('#theme-menu [data-choice]');
    Array.prototype.forEach.call(items, function (el) {
      el.setAttribute('aria-checked', el.getAttribute('data-choice') === chosen() ? 'true' : 'false');
    });
  }
  function closeMenu() {
    var menu = document.getElementById('theme-menu');
    var btn = document.getElementById('theme-toggle');
    if (menu) menu.hidden = true;
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }
  function choose(choice) {
    save(choice === 'auto' ? null : choice);
    apply();
    closeMenu();
  }
  function addButton() {
    var host = document.querySelector('main > .content');
    if (!host || document.getElementById('theme-toggle')) return;
    var btn = document.createElement('button');
    btn.id = 'theme-toggle';
    btn.type = 'button';
    btn.innerHTML = ICON;
    btn.setAttribute('aria-label', 'Choose a theme');
    btn.setAttribute('aria-haspopup', 'true');
    btn.setAttribute('aria-expanded', 'false');

    var menu = document.createElement('div');
    menu.id = 'theme-menu';
    menu.setAttribute('role', 'menu');
    menu.hidden = true;
    [{ id: 'auto', label: 'Auto (device)', bg: 'linear-gradient(90deg,#fff 50%,#16181c 50%)' }].concat(THEMES).forEach(function (t) {
      var item = document.createElement('button');
      item.type = 'button';
      item.setAttribute('role', 'menuitemradio');
      item.setAttribute('data-choice', t.id);
      var sw = document.createElement('span');
      sw.className = 'swatch';
      sw.style.background = t.bg;
      item.appendChild(sw);
      item.appendChild(document.createTextNode(t.label));
      item.addEventListener('click', function () { choose(t.id); });
      menu.appendChild(item);
    });

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = menu.hidden;
      menu.hidden = !open;
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', function (e) {
      if (!menu.hidden && !menu.contains(e.target)) closeMenu();
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
    host.appendChild(btn);
    host.appendChild(menu);
    apply();
  }

  apply();
  if (window.matchMedia) {
    var mq = matchMedia('(prefers-color-scheme: dark)');
    var follow = function () { if (chosen() === 'auto') apply(); };
    if (mq.addEventListener) mq.addEventListener('change', follow);
  }
  window.themeToggle = function (hook) { hook.ready(addButton); };
})();
