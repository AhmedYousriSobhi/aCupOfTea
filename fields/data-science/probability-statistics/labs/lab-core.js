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
    var st = getComputedStyle(document.documentElement);
    var v = function (n) { return st.getPropertyValue(n).trim(); };
    return { fg: v("--ink"), mut: v("--mut"), line: v("--line"), card: v("--card"), bg: v("--bg"), acc: v("--leaf"), acc2: v("--kettle"), acc3: v("--sky") };
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
  function roundTop(c, x, y, w, h, r) {
    r = Math.min(r, w / 2, h);
    c.beginPath(); c.moveTo(x, y + h); c.lineTo(x, y + r); c.quadraticCurveTo(x, y, x + r, y);
    c.lineTo(x + w - r, y); c.quadraticCurveTo(x + w, y, x + w, y + r); c.lineTo(x + w, y + h); c.closePath(); c.fill();
  }
  // Bar chart on a canvas. o: bars [{x,y,shade}], line [{x,y}], xlabel, ylabel, hoverX, simBars [{x,y}] (ticks).
  function barChart(cv, o) {
    var P = prep(cv, o.ratio), c = P.ctx, col = colors();
    var L = 50, R = 12, T = 14, B = 44, W = P.w - L - R, H = P.h - T - B;
    var xs = o.bars.map(function (b) { return b.x; });
    var xmin = o.xmin !== undefined ? o.xmin : Math.min.apply(null, xs) - 0.5;
    var xmax = o.xmax !== undefined ? o.xmax : Math.max.apply(null, xs) + 0.5;
    var ymax = o.ymax || Math.max.apply(null, o.bars.map(function (b) { return b.y; }).concat((o.line || []).map(function (p) { return p.y; }), [1e-9])) * 1.1;
    (function () { // round the top of the axis so the four ticks fall on clean values
      var raw = ymax / 4, mag = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / mag;
      ymax = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * mag * 4;
    })();
    var X = function (x) { return L + (x - xmin) / (xmax - xmin) * W; };
    var Y = function (y) { return T + H - y / ymax * H; };
    c.clearRect(0, 0, P.w, P.h);
    c.font = "12px system-ui,sans-serif"; c.fillStyle = col.mut; c.strokeStyle = col.line; c.lineWidth = 1;
    c.textAlign = "right";
    for (var i = 0; i <= 4; i++) {
      var yv = ymax * i / 4, yy = Math.round(Y(yv)) + 0.5;
      c.beginPath(); c.moveTo(L, yy); c.lineTo(P.w - R, yy); c.stroke();
      c.fillText(o.pctAxis ? (100 * yv).toFixed(100 * ymax < 10 ? 1 : 0) + "%" : yv.toFixed(3), L - 6, yy + 4);
    }
    var bw = Math.max(1, W / (xmax - xmin) * (o.bw || o.barw || 0.8));
    o.bars.forEach(function (b) {
      var hot = o.hoverX !== undefined && o.hoverX !== null && Math.abs(b.x - o.hoverX) < (o.bw || 0.5) / 2 + 1e-9;
      c.fillStyle = b.shade ? col.acc2 : col.acc;
      c.globalAlpha = (o.alpha || 1) * (o.hoverX !== undefined && o.hoverX !== null && !hot ? 0.55 : 1);
      roundTop(c, X(b.x) - bw / 2, Y(b.y), bw, Math.max(0, Y(0) - Y(b.y)), Math.min(5, bw / 2));
      c.globalAlpha = 1;
    });
    if (o.line) {
      c.strokeStyle = col.fg; c.lineWidth = 2.2; c.lineJoin = "round"; c.beginPath();
      o.line.forEach(function (p, j) { if (j) c.lineTo(X(p.x), Y(p.y)); else c.moveTo(X(p.x), Y(p.y)); });
      c.stroke(); c.lineWidth = 1;
    }
    if (o.sim) {
      c.strokeStyle = col.acc3; c.lineWidth = 3; c.lineCap = "round";
      o.sim.forEach(function (b) { c.beginPath(); c.moveTo(X(b.x) - bw * 0.42, Y(b.y)); c.lineTo(X(b.x) + bw * 0.42, Y(b.y)); c.stroke(); });
      c.lineWidth = 1;
    }
    c.fillStyle = col.mut; c.textAlign = "center";
    var step = Math.max(1, Math.ceil((xmax - xmin) / 10 / (o.xstep || 1)) * (o.xstep || 1));
    var start = Math.ceil(xmin / step) * step;
    for (var xv = start; xv <= xmax; xv += step) c.fillText(String(Math.round(xv * 100) / 100), X(xv), T + H + 16);
    if (o.xlabel) { c.font = "600 12px system-ui,sans-serif"; c.fillText(o.xlabel, L + W / 2, P.h - 6); }
    if (o.ylabel) { c.save(); c.translate(12, T + H / 2); c.rotate(-Math.PI / 2); c.font = "600 12px system-ui,sans-serif"; c.fillText(o.ylabel, 0, 0); c.restore(); }
    var geom = { X: X, Y: Y, ctx: c, col: col, W: P.w, H: P.h, L: L, R: R, T: T, B: B, xmin: xmin, xmax: xmax, inv: function (px) { return xmin + (px - L) / W * (xmax - xmin); } };
    cv._geom = geom;
    return geom;
  }
  // Pointer + keyboard readout. tipFn(x) -> html string or null; redraw(x) draws with a highlighted x.
  function hover(cv, tip, tipFn, redraw, step) {
    var cur = null;
    function stepNow() { return typeof step === "function" ? step() : step; }
    function at(clientX) {
      var r = cv.getBoundingClientRect(), g = cv._geom; if (!g) return;
      var s = stepNow(), x = g.inv(clientX - r.left); if (s) x = Math.round(x / s) * s;
      show(x, g.X(x));
    }
    function show(x, px) {
      var g = cv._geom, t = tipFn(x);
      if (t === null) { hide(); return; }
      cur = x; redraw(x);
      tip.innerHTML = t; tip.style.left = Math.min(Math.max(px, 70), cv.clientWidth - 70) + "px"; tip.style.top = Math.max(40, g.T + 26) + "px"; tip.classList.add("on");
    }
    function hide() { cur = null; tip.classList.remove("on"); redraw(null); }
    cv.addEventListener("pointermove", function (e) { at(e.clientX); });
    cv.addEventListener("pointerdown", function (e) { at(e.clientX); });
    cv.addEventListener("pointerleave", hide);
    cv.addEventListener("blur", hide);
    cv.addEventListener("keydown", function (e) {
      var g = cv._geom; if (!g) return; var s0 = stepNow(), s = s0 || (g.xmax - g.xmin) / 40, k = e.key;
      if (k === "ArrowRight" || k === "ArrowLeft") { var x = (cur === null ? (g.xmin + g.xmax) / 2 : cur) + (k === "ArrowRight" ? s : -s); if (s0) x = Math.round(x / s0) * s0; show(x, g.X(x)); e.preventDefault(); }
      if (k === "Escape") hide();
    });
  }
  // Bind a range input to its <output>; paints the filled track; call cb on change.
  function paint(el) { var p = (el.value - el.min) / (el.max - el.min) * 100; el.style.setProperty("--pct", p + "%"); }
  function slider(id, fmtFn, cb) {
    var el = $(id), out = $(id + "-v");
    function upd() { out.textContent = fmtFn(+el.value); paint(el); }
    el.addEventListener("input", function () { upd(); cb(); });
    el._upd = upd; upd();
    return function () { return +el.value; };
  }
  // Light / dark / auto toggle stored in localStorage (failures are ignored).
  function theme(btn) {
    var root = document.documentElement, key = "lab-theme";
    function get() { try { return localStorage.getItem(key); } catch (e) { return null; } }
    function set(v) { try { if (v) localStorage.setItem(key, v); else localStorage.removeItem(key); } catch (e) { /* ignore */ } }
    function apply(v) { if (root.classList.contains("embed")) return; if (v) root.setAttribute("data-theme", v); else root.removeAttribute("data-theme"); btn.setAttribute("aria-label", "Theme: " + (v || "auto") + ". Press to change."); btn.querySelector("span").textContent = v ? v[0].toUpperCase() + v.slice(1) : "Auto"; }
    var order = [null, "light", "dark"], cur = get(); if (cur !== "light" && cur !== "dark") cur = null;
    apply(cur);
    btn.addEventListener("click", function () { cur = order[(order.indexOf(cur) + 1) % 3]; set(cur); apply(cur); window.dispatchEvent(new Event("resize")); });
    if (window.matchMedia) window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () { window.dispatchEvent(new Event("resize")); });
  }

  // Embedded in a docs page (a sandboxed frame): hide the page chrome, take the site's theme and report the height.
  // The theme and the height are the only things exchanged; both are validated, and nothing is ever put in as HTML.
  (function embed() {
    var q = new URLSearchParams(location.search);
    if (q.get("embed") !== "1" || window.parent === window) return;
    var root = document.documentElement;
    root.classList.add("embed");
    function setTheme(t) { if (t === "light" || t === "dark") { root.setAttribute("data-theme", t); window.dispatchEvent(new Event("resize")); } }
    setTheme(q.get("theme"));
    window.addEventListener("message", function (e) {
      var d = e.data;
      if (e.source === window.parent && d && typeof d === "object" && d.type === "lab-theme") setTheme(d.theme);
    });
    function send() {
      var m = document.querySelector("main");
      window.parent.postMessage({ type: "lab-height", h: Math.ceil((m ? m.getBoundingClientRect().height : document.body.scrollHeight) + 8) }, "*");
    }
    window.addEventListener("load", send);
    window.addEventListener("resize", send);
    if (window.ResizeObserver) new ResizeObserver(send).observe(document.body);
  })();
  g.Lab = { rng: rng, normal: normal, erf: erf, ncdf: ncdf, ninv: ninv, binomPmf: binomPmf, poisPmf: poisPmf,
    binomSample: binomSample, poisSample: poisSample, $: $, fmt: fmt, pct: pct, colors: colors, prep: prep,
    barChart: barChart, slider: slider, hover: hover, paint: paint, theme: theme };
})(window);
