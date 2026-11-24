(function () {
  "use strict";
  var $ = Lab.$, M = 5000, seed = 7, sample = null, hoverX = null, K = "binom";
  Lab.theme($("theme"));
  var DESC = {
    binom: "How many yeses in n independent tries, each with the same chance p? (Customers who pick the smoky blend, defective bulbs in a box, heads in flips.)",
    pois: "How many events land in a window of time, when they arrive at a steady average rate λ? (Customers per 10 minutes, emails per hour.)",
    norm: "Measurements that pile up around a mean with a symmetric spread: probability is the area under the bell between two values."
  };
  function show(id, on) { $(id).hidden = !on; }
  function hiPois() { var l = +$("lam").value; return Math.ceil(l + 6 * Math.sqrt(l) + 5); }
  function setRange(lo, hi, step, a, b) {
    ["a", "b"].forEach(function (id) { var e = $(id); e.min = lo; e.max = hi; e.step = step; });
    $("a").value = a; $("b").value = b; $("a")._upd(); $("b")._upd();
  }
  function theory() {
    if (K === "binom") { var n = +$("n").value, p = +$("p").value; return { m: n * p, v: n * p * (1 - p) }; }
    if (K === "pois") { var l = +$("lam").value; return { m: l, v: l }; }
    var s = +$("sd").value; return { m: +$("mu").value, v: s * s };
  }
  function pmf(j) { return K === "binom" ? Lab.binomPmf(+$("n").value, +$("p").value, j) : Lab.poisPmf(+$("lam").value, j); }
  function kmax() { return K === "binom" ? +$("n").value : hiPois(); }

  function setKind(k, keepRange) {
    K = k; sample = null; hoverX = null; $("msg").textContent = "";
    Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-k") === k ? "true" : "false"); });
    show("g-n", k === "binom"); show("g-p", k === "binom"); show("g-lam", k === "pois"); show("g-mu", k === "norm"); show("g-sd", k === "norm");
    $("overrow").hidden = k !== "binom"; $("disp-card").hidden = k === "norm";
    $("qdesc").textContent = DESC[k];
    if (!keepRange) resetRange();
    render();
  }
  function resetRange() {
    if (K === "binom") { var n = +$("n").value; setRange(0, n, 1, Math.min(2, n), Math.min(4, n)); }
    if (K === "pois") setRange(0, hiPois(), 1, 2, 6);
    if (K === "norm") { var mu = +$("mu").value, sd = +$("sd").value; setRange(mu - 4 * sd, mu + 4 * sd, 0.5, mu - 2 * sd, mu + 2 * sd); }
  }

  function draw() {
    var r = Lab.rng(seed++), xs = new Array(M), i;
    for (i = 0; i < M; i++) {
      xs[i] = K === "binom" ? Lab.binomSample(+$("n").value, +$("p").value, r) : K === "pois" ? Lab.poisSample(+$("lam").value, r) : +$("mu").value + +$("sd").value * Lab.normal(r);
    }
    sample = xs; render();
    $("msg").textContent = "Drew " + M.toLocaleString("en") + " values (seed " + (seed - 1) + "). Draw again for a new batch.";
  }
  function sampleStats() {
    if (!sample) return null; var m = 0, v = 0, i;
    for (i = 0; i < sample.length; i++) m += sample[i]; m /= sample.length;
    for (i = 0; i < sample.length; i++) v += (sample[i] - m) * (sample[i] - m); v /= sample.length - 1;
    return { m: m, v: v };
  }
  function simCounts() {
    if (!sample) return null; var cn = new Array(kmax() + 1).fill(0);
    sample.forEach(function (s) { if (s >= 0 && s <= kmax()) cn[s]++; });
    return cn;
  }

  function legend(over) {
    if (K === "norm") { $("legend").innerHTML = '<span><i class="dot ink"></i>normal curve</span><span><i class="dot kettle"></i>area from a to b</span>' + (sample ? '<span><i class="dot leaf"></i>sample histogram</span>' : ""); return; }
    var items = ['<span><i class="dot leaf"></i>exact probability</span>', '<span><i class="dot kettle"></i>inside a..b</span>'];
    if (sample) items.push('<span><i class="dot sky"></i>sample share</span>');
    if (over) items.push('<span><i class="dot ink"></i>Poisson(np)</span>');
    $("legend").innerHTML = items.join("");
  }

  function render() {
    var th = theory(), a = +$("a").value, b = +$("b").value, lo = Math.min(a, b), hi = Math.max(a, b), pr = 0, bars = [], x, ch;
    var cv = $("cv");
    if (K === "norm") {
      var mu = +$("mu").value, sd = +$("sd").value, xmin = mu - 4.5 * sd, xmax = mu + 4.5 * sd, nb = 36, bw = (xmax - xmin) / nb;
      pr = Lab.ncdf((hi - mu) / sd) - Lab.ncdf((lo - mu) / sd);
      var dens = function (t) { return Math.exp(-0.5 * Math.pow((t - mu) / sd, 2)) / (sd * Math.sqrt(2 * Math.PI)); };
      var line = []; for (x = xmin; x <= xmax; x += bw / 5) line.push({ x: x, y: dens(x) });
      if (sample) {
        var cnt = new Array(nb).fill(0);
        sample.forEach(function (s) { var j = Math.floor((s - xmin) / bw); if (j >= 0 && j < nb) cnt[j]++; });
        cnt.forEach(function (c, j) { bars.push({ x: xmin + (j + 0.5) * bw, y: c / sample.length / bw }); });
      } else bars.push({ x: mu, y: 0 });
      ch = Lab.barChart(cv, { bars: bars, line: line, bw: bw, alpha: 0.55, ymax: dens(mu) * 1.25, xmin: xmin, xmax: xmax, xstep: sd, xlabel: "value", ylabel: "density" });
      var c = ch.ctx; c.fillStyle = ch.col.acc2; c.globalAlpha = 0.4; c.beginPath(); c.moveTo(ch.X(lo), ch.Y(0));
      for (x = lo; x <= hi; x += bw / 10) c.lineTo(ch.X(x), ch.Y(dens(x)));
      c.lineTo(ch.X(hi), ch.Y(0)); c.closePath(); c.fill(); c.globalAlpha = 1;
      if (hoverX !== null) { c.strokeStyle = ch.col.fg; c.setLineDash([4, 4]); c.beginPath(); c.moveTo(ch.X(hoverX), ch.T); c.lineTo(ch.X(hoverX), ch.Y(0)); c.stroke(); c.setLineDash([]); }
      legend(false);
    } else {
      var km = kmax(), cn = simCounts();
      for (var j = 0; j <= km; j++) { var y = pmf(j), inr = j >= lo && j <= hi; if (inr) pr += y; bars.push({ x: j, y: y, shade: inr }); }
      var over = K === "binom" && $("over").checked, ln = null, sim = null;
      if (over) { ln = []; var l2 = +$("n").value * +$("p").value; for (var q = 0; q <= km; q++) ln.push({ x: q, y: Lab.poisPmf(l2, q) }); }
      if (cn) sim = cn.map(function (cc, jj) { return { x: jj, y: cc / M }; });
      var ys = bars.map(function (z) { return z.y; }).concat(sim ? sim.map(function (z) { return z.y; }) : [], ln ? ln.map(function (z) { return z.y; }) : [0]);
      ch = Lab.barChart(cv, { bars: bars, line: ln, sim: sim, pctAxis: true, ymax: Math.max.apply(null, ys) * 1.18, xmin: -0.5, xmax: km + 0.5, xstep: km > 40 ? 5 : 1, barw: 0.8, hoverX: hoverX, xlabel: K === "binom" ? "number of yeses (k)" : "events in the window (k)", ylabel: "probability" });
      legend(over);
    }
    $("l-range").innerHTML = K === "norm" ? "P(a ≤ X ≤ b), area" : "P(a ≤ X ≤ b), sum of bars";
    $("prange").textContent = Lab.pct(pr, 2);
    var st = sampleStats();
    $("mean").textContent = Lab.fmt(th.m, 2) + " / " + (st ? Lab.fmt(st.m, 2) : "–");
    $("var").textContent = Lab.fmt(th.v, 2) + " / " + (st ? Lab.fmt(st.v, 2) : "–");
    if (K !== "norm") {
      var d = th.v / th.m; $("disp").textContent = Lab.fmt(d, 2) + (st ? " / " + Lab.fmt(st.v / st.m, 2) : "");
      var bd = $("disp-b"); bd.textContent = Math.abs(d - 1) < 0.05 ? "Poisson-like" : d < 1 ? "tighter than Poisson" : "wilder than Poisson"; bd.className = "badge" + (Math.abs(d - 1) < 0.05 ? "" : " bad");
    }
    ["n", "p", "lam", "mu", "sd", "a", "b"].forEach(function (id) { $(id)._upd(); });
    cv.setAttribute("aria-label", "Chart for " + (K === "binom" ? "binomial" : K === "pois" ? "Poisson" : "normal") + ". P(a to b) is " + Lab.pct(pr, 1) + ". Use arrow keys to read values.");
  }

  function tipFn(x) {
    if (K === "norm") {
      var mu = +$("mu").value, sd = +$("sd").value, z = (x - mu) / sd;
      return "<b>x = " + Lab.fmt(x, 1) + "</b> (z = " + Lab.fmt(z, 2) + ")<br>P(X ≤ x) = " + Lab.pct(Lab.ncdf(z), 2);
    }
    var k = Math.round(x); if (k < 0 || k > kmax()) return null;
    var t = "<b>k = " + k + "</b><br>exact " + Lab.pct(pmf(k), 2), cn = simCounts();
    if (cn) t += "<br>sample " + Lab.pct(cn[k] / M, 2);
    return t;
  }
  // discrete recipes snap to whole counts; the normal reads any value, in tenths of a spread
  Lab.hover($("cv"), $("tip"), tipFn, function (x) { hoverX = x; render(); }, function () { return K === "norm" ? +$("sd").value / 10 : 1; });

  var cfg = function (id, f) { Lab.slider(id, f, function () { if (id === "a" || id === "b" || id === "p") { sample = null; render(); } else { sample = null; hoverX = null; resetRange(); render(); } }); };
  cfg("n", String); cfg("lam", function (v) { return v.toFixed(1); }); cfg("mu", String); cfg("sd", function (v) { return v.toFixed(1); });
  Lab.slider("p", function (v) { return Math.round(v * 100) + "%"; }, function () { sample = null; render(); });
  Lab.slider("a", function (v) { return K === "norm" ? v.toFixed(1) : String(v); }, function () { render(); });
  Lab.slider("b", function (v) { return K === "norm" ? v.toFixed(1) : String(v); }, function () { render(); });

  Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) {
    b.addEventListener("click", function () { clearX(); setKind(b.getAttribute("data-k")); });
  });
  function clearX() { Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (c) { c.setAttribute("aria-pressed", "false"); }); }
  Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (btn) {
    btn.addEventListener("click", function () {
      clearX(); btn.setAttribute("aria-pressed", "true");
      var v = btn.getAttribute("data-x").split("|");
      $("n").value = Math.max(1, +v[1] || 10); $("p").value = +v[2] || 0.3; $("lam").value = +v[3] || 4; $("mu").value = +v[4] || 100; $("sd").value = +v[5] || 4;
      setKind(v[0]);
      $("a").value = v[6]; $("b").value = v[7];
      $("over").checked = v[8] === "1" && v[0] === "binom";
      draw();
      $("cv").scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  });
  $("over").addEventListener("change", render);
  $("draw").addEventListener("click", draw);
  $("clear").addEventListener("click", function () { sample = null; $("msg").textContent = ""; render(); });
  window.addEventListener("resize", render);
  setKind("binom");
})();
