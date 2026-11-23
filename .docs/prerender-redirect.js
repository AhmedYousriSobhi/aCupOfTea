/* Share pages carry the page text as static HTML (for search engines and readers
   without scripts); a browser that runs scripts goes on to the interactive page. */
(function () {
  var s = document.currentScript;
  var target = s && s.getAttribute('data-target');
  if (target) location.replace(target);
})();
