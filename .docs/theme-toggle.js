// Themes. A button at the top of the page opens a small list: Auto (follow the
// device), Light, Sepia, Dark, Midnight and Black. The choice is remembered in
// the browser; with none yet, the device setting picks Light or Dark.
// Docsify 5 ships a dark stylesheet (#dark-css in index.html); this script
// switches it on for the dark themes. Each theme's colours live in index.html
// under html[data-theme="..."]; data-mode ("light" or "dark") marks the family
// so rules shared by all dark themes (code colour, diagrams) stay in one place.
// The same menu has a text size row (four sizes, remembered like the theme;
// html[data-size] sets --font-size in index.html).
// Loaded in <head> so the right theme is on screen from the first paint.
(function () {
  var KEY = 'aCupOfTea-theme';
  var SIZE_KEY = 'aCupOfTea-size';
  var SIZES = [
    { id: 's', label: 'Small text', px: 13 },
    { id: 'm', label: 'Normal text', px: 15 },
    { id: 'l', label: 'Large text', px: 17 },
    { id: 'xl', label: 'Extra large text', px: 19 }
  ];
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
  function stored(key) {
    try { return localStorage.getItem(key || KEY); } catch (e) { return null; }
  }
  function save(id, key) {
    try { if (id) localStorage.setItem(key || KEY, id); else localStorage.removeItem(key || KEY); } catch (e) { /* private mode: still switches */ }
  }
  function size() {
    var s = stored(SIZE_KEY);
    return /^(s|l|xl)$/.test(s || '') ? s : 'm';
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
    if (size() === 'm') root.removeAttribute('data-size'); else root.setAttribute('data-size', size());
    var css = document.getElementById('dark-css');
    if (css) css.disabled = theme.mode !== 'dark';
    var items = document.querySelectorAll('#theme-menu [data-choice]');
    Array.prototype.forEach.call(items, function (el) {
      el.setAttribute('aria-checked', el.getAttribute('data-choice') === chosen() ? 'true' : 'false');
    });
    Array.prototype.forEach.call(document.querySelectorAll('#theme-menu [data-size]'), function (el) {
      el.setAttribute('aria-checked', el.getAttribute('data-size') === size() ? 'true' : 'false');
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
    btn.setAttribute('aria-label', 'Theme and text size');
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

    var row = document.createElement('div');
    row.className = 'size-row';
    row.setAttribute('role', 'group');
    row.setAttribute('aria-label', 'Text size');
    var label = document.createElement('span');
    label.textContent = 'Text';
    row.appendChild(label);
    SIZES.forEach(function (z) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('role', 'menuitemradio');
      b.setAttribute('data-size', z.id);
      b.setAttribute('aria-label', z.label);
      b.title = z.label;
      b.textContent = 'A';
      b.style.fontSize = z.px + 'px';
      // stays open, so a reader can try the sizes one after another
      b.addEventListener('click', function () { save(z.id === 'm' ? null : z.id, SIZE_KEY); apply(); });
      row.appendChild(b);
    });
    menu.appendChild(row);

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
