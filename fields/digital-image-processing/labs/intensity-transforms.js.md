# intensity-transforms.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/digital-image-processing/labs/intensity-transforms.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/digital-image-processing/labs/intensity-transforms.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, I = Img, N = I.N, i;
  Lab.theme($("theme"));
  var PRESETS = { page: [24, 16, 10, 6, 4, 2, 2, 0], flat: [8, 8, 8, 8, 8, 8, 8, 8], dark: [60, 4, 0, 0, 0, 0, 0, 0], two: [32, 0, 0, 0, 0, 0, 0, 32] };
  var scene = I.scene(), dark = scene.map(function (v) { return Math.round(v * 0.25); });
  function f(x, d) { return String(Number(x.toFixed(d === undefined ? 2 : d))); }
  function distinct(a) { var s = {}, n = 0, k; for (k = 0; k < a.length; k++) { var v = Math.round(a[k]); if (!s[v]) { s[v] = 1; n++; } } return n; }
  function range(a) { var lo = 1e9, hi = -1e9, k; for (k = 0; k < a.length; k++) { if (a[k] < lo) lo = a[k]; if (a[k] > hi) hi = a[k]; } return Math.round(lo) + " to " + Math.round(hi); }

  // ---- the bag of eight levels ----
  function bag() { var c = [], t = 0; for (i = 0; i < 8; i++) { var v = Math.max(0, Math.min(99, Math.floor(+$("n" + i).value) || 0)); c.push(v); t += v; } return { c: c, total: t }; }
  function renderBag() {
    var b = bag(), c = b.c, total = b.total, rows = "", cum = 0, k, lut, after = new Array(8).fill(0);
    if (!total) { $("big").innerHTML = "–<small>put at least one pixel in the bag</small>"; $("says").textContent = ""; $("tb").innerHTML = ""; return; }
    lut = I.equalizeLut(c, 8);
    for (k = 0; k < 8; k++) { cum += c[k]; after[lut[k]] += c[k]; rows += "<tr><td>" + k + "</td><td>" + c[k] + "</td><td>" + cum + "</td><td>" + f(7 * cum / total) + "</td><td><b>" + lut[k] + "</b></td></tr>"; }
    $("tb").innerHTML = rows;
    var first = 0; while (first < 8 && c[first] === 0) first++;
    var cumFirst = 0; for (k = 0; k <= first; k++) cumFirst += c[k];
    $("big").innerHTML = lut[first] + "<small>new level for the " + c[first] + " pixels at level " + first + " (7 &times; " + cumFirst + " / " + total + " = " + f(7 * cumFirst / total) + ")</small>";
    var nb = c.filter(function (v) { return v > 0; }).length, seen = {}, na = 0;
    for (k = 0; k < 8; k++) if (c[k] > 0 && !seen[lut[k]]) { seen[lut[k]] = 1; na++; }
    $("m-before").textContent = nb; $("m-after").textContent = na; $("m-total").textContent = total;
    var lo = lut[first], hi = lut[7 - c.slice().reverse().findIndex(function (v) { return v > 0; })];
    $("says").innerHTML = "The pixels now sit on levels <b>" + lo + " to " + hi + "</b>. " + (na < nb ? "<b>" + nb + " levels became " + na + "</b>: pixels that share a level must move together, so the result is spread out but not flat." : "No two levels merged here.");
    $("newh").textContent = "New counts per level 0 to 7: " + after.join(", ") + " (total " + after.reduce(function (a, b) { return a + b; }, 0) + ", nobody lost).";
    var col = Lab.colors();
    Img.drawHist($("cv1"), (function () { var h = new Array(256).fill(0); for (k = 0; k < 8; k++) h[k * 32 + 16] = c[k]; return h; })(), col.acc, 8);
    Img.drawHist($("cv2"), (function () { var h = new Array(256).fill(0); for (k = 0; k < 8; k++) h[k * 32 + 16] = after[k]; return h; })(), col.acc2, 8);
  }
  function setBag(key) { PRESETS[key].forEach(function (v, k) { $("n" + k).value = v; }); renderBag(); }
  function clearP(sel) { Array.prototype.forEach.call(document.querySelectorAll(sel), function (b) { b.setAttribute("aria-pressed", "false"); }); }
  Array.prototype.forEach.call(document.querySelectorAll("[data-p]"), function (b) { b.addEventListener("click", function () { clearP("[data-p]"); b.setAttribute("aria-pressed", "true"); setBag(b.getAttribute("data-p")); }); });
  for (i = 0; i < 8; i++) $("n" + i).addEventListener("input", function () { clearP("[data-p]"); renderBag(); });

  // ---- the picture ----
  function apply(img, op, g) {
    var o = new Float32Array(img.length), k, lut;
    if (op === "gamma") for (k = 0; k < img.length; k++) o[k] = Math.round(255 * Math.pow(img[k] / 255, g));
    else if (op === "log") for (k = 0; k < img.length; k++) o[k] = Math.round(255 * Math.log(1 + img[k]) / Math.log(256));
    else if (op === "neg") for (k = 0; k < img.length; k++) o[k] = 255 - img[k];
    else { lut = I.equalizeLut(I.counts(img), 256); for (k = 0; k < img.length; k++) o[k] = lut[Math.round(img[k])]; }
    return o;
  }
  var NAMES = { gamma: "Power law", log: "Log", neg: "Negative", equal: "Equalization" };
  function renderPic() {
    var src = $("src").value === "dark" ? dark : scene, op = $("op").value, g = +$("g").value, out = apply(src, op, g), col = Lab.colors();
    $("g").disabled = op !== "gamma";
    I.draw($("pA"), src); I.draw($("pB"), out);
    I.drawHist($("hA"), I.counts(src), col.acc); I.drawHist($("hB"), I.counts(out), col.acc2);
    var px = op === "gamma" ? Math.pow(0.25, g) : op === "log" ? Math.log(1 + 0.25) / Math.log(2) : op === "neg" ? 0.75 : null;
    $("px").textContent = px === null ? "depends on the picture" : f(px, 4);
    $("r0").textContent = range(src); $("r1").textContent = range(out);
    var d0 = distinct(src), d1 = distinct(out);
    $("lv").textContent = d0 + " → " + d1;
    $("picsays").innerHTML = NAMES[op] + " moves every pixel through a table of its own value, so it can <b>never create a level</b>: " + (d1 < d0 ? "here " + (d0 - d1) + " merged." : d1 === d0 ? "here none merged, and none were added." : "") ;
  }
  Lab.slider("g", function (v) { return f(v, 2); }, function () { clearP("[data-x]"); renderPic(); });
  $("src").addEventListener("change", function () { clearP("[data-x]"); renderPic(); }); $("op").addEventListener("change", function () { clearP("[data-x]"); renderPic(); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-x]"), function (b) {
    b.addEventListener("click", function () {
      var a = b.getAttribute("data-x").split("|"); clearP("[data-x]"); b.setAttribute("aria-pressed", "true");
      $("src").value = a[0]; $("op").value = a[1]; $("g").value = a[2]; $("g")._upd(); renderPic();
    });
  });
  window.addEventListener("resize", function () { renderBag(); renderPic(); });
  setBag("page"); document.querySelector("[data-p]").setAttribute("aria-pressed", "true"); renderPic();
})();
```
