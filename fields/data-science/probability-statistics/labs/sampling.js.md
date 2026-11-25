# sampling.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/labs/sampling.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/data-science/probability-statistics/labs/sampling.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, K = "scores", mode = "z", seed = 21, means = null, hoverX = null;
  Lab.theme($("theme"));
  var TINS = [].concat(rep(1, 5), rep(2, 10), rep(3, 20), rep(4, 35), rep(5, 30));
  var POPS = {
    scores: { v: [52, 55, 55, 58, 58, 58, 62, 62, 62, 71, 71, 89, 89, 89, 93, 93, 94, 94, 95, 104], d: "Mira's 20 tasting scores: two clumps, one near 58 and one near 92. Nothing bell-shaped about the crowd itself." },
    tins: { v: TINS, d: "Tin ratings from 1 to 5 stars, piled towards 4 and 5: a lopsided crowd (5, 10, 20, 35 and 30 in every 100)." },
    fans: { v: TINS.filter(function (x) { return x >= 4; }), d: "Only people who already love the tin are asked (ratings of 4 and 5). Bias: the true mean still belongs to everyone." }
  };
  function rep(x, n) { var a = []; while (n--) a.push(x); return a; }
  function mean(a) { var s = 0; a.forEach(function (x) { s += x; }); return s / a.length; }
  function sdp(a) { var m = mean(a), s = 0; a.forEach(function (x) { s += (x - m) * (x - m); }); return Math.sqrt(s / a.length); }
  function sds(a) { var m = mean(a), s = 0; a.forEach(function (x) { s += (x - m) * (x - m); }); return Math.sqrt(s / (a.length - 1)); }
  function f(x, d) { return Number(x).toFixed(d === undefined ? 2 : d); }
  function pool() { return POPS[K].v; }
  function truth() { return K === "scores" ? mean(POPS.scores.v) : mean(TINS); }
  function draw(n, r) { var p = pool(), a = new Array(n), i; for (i = 0; i < n; i++) a[i] = p[Math.floor(r() * p.length)]; return a; }

  function head() {
    var n = +$("n").value, p = pool();
    $("p-mu").textContent = f(truth()); $("p-sd").textContent = f(sdp(p)); $("p-se").textContent = f(sdp(p) / Math.sqrt(n), 3);
    $("desc").textContent = POPS[K].d; $("c-crit").textContent = critical() ? f(critical(), 3) : "n/a";
  }
  function critical() { var n = +$("n").value; if (n < 2) return null; return mode === "z" ? 1.96 : Lab.tInv(n - 1, 0.975); }

  function range() { var p = pool(), lo = Math.min.apply(null, p), hi = Math.max.apply(null, p), pad = (hi - lo) * 0.08; lo = Math.min(lo, truth() - pad); hi = Math.max(hi, truth() + pad); return [lo - pad, hi + pad]; }
  function renderMeans() {
    var n = +$("n").value, p = pool(), pm = mean(p), ps = sdp(p), se = ps / Math.sqrt(n), lo = Math.min.apply(null, p), hi = Math.max.apply(null, p);
    var pad = (hi - lo) * 0.08; lo = Math.min(lo, truth() - pad); hi = Math.max(hi, truth() + pad); lo -= pad; hi += pad;
    var nb = 36, bw = (hi - lo) / nb, bars = [], line = [], x, dens = function (t) { return Math.exp(-0.5 * Math.pow((t - pm) / se, 2)) / (se * Math.sqrt(2 * Math.PI)); };
    for (x = lo; x <= hi; x += bw / 6) line.push({ x: x, y: dens(x) });
    var top = dens(pm);
    if (means) {
      var cnt = new Array(nb).fill(0); means.forEach(function (m) { var j = Math.floor((m - lo) / bw); if (j >= 0 && j < nb) cnt[j]++; });
      cnt.forEach(function (c, j) { bars.push({ x: lo + (j + 0.5) * bw, y: c / means.length / bw }); top = Math.max(top, c / means.length / bw); });
    } else bars.push({ x: pm, y: 0 });
    var ch = Lab.barChart($("cv"), { bars: bars, line: line, bw: bw, alpha: 0.7, ymax: top * 1.15, xmin: lo, xmax: hi, xstep: Math.max(1, Math.round((hi - lo) / 8)), xlabel: "sample average", ylabel: "density", hoverX: hoverX });
    var c = ch.ctx; c.strokeStyle = ch.col.acc2; c.lineWidth = 3; c.setLineDash([6, 4]); c.beginPath(); c.moveTo(ch.X(truth()), ch.T); c.lineTo(ch.X(truth()), ch.Y(0)); c.stroke(); c.setLineDash([]); c.lineWidth = 1;
    $("m-mean").textContent = means ? f(mean(means), 3) : "–"; $("m-sd").textContent = means ? f(sds(means), 3) + " (formula " + f(se, 3) + ")" : "–";
    head();
  }
  function doMeans() {
    var r = Lab.rng(seed++), n = +$("n").value, i; means = new Array(1000);
    for (i = 0; i < 1000; i++) means[i] = mean(draw(n, r));
    $("msg").textContent = "1,000 samples of " + n + " (seed " + (seed - 1) + ")."; renderMeans();
  }

  var ivs = null;
  function doCI() {
    var n = +$("n").value, r = Lab.rng(seed++), crit = critical(), i;
    if (!crit) { $("c-cov").textContent = "n/a"; return; }
    ivs = []; var mu = truth(), cov = 0, w = 0;
    for (i = 0; i < 100; i++) { var s = draw(n, r), m = mean(s), se = sds(s) / Math.sqrt(n), lo = m - crit * se, hi = m + crit * se, ok = lo <= mu && mu <= hi; ivs.push({ lo: lo, hi: hi, ok: ok }); if (ok) cov++; w += hi - lo; }
    $("c-cov").textContent = cov + " of 100"; $("c-w").textContent = f(w / 100, 3); renderCI();
  }
  function renderCI() {
    var cv = $("cc"), P = Lab.prep(cv, 0.6), c = P.ctx, col = Lab.colors(), L = 14, R = 14, T = 10, B = 28, W = P.w - L - R, H = P.h - T - B;
    c.clearRect(0, 0, P.w, P.h); if (!ivs) { c.fillStyle = col.mut; c.font = "14px system-ui,sans-serif"; c.textAlign = "center"; c.fillText("Press “Build 100 intervals”", P.w / 2, P.h / 2); return; }
    var mu = truth(), lo = Math.min(mu, Math.min.apply(null, ivs.map(function (a) { return a.lo; }))), hi = Math.max(mu, Math.max.apply(null, ivs.map(function (a) { return a.hi; })));
    var pad = (hi - lo) * 0.05; lo -= pad; hi += pad; var X = function (x) { return L + (x - lo) / (hi - lo) * W; }, rh = H / 100;
    ivs.forEach(function (a, i) { c.strokeStyle = a.ok ? col.acc : col.acc2; c.lineWidth = Math.max(1.5, rh * 0.6); var y = T + (i + 0.5) * rh; c.beginPath(); c.moveTo(X(a.lo), y); c.lineTo(X(a.hi), y); c.stroke(); });
    c.strokeStyle = col.fg; c.lineWidth = 2; c.beginPath(); c.moveTo(X(mu), T); c.lineTo(X(mu), T + H); c.stroke();
    c.fillStyle = col.mut; c.font = "12px system-ui,sans-serif"; var lx = X(mu); c.textAlign = lx < 70 ? "left" : lx > P.w - 70 ? "right" : "center"; c.fillText("true mean " + f(mu), lx < 70 ? L : lx > P.w - 70 ? P.w - R : lx, P.h - 8);
  }

  function setPop(k) {
    K = k; means = null; ivs = null; $("msg").textContent = "";
    Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-k") === k ? "true" : "false"); });
    $("c-cov").textContent = "–"; $("c-w").textContent = "–"; renderMeans(); renderCI();
  }
  function setMode(m) { mode = m; ivs = null; Array.prototype.forEach.call(document.querySelectorAll("#mode button"), function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-m") === m ? "true" : "false"); }); $("c-cov").textContent = "–"; head(); renderCI(); }
  Lab.slider("n", String, function () { means = null; ivs = null; $("msg").textContent = ""; $("c-cov").textContent = "–"; renderMeans(); renderCI(); });
  Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.addEventListener("click", function () { clearX(); setPop(b.getAttribute("data-k")); }); });
  Array.prototype.forEach.call(document.querySelectorAll("#mode button"), function (b) { b.addEventListener("click", function () { setMode(b.getAttribute("data-m")); }); });
  function clearX() { Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (c) { c.setAttribute("aria-pressed", "false"); }); }
  Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (btn) {
    btn.addEventListener("click", function () {
      var a = btn.getAttribute("data-x").split("|"); clearX(); btn.setAttribute("aria-pressed", "true");
      $("n").value = a[1]; $("n")._upd(); setPop(a[0]); setMode(a[2]); doMeans(); doCI();
    });
  });
  $("draw").addEventListener("click", doMeans); $("ci").addEventListener("click", doCI);
  Lab.hover($("cv"), $("tip"), function (x) {
    if (!means) return null; var r0 = range(), lo = r0[0], hi = r0[1];
    var bw = (hi - lo) / 36, j = Math.floor((x - lo) / bw); if (j < 0 || j >= 36) return null;
    var a = lo + j * bw, k = means.filter(function (m) { return m >= a && m < a + bw; }).length;
    return "<b>" + f(a) + " to " + f(a + bw) + "</b><br>" + k + " of 1,000 averages";
  }, function (x) { hoverX = null; if (x !== null && means) { var r1 = range(), lo = r1[0], hi = r1[1], bw = (hi - lo) / 36; hoverX = lo + (Math.floor((x - lo) / bw) + 0.5) * bw; } renderMeans(); }, function () { return 0; });
  window.addEventListener("resize", function () { renderMeans(); renderCI(); });
  setPop("scores");
})();
```
