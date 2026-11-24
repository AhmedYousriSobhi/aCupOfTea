// Shared helpers for the probability & statistics labs (vanilla JS, no libraries).
(function (g) {
  "use strict";
  // Small seeded generator so a run can be repeated (mulberry32).
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function normal(r) { // Box-Muller
    var u = 0, v = 0;
    while (u === 0) u = r();
    v = r();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
  // Error function (Abramowitz-Stegun 7.1.26 is too coarse; use a series/continued form).
  function erf(x) {
    var s = x < 0 ? -1 : 1; x = Math.abs(x);
    if (x < 3) { // Taylor series
      var sum = x, term = x, n = 0;
      while (Math.abs(term) > 1e-16 * Math.abs(sum)) {
        n++; term *= -x * x / n; sum += term / (2 * n + 1);
      }
      return s * 2 / Math.sqrt(Math.PI) * sum;
    }
    // continued fraction for erfc
    var f = 0;
    for (var k = 60; k >= 1; k--) f = k / 2 / (x + f);
    return s * (1 - Math.exp(-x * x) / Math.sqrt(Math.PI) / (x + f));
  }
  function ncdf(z) { return 0.5 * (1 + erf(z / Math.SQRT2)); }
  function ninv(p) { // bisection on ncdf, good to ~1e-12
    var lo = -10, hi = 10;
    for (var i = 0; i < 100; i++) { var m = (lo + hi) / 2; if (ncdf(m) < p) lo = m; else hi = m; }
    return (lo + hi) / 2;
  }
  function lgam(n) { var s = 0; for (var i = 2; i <= n; i++) s += Math.log(i); return s; }
  function binomPmf(n, p, k) {
    if (k < 0 || k > n) return 0;
    if (p === 0) return k === 0 ? 1 : 0;
    if (p === 1) return k === n ? 1 : 0;
    return Math.exp(lgam(n) - lgam(k) - lgam(n - k) + k * Math.log(p) + (n - k) * Math.log(1 - p));
  }
  function poisPmf(lam, k) { return Math.exp(-lam + k * Math.log(lam) - lgam(k)); }
  function binomSample(n, p, r) { var c = 0; for (var i = 0; i < n; i++) if (r() < p) c++; return c; }
  function poisSample(lam, r) { var L = Math.exp(-lam), k = 0, p = 1; do { k++; p *= r(); } while (p > L); return k - 1; }
  function $(id) { return document.getElementById(id); }
  function fmt(x, d) { return Number(x).toFixed(d === undefined ? 4 : d); }
  function pct(x, d) { return (100 * x).toFixed(d === undefined ? 2 : d) + "%"; }
  function colors() {
    var s = getComputedStyle(document.documentElement);
    var v = function (n) { return s.getPropertyValue(n).trim(); };
    return { fg: v("--fg"), mut: v("--mut"), line: v("--line"), card: v("--card"), acc: v("--acc"), acc2: v("--acc2"), acc3: v("--acc3") };
  }
  // Prepare a canvas for crisp drawing; returns {ctx,w,h}.
  function prep(cv, ratio) {
    var w = cv.parentNode.clientWidth || 600, h = Math.round(w * (ratio || 0.55));
    var d = window.devicePixelRatio || 1;
    cv.width = Math.round(w * d); cv.height = Math.round(h * d);
    cv.style.height = h + "px";
    var c = cv.getContext("2d"); c.setTransform(d, 0, 0, d, 0, 0);
    return { ctx: c, w: w, h: h };
  }
  // Bar chart: bars = [{x,y,color}], optional line points [{x,y}] for a model curve.
  function barChart(cv, o) {
    var P = prep(cv, o.ratio), c = P.ctx, col = colors();
    var L = 44, R = 10, T = 12, B = 30, W = P.w - L - R, H = P.h - T - B;
    var xs = o.bars.map(function (b) { return b.x; });
    var xmin = o.xmin !== undefined ? o.xmin : Math.min.apply(null, xs) - 0.5;
    var xmax = o.xmax !== undefined ? o.xmax : Math.max.apply(null, xs) + 0.5;
    var ymax = o.ymax || Math.max.apply(null, o.bars.map(function (b) { return b.y; }).concat((o.line || []).map(function (p) { return p.y; }), [1e-9])) * 1.1;
    var X = function (x) { return L + (x - xmin) / (xmax - xmin) * W; };
    var Y = function (y) { return T + H - y / ymax * H; };
    c.clearRect(0, 0, P.w, P.h);
    c.font = "12px system-ui,sans-serif"; c.fillStyle = col.mut; c.strokeStyle = col.line;
    c.textAlign = "right";
    for (var i = 0; i <= 4; i++) {
      var yv = ymax * i / 4, yy = Y(yv);
      c.beginPath(); c.moveTo(L, yy); c.lineTo(P.w - R, yy); c.stroke();
      c.fillText((o.pctAxis ? (100 * yv).toFixed(0) + "%" : yv.toFixed(2)), L - 4, yy + 4);
    }
    var bw = Math.max(1, W / (xmax - xmin) * (o.bw || o.barw || 0.8));
    o.bars.forEach(function (b) {
      if (b.shade) c.fillStyle = col.acc2; else c.fillStyle = b.color || col.acc;
      c.globalAlpha = o.alpha || 1;
      c.fillRect(X(b.x) - bw / 2, Y(b.y), bw, Y(0) - Y(b.y));
      c.globalAlpha = 1;
    });
    if (o.line) {
      c.strokeStyle = col.fg; c.lineWidth = 2; c.beginPath();
      o.line.forEach(function (p, i) { if (i) c.lineTo(X(p.x), Y(p.y)); else c.moveTo(X(p.x), Y(p.y)); });
      c.stroke(); c.lineWidth = 1;
    }
    c.fillStyle = col.mut; c.textAlign = "center";
    var step = Math.max(1, Math.ceil((xmax - xmin) / 10 / (o.xstep || 1)) * (o.xstep || 1));
    var start = Math.ceil(xmin / step) * step;
    for (var xv = start; xv <= xmax; xv += step) c.fillText(String(Math.round(xv * 100) / 100), X(xv), P.h - 10);
    return { X: X, Y: Y, ctx: c, col: col, W: P.w, H: P.h };
  }
  // Bind a range input to a label; call cb on change. Returns getter.
  function slider(id, fmtFn, cb) {
    var el = $(id), out = $(id + "-v");
    function upd() { out.textContent = fmtFn(+el.value); }
    el.addEventListener("input", function () { upd(); cb(); });
    upd();
    return function () { return +el.value; };
  }
  g.Lab = { rng: rng, normal: normal, erf: erf, ncdf: ncdf, ninv: ninv, binomPmf: binomPmf, poisPmf: poisPmf,
    binomSample: binomSample, poisSample: poisSample, $: $, fmt: fmt, pct: pct, colors: colors, prep: prep,
    barChart: barChart, slider: slider };
})(window);
