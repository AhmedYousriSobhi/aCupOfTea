# grouped-tables.js

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/labs/grouped-tables.js)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/data-science/probability-statistics/labs/grouped-tables.js)

</div>

```javascript
(function () {
  "use strict";
  var $ = Lab.$, K = "scores", V = "hist", hoverX = null, MAXROWS = 12;
  Lab.theme($("theme"));
  var SCORES = [52, 55, 55, 58, 58, 58, 62, 62, 62, 71, 71, 89, 89, 89, 93, 93, 94, 94, 95, 104];
  var DAYS = { f: [2, 8, 18, 13, 7, 1, 1], lo: 100, h: 5 };
  function f2(x) { return String(Number(x.toFixed(2))); }
  function mean(a) { var s = 0; a.forEach(function (x) { s += x; }); return s / a.length; }
  function median(a) { var b = a.slice().sort(function (x, y) { return x - y; }), m = b.length >> 1; return b.length % 2 ? b[m] : (b[m - 1] + b[m]) / 2; }

  // Build the classes for the current dials: [{lo, hi, bl, bu, f, M, cf}], n.
  function build() {
    var rows = [], cf = 0, n, h, start, k, j, lo, hi, c;
    if (K === "days") {
      h = DAYS.h; n = 0; DAYS.f.forEach(function (x) { n += x; });
      DAYS.f.forEach(function (fr, i) { lo = DAYS.lo + i * h; hi = lo + h - 1; cf += fr; rows.push({ lo: lo, hi: hi, bl: lo - 0.5, bu: hi + 0.5, f: fr, M: (lo + hi) / 2, cf: cf }); });
      return { rows: rows, n: n, h: h };
    }
    h = +$("h").value; start = Math.min.apply(null, SCORES) - Math.min(+$("off").value, h - 1); n = SCORES.length;
    k = Math.ceil((Math.max.apply(null, SCORES) - start + 1) / h);
    for (j = 0; j < k; j++) {
      lo = start + j * h; hi = lo + h - 1; c = SCORES.filter(function (v) { return v >= lo && v <= hi; }).length; cf += c;
      rows.push({ lo: lo, hi: hi, bl: lo - 0.5, bu: hi + 0.5, f: c, M: (lo + hi) / 2, cf: cf });
    }
    return { rows: rows, n: n, h: h };
  }
  function summary(T) {
    var s = 0, med = null;
    T.rows.forEach(function (r) { s += r.f * r.M; if (med === null && r.cf >= T.n / 2) med = r.bl + ((T.n / 2 - (r.cf - r.f)) / r.f) * T.h; });
    return { mean: s / T.n, med: med };
  }
  function cfAt(T, x) { // the ogive: straight lines between (boundary, CF)
    var i, r;
    if (x <= T.rows[0].bl) return 0;
    for (i = 0; i < T.rows.length; i++) { r = T.rows[i]; if (x <= r.bu) return (r.cf - r.f) + (x - r.bl) / T.h * r.f; }
    return T.n;
  }

  function render() {
    var T = build(), S = summary(T), isS = K === "scores", total = 0;
    T.rows.forEach(function (r) { total += r.f; });
    $("big").innerHTML = f2(S.mean) + "<small>grouped mean</small>";
    $("gmed").textContent = f2(S.med); $("k").textContent = String(T.rows.length);
    $("tmean").textContent = isS ? f2(mean(SCORES)) : "not kept"; $("tmed").textContent = isS ? f2(median(SCORES)) : "not kept";
    $("sturges").textContent = (1 + 3.322 * Math.log10(T.n)).toFixed(1); $("check").textContent = total === T.n ? "yes, " + total : "no, " + total;
    $("says").innerHTML = isS ? "Grouped mean <b>" + f2(S.mean) + "</b> against the true <b>" + f2(mean(SCORES)) + "</b> (off by " + f2(Math.abs(S.mean - mean(SCORES))) + "); grouped median <b>" + f2(S.med) + "</b> against <b>" + f2(median(SCORES)) + "</b> (off by " + f2(Math.abs(S.med - median(SCORES))) + ")." : "Only the counts per class are kept, so the mean and the median are estimates from midpoints and the ogive.";
    $("desc").textContent = isS ? "Mira's 20 tasting scores on a 0 to 120 scale: two clumps, one around 58 and one around 92, and nothing between 71 and 89." : "Customers per day over the last 50 days, in classes of width 5 (boundaries 99.5 to 134.5). Counts only; the raw days are gone.";
    $("dials").hidden = !isS; $("recipe").hidden = !isS;
    var rowsHtml = "", shown = T.rows.slice(0, MAXROWS);
    shown.forEach(function (r) { rowsHtml += "<tr><td>" + r.lo + " to " + r.hi + "</td><td>" + r.bl + " to " + r.bu + "</td><td>" + r.f + "</td><td>" + r.M + "</td><td>" + r.cf + "</td></tr>"; });
    $("tb").innerHTML = rowsHtml; $("tmore").textContent = T.rows.length > MAXROWS ? "… and " + (T.rows.length - MAXROWS) + " more classes (the last cumulative frequency is " + T.n + ")." : "";
    drawView(T, S);
  }

  function drawView(T, S) {
    var rows = T.rows, h = T.h, lo = rows[0].bl, hi = rows[rows.length - 1].bu, pad = h, ch, c, i, bars, maxf = Math.max.apply(null, rows.map(function (r) { return r.f; }));
    var xstep = Math.max(1, Math.round((hi - lo) / 8));
    if (V === "hist") {
      $("vdesc").textContent = "Bars touch because the ruler has no holes; the axis shows boundaries, and area means amount.";
      bars = rows.map(function (r) { return { x: r.M, y: r.f }; });
      Lab.barChart($("cv"), { bars: bars, bw: h, alpha: 0.85, yint: true, ymax: Math.max(4, maxf * 1.15), xmin: lo, xmax: hi, xstep: xstep, xlabel: "value (class boundaries)", ylabel: "frequency", hoverX: hoverX, ratio: 0.5 });
      $("readrow").hidden = true; $("rmsg").textContent = "";
    } else if (V === "poly") {
      $("vdesc").textContent = "A dot above each midpoint at the height of its frequency, closed to zero one class beyond each end. Lines overlay; bars do not.";
      var pts = [{ x: rows[0].M - h, y: 0 }].concat(rows.map(function (r) { return { x: r.M, y: r.f }; }), [{ x: rows[rows.length - 1].M + h, y: 0 }]);
      ch = Lab.barChart($("cv"), { bars: rows.map(function (r) { return { x: r.M, y: 0 }; }), line: pts, bw: h * 0.1, yint: true, ymax: Math.max(4, maxf * 1.15), xmin: lo - h, xmax: hi + h, xstep: xstep, xlabel: "value (class midpoints)", ylabel: "frequency", ratio: 0.5 });
      c = ch.ctx; c.fillStyle = ch.col.acc; pts.forEach(function (p) { c.beginPath(); c.arc(ch.X(p.x), ch.Y(p.y), 4, 0, 6.2832); c.fill(); });
      $("readrow").hidden = true; $("rmsg").textContent = "";
    } else {
      $("vdesc").textContent = "A running total plotted at the upper boundary of each class, from zero to n: it only goes up. Read it in either direction.";
      var og = [{ x: rows[0].bl, y: 0 }].concat(rows.map(function (r) { return { x: r.bu, y: r.cf }; }));
      ch = Lab.barChart($("cv"), { bars: [{ x: lo, y: 0 }], line: og, bw: 0.0001, yint: true, ymax: T.n, xmin: lo - h * 0.3, xmax: hi + h * 0.3, xstep: xstep, xlabel: "value (upper class boundaries)", ylabel: "days or tasters at or below", ratio: 0.5 });
      c = ch.ctx; c.fillStyle = ch.col.acc; og.forEach(function (p) { c.beginPath(); c.arc(ch.X(p.x), ch.Y(p.y), 3.5, 0, 6.2832); c.fill(); });
      var rx = +$("rx").value, cnt = cfAt(T, rx);
      c.strokeStyle = ch.col.acc2; c.lineWidth = 2.5; c.setLineDash([6, 4]); c.beginPath(); c.moveTo(ch.X(rx), ch.Y(0)); c.lineTo(ch.X(rx), ch.Y(cnt)); c.lineTo(ch.X(lo - h * 0.3), ch.Y(cnt)); c.stroke(); c.setLineDash([]); c.lineWidth = 1;
      c.fillStyle = ch.col.acc2; c.beginPath(); c.arc(ch.X(rx), ch.Y(cnt), 5, 0, 6.2832); c.fill();
      $("readrow").hidden = false;
      $("rmsg").innerHTML = "At <b>" + f2(rx) + "</b> or below: about <b>" + f2(cnt) + "</b> of " + T.n + " (" + Lab.pct(cnt / T.n, 0) + "). Half the data lie at or below about <b>" + f2(S.med) + "</b>, the median read by ruler.";
    }
  }
  function setRead(T) { var a = T.rows[0].bl, b = T.rows[T.rows.length - 1].bu, el = $("rx"); el.min = a; el.max = b; el.step = 0.5; $("rx-lo").textContent = a; $("rx-hi").textContent = b; if (+el.value < a || +el.value > b) el.value = (a + b) / 2; el._upd(); }

  function clampOff() { var h = +$("h").value, el = $("off"); el.max = h - 1; $("off").nextElementSibling.lastElementChild.textContent = String(h - 1); if (+el.value > h - 1) el.value = h - 1; el._upd(); }
  function setK(k) { K = k; Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-k") === k ? "true" : "false"); }); setRead(build()); render(); }
  function setV(v) { V = v; Array.prototype.forEach.call(document.querySelectorAll("#view button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-v") === v ? "true" : "false"); }); setRead(build()); render(); }
  function clearX() { Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (c) { c.setAttribute("aria-pressed", "false"); }); }

  Lab.slider("h", String, function () { clearX(); clampOff(); setRead(build()); render(); });
  Lab.slider("off", String, function () { clearX(); setRead(build()); render(); });
  Lab.slider("rx", function (v) { return f2(v); }, render);
  Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.addEventListener("click", function () { clearX(); setK(b.getAttribute("data-k")); }); });
  Array.prototype.forEach.call(document.querySelectorAll("#view button"), function (b) { b.addEventListener("click", function () { setV(b.getAttribute("data-v")); }); });
  $("rec").addEventListener("click", function () { clearX(); $("h").value = 11; $("h")._upd(); $("off").value = 0; clampOff(); setRead(build()); render(); });
  Array.prototype.forEach.call(document.querySelectorAll(".xcard"), function (btn) {
    btn.addEventListener("click", function () {
      var a = btn.getAttribute("data-x").split("|"); clearX(); btn.setAttribute("aria-pressed", "true");
      if (a[0] === "scores") { $("h").value = a[1]; $("h")._upd(); clampOff(); $("off").value = a[2]; $("off")._upd(); }
      K = a[0]; Array.prototype.forEach.call(document.querySelectorAll("#seg button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-k") === a[0] ? "true" : "false"); });
      V = a[3]; Array.prototype.forEach.call(document.querySelectorAll("#view button"), function (b) { b.setAttribute("aria-selected", b.getAttribute("data-v") === a[3] ? "true" : "false"); });
      var T = build(); setRead(T); if (a[0] === "days") { $("rx").value = 114.5; $("rx")._upd(); } render();
    });
  });
  Lab.hover($("cv"), $("tip"), function (x) {
    if (V !== "hist") return null; var T = build(), r = T.rows.filter(function (q) { return x >= q.bl && x < q.bu; })[0]; if (!r) return null;
    return "<b>" + r.bl + " to " + r.bu + "</b><br>" + r.f + " values (" + Lab.pct(r.f / T.n, 0) + ")";
  }, function (x) { hoverX = null; if (x !== null && V === "hist") { var T = build(), r = T.rows.filter(function (q) { return x >= q.bl && x < q.bu; })[0]; if (r) hoverX = r.M; } render(); }, function () { return 0; });
  window.addEventListener("resize", render);
  clampOff(); setRead(build()); render(); document.querySelector(".xcard").setAttribute("aria-pressed", "true");
})();
```
