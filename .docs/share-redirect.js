// Share pages (/folder/page/, written by share_pages.py on the deployed site)
// carry the page as plain HTML for link previews, crawlers and readers without
// JavaScript. A reader with JavaScript goes straight on to the real page
// (/#/folder/page), where Docsify draws it: this runs in <head>, before the
// static copy is painted, and replaces the history entry, so Back does not
// return to the share page. A section in the address (#name) is kept as ?id=.
// A file, not an inline script: the site's Content-Security-Policy forbids those.
(function () {
  var s = document.currentScript;
  var target = s && s.getAttribute('data-target');
  if (!target) return;
  var section = location.hash.replace(/^#/, '');
  if (section && section.charAt(0) !== '/') target += '?id=' + section;
  document.documentElement.hidden = true;
  location.replace(target);
})();
