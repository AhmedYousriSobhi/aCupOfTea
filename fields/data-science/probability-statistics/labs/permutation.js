(function () {
  "use strict";
  var $ = Lab.$, K = "mira", seed = 40, gaps = [], last = null, hoverX = null;
  Lab.theme($("theme"));
  var SETS = {
    mira: { a: [7, 8, 6, 9, 7, 8, 9, 7, 8, 6], b: [6, 7, 5, 7, 6, 8, 6, 5, 7, 6], w: 0.2, lim: 3, exact: "1413 / 92378 = 0.0153", ex: 0.0153, ways: "all 184,756 splits" },
    tiny: { a: [8, 9, 7], b: [5, 6, 7], w: 0.5, lim: 4, exact: "2 / 20 = 0.1000", ex: 0.1, ways: "all 20 splits" }
  };
  function mean(a) { var s = 0; a.forEach(function (x) { s += x; }); return s / a.length; }
  function f(x, d) { return Number(x).toFixed(d === undefined ? 2 : d); }
  function obs() { var S = SETS[K]; return mean(S.a) - mean(S.b); }
  function shuffled(pool, na, r) { // Fisher-Yates, then split
    var p = pool.slice(), i, j, t; for (i = p.length - 1; i > 0; i--) { j = Math.floor(r() * (i + 1)); t = p[i]; p[i] = p[j]; p[j] = t; }
    return { a: p.slice(0, na), b: p.slice(na) };
  }
  function head() {
    var S = SETS[K]; $("a-m").textContent = f(mean(S.a)); $("b-m").textContent = f(mean(S.b)); $("gap").textContent = "+" + f(obs());
    $("vals").textContent = "A: " + S.a.join(", ") + "   B: " + S.b.join(", ");
    $("pex").textContent = f(S.ex, 4); $("pnote").textContent = "Exact p = " + S.exact + " (" + S.ways + " listed). The shuffled estimate should land close, and closer with more shuffles.";
  }
  function render() {
    var S = SETS[K], w = S.w, lim = S.lim, nb = Math.round(2 * lim / w) + 1, x0 = -lim, counts = new Array(nb).fill(0), o = obs();
    gaps.forEach(function (g) { var j = Math.round((g - x0) / w); if (j >= 0 && j < nb) counts[j]++; });
    var bars = counts.map(function (c, j) { var x = x0 + j * w; return { x: x, y: gaps.length ? c / gaps.length : 0, shade: x >= o - 1e-9 }; });
    var top = Math.max.apply(null, bars.map(function (b) { return b.y; }).concat([0.05]));
    var ch = Lab.barChart($("cv"), { bars: bars, bw: w * 0.9, xmin: x0 - w, xmax: lim + w, ymax: top * 1.2, pctAxis: true, xstep: 1, xlabel: "gap in means, A − B", ylabel: "share of shuffles", hoverX: hoverX, alpha: 0.9 });
    var c = ch.ctx; c.strokeStyle = ch.col.fg; c.lineWidth = 2.5; c.beginPath(); c.moveTo(ch.X(o), ch.T); c.lineTo(ch.X(o), ch.Y(0)); c.stroke(); c.lineWidth = 1;
    c.fillStyle = ch.col.mut; c.font = "12px system-ui,sans-serif"; c.textAlign = "left"; c.fillText("real gap +" + f(o), Math.min(ch.X(o) + 6, ch.W - 90), ch.T + 12);
    var hits = gaps.filter(function (g) { return g >= o - 1e-9; }).length;
    $("cnt").textContent = gaps.length.toLocaleString("en"); $("pv").textContent = gaps.length ? f(hits / gaps.length, 4) + " (" + hits + " of " + gaps.length.toLocaleString("en") + ")" : "–";
  }
  function once() {
    var S = SETS[K], r = Lab.rng(seed++), p = shuffled(S.a.concat(S.b), S.a.length, r), g = mean(p.a) - mean(p.b);
    gaps.push(g); last = g;
    $("onesay").innerHTML = "This re-deal: A mean <b>" + f(mean(p.a)) + "</b>, B mean <b>" + f(mean(p.b)) + "</b>, gap <b>" + (g >= 0 ? "+" : "") + f(g) + "</b>. " + (g >= obs() - 1e-9 ? "<b>As good as the real gap</b>: luck did it." : "Smaller than the real gap.");
    render();
  }
  function many() {
    var S = SETS[K], r = Lab.rng(seed++), i, pool = S.a.concat(S.b);
    for (i = 0; i < 1000; i++) { var p = shuffled(pool, S.a.length, r); gaps.push(mean(p.a) - mean(p.b)); }
    $("onesay").textContent = "1,000 more re-deals (seed " + (seed - 1) + ")."; render();
  }
  function reset() { gaps = []; $("onesay").textContent = ""; render(); }
  function setKind(k) {
    K = k; Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-k") === k ? "true" : "false"); });
    head(); reset();
  }
  // --- twenty tries on noise
  function oneTest(r, m, reps) {
    var x = [], y = [], i; for (i = 0; i < m; i++) { x.push(Lab.normal(r)); y.push(Lab.normal(r)); }
    var o = Math.abs(mean(x) - mean(y)), pool = x.concat(y), c = 0, k, j, t;
    for (k = 0; k < reps; k++) { for (i = pool.length - 1; i > 0; i--) { j = Math.floor(r() * (i + 1)); t = pool[i]; pool[i] = pool[j]; pool[j] = t; } if (Math.abs(mean(pool.slice(0, m)) - mean(pool.slice(m))) >= o) c++; }
    return c / reps;
  }
  function twenty() {
    var r = Lab.rng(seed++), ps = [], i; for (i = 0; i < 20; i++) ps.push(oneTest(r, 10, 200));
    var hit = ps.filter(function (p) { return p <= 0.05; }).length;
    var bars = ps.map(function (p, j) { return { x: j + 1, y: p, shade: p <= 0.05 }; });
    var ch = Lab.barChart($("cp"), { bars: bars, bw: 0.8, xmin: 0.4, xmax: 20.6, ymax: 1, xstep: 1, pctAxis: true, xlabel: "test number", ylabel: "p-value", alpha: 0.9, ratio: 0.45 });
    var c = ch.ctx; c.strokeStyle = ch.col.fg; c.setLineDash([5, 4]); c.lineWidth = 1.5; c.beginPath(); c.moveTo(ch.L, ch.Y(0.05)); c.lineTo(ch.W - ch.R, ch.Y(0.05)); c.stroke(); c.setLineDash([]);
    $("twsay").innerHTML = "<b>" + hit + "</b> of 20 tests came out at or below 0.05 although every group was pure noise. " + (hit ? "A researcher who reports only those would call them findings." : "None this time; try again.") + " Chance of at least one: 1 &minus; 0.95<sup>20</sup> = 64%.";
  }
  function studies() {
    var r = Lab.rng(seed++), hits = 0, i, j;
    for (i = 0; i < 100; i++) { var any = false; for (j = 0; j < 20; j++) if (oneTest(r, 10, 200) <= 0.05) { any = true; break; } if (any) hits++; }
    $("twsay").innerHTML = "In <b>" + hits + "</b> of 100 whole studies, at least one of the 20 noise tests came out at or below 0.05 (theory: about 64).";
  }
  Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.addEventListener("click", function () { clearX(); setKind(b.getAttribute("data-k")); }); });
  function clearX() { Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (c) { c.setAttribute("aria-pressed", "false"); }); }
  Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (btn) {
    btn.addEventListener("click", function () { var a = btn.getAttribute("data-x").split("|"); clearX(); btn.setAttribute("aria-pressed", "true"); setKind(a[0]); many(); });
  });
  $("one").addEventListener("click", once); $("many").addEventListener("click", many); $("reset").addEventListener("click", reset);
  $("twenty").addEventListener("click", twenty); $("studies").addEventListener("click", studies);
  Lab.hover($("cv"), $("tip"), function (x) {
    var S = SETS[K], j = Math.round((x + S.lim) / S.w), v = -S.lim + j * S.w; if (!gaps.length || Math.abs(v) > S.lim + 1e-9) return null;
    var k = gaps.filter(function (g) { return Math.abs(g - v) < S.w / 2 - 1e-9; }).length; return "<b>gap " + f(v) + "</b><br>" + k + " of " + gaps.length.toLocaleString("en") + " shuffles";
  }, function (x) { hoverX = x === null ? null : (function () { var S = SETS[K]; return -S.lim + Math.round((x + S.lim) / S.w) * S.w; })(); render(); }, function () { return SETS[K].w; });
  window.addEventListener("resize", render);
  setKind("mira");
})();
