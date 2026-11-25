# restoration.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/digital-image-processing/labs/restoration.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/digital-image-processing/labs/restoration.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, I = Img;
  Lab.theme($("theme"));
  var scene = I.scene(), cache = { key: "", d: null };
  function f(x, d) { return String(Number(x.toFixed(d === undefined ? 1 : d))); }
  function sig(x) { return x >= 100 ? f(x, 0) : x >= 1 ? f(x, 2) : f(x, 4); }
  function clearP(sel) { Array.prototype.forEach.call(document.querySelectorAll(sel), function (b) { b.setAttribute("aria-pressed", "false"); }); }

  // ---- one frequency: how much is the noise multiplied? ----
  function renderGain() {
    var h = Math.pow(10, +$("h").value), K = Math.pow(10, +$("kw").value), inv = 1 / h, wie = h / (h * h + K);
    $("big").innerHTML = (inv >= 100 ? f(inv, 0) : f(inv, 1)) + "&times;<small>noise amplification of the inverse filter</small>";
    $("m-inv").textContent = sig(inv); $("m-wie").textContent = sig(wie); $("m-turn").textContent = sig(Math.sqrt(K));
    $("says").innerHTML = "With |H| = " + sig(h) + " and noise N ≈ 1 there, dividing by H makes the noise <b>" + sig(inv) + " times</b> bigger. Wiener multiplies it by only <b>" + sig(wie) + "</b>" + (wie < 1 ? ": it has stopped trying." : ".");
    var cv = $("cg"), P = Lab.prep(cv, 0.5), c = P.ctx, col = Lab.colors(), L = 46, R = 10, T = 10, B = 30, W = P.w - L - R, H = P.h - T - B, k;
    var X = function (e) { return L + (e + 3) / 3 * W; }, Y = function (g) { return T + H - (Math.log10(g) + 2) / 5 * H; };
    c.clearRect(0, 0, P.w, P.h); c.font = "12px system-ui,sans-serif"; c.fillStyle = col.mut; c.strokeStyle = col.line; c.textAlign = "right";
    [0.01, 0.1, 1, 10, 100, 1000].forEach(function (g) { var y = Math.round(Y(g)) + 0.5; c.beginPath(); c.moveTo(L, y); c.lineTo(P.w - R, y); c.stroke(); c.fillText(String(g), L - 6, y + 4); });
    c.textAlign = "center"; [-3, -2, -1, 0].forEach(function (e) { c.fillText(String(Math.pow(10, e)), X(e), P.h - 14); }); c.fillText("|H|: the blur's strength at this frequency", L + W / 2, P.h - 1);
    function curve(fn, style) { c.strokeStyle = style; c.lineWidth = 2.4; c.beginPath(); for (k = 0; k <= 120; k++) { var e = -3 + 3 * k / 120, g = fn(Math.pow(10, e)); if (k) c.lineTo(X(e), Y(g)); else c.moveTo(X(e), Y(g)); } c.stroke(); c.lineWidth = 1; }
    curve(function (x) { return 1 / x; }, col.acc2); curve(function (x) { return x / (x * x + K); }, col.acc);
    var e0 = +$("h").value; c.strokeStyle = col.fg; c.setLineDash([5, 4]); c.beginPath(); c.moveTo(X(e0), T); c.lineTo(X(e0), T + H); c.stroke(); c.setLineDash([]);
  }
  Lab.slider("h", function (v) { return "10^" + f(v, 2); }, renderGain); Lab.slider("kw", function (v) { return "10^" + f(v, 2); }, renderGain);

  // ---- a picture ----
  function observed(a, sg) { var key = a + "|" + sg; if (cache.key !== key) cache = { key: key, d: I.degrade(scene, a, sg, 1) }; return cache.d; }
  function renderPic() {
    var a = +$("a").value, sg = +$("sg").value, ke = +$("k").value, d = observed(a, sg);
    var inv = I.restore(d.g, d.hr, d.hi, "inverse", 0), wie = I.restore(d.g, d.hr, d.hi, "wiener", Math.pow(10, ke));
    I.draw($("pA"), scene); I.draw($("pB"), d.g); I.draw($("pC"), inv); I.draw($("pD"), wie);
    var pb = I.psnr(scene, d.g), pi = I.psnr(scene, inv), pw = I.psnr(scene, wie);
    $("pBc").innerHTML = "Blurred and noisy &middot; <b>" + f(pb) + " dB</b>"; $("pCc").innerHTML = "Inverse filter &middot; <b>" + (pi >= 99 ? "≥ 99" : f(pi)) + " dB</b>"; $("pDc").innerHTML = "Wiener &middot; <b>" + f(pw) + " dB</b>";
    $("picsays").innerHTML = sg === 0 ? "With no noise the inverse filter is exact (apart from frequencies the blur erased outright). Add noise and watch it fall apart." : pi < pb ? "The inverse filter scored <b>below</b> the blurred picture: it amplified the noise where the blur had crushed the signal. Wiener scored " + f(pw) + " dB." : "Wiener scored " + f(pw) + " dB against the inverse filter's " + f(pi) + " dB.";
  }
  Lab.slider("a", String, function () { clearP("[data-x]"); renderPic(); }); Lab.slider("sg", function (v) { return f(v, 1); }, function () { clearP("[data-x]"); renderPic(); }); Lab.slider("k", function (v) { return "10^" + f(v, 2); }, function () { clearP("[data-x]"); renderPic(); });
  Array.prototype.forEach.call(document.querySelectorAll("[data-x]"), function (b) {
    b.addEventListener("click", function () { var v = b.getAttribute("data-x").split("|"); clearP("[data-x]"); b.setAttribute("aria-pressed", "true"); $("a").value = v[0]; $("a")._upd(); $("sg").value = v[1]; $("sg")._upd(); $("k").value = v[2]; $("k")._upd(); renderPic(); });
  });

  // ---- PSNR ----
  function renderPsnr() { var m = Math.pow(10, +$("ms").value); $("mse").textContent = f(m, m < 10 ? 2 : 0); $("ps").textContent = f(10 * Math.log10(65025 / m), 2) + " dB"; $("ps2").textContent = f(10 * Math.log10(65025 / (m / 2)), 2) + " dB"; }
  Lab.slider("ms", function (v) { return "10^" + f(v, 2); }, renderPsnr);

  window.addEventListener("resize", function () { renderGain(); renderPic(); });
  renderGain(); renderPsnr(); document.querySelector("[data-x]").click();
})();
```
