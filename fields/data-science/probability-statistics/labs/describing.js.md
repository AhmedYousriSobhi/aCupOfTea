# describing.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/labs/describing.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/data-science/probability-statistics/labs/describing.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, K = "scores", div = "p", hoverX = null;
  Lab.theme($("theme"));
  var SETS = {
    scores: { v: [52, 55, 55, 58, 58, 58, 62, 62, 62, 71, 71, 89, 89, 89, 93, 93, 94, 94, 95, 104], bin: 8, max: 120, d: "Mira's 20 tasting scores: two clumps, one around 58 and one around 92. The mean falls in the gap between them." },
    houses: { v: [1, 2, 2, 3, 5, 9, 20], bin: 1, max: 300, d: "Kettle Street's seven houses, counted in rooms: one huge house stretches the right tail." }
  };
  function quant(sorted, p) { // exclusive method (Python's statistics.quantiles default)
    var n = sorted.length, pos = p * (n + 1);
    if (pos <= 1) return sorted[0]; if (pos >= n) return sorted[n - 1];
    var i = Math.floor(pos), fr = pos - i; return sorted[i - 1] + fr * (sorted[i] - sorted[i - 1]);
  }
  function data() {
    var v = SETS[K].v.slice(), e = +$("extra").value; if (e > 0) v.push(e); return v.sort(function (a, b) { return a - b; });
  }
  function stats(v) {
    var n = v.length, m = v.reduce(function (a, b) { return a + b; }, 0) / n, ss = 0;
    v.forEach(function (x) { ss += (x - m) * (x - m); });
    var q1 = quant(v, 0.25), md = quant(v, 0.5), q3 = quant(v, 0.75);
    return { n: n, m: m, md: md, q1: q1, q3: q3, sd: Math.sqrt(ss / (div === "p" ? n : n - 1)) };
  }
  function f(x, d) { return Number(x).toFixed(d === undefined ? 2 : d); }
  function render() {
    var v = data(), s = stats(v), w = +$("bin").value, lo = Math.floor(Math.min(v[0], 0) / w) * w, hi = Math.ceil((v[v.length - 1] + 1) / w) * w, bins = [], x, j;
    if (hi === lo) hi += w;
    for (x = lo; x < hi; x += w) bins.push(0);
    v.forEach(function (a) { j = Math.min(bins.length - 1, Math.floor((a - lo) / w)); bins[j]++; });
    var bars = bins.map(function (c, i) { return { x: lo + (i + 0.5) * w, y: c }; });
    var ch = Lab.barChart($("cv"), { bars: bars, bw: w, xmin: lo, xmax: hi, ymax: Math.max.apply(null, bins) * 1.15, yint: true, xstep: Math.max(1, Math.round((hi - lo) / 8)), xlabel: "value", ylabel: "count", hoverX: hoverX === null ? null : hoverX, alpha: 0.9, barw: 0.95 });
    var c = ch.ctx;
    [[s.m, ch.col.acc2, "mean"], [s.md, ch.col.acc3, "median"]].forEach(function (t, i) {
      c.strokeStyle = t[1]; c.lineWidth = 3; c.setLineDash(i ? [6, 4] : []); c.beginPath(); c.moveTo(ch.X(t[0]), ch.T); c.lineTo(ch.X(t[0]), ch.Y(0)); c.stroke();
    });
    c.setLineDash([]); c.lineWidth = 1;
    $("r-n").textContent = s.n; $("r-mean").textContent = f(s.m); $("r-med").textContent = f(s.md); $("r-sd").textContent = f(s.sd); $("r-iqr").textContent = f(s.q3 - s.q1);
    var gap = s.m - s.md; $("r-gap").textContent = (gap > 0 ? "+" : "") + f(gap);
    var big = Math.abs(gap) > 0.25 * s.sd, b = $("r-b"); b.textContent = !big ? "balanced" : gap > 0 ? "right tail" : "left tail"; b.className = "badge" + (big ? " bad" : "");
    $("extra-v").textContent = +$("extra").value === 0 ? "none" : $("extra").value; $("bin-v").textContent = w;
    $("cv").setAttribute("aria-label", "Histogram with bins " + w + " wide. Mean " + f(s.m, 1) + ", median " + f(s.md, 1) + ".");
    box(v, s);
  }
  function box(v, s) {
    var cv = $("bx"), P = Lab.prep(cv, 0.2), c = P.ctx, col = Lab.colors(), L = 50, R = 12, W = P.w - L - R;
    var iqr = s.q3 - s.q1, lf = s.q1 - 1.5 * iqr, uf = s.q3 + 1.5 * iqr;
    var inside = v.filter(function (a) { return a >= lf && a <= uf; }), wl = inside[0], wh = inside[inside.length - 1], out = v.filter(function (a) { return a < lf || a > uf; });
    var lo = Math.min(v[0], 0), hi = v[v.length - 1] * 1.02, X = function (x) { return L + (x - lo) / (hi - lo) * W; }, y = P.h * 0.45, h = P.h * 0.34;
    c.clearRect(0, 0, P.w, P.h); c.strokeStyle = col.fg; c.fillStyle = col.acc; c.lineWidth = 2;
    c.beginPath(); c.moveTo(X(wl), y); c.lineTo(X(s.q1), y); c.moveTo(X(s.q3), y); c.lineTo(X(wh), y); c.moveTo(X(wl), y - h / 3); c.lineTo(X(wl), y + h / 3); c.moveTo(X(wh), y - h / 3); c.lineTo(X(wh), y + h / 3); c.stroke();
    c.globalAlpha = 0.35; c.fillRect(X(s.q1), y - h / 2, X(s.q3) - X(s.q1), h); c.globalAlpha = 1; c.strokeRect(X(s.q1), y - h / 2, X(s.q3) - X(s.q1), h);
    c.strokeStyle = col.acc3; c.beginPath(); c.moveTo(X(s.md), y - h / 2); c.lineTo(X(s.md), y + h / 2); c.stroke();
    c.fillStyle = col.acc2; out.forEach(function (a) { c.beginPath(); c.arc(X(a), y, 5, 0, 6.2832); c.fill(); });
    c.fillStyle = col.mut; c.font = "12px system-ui,sans-serif"; c.textAlign = "center"; c.fillText("Q1 " + f(s.q1, 1) + "   median " + f(s.md, 1) + "   Q3 " + f(s.q3, 1), L + W / 2, P.h - 6);
    $("bxcap").textContent = out.length ? "Outside the fences (" + f(lf, 1) + " to " + f(uf, 1) + "): " + out.map(function (a) { return f(a, 0); }).join(", ") + "." : "No value falls outside the fences (" + f(lf, 1) + " to " + f(uf, 1) + ").";
  }
  function setKind(k) {
    K = k; $("bin").value = SETS[k].bin; $("extra").max = SETS[k].max; $("extra").value = 0; $("desc").textContent = SETS[k].d;
    Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-k") === k ? "true" : "false"); });
    $("bin").max = k === "scores" ? 60 : 30; $("bin")._upd(); $("extra")._upd(); render();
  }
  function setDiv(d) { div = d; Array.prototype.forEach.call(document.querySelectorAll("#div button"), function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-d") === d ? "true" : "false"); }); render(); }
  Lab.slider("bin", String, render); Lab.slider("extra", function (v) { return v === 0 ? "none" : String(v); }, render);
  Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.addEventListener("click", function () { clearX(); setKind(b.getAttribute("data-k")); }); });
  Array.prototype.forEach.call(document.querySelectorAll("#div button"), function (b) { b.addEventListener("click", function () { setDiv(b.getAttribute("data-d")); }); });
  function clearX() { Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (c) { c.setAttribute("aria-pressed", "false"); }); }
  Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (btn) {
    btn.addEventListener("click", function () {
      var a = btn.getAttribute("data-x").split("|"); clearX(); btn.setAttribute("aria-pressed", "true");
      setKind(a[0]); $("bin").value = a[1]; $("extra").value = a[2]; $("bin")._upd(); $("extra")._upd(); setDiv(a[3]);
    });
  });
  // the histogram reads out the count of the bin under the pointer, arrow keys too
  Lab.hover($("cv"), $("tip"), function (x) {
    var v = data(), w = +$("bin").value, lo = Math.floor(Math.min(v[0], 0) / w) * w, i = Math.floor((x - lo) / w), a = lo + i * w;
    if (x < lo || i < 0) return null; var n = v.filter(function (t) { return t >= a && t < a + w; }).length;
    return "<b>" + f(a, 0) + " to " + f(a + w, 0) + "</b><br>" + n + " value" + (n === 1 ? "" : "s");
  }, function (x) { hoverX = x === null ? null : (function () { var w = +$("bin").value, v = data(), lo = Math.floor(Math.min(v[0], 0) / w) * w; return lo + (Math.floor((x - lo) / w) + 0.5) * w; })(); render(); }, function () { return +$("bin").value; });
  window.addEventListener("resize", render);
  setKind("scores");
})();
```
