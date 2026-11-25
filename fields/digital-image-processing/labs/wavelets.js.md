# wavelets.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/digital-image-processing/labs/wavelets.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/digital-image-processing/labs/wavelets.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, I = Img, N = I.N, MODE = "soft", i;
  Lab.theme($("theme"));
  var scene = I.scene(), cache = { key: "", nz: null };
  function f(x, d) { return String(Number(x.toFixed(d === undefined ? 1 : d))); }
  function clearP(sel) { Array.prototype.forEach.call(document.querySelectorAll(sel), function (b) { b.setAttribute("aria-pressed", "false"); }); }

  // ---- a row: the page's average and half-difference ----
  function rowValues() { var v = []; for (i = 0; i < 8; i++) if (!$("v" + i).parentNode.hidden) v.push(+$("v" + i).value || 0); return v; }
  function show(a) { return a.map(function (x) { return f(x, 2); }).join(", "); }
  function rebuild(out) { // undo the levels: first = average + detail, second = average - detail
    var cur = [out[0]], pos = 1, n;
    while (cur.length < out.length) { n = cur.length; var next = []; for (var k = 0; k < n; k++) { next.push(cur[k] + out[pos + k]); next.push(cur[k] - out[pos + k]); } pos += n; cur = next; }
    return cur;
  }
  function renderRow(v) {
    var h = I.haarRow(v), out = h.out, det = out.slice(1), nz = det.filter(function (x) { return Math.abs(x) > 1e-9; }).length, back = rebuild(out);
    var ok = back.every(function (x, k) { return Math.abs(x - v[k]) < 1e-9; });
    $("big").innerHTML = nz + " of " + det.length + "<small>detail coefficients that are not zero</small>";
    var parts = [f(out[0], 2)], pos = 1, n = 1; while (pos < out.length) { parts.push(show(out.slice(pos, pos + n))); pos += n; n *= 2; }
    $("m-out").textContent = "[" + parts.join(" | ") + "]"; $("m-back").textContent = ok ? "exactly the row" : "not equal";
    var fine = h.levels[0].det, at = -1; fine.forEach(function (x, k) { if (Math.abs(x) > 1e-9 && at < 0) at = k; });
    $("says").innerHTML = nz === 0 ? "Every detail is zero: the whole row is its average, <b>" + f(out[0], 2) + "</b>." : at >= 0 ? "At the finest scale the first nonzero detail is in <b>pair " + (at + 1) + "</b> (positions " + (2 * at + 1) + " and " + (2 * at + 2) + "): that is where the row changes." : "Only coarser scales see a change here.";
    var lines = [], k2; for (k2 = 0; k2 < h.levels.length; k2++) lines.push("level " + (k2 + 1) + ": averages [" + show(h.levels[k2].avg) + "]  details [" + show(h.levels[k2].det) + "]");
    $("lvs").textContent = lines.join("\n");
  }
  function onRow() { clearP("[data-r]"); renderRow(rowValues()); }
  for (i = 0; i < 8; i++) $("v" + i).addEventListener("input", onRow);
  Array.prototype.forEach.call(document.querySelectorAll("[data-r]"), function (b) {
    b.addEventListener("click", function () {
      var v = b.getAttribute("data-r").split(",").map(Number); clearP("[data-r]"); b.setAttribute("aria-pressed", "true");
      var n = v.length; for (i = 0; i < 8; i++) { $("v" + i).value = i < n ? v[i] : 0; $("v" + i).parentNode.hidden = i >= n; } renderRow(v);
    });
  });

  // ---- a picture: orthonormal Haar ----
  function noisy(sg) { var key = String(sg); if (cache.key !== key) cache = { key: key, nz: sg === 0 ? scene : I.gaussNoise(scene, sg, 7) }; return cache.nz; }
  function renderPic() {
    var L = +$("lv").value, sg = +$("sg").value, T = +$("th").value, nz = noisy(sg), c = new Float64Array(nz), A = N >> L, x, y, v, zero = 0, tot = 0, out;
    $("th").disabled = MODE === "edge";
    I.haar2(c, L, false);
    var disp = new Float32Array(N * N); for (y = 0; y < N; y++) for (x = 0; x < N; x++) { v = c[y * N + x]; disp[y * N + x] = (x < A && y < A) ? v / Math.pow(2, L) : Math.min(255, Math.abs(v) * 4); }
    if (MODE === "edge") {
      var e = new Float64Array(scene); I.haar2(e, L, false); for (y = 0; y < A; y++) for (x = 0; x < A; x++) e[y * N + x] = 0; I.haar2(e, L, true);
      out = Float32Array.from(e, function (q) { return Math.min(255, Math.abs(q) * 3); });
      $("pDc").textContent = "Edges: the clean picture with the approximation zeroed";
    } else {
      for (y = 0; y < N; y++) for (x = 0; x < N; x++) { if (x < A && y < A) continue; v = c[y * N + x]; tot++; var w = MODE === "hard" ? (Math.abs(v) > T ? v : 0) : Math.sign(v) * Math.max(0, Math.abs(v) - T); if (w === 0) zero++; c[y * N + x] = w; }
      I.haar2(c, L, true); out = Float32Array.from(c, I.clamp);
      $("pDc").innerHTML = (MODE === "soft" ? "Soft" : "Hard") + " threshold &middot; <b>" + f(I.psnr(scene, out)) + " dB</b>";
    }
    I.draw($("pA"), scene); I.draw($("pB"), nz); I.draw($("pC"), disp); I.draw($("pD"), out);
    $("pBc").innerHTML = "Noisy &middot; <b>" + f(I.psnr(scene, nz)) + " dB</b>";
    $("zr").textContent = MODE === "edge" ? "n/a" : f(100 * zero / tot) + "%";
    var cc = new Float64Array(scene), near = 0, n2 = 0; I.haar2(cc, L, false);
    for (y = 0; y < N; y++) for (x = 0; x < N; x++) { if (x < A && y < A) continue; n2++; if (Math.abs(cc[y * N + x]) <= 1) near++; }
    $("sp").textContent = f(100 * near / n2) + "%";
    var p0 = I.psnr(scene, nz), p1 = MODE === "edge" ? 0 : I.psnr(scene, out);
    $("picsays").innerHTML = MODE === "edge" ? "With the approximation zeroed only the details remain: a few bright lines at the edges, black elsewhere." : "PSNR " + f(p0) + " → <b>" + f(p1) + " dB</b>" + (p1 < p0 ? ": the threshold is so high that it removed real edges too, so the result is worse than doing nothing." : p1 === p0 ? ": nothing changed." : ".") + " Noise spreads thinly over every detail coefficient; edges sit in a few large ones.";
  }
  function setMode(m) { MODE = m; Array.prototype.forEach.call(document.querySelectorAll("#md button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-m") === m ? "true" : "false"); }); }
  Lab.slider("lv", String, function () { clearP("[data-x]"); renderPic(); }); Lab.slider("sg", String, function () { clearP("[data-x]"); renderPic(); }); Lab.slider("th", String, function () { clearP("[data-x]"); renderPic(); });
  Array.prototype.forEach.call(document.querySelectorAll("#md button"), function (b) { b.addEventListener("click", function () { clearP("[data-x]"); setMode(b.getAttribute("data-m")); renderPic(); }); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-x]"), function (b) {
    b.addEventListener("click", function () { var a = b.getAttribute("data-x").split("|"); clearP("[data-x]"); b.setAttribute("aria-pressed", "true"); setMode(a[0]); $("sg").value = a[1]; $("sg")._upd(); $("th").value = a[2]; $("th")._upd(); $("lv").value = a[3]; $("lv")._upd(); renderPic(); });
  });
  window.addEventListener("resize", renderPic);
  document.querySelector("[data-r]").click(); document.querySelector("[data-x]").click();
})();
```
