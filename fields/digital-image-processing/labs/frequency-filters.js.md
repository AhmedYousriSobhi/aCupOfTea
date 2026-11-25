# frequency-filters.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/digital-image-processing/labs/frequency-filters.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/digital-image-processing/labs/frequency-filters.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, I = Img, TYPE = "gauss", HP = false;
  Lab.theme($("theme"));
  var scene = I.scene();
  function f(x, d) { return String(Number(x.toFixed(d === undefined ? 1 : d))); }
  function clearP(sel) { Array.prototype.forEach.call(document.querySelectorAll(sel), function (b) { b.setAttribute("aria-pressed", "false"); }); }
  var NAMES = { ideal: "Ideal", butter: "Butterworth", gauss: "Gaussian" };

  // ---- ringing strip: a pulse through the low-pass of the same kind ----
  function renderRing() {
    var d0 = +$("d0").value, n = +$("on").value, r = I.ring1d(TYPE, d0, n), cv = $("cv"), P = Lab.prep(cv, 0.5), c = P.ctx, col = Lab.colors();
    var L = 44, R = 10, T = 10, B = 28, W = P.w - L - R, H = P.h - T - B, lo = -40, hi = 300;
    var X = function (k) { return L + k / 255 * W; }, Y = function (y) { return T + H - (y - lo) / (hi - lo) * H; };
    c.clearRect(0, 0, P.w, P.h); c.font = "12px system-ui,sans-serif"; c.fillStyle = col.mut; c.strokeStyle = col.line; c.textAlign = "right";
    [0, 100, 200, 255].forEach(function (v) { var y = Math.round(Y(v)) + 0.5; c.beginPath(); c.moveTo(L, y); c.lineTo(P.w - R, y); c.stroke(); c.fillText(String(v), L - 6, y + 4); });
    c.textAlign = "center"; c.fillText("position along the strip", L + W / 2, P.h - 6);
    c.strokeStyle = col.acc2; c.lineWidth = 2; c.setLineDash([6, 4]); c.beginPath(); c.moveTo(X(0), Y(0)); c.lineTo(X(63.5), Y(0)); c.lineTo(X(63.5), Y(255)); c.lineTo(X(191.5), Y(255)); c.lineTo(X(191.5), Y(0)); c.lineTo(X(255), Y(0)); c.stroke(); c.setLineDash([]);
    c.strokeStyle = col.fg; c.lineWidth = 2.2; c.lineJoin = "round"; c.beginPath(); var k;
    for (k = 0; k < 256; k++) { if (k) c.lineTo(X(k), Y(r.signal[k])); else c.moveTo(X(k), Y(r.signal[k])); } c.stroke(); c.lineWidth = 1;
    $("big").innerHTML = f(r.over) + "%<small>overshoot above the pulse's top</small>";
    $("m-over").textContent = f(r.over, 2) + "%"; $("m-under").textContent = f(r.under, 2) + "%";
    $("says").innerHTML = TYPE === "gauss" ? "The Gaussian mask is smooth, so its twin in space is a Gaussian: <b>no ripples</b>." : TYPE === "ideal" ? "A hard wall in the spectrum is a <b>sinc</b> in space: ripples that never quite die. Gibbs overshoot is about 9% however far you move the cut-off." : "Butterworth order " + n + ": the steeper the wall, the closer it gets to the ideal filter's ripples.";
  }

  // ---- the picture ----
  function renderPic() {
    var d0 = +$("d0").value, n = +$("on").value, r = I.freqFilter(scene, TYPE, HP, d0, n);
    $("on").disabled = TYPE !== "butter";
    I.draw($("pA"), scene); I.draw($("pS"), r.spec, r.P, function (v) { return 255 * v / r.top; }); I.draw($("pH"), r.H, r.P, function (v) { return 255 * v; });
    I.draw($("pR"), r.out);
    $("pRc").innerHTML = "Result &middot; <b>" + f(I.psnr(scene, r.out)) + " dB</b>";
    $("picsays").textContent = (HP ? "High-pass" : "Low-pass") + ", " + NAMES[TYPE].toLowerCase() + ", D₀ = " + d0 + (TYPE === "butter" ? ", n = " + n : "") + ". " + (HP ? "The mask is 1 − H: the smooth shading and the average brightness go, and edges remain." : "A bigger D₀ keeps more of the spectrum, so the result stays closer to the original.");
  }
  function setType(t) { TYPE = t; Array.prototype.forEach.call(document.querySelectorAll("#typ button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-t") === t ? "true" : "false"); }); }
  function setHp(h) { HP = h; Array.prototype.forEach.call(document.querySelectorAll("#hp button"), function (b) { b.setAttribute("aria-selected", (b.getAttribute("data-h") === "1") === h ? "true" : "false"); }); }
  function all() { renderRing(); renderPic(); }
  Lab.slider("d0", String, function () { clearP("[data-x]"); all(); }); Lab.slider("on", String, function () { clearP("[data-x]"); all(); });
  Array.prototype.forEach.call(document.querySelectorAll("#typ button"), function (b) { b.addEventListener("click", function () { clearP("[data-x]"); setType(b.getAttribute("data-t")); all(); }); });
  Array.prototype.forEach.call(document.querySelectorAll("#hp button"), function (b) { b.addEventListener("click", function () { clearP("[data-x]"); setHp(b.getAttribute("data-h") === "1"); all(); }); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-x]"), function (b) {
    b.addEventListener("click", function () {
      var a = b.getAttribute("data-x").split("|"); clearP("[data-x]"); b.setAttribute("aria-pressed", "true");
      setType(a[0]); setHp(a[1] === "1"); $("d0").value = a[2]; $("d0")._upd(); $("on").value = a[3]; $("on")._upd(); all();
    });
  });

  // ---- notch out periodic noise: click the dots in the spectrum ----
  var N = I.N, holes = [], nzCache = { key: "", img: null };
  function striped() { var a = +$("sa").value, c = +$("sc").value, key = a + "|" + c; if (nzCache.key !== key) nzCache = { key: key, img: I.stripes(scene, a, c) }; return nzCache.img; }
  function addHole(x, y) { holes.push([x, y]); if (x !== N / 2 || y !== N / 2) holes.push([N - x, N - y]); }
  function renderNotch() {
    var img = striped(), r = +$("nr").value, res = I.notchFilter(img, holes, r), cv = $("nS");
    I.draw($("nA"), img, N, function (v) { return v; }); I.draw(cv, res.spec, N, function (v) { return 255 * v / res.top; }); I.draw($("nR"), res.out);
    var c = cv.getContext("2d"); c.strokeStyle = Lab.colors().acc2; c.lineWidth = 1.5; holes.forEach(function (h) { c.beginPath(); c.arc(h[0] + 0.5, h[1] + 0.5, r + 1, 0, 2 * Math.PI); c.stroke(); });
    $("np0").textContent = f(I.psnr(scene, img)) + " dB"; $("np1").textContent = f(I.psnr(scene, res.out)) + " dB"; $("nh").textContent = holes.length;
    $("nsays").textContent = holes.length === 0 ? "Two bright dots sit left and right of the centre: that is the stripe. Everything else in the spectrum is the picture." : "A small hole removes the pattern and little else; a big one cuts the picture around the dots too.";
  }
  function onNotch() { clearP("[data-n]"); renderNotch(); }
  Lab.slider("sa", String, function () { holes = []; onNotch(); }); Lab.slider("sc", String, function () { holes = []; onNotch(); }); Lab.slider("nr", String, onNotch);
  $("nS").addEventListener("pointerdown", function (e) { var b = this.getBoundingClientRect(); addHole(Math.round((e.clientX - b.left) / b.width * N - 0.5), Math.round((e.clientY - b.top) / b.height * N - 0.5)); onNotch(); });
  $("nfind").addEventListener("click", function () { var p = I.strongestPeak(I.notchFilter(striped(), [], 1).mag, 3); addHole(p[0], p[1]); onNotch(); });
  $("nclr").addEventListener("click", function () { holes = []; onNotch(); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-n]"), function (b) {
    b.addEventListener("click", function () { var a = b.getAttribute("data-n").split("|"); clearP("[data-n]"); b.setAttribute("aria-pressed", "true"); $("sc").value = a[0]; $("sc")._upd(); $("sa").value = a[1]; $("sa")._upd(); $("nr").value = a[2]; $("nr")._upd(); holes = []; if (a[3] === "1") { var p = I.strongestPeak(I.notchFilter(striped(), [], 1).mag, 3); addHole(p[0], p[1]); } renderNotch(); });
  });

  // ---- aliasing ----
  function renderAlias() {
    var f0 = +$("fa").value, fs = +$("fs").value, ap = I.alias(f0, fs), ok = f0 < fs / 2;
    $("ap").textContent = f(ap, 0) + " Hz"; $("ny").textContent = f(fs / 2, 1) + " Hz";
    $("vd").textContent = ok ? "honest" : "aliased"; $("vd").parentNode.classList.toggle("warn", !ok);
    var cv = $("ca"), P = Lab.prep(cv, 0.42), c = P.ctx, col = Lab.colors(), L = 34, R = 10, T = 12, B = 24, W = P.w - L - R, H = P.h - T - B, T1 = 1;
    var X = function (t) { return L + t / T1 * W; }, Y = function (v) { return T + H / 2 - v * H / 2 * 0.9; }, k;
    c.clearRect(0, 0, P.w, P.h); c.font = "12px system-ui,sans-serif"; c.fillStyle = col.mut; c.strokeStyle = col.line; c.textAlign = "center";
    c.beginPath(); c.moveTo(L, Y(0)); c.lineTo(P.w - R, Y(0)); c.stroke(); c.fillText("one second", L + W / 2, P.h - 6);
    function wave(freq, style, dash, wd) { c.strokeStyle = style; c.lineWidth = wd; c.setLineDash(dash); c.beginPath(); for (k = 0; k <= 600; k++) { var t = k / 600; if (k) c.lineTo(X(t), Y(Math.cos(2 * Math.PI * freq * t))); else c.moveTo(X(t), Y(Math.cos(2 * Math.PI * freq * t))); } c.stroke(); c.setLineDash([]); c.lineWidth = 1; }
    wave(ap, col.acc3, [7, 5], 2.5); wave(f0, col.acc, [], 1.8);
    c.fillStyle = col.acc2; for (k = 0; k <= fs; k++) { c.beginPath(); c.arc(X(k / fs), Y(Math.cos(2 * Math.PI * f0 * k / fs)), 4.5, 0, 2 * Math.PI); c.fill(); }
  }
  Lab.slider("fa", String, function () { clearP("[data-a]"); renderAlias(); }); Lab.slider("fs", String, function () { clearP("[data-a]"); renderAlias(); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-a]"), function (b) {
    b.addEventListener("click", function () { var a = b.getAttribute("data-a").split("|"); clearP("[data-a]"); b.setAttribute("aria-pressed", "true"); $("fa").value = a[0]; $("fa")._upd(); $("fs").value = a[1]; $("fs")._upd(); renderAlias(); });
  });

  window.addEventListener("resize", function () { all(); renderNotch(); renderAlias(); });
  setType("gauss"); setHp(false);
  document.querySelector("[data-x]").click(); document.querySelector("[data-n]").click(); document.querySelector("[data-a]").click();
})();
```
