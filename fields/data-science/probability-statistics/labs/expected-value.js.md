# expected-value.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/labs/expected-value.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/data-science/probability-statistics/labs/expected-value.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, seed = 41, run = null, hoverX = null, prizes = [], i;
  Lab.theme($("theme"));
  var PRESETS = {
    tin: { prizes: [0, 5, 10, 20], counts: [5, 3, 1, 1], price: 5, max: 10 },
    tin6: { prizes: [0, 5, 10, 20], counts: [5, 3, 1, 1], price: 6, max: 10 },
    die: { prizes: [1, 2, 3, 4, 5, 6], counts: [1, 1, 1, 1, 1, 1], price: 0, max: 10 },
    lotto: { prizes: [0, 1000], counts: [999, 1], price: 0, max: 1000 }
  };
  function f(x, d) { return String(Number(x.toFixed(d === undefined ? 4 : d))); }
  function money(x) { return (x < 0 ? "−" : "") + f(Math.abs(x), 4); }

  function table() { // active slots: prize with its card count
    var t = [], j, total = 0;
    for (j = 0; j < prizes.length; j++) { var c = +$("c" + j).value; total += c; t.push({ x: prizes[j], c: c }); }
    t.forEach(function (r) { r.p = total ? r.c / total : 0; });
    return { rows: t, total: total };
  }
  function stats(t) {
    var E = 0, E2 = 0, best = -1, modes = [];
    t.rows.forEach(function (r) { E += r.x * r.p; E2 += r.x * r.x * r.p; best = Math.max(best, r.c); });
    t.rows.forEach(function (r) { if (r.c === best && r.c > 0) modes.push(r.x); });
    var v = Math.max(0, E2 - E * E), exact = 0;
    t.rows.forEach(function (r) { if (Math.abs(r.x - E) < 1e-9) exact += r.p; });
    return { E: E, V: v, SD: Math.sqrt(v), modes: modes, allTie: modes.length === t.rows.filter(function (r) { return r.c > 0; }).length && modes.length > 1, exact: exact };
  }

  function render() {
    var t = table(), s = stats(t), price = +$("price").value;
    if (!t.total) { $("ev").innerHTML = "n/a<small>put at least one card in the bag</small>"; return; }
    $("ev").innerHTML = f(s.E) + "<small>expected prize per pull</small>";
    $("var").textContent = f(s.V); $("sd").textContent = f(s.SD);
    $("mode").textContent = s.allTie ? "all tie" : s.modes.join(" and ");
    $("net").textContent = money(s.E - price); $("exact").textContent = Lab.pct(s.exact, 1);
    var isPrize = t.rows.some(function (r) { return r.c > 0 && Math.abs(r.x - s.E) < 1e-9; });
    $("says").innerHTML = "Over many pulls the prize averages <b>" + f(s.E) + "</b>. " + (isPrize ? "Here that happens to be a real prize." : "No card says " + f(s.E) + ": it is the balance point, not a prediction of one pull.") + " The most likely single prize is <b>" + (s.allTie ? "a tie between all of them" : s.modes.join(" and ")) + "</b>.";
    $("e2").textContent = f(2 * s.E); $("v2").textContent = f(2 * s.V); $("v2x").textContent = f(4 * s.V);
    // chart: one bar per prize, a dashed line at E
    var xs = t.rows.map(function (r) { return r.x; }), lo = Math.min.apply(null, xs), hi = Math.max.apply(null, xs), span = Math.max(hi - lo, 1), pad = span * 0.12;
    var bars = t.rows.map(function (r) { return { x: r.x, y: r.p }; });
    var ch = Lab.barChart($("cv"), { bars: bars, bw: span / (xs.length * 2.4), alpha: 0.85, pctAxis: true, ymax: Math.max.apply(null, bars.map(function (b) { return b.y; })) * 1.15, xmin: lo - pad - span * 0.05, xmax: hi + pad + span * 0.05, xlabel: "prize", ylabel: "probability", hoverX: hoverX, ratio: 0.42, xstep: span > 30 ? 100 : 1 });
    var c = ch.ctx; c.strokeStyle = ch.col.acc2; c.lineWidth = 3; c.setLineDash([6, 4]); c.beginPath(); c.moveTo(ch.X(s.E), ch.T); c.lineTo(ch.X(s.E), ch.Y(0)); c.stroke(); c.setLineDash([]); c.lineWidth = 1;
    c.fillStyle = ch.col.acc2; c.font = "600 12px system-ui,sans-serif"; c.textAlign = ch.X(s.E) > ch.W - 70 ? "right" : "left"; c.fillText("E = " + f(s.E, 3), ch.X(s.E) + (ch.X(s.E) > ch.W - 70 ? -6 : 6), ch.T + 12);
    renderRun();
  }

  function renderRun() {
    var cv = $("cr"), P = Lab.prep(cv, 0.5), c = P.ctx, col = Lab.colors(), L = 50, R = 14, T = 10, B = 36, W = P.w - L - R, H = P.h - T - B, t = table(), s = stats(t);
    c.clearRect(0, 0, P.w, P.h); c.font = "12px system-ui,sans-serif";
    if (!run || !t.total) { c.fillStyle = col.mut; c.textAlign = "center"; c.fillText("Press one of the pull buttons", P.w / 2, P.h / 2); return; }
    var xs = t.rows.map(function (r) { return r.x; }), lo = Math.min.apply(null, xs), hi = Math.max.apply(null, xs), pad = (hi - lo) * 0.05 || 1; lo -= pad; hi += pad;
    var lx = Math.log10(run.N), X = function (n) { return L + Math.log10(n) / lx * W; }, Y = function (y) { return T + H - (y - lo) / (hi - lo) * H; };
    var k, y;
    c.strokeStyle = col.line; c.fillStyle = col.mut; c.textAlign = "right";
    for (k = 0; k <= 4; k++) { y = lo + (hi - lo) * k / 4; var yy = Math.round(Y(y)) + 0.5; c.beginPath(); c.moveTo(L, yy); c.lineTo(P.w - R, yy); c.stroke(); c.fillText(f(y, 1), L - 6, yy + 4); }
    c.textAlign = "center"; for (k = 0; k <= lx; k++) c.fillText(Math.pow(10, k).toLocaleString("en"), X(Math.pow(10, k)), T + H + 16);
    c.font = "600 12px system-ui,sans-serif"; c.fillText("number of pulls", L + W / 2, P.h - 4); c.font = "12px system-ui,sans-serif";
    // band E +/- 2 SD / sqrt(n)
    c.fillStyle = col.line; c.globalAlpha = 0.5; c.beginPath();
    var n;
    for (k = 0; k <= 120; k++) { n = Math.pow(10, lx * k / 120); y = Math.min(hi, s.E + 2 * s.SD / Math.sqrt(n)); if (k) c.lineTo(X(n), Y(y)); else c.moveTo(X(n), Y(y)); }
    for (k = 120; k >= 0; k--) { n = Math.pow(10, lx * k / 120); y = Math.max(lo, s.E - 2 * s.SD / Math.sqrt(n)); c.lineTo(X(n), Y(y)); }
    c.closePath(); c.fill(); c.globalAlpha = 1;
    c.strokeStyle = col.acc2; c.lineWidth = 2.5; c.setLineDash([6, 4]); c.beginPath(); c.moveTo(L, Y(s.E)); c.lineTo(L + W, Y(s.E)); c.stroke(); c.setLineDash([]);
    c.strokeStyle = col.acc; c.lineWidth = 2.2; c.lineJoin = "round"; c.beginPath();
    run.pts.forEach(function (p, j) { if (j) c.lineTo(X(p.n), Y(p.m)); else c.moveTo(X(p.n), Y(p.m)); }); c.stroke(); c.lineWidth = 1;
  }

  function pull(N) {
    var t = table(); if (!t.total) return;
    var r = Lab.rng(seed++), cum = [], a = 0, j, sum = 0, zero = 0, pts = [], next = 1, step = Math.pow(10, 1 / 12);
    t.rows.forEach(function (row) { a += row.p; cum.push(a); });
    for (j = 1; j <= N; j++) {
      var u = r(), q = 0; while (q < cum.length - 1 && u >= cum[q]) q++;
      var x = t.rows[q].x; sum += x; if (x === 0) zero++;
      if (j >= next || j === N) { pts.push({ n: j, m: sum / j }); next = Math.max(j + 1, Math.ceil(j * step)); }
    }
    var s = stats(t); run = { N: N, pts: pts };
    $("r-mean").textContent = f(sum / N, 3); $("r-off").textContent = f(Math.abs(sum / N - s.E), 3); $("r-zero").textContent = Lab.pct(zero / N, 1);
    renderRun();
  }

  function setPreset(key) {
    var p = PRESETS[key]; prizes = p.prizes.slice(); run = null;
    ["r-mean", "r-off", "r-zero"].forEach(function (id) { $(id).textContent = "–"; });
    for (i = 0; i < 6; i++) {
      var on = i < prizes.length, el = $("c" + i);
      $("d" + i).hidden = !on;
      if (on) { el.max = p.max; $("cmax" + i).textContent = p.max; el.value = p.counts[i]; $("cl" + i).textContent = "Cards that say " + prizes[i]; el._upd(); }
    }
    $("price").value = p.price; $("price")._upd(); render();
  }
  function clearX() { Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (c) { c.setAttribute("aria-pressed", "false"); }); }
  for (i = 0; i < 6; i++) Lab.slider("c" + i, function (v) { return String(v); }, function () { clearX(); run = null; render(); });
  Lab.slider("price", function (v) { return f(v, 1); }, render);
  Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (b) { b.addEventListener("click", function () { clearX(); b.setAttribute("aria-pressed", "true"); setPreset(b.getAttribute("data-p")); }); });
  $("p10").addEventListener("click", function () { pull(10); }); $("p1k").addEventListener("click", function () { pull(1000); }); $("p100k").addEventListener("click", function () { pull(100000); });
  Lab.hover($("cv"), $("tip"), function (x) {
    var t = table(), best = null; t.rows.forEach(function (r) { if (best === null || Math.abs(r.x - x) < Math.abs(best.x - x)) best = r; }); if (!best || !t.total) return null;
    return "<b>Prize " + best.x + "</b><br>" + best.c + " of " + t.total + " cards (" + Lab.pct(best.p, 1) + ")";
  }, function (x) { var t = table(), best = null; hoverX = null; if (x !== null) { t.rows.forEach(function (r) { if (best === null || Math.abs(r.x - x) < Math.abs(best.x - x)) best = r; }); if (best) hoverX = best.x; } render(); }, function () { return 0; });
  window.addEventListener("resize", render);
  prizes = PRESETS.tin.prizes.slice(); setPreset("tin"); document.querySelector(".xcard").setAttribute("aria-pressed", "true");
})();
```
