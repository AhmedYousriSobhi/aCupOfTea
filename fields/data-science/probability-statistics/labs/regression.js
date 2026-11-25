(function () {
  "use strict";
  var $ = Lab.$, K = "tea", pts = [], sel = 0, drag = -1, geom = null;
  Lab.theme($("theme"));
  var X123 = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5];
  var SETS = {
    tea: { x: [2, 4, 6, 8, 10, 12, 14, 16], y: [58, 50, 52, 42, 40, 30, 28, 20], xr: [0, 44], yr: [-50, 80], u: "degrees C", v: "cups", n: "Cold days, full cups: r is strongly negative. Each extra degree goes with about 2.6 fewer cups." },
    fest: { x: [2, 4, 6, 8, 10, 12, 14, 16, 30], y: [58, 50, 52, 42, 40, 30, 28, 20, 60], xr: [0, 44], yr: [-50, 80], u: "degrees C", v: "cups", n: "One heatwave festival day (30 degrees, 60 cups) joins the tea-shop days. One point swings r and the slope." },
    a1: { x: X123, y: [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68], xr: [0, 20], yr: [0, 14], u: "x", v: "y", n: "Anscombe I: a plain cloud, where the line is a fair summary. r = 0.816." },
    a2: { x: X123, y: [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74], xr: [0, 20], yr: [0, 14], u: "x", v: "y", n: "Anscombe II: a smooth curve with the very same r and the very same line. A straight line is the wrong shape." },
    a3: { x: X123, y: [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73], xr: [0, 20], yr: [0, 14], u: "x", v: "y", n: "Anscombe III: a perfect line plus one stray point that tilts the fitted line." },
    a4: { x: [8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], y: [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.5, 5.56, 7.91, 6.89], xr: [0, 20], yr: [0, 14], u: "x", v: "y", n: "Anscombe IV: a stack of points at x = 8 and one lever at x = 19 that decides the whole line. Drag it." }
  };
  function f(x, d) { return Number(x).toFixed(d === undefined ? 2 : d); }
  function fit() {
    var n = pts.length, mx = 0, my = 0, i; pts.forEach(function (p) { mx += p.x; my += p.y; }); mx /= n; my /= n;
    var sxx = 0, syy = 0, sxy = 0; pts.forEach(function (p) { sxx += (p.x - mx) * (p.x - mx); syy += (p.y - my) * (p.y - my); sxy += (p.x - mx) * (p.y - my); });
    var b = sxx ? sxy / sxx : 0, a = my - b * mx, r = sxx && syy ? sxy / Math.sqrt(sxx * syy) : 0, ssr = 0; pts.forEach(function (p) { var e = p.y - (a + b * p.x); ssr += e * e; });
    return { a: a, b: b, r: r, ssr: ssr, sst: syy, mx: mx, my: my };
  }
  function ticks(lo, hi, k) { var step = (hi - lo) / k, mag = Math.pow(10, Math.floor(Math.log10(step))), fr = step / mag, ns = (fr <= 1 ? 1 : fr <= 2 ? 2 : fr <= 5 ? 5 : 10) * mag, t = [], v = Math.ceil(lo / ns) * ns; for (; v <= hi + 1e-9; v += ns) t.push(Math.round(v * 1e6) / 1e6); return t; }
  function render() {
    var S = SETS[K], cv = $("cv"), P = Lab.prep(cv, 0.62), c = P.ctx, col = Lab.colors(), L = 46, R = 12, T = 12, B = 38, W = P.w - L - R, H = P.h - T - B;
    var X = function (x) { return L + (x - S.xr[0]) / (S.xr[1] - S.xr[0]) * W; }, Y = function (y) { return T + H - (y - S.yr[0]) / (S.yr[1] - S.yr[0]) * H; };
    geom = { X: X, Y: Y, L: L, T: T, W: W, H: H, S: S };
    c.clearRect(0, 0, P.w, P.h); c.font = "12px system-ui,sans-serif"; c.lineWidth = 1;
    ticks(S.yr[0], S.yr[1], 5).forEach(function (v) { c.strokeStyle = col.line; c.beginPath(); c.moveTo(L, Math.round(Y(v)) + .5); c.lineTo(L + W, Math.round(Y(v)) + .5); c.stroke(); c.fillStyle = col.mut; c.textAlign = "right"; c.fillText(String(v), L - 6, Y(v) + 4); });
    ticks(S.xr[0], S.xr[1], 6).forEach(function (v) { c.fillStyle = col.mut; c.textAlign = "center"; c.fillText(String(v), X(v), T + H + 16); });
    c.fillText(S.u, L + W / 2, P.h - 6); c.save(); c.translate(11, T + H / 2); c.rotate(-Math.PI / 2); c.fillText(S.v, 0, 0); c.restore();
    var m = fit();
    pts.forEach(function (p) { var yh = m.a + m.b * p.x; c.strokeStyle = col.acc2; c.lineWidth = 1.5; c.setLineDash([3, 3]); c.beginPath(); c.moveTo(X(p.x), Y(p.y)); c.lineTo(X(p.x), Y(yh)); c.stroke(); });
    c.setLineDash([]); c.strokeStyle = col.fg; c.lineWidth = 2.4; c.beginPath(); c.moveTo(X(S.xr[0]), Y(m.a + m.b * S.xr[0])); c.lineTo(X(S.xr[1]), Y(m.a + m.b * S.xr[1])); c.stroke();
    pts.forEach(function (p, i) { c.fillStyle = col.acc; c.strokeStyle = i === sel ? col.fg : col.card; c.lineWidth = i === sel ? 3 : 2; c.beginPath(); c.arc(X(p.x), Y(p.y), 7, 0, 6.2832); c.fill(); c.stroke(); });
    var px = +$("px").value, py = m.a + m.b * px; c.strokeStyle = col.acc3; c.lineWidth = 2; c.beginPath(); c.arc(X(px), Y(py), 9, 0, 6.2832); c.stroke();
    var inside = px >= Math.min.apply(null, pts.map(function (p) { return p.x; })) && px <= Math.max.apply(null, pts.map(function (p) { return p.x; }));
    $("r").textContent = f(m.r, 3); $("r2").textContent = f(m.r * m.r, 3); $("sl").textContent = f(m.b, 3); $("ic").textContent = f(m.a, 2); $("ss").textContent = f(m.ssr, 1) + " / " + f(m.sst, 1);
    $("pred").innerHTML = "At <b>" + f(px, 1) + "</b> the line says <b>" + f(py, 1) + "</b> " + S.v + ". " + (inside ? "That is inside the x values you observed." : "<b>Extrapolation</b>: outside the x values observed, the line is a guess, not a law." ) + (S.v === "cups" && py < 0 ? " A negative number of cups is impossible." : "");
    $("px-v").textContent = f(px, 1); Lib();
  }
  function Lib() { Lab.paint($("px")); }
  function load(k) {
    K = k; var S = SETS[k]; pts = S.x.map(function (x, i) { return { x: x, y: S.y[i] }; }); sel = pts.length - 1; drag = -1;
    Array.prototype.forEach.call(document.querySelectorAll("#sets .chip"), function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-k") === k ? "true" : "false"); });
    $("notice").textContent = S.n; var px = $("px"); px.min = S.xr[0]; px.max = S.xr[1]; px.value = Math.round((S.x.reduce(function (a, b) { return a + b; }, 0) / S.x.length) * 2) / 2; $("px-lo").textContent = S.xr[0]; $("px-hi").textContent = S.xr[1]; render();
  }
  function ptAt(e) { var r = $("cv").getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top, best = -1, bd = 22 * 22; pts.forEach(function (p, i) { var dx = geom.X(p.x) - mx, dy = geom.Y(p.y) - my, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = i; } }); return best; }
  function move(e) {
    var r = $("cv").getBoundingClientRect(), S = geom.S, x = S.xr[0] + (e.clientX - r.left - geom.L) / geom.W * (S.xr[1] - S.xr[0]), y = S.yr[0] + (1 - (e.clientY - r.top - geom.T) / geom.H) * (S.yr[1] - S.yr[0]);
    pts[drag].x = Math.min(S.xr[1], Math.max(S.xr[0], x)); pts[drag].y = Math.min(S.yr[1], Math.max(S.yr[0], y));
  }
  var cv = $("cv"), tip = $("tip");
  cv.addEventListener("pointerdown", function (e) { var i = ptAt(e); if (i >= 0) { drag = i; sel = i; cv.setPointerCapture(e.pointerId); move(e); render(); e.preventDefault(); } });
  cv.addEventListener("pointermove", function (e) {
    if (drag >= 0) { move(e); render(); tip.classList.remove("on"); return; }
    var i = ptAt(e); if (i >= 0) { var p = pts[i]; tip.innerHTML = "<b>(" + f(p.x, 1) + ", " + f(p.y, 1) + ")</b><br>drag to move"; tip.style.left = Math.min(Math.max(geom.X(p.x), 70), cv.clientWidth - 70) + "px"; tip.style.top = Math.max(40, geom.Y(p.y) - 6) + "px"; tip.classList.add("on"); cv.style.cursor = "grab"; } else { tip.classList.remove("on"); cv.style.cursor = "default"; }
  });
  cv.addEventListener("pointerup", function () { drag = -1; }); cv.addEventListener("pointercancel", function () { drag = -1; });
  cv.addEventListener("pointerleave", function () { tip.classList.remove("on"); });
  cv.addEventListener("keydown", function (e) {
    var S = geom.S, sx = (S.xr[1] - S.xr[0]) / 60, sy = (S.yr[1] - S.yr[0]) / 60, p = pts[sel], k = e.key;
    if (k === "ArrowLeft") p.x -= sx; else if (k === "ArrowRight") p.x += sx; else if (k === "ArrowUp") p.y += sy; else if (k === "ArrowDown") p.y -= sy;
    else if (k === "[") sel = (sel + pts.length - 1) % pts.length; else if (k === "]") sel = (sel + 1) % pts.length; else return;
    p.x = Math.min(S.xr[1], Math.max(S.xr[0], p.x)); p.y = Math.min(S.yr[1], Math.max(S.yr[0], p.y)); e.preventDefault(); render();
  });
  Array.prototype.forEach.call(document.querySelectorAll("#sets .chip"), function (b) { b.addEventListener("click", function () { clearX(); load(b.getAttribute("data-k")); }); });
  function clearX() { Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (c) { c.setAttribute("aria-pressed", "false"); }); }
  Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (btn) {
    btn.addEventListener("click", function () { var a = btn.getAttribute("data-x").split("|"); clearX(); btn.setAttribute("aria-pressed", "true"); load(a[0]); $("px").value = a[1]; render(); });
  });
  $("px").addEventListener("input", render); $("reset").addEventListener("click", function () { load(K); });
  window.addEventListener("resize", render);
  load("tea");
})();
