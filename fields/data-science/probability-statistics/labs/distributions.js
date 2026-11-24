(function () {
  "use strict";
  var $ = Lab.$, M = 5000, seed = 7, sample = null;
  function kind() { return $("dist").value; }
  function show(id, on) { $(id).hidden = !on; }
  function setRange(lo, hi, step, aVal, bVal) {
    ["a", "b"].forEach(function (id) { var e = $(id); e.min = lo; e.max = hi; e.step = step; });
    $("a").value = aVal; $("b").value = bVal;
  }
  function configure() {
    var k = kind();
    show("g-n", k === "binom"); show("g-p", k === "binom"); show("g-lam", k === "pois");
    show("g-mu", k === "norm"); show("g-sd", k === "norm"); $("over").parentNode.hidden = k !== "binom";
    sample = null; $("msg").textContent = "";
    if (k === "binom") { var n = +$("n").value; setRange(0, n, 1, Math.min(2, n), Math.min(4, n)); }
    if (k === "pois") { setRange(0, hiPois(), 1, 2, 6); }
    if (k === "norm") { setRange(+$("mu").value - 4 * +$("sd").value, +$("mu").value + 4 * +$("sd").value, 0.5, +$("mu").value - 2 * +$("sd").value, +$("mu").value + 2 * +$("sd").value); }
    labels(); render();
  }
  function hiPois() { var l = +$("lam").value; return Math.ceil(l + 6 * Math.sqrt(l) + 5); }
  function labels() {
    var d = function (id, f) { $(id + "-v").textContent = f($(id).value); };
    d("n", String); d("p", function (v) { return (+v).toFixed(2); }); d("lam", function (v) { return (+v).toFixed(1); });
    d("mu", String); d("sd", function (v) { return (+v).toFixed(1); });
    $("a-v").textContent = (+$("a").value).toFixed(kind() === "norm" ? 1 : 0);
    $("b-v").textContent = (+$("b").value).toFixed(kind() === "norm" ? 1 : 0);
  }
  function theory() {
    var k = kind();
    if (k === "binom") { var n = +$("n").value, p = +$("p").value; return { m: n * p, v: n * p * (1 - p) }; }
    if (k === "pois") { var l = +$("lam").value; return { m: l, v: l }; }
    var s = +$("sd").value; return { m: +$("mu").value, v: s * s };
  }
  function draw() {
    var k = kind(), r = Lab.rng(seed++), xs = new Array(M), i;
    for (i = 0; i < M; i++) {
      xs[i] = k === "binom" ? Lab.binomSample(+$("n").value, +$("p").value, r)
        : k === "pois" ? Lab.poisSample(+$("lam").value, r)
        : +$("mu").value + +$("sd").value * Lab.normal(r);
    }
    sample = xs; render();
    $("msg").textContent = "Drew " + M + " values (seed " + (seed - 1) + "). Draw again for another batch.";
  }
  function sampleStats() {
    var m = 0, v = 0, i; if (!sample) return null;
    for (i = 0; i < sample.length; i++) m += sample[i]; m /= sample.length;
    for (i = 0; i < sample.length; i++) v += (sample[i] - m) * (sample[i] - m); v /= sample.length - 1;
    return { m: m, v: v };
  }
  function render() {
    labels();
    var k = kind(), th = theory(), a = +$("a").value, b = +$("b").value, lo = Math.min(a, b), hi = Math.max(a, b), bars = [], line = null, opt = {pctAxis: true}, pr = 0, x;
    if (k === "norm") {
      var mu = +$("mu").value, sd = +$("sd").value, xmin = mu - 4.5 * sd, xmax = mu + 4.5 * sd, nb = 36, bw = (xmax - xmin) / nb;
      pr = Lab.ncdf((hi - mu) / sd) - Lab.ncdf((lo - mu) / sd);
      var dens = function (x) { return Math.exp(-0.5 * Math.pow((x - mu) / sd, 2)) / (sd * Math.sqrt(2 * Math.PI)); };
      line = [];
      for (x = xmin; x <= xmax; x += bw / 5) line.push({ x: x, y: dens(x) });
      if (sample) {
        var cnt = new Array(nb).fill(0);
        sample.forEach(function (s) { var j = Math.floor((s - xmin) / bw); if (j >= 0 && j < nb) cnt[j]++; });
        cnt.forEach(function (c, j) { bars.push({ x: xmin + (j + 0.5) * bw, y: c / sample.length / bw }); });
      } else { bars.push({ x: mu, y: 0 }); }
      opt = { xmin: xmin, xmax: xmax, bw: bw, alpha: 0.6, line: line, ymax: dens(mu) * 1.25, xstep: sd };
      var ch = Lab.barChart($("cv"), Object.assign({ bars: bars }, opt));
      // shade the chosen range under the curve
      var c = ch.ctx; c.fillStyle = ch.col.acc2; c.globalAlpha = 0.35; c.beginPath();
      c.moveTo(ch.X(lo), ch.Y(0));
      for (x = lo; x <= hi; x += bw / 10) c.lineTo(ch.X(x), ch.Y(dens(x)));
      c.lineTo(ch.X(hi), ch.Y(0)); c.closePath(); c.fill(); c.globalAlpha = 1;
      $("legend").textContent = "Line = normal density; shaded = P(a ≤ X ≤ b) as area; bars = sample histogram (if drawn).";
    } else {
      var kmax = k === "binom" ? +$("n").value : hiPois(), pmf = function (j) { return k === "binom" ? Lab.binomPmf(+$("n").value, +$("p").value, j) : Lab.poisPmf(+$("lam").value, j); };
      for (var j = 0; j <= kmax; j++) {
        var y = pmf(j), inr = j >= lo && j <= hi; if (inr) pr += y;
        bars.push({ x: j, y: y, shade: inr, color: undefined });
      }
      var simBars = null;
      if (sample) {
        var cn = new Array(kmax + 1).fill(0);
        sample.forEach(function (s) { if (s >= 0 && s <= kmax) cn[s]++; });
        simBars = cn;
      }
      var over = k === "binom" && $("over").checked, ln = null;
      if (over) { ln = []; var l2 = +$("n").value * +$("p").value; for (var q = 0; q <= kmax; q++) ln.push({ x: q, y: Lab.poisPmf(l2, q) }); }
      var allY = bars.map(function (z) { return z.y; }).concat(simBars ? simBars.map(function (z) { return z / M; }) : [], ln ? ln.map(function (z) { return z.y; }) : [0]);
      var ch2 = Lab.barChart($("cv"), { bars: bars, line: ln, pctAxis: true, ymax: Math.max.apply(null, allY) * 1.15, xmin: -0.5, xmax: kmax + 0.5, xstep: kmax > 40 ? 5 : 1, barw: 0.85, alpha: 0.85 });
      if (simBars) {
        var c2 = ch2.ctx; c2.strokeStyle = ch2.col.acc3; c2.lineWidth = 2;
        simBars.forEach(function (cc, jj) { var yy = cc / M, x0 = ch2.X(jj - 0.42), x1 = ch2.X(jj + 0.42); c2.beginPath(); c2.moveTo(x0, ch2.Y(yy)); c2.lineTo(x1, ch2.Y(yy)); c2.stroke(); });
        c2.lineWidth = 1;
      }
      $("legend").textContent = "Bars = exact probabilities (orange = inside a..b); blue ticks = sample share" + (over ? "; black line = Poisson(np)." : ".");
    }
    $("l-range").textContent = k === "norm" ? "P(a ≤ X ≤ b), area" : "P(a ≤ X ≤ b), sum of bars";
    $("prange").textContent = Lab.pct(pr, 3);
    var st = sampleStats();
    $("mean").textContent = Lab.fmt(th.m, 3) + " / " + (st ? Lab.fmt(st.m, 3) : "–");
    $("var").textContent = Lab.fmt(th.v, 3) + " / " + (st ? Lab.fmt(st.v, 3) : "–");
  }
  ["n", "p", "lam", "mu", "sd"].forEach(function (id) {
    $(id).addEventListener("input", function () {
      if (id === "n" || id === "lam" || id === "mu" || id === "sd") configure(); else { sample = null; render(); }
    });
  });
  ["a", "b"].forEach(function (id) { $(id).addEventListener("input", render); });
  $("over").addEventListener("change", render);
  $("dist").addEventListener("change", configure);
  $("draw").addEventListener("click", draw);
  $("clear").addEventListener("click", function () { sample = null; $("msg").textContent = ""; render(); });
  Array.prototype.forEach.call(document.querySelectorAll("button[data-x]"), function (btn) {
    btn.addEventListener("click", function () {
      var v = btn.getAttribute("data-x").split("|");
      $("dist").value = v[0]; $("n").value = Math.max(1, +v[1] || 10); $("p").value = +v[2] || 0.3;
      $("lam").value = +v[3] || 4; $("mu").value = +v[4] || 100; $("sd").value = +v[5] || 4;
      configure();
      $("a").value = v[6]; $("b").value = v[7] !== undefined ? v[7] : v[6];
      $("over").checked = v[8] === "1" && v[0] === "binom";
      draw();
    });
  });
  window.addEventListener("resize", render);
  configure();
})();
