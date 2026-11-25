# sampling-methods.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/labs/sampling-methods.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/data-science/probability-statistics/labs/sampling-methods.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, N = 4000, K = "door", ORDER = "pat", seed = 31, est = null, hoverX = null, BINS = 50;
  Lab.theme($("theme"));

  // The crowd: a pattern of 20 (8 students, 7 office workers, 5 retirees, spread evenly) repeated 200 times.
  var TARGET = { S: 8, O: 7, R: 5 }, SHARE = { S: 0.7, O: 0.5, R: 0.25 }, NAME = { S: "students", O: "office workers", R: "retirees" };
  var pattern = (function () {
    var got = { S: 0, O: 0, R: 0 }, out = [], i, best, g, v, bv;
    for (i = 0; i < 20; i++) {
      bv = -1e9; best = "S";
      ["S", "O", "R"].forEach(function (g2) { v = TARGET[g2] * (i + 1) / 20 - got[g2]; if (v > bv + 1e-12) { bv = v; best = g2; } });
      out.push(best); got[best]++;
    }
    return out;
  })();
  var group = new Array(N), loves = new Array(N), byGroup = { S: [], O: [], R: [] }, i;
  for (i = 0; i < N; i++) { group[i] = pattern[i % 20]; byGroup[group[i]].push(i); loves[i] = 0; }
  (function () { // exactly 70% / 50% / 25% of each group, chosen at random once
    var r = Lab.rng(5);
    ["S", "O", "R"].forEach(function (g) {
      var idx = byGroup[g].slice(), j, t, k, want = Math.round(idx.length * SHARE[g]);
      for (j = idx.length - 1; j > 0; j--) { k = Math.floor(r() * (j + 1)); t = idx[j]; idx[j] = idx[k]; idx[k] = t; }
      for (j = 0; j < want; j++) loves[idx[j]] = 1;
    });
  })();
  var truth = (function () { var s = 0; loves.forEach(function (x) { s += x; }); return s / N; })();
  var sortedOrder = [].concat(byGroup.S, byGroup.O, byGroup.R);           // neighbourhoods: blocks of 100 of one kind
  var shuffled = (function () { var a = [], r = Lab.rng(9), j, k, t; for (j = 0; j < N; j++) a.push(j); for (j = N - 1; j > 0; j--) { k = Math.floor(r() * (j + 1)); t = a[j]; a[j] = a[k]; a[k] = t; } return a; })();
  var identity = (function () { var a = [], j; for (j = 0; j < N; j++) a.push(j); return a; })();

  var NAMES = { door: "Doorstep", srs: "Simple random", sys: "Systematic", strat: "Stratified", clus: "Cluster" };
  function descr() {
    var n = +$("n").value, k = Math.floor(N / n), c = Math.max(1, Math.round(n / 10));
    return {
      door: "Whoever comes in first on a Saturday morning: people who love new things are nine times as likely to be asked. Easy, and biased.",
      srs: "Number the 4,000 customers and let the generator pick " + n + ". Everyone, and every possible group of " + n + ", has the same chance.",
      sys: "Step k = 4,000 / " + n + " = " + k + ", random start, then every " + k + "th customer. Fair only if the list has no rhythm that matches " + k + ".",
      strat: "Split into students, office workers and retirees and draw at random inside each, in proportion: " + [["S", 0], ["O", 0], ["R", 0]].map(function (p) { return Math.round(n * byGroup[p[0]].length / N) + " " + NAME[p[0]]; }).join(", ") + ".",
      clus: "Pick " + c + " random neighbourhoods (blocks of 100 neighbours who resemble each other) and ask everyone in them: " + (c * 100) + " people."
    };
  }
  function share(arr) { var s = 0, j; for (j = 0; j < arr.length; j++) s += loves[arr[j]]; return s / arr.length; }
  function pick(k, n, r, ord) {
    var i2, out = [], seen, idx, j, t, c, a, st;
    if (k === "srs") { seen = {}; while (out.length < n) { j = Math.floor(r() * N); if (!seen[j]) { seen[j] = 1; out.push(j); } } return out; }
    if (k === "door") { seen = {}; while (out.length < n) { j = Math.floor(r() * N); if (!seen[j] && r() * 9 < (loves[j] ? 9 : 1)) { seen[j] = 1; out.push(j); } } return out; }
    if (k === "sys") { st = Math.floor(N / n); a = ord === "pat" ? identity : shuffled; j = Math.floor(r() * st); for (i2 = 0; i2 < n; i2++) out.push(a[j + i2 * st]); return out; }
    if (k === "strat") {
      ["S", "O", "R"].forEach(function (g) {
        var pool = byGroup[g], m = Math.round(n * pool.length / N), s2 = {}, c2 = 0, q;
        while (c2 < m) { q = Math.floor(r() * pool.length); if (!s2[q]) { s2[q] = 1; c2++; out.push(pool[q]); } }
      });
      return out;
    }
    c = Math.max(1, Math.round(n / 10)); seen = {};
    while (Object.keys(seen).length < c) seen[Math.floor(r() * 40)] = 1;
    Object.keys(seen).forEach(function (b) { for (t = 0; t < 100; t++) out.push(sortedOrder[+b * 100 + t]); });
    return out;
  }
  function repeat(k, n, reps, ord, r) {
    var e = new Array(reps), s = 0, ss = 0, sz = 0, j, x, p;
    for (j = 0; j < reps; j++) { p = pick(k, n, r, ord); x = share(p); e[j] = x; s += x; ss += x * x; sz = p.length; }
    var m = s / reps, sd = Math.sqrt(Math.max(0, ss / reps - m * m));
    return { e: e, mean: m, sd: sd, size: sz };
  }
  function pc(x, d) { return Lab.pct(x, d === undefined ? 1 : d); }

  function head() {
    var d = descr(); $("desc").textContent = d[K]; $("truth").textContent = pc(truth, 2);
    $("orderrow").hidden = K !== "sys";
  }
  function render() {
    var bars = [], cnt = new Array(BINS).fill(0), j, top = 0.05;
    if (est) {
      est.e.forEach(function (x) { var b = Math.min(BINS - 1, Math.floor(x * BINS)); cnt[b]++; });
      cnt.forEach(function (c, b) { var y = c / est.e.length; bars.push({ x: (b + 0.5) * 100 / BINS, y: y }); top = Math.max(top, y); });
    } else bars.push({ x: 50, y: 0 });
    var ch = Lab.barChart($("cv"), { bars: bars, bw: 100 / BINS, alpha: 0.8, pctAxis: true, ymax: top * 1.15, xmin: 0, xmax: 100, xstep: 10, xlabel: "estimated share who would buy (%)", ylabel: "share of samples", hoverX: hoverX, ratio: 0.46 });
    var c = ch.ctx; c.strokeStyle = ch.col.acc2; c.lineWidth = 3; c.setLineDash([6, 4]); c.beginPath(); c.moveTo(ch.X(truth * 100), ch.T); c.lineTo(ch.X(truth * 100), ch.Y(0)); c.stroke(); c.setLineDash([]); c.lineWidth = 1;
    $("m-mean").textContent = est ? pc(est.mean, 1) : "–";
    $("m-sd").textContent = est ? (est.sd * 100).toFixed(1) + " points" : "–";
    $("m-n").textContent = est ? String(est.size) : "–";
    head();
  }
  function doMany() { est = repeat(K, +$("n").value, 1000, ORDER, Lab.rng(seed++)); render(); }
  function doOne() {
    var r = Lab.rng(seed++), n = +$("n").value, p = pick(K, n, r, ORDER), g = { S: 0, O: 0, R: 0 }, j;
    for (j = 0; j < p.length; j++) g[group[p[j]]]++;
    $("onemsg").innerHTML = NAMES[K] + ": asked <b>" + p.length + "</b> people (" + g.S + " students, " + g.O + " office workers, " + g.R + " retirees). <b>" + pc(share(p), 1) + "</b> would buy; the truth is <b>" + pc(truth, 2) + "</b>.";
  }
  function doAll() {
    var n = +$("n").value, rows = "", k;
    ["door", "srs", "sys", "strat", "clus"].forEach(function (k2) {
      var o = repeat(k2, n, 400, ORDER, Lab.rng(seed++));
      rows += "<tr><td>" + NAMES[k2] + (k2 === "sys" ? (ORDER === "pat" ? " (patterned list)" : " (shuffled list)") : "") + "</td><td>" + o.size + "</td><td>" + pc(o.mean, 1) + "</td><td>" + (o.sd * 100).toFixed(1) + " points</td></tr>";
    });
    $("cmpb").innerHTML = rows; $("cmp").hidden = false; $("cmp").open = true;
  }

  function setK(k) {
    K = k; est = null; $("onemsg").textContent = "";
    Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-k") === k ? "true" : "false"); });
    render();
  }
  function setOrder(o) { ORDER = o; est = null; Array.prototype.forEach.call(document.querySelectorAll("#order button"), function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-o") === o ? "true" : "false"); }); render(); }
  function clearX() { Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (c) { c.setAttribute("aria-pressed", "false"); }); }
  Lab.slider("n", String, function () { est = null; $("onemsg").textContent = ""; render(); });
  Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.addEventListener("click", function () { clearX(); setK(b.getAttribute("data-k")); }); });
  Array.prototype.forEach.call(document.querySelectorAll("#order button"), function (b) { b.addEventListener("click", function () { setOrder(b.getAttribute("data-o")); }); });
  Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (btn) {
    btn.addEventListener("click", function () {
      var a = btn.getAttribute("data-x").split("|"); clearX(); btn.setAttribute("aria-pressed", "true");
      $("n").value = a[1]; $("n")._upd(); ORDER = a[2]; setOrder(a[2]); setK(a[0]); doMany();
    });
  });
  $("one").addEventListener("click", doOne); $("many").addEventListener("click", doMany); $("all").addEventListener("click", doAll);
  Lab.hover($("cv"), $("tip"), function (x) {
    if (!est) return null; var b = Math.floor(x * BINS / 100); if (b < 0 || b >= BINS) return null;
    var k = est.e.filter(function (v) { return Math.min(BINS - 1, Math.floor(v * BINS)) === b; }).length;
    return "<b>" + (b * 100 / BINS).toFixed(0) + "% to " + ((b + 1) * 100 / BINS).toFixed(0) + "%</b><br>" + k + " of 1,000 samples";
  }, function (x) { hoverX = null; if (x !== null && est) { hoverX = (Math.floor(x * BINS / 100) + 0.5) * 100 / BINS; } render(); }, function () { return 0; });
  window.addEventListener("resize", render);
  setK("door");
})();
```
