// Light/dark theme. Docsify 5 ships a dark stylesheet (#dark-css in index.html)
// that this script switches on and off. The choice is remembered in the
// browser; with no choice yet the device setting decides. Loaded in <head> so
// the right theme is on screen from the first paint.
(function () {
  var KEY = 'aCupOfTea-theme';
  var root = document.documentElement;
  var SUN = '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function systemDark() {
    return !!(window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
  }
  function current() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }
  function apply(theme) {
    root.setAttribute('data-theme', theme);
    var css = document.getElementById('dark-css');
    if (css) css.disabled = theme !== 'dark';
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.innerHTML = theme === 'dark' ? SUN : MOON;
      btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to the light theme' : 'Switch to the dark theme');
    }
  }
  function addButton() {
    var host = document.querySelector('main > .content');
    if (!host || document.getElementById('theme-toggle')) return;
    var btn = document.createElement('button');
    btn.id = 'theme-toggle';
    btn.type = 'button';
    btn.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(KEY, next); } catch (e) { /* private mode: still switches */ }
      apply(next);
    });
    host.appendChild(btn);
    apply(current());
  }

  apply(stored() || (systemDark() ? 'dark' : 'light'));
  if (window.matchMedia) {
    var mq = matchMedia('(prefers-color-scheme: dark)');
    var follow = function (e) { if (!stored()) apply(e.matches ? 'dark' : 'light'); };
    if (mq.addEventListener) mq.addEventListener('change', follow);
  }
  window.themeToggle = function (hook) { hook.ready(addButton); };
})();
