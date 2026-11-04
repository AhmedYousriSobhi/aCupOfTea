// Lazy images: every picture in a page except the first is marked
// loading="lazy", so a long page fetches images as the reader scrolls instead
// of all at once (matters on a phone connection). The first image stays eager
// because it is usually on screen at the start. Done on the page's HTML before
// it is inserted, so the browser never starts the early download.
(function () {
  var cfg = window.$docsify = window.$docsify || {};
  cfg.plugins = [].concat(cfg.plugins || [], function (hook) {
    hook.afterEach(function (html) {
      var seen = 0;
      return html.replace(/<img\b(?![^>]*\bloading=)/g, function (tag) {
        seen += 1;
        return seen === 1 ? tag : tag + ' loading="lazy" decoding="async"';
      });
    });
  });
})();
