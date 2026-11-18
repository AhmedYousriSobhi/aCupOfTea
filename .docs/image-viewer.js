/* Phone image viewer. On narrow screens Docsify's zoom only grows a picture to
 * the screen width, which does nothing for a wide chart. Tapping a picture here
 * opens it large in a full-screen layer you can pan and pinch.
 * Desktop keeps Docsify's own zoom (zoom-image plugin). */
(function () {
  var PHONE = '(max-width: 768px)';
  var layer = null;

  function close() {
    if (!layer) return;
    layer.remove();
    layer = null;
    document.documentElement.style.overflow = '';
  }

  function open(src, alt, naturalWidth) {
    close();
    layer = document.createElement('div');
    layer.setAttribute('role', 'dialog');
    layer.setAttribute('aria-label', alt || 'Image');
    layer.style.cssText = 'position:fixed;inset:0;z-index:100000;overflow:auto;background:#0b0b0b;' +
      '-webkit-overflow-scrolling:touch;touch-action:pan-x pan-y pinch-zoom;overscroll-behavior:contain';
    var img = document.createElement('img');
    img.src = src;
    img.alt = alt || '';
    // Open at 1.5x to 2.5x the screen width (its own size when that fits), so a
    // wide chart is readable yet still shows its layout; pinch to go further.
    var width = Math.min(Math.max(naturalWidth || 0, window.innerWidth * 1.5), window.innerWidth * 2.5);
    img.style.cssText = 'display:block;max-width:none;width:' + width + 'px;height:auto;margin:56px auto 24px;background:#fff';
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = '\u00d7';
    btn.setAttribute('aria-label', 'Close image');
    btn.style.cssText = 'position:fixed;top:8px;right:8px;z-index:100001;width:44px;height:44px;border:0;border-radius:22px;' +
      'font:28px/44px sans-serif;color:#fff;background:rgba(0,0,0,.65);cursor:pointer';
    btn.addEventListener('click', close);
    layer.addEventListener('click', function (e) { if (e.target === layer) close(); });
    layer.appendChild(img);
    layer.appendChild(btn);
    document.body.appendChild(layer);
    document.documentElement.style.overflow = 'hidden';
    // Start centred horizontally, so a wide chart opens on its middle.
    layer.scrollLeft = Math.max(0, (width - window.innerWidth) / 2);
  }

  document.addEventListener('click', function (e) {
    if (!window.matchMedia(PHONE).matches) return;
    var img = e.target.closest && e.target.closest('.markdown-section img');
    if (!img || img.closest('a')) return; // pictures that are links keep their link
    e.preventDefault();
    e.stopPropagation();
    open(img.currentSrc || img.src, img.alt, img.naturalWidth);
  }, true);

  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  window.addEventListener('hashchange', close);
})();
