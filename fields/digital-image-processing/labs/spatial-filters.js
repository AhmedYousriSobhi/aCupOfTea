(function () {
  "use strict";
  var $ = Lab.$, I = Img, N = I.N, i, KIND = "sp", seed = 1;
  Lab.theme($("theme"));
  var scene = I.scene(), PATCH = [64, 50, 18, 26]; // x, y, width, height of a smooth area (no edges)
  function f(x, d) { return String(Number(x.toFixed(d === undefined ? 1 : d))); }

  // ---- the 3 x 3 window ----
  var BIN3 = [1, 2, 1, 2, 4, 2, 1, 2, 1];
  function window3() { var v = [], k; for (k = 0; k < 9; k++) v.push(Math.max(0, Math.min(255, +$("k" + k).value || 0))); return v; }
  function renderWindow() {
    var v = window3(), mean = v.reduce(function (a, b) { return a + b; }, 0) / 9, s = v.slice().sort(function (a, b) { return a - b; }), med = s[4];
    var bin = v.reduce(function (a, b, k) { return a + b * BIN3[k]; }, 0) / 16;
    $("big").innerHTML = f(mean) + "<small>box filter: the mean of nine pixels</small>";
    $("m-mean").textContent = f(mean, 2); $("m-med").textContent = f(med, 0); $("m-bin").textContent = f(bin, 2);
    $("sorted").textContent = "Sorted: " + s.join(" ") + "  → the middle one is " + med;
    var c = v[4];
    $("says").innerHTML = "The centre pixel was <b>" + c + "</b>. The mean turns it into <b>" + f(mean, 2) + "</b> (a move of " + f(Math.abs(mean - c), 2) + "), the median into <b>" + f(med, 0) + "</b> (a move of " + f(Math.abs(med - c), 0) + ").";
    Array.prototype.forEach.call(document.querySelectorAll("#nbg input"), function (el, k) { el.classList.toggle("hl", k === 4); });
  }
  function clearP(sel) { Array.prototype.forEach.call(document.querySelectorAll(sel), function (b) { b.setAttribute("aria-pressed", "false"); }); }
  for (i = 0; i < 9; i++) $("k" + i).addEventListener("input", function () { clearP("[data-c]"); renderWindow(); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-c]"), function (b) {
    b.addEventListener("click", function () { clearP("[data-c]"); b.setAttribute("aria-pressed", "true"); b.getAttribute("data-c").split(",").forEach(function (v, k) { $("k" + k).value = v; }); renderWindow(); });
  });

  // ---- the picture ----
  var cache = { key: "", noisy: null };
  function noisy(st) {
    var key = KIND + "|" + st; if (cache.key === key) return cache.noisy;
    cache = { key: key, noisy: st === 0 ? scene : KIND === "g" ? I.gaussNoise(scene, st, seed) : I.impulseNoise(scene, st / 100, seed) };
    return cache.noisy;
  }
  function outline(cv) { var c = cv.getContext("2d"); c.strokeStyle = Lab.colors().acc2; c.lineWidth = 1.5; c.strokeRect(PATCH[0] + 0.5, PATCH[1] + 0.5, PATCH[2], PATCH[3]); }
  function renderPic() {
    var st = +$("st").value, flt = $("flt").value, m = +$("win").value, pad = $("pad").value, nz = noisy(st), out;
    if (flt === "median") out = I.medianFilter(nz, m, pad); else out = I.convolve(nz, flt === "box" ? I.boxKernel(m) : I.binomialKernel(m), m, pad);
    I.draw($("pA"), scene); I.draw($("pB"), nz); I.draw($("pC"), out);
    [$("pA"), $("pB"), $("pC")].forEach(outline);
    $("q0").textContent = f(I.psnr(scene, nz)) + " dB"; $("q1").textContent = f(I.psnr(scene, out)) + " dB";
    $("q2").textContent = f(I.psnrRect(scene, out, PATCH[0], PATCH[1], PATCH[2], PATCH[3])) + " dB"; $("q3").textContent = f(out[0]);
    $("pBc").textContent = (KIND === "g" ? "Gaussian noise" : "Salt and pepper") + (st === 0 ? " (none)" : "");
    var tip = KIND === "sp" ? (flt === "median" ? "Median: an isolated extreme pixel is never the middle of nine, so it simply disappears." : "A mean cannot ignore an outlier: each speck leaks into its neighbours.") : (flt === "median" ? "Median on Gaussian noise keeps edges but averages less: look at the smooth patch against the whole picture." : "Averaging independent errors cancels them: best in the smooth patch, at the price of blurred edges.");
    $("picsays").textContent = tip;
  }
  function setKind(k) { KIND = k; Array.prototype.forEach.call(document.querySelectorAll("#kind button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-k") === k ? "true" : "false"); }); }
  Lab.slider("st", String, function () { clearP("[data-x]"); renderPic(); });
  Array.prototype.forEach.call(document.querySelectorAll("#kind button"), function (b) { b.addEventListener("click", function () { clearP("[data-x]"); setKind(b.getAttribute("data-k")); renderPic(); }); });
  ["flt", "win", "pad"].forEach(function (id) { $(id).addEventListener("change", function () { clearP("[data-x]"); renderPic(); }); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-x]"), function (b) {
    b.addEventListener("click", function () {
      var a = b.getAttribute("data-x").split("|"); clearP("[data-x]"); b.setAttribute("aria-pressed", "true");
      setKind(a[0]); $("st").value = a[1]; $("st")._upd(); $("flt").value = a[2]; $("win").value = a[3]; $("pad").value = a[4]; renderPic();
    });
  });

  // ---- separable cost ----
  function renderSep() { var k = +$("kk").value; $("s2").textContent = k * k; $("s1").textContent = 2 * k; $("sv").textContent = f(k * k / (2 * k)) + "×"; }
  Lab.slider("kk", String, renderSep);

  window.addEventListener("resize", function () { renderPic(); });
  renderSep(); setKind("sp");
  document.querySelector("[data-c]").click();
  document.querySelector("[data-x]").click();
})();
