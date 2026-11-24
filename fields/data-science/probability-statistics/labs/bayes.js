(function () {
  "use strict";
  var $ = Lab.$, N = 100000, seed = 1, dots = [], order = [];
  Lab.theme($("theme"));

  // 100 dots in a fixed shuffled order, so "real" ones look scattered, not in a block.
  (function build() {
    var w = $("waffle"), r = Lab.rng(3), i, j, t;
    for (i = 0; i < 100; i++) { var d = document.createElement("i"); w.appendChild(d); dots.push(d); order.push(i); }
    for (i = 99; i > 0; i--) { j = Math.floor(r() * (i + 1)); t = order[i]; order[i] = order[j]; order[j] = t; }
  })();

  function params() { return { p: Math.pow(10, +$("base").value), se: +$("sens").value / 100, fp: +$("fpr").value / 100 }; }
  function post(prior, se, fp) { var tp = se * prior, f = fp * (1 - prior); return tp + f === 0 ? NaN : tp / (tp + f); }
  function fmtP(x, d) { return isNaN(x) ? "n/a" : Lab.pct(x, d === undefined ? 1 : d); }
  function rnd(x) { return Math.round(x).toLocaleString("en"); }

  function render() {
    var q = params();
    var sick = N * q.p, clean = N - sick, tp = sick * q.se, fn = sick - tp, fp = clean * q.fp, tn = clean - fp;
    var p1 = post(q.p, q.se, q.fp), p2 = post(p1, q.se, q.fp), neg = fn + tn;
    $("post").innerHTML = fmtP(p1) + "<small>chance it is really contaminated</small>";
    $("post2").textContent = fmtP(p2);
    $("postneg").textContent = neg ? Lab.pct(fn / neg, 4) + " bad" : "n/a";
    var real = isNaN(p1) ? 0 : Math.round(p1 * 100);
    $("says").innerHTML = isNaN(p1) ? "No tin ever tests positive with these dials." :
      "Of every 100 positive tins, about <b>" + Lab.fmt(p1 * 100, p1 * 100 < 10 ? 1 : 0) + "</b> are really contaminated. False alarms: <b>" + Lab.fmt(100 - p1 * 100, p1 * 100 < 10 ? 1 : 0) + "</b>.";
    var rank = new Array(100), k;
    for (k = 0; k < 100; k++) rank[order[k]] = k;
    dots.forEach(function (d, idx) { d.className = rank[idx] < real ? "real" : ""; });
    $("wcap").textContent = "Each dot is one positive tin (rounded to whole dots).";
    // counts
    ["sick", "clean", "tp", "fp"].forEach(function (id) { $("n-" + id).textContent = rnd({ sick: sick, clean: clean, tp: tp, fp: fp }[id]); });
    var T = tp + fp;
    $("b-sick").style.width = Math.max(1.2, 100 * q.p) + "%";
    $("b-tp").style.width = (T ? 100 * tp / T : 0) + "%";
    $("b-fp").style.width = (T ? 100 * fp / T : 0) + "%";
    $("t-tp").textContent = rnd(tp); $("t-fn").textContent = rnd(fn); $("t-sick").textContent = rnd(sick);
    $("t-fp").textContent = rnd(fp); $("t-tn").textContent = rnd(tn); $("t-clean").textContent = rnd(clean);
  }

  function simulate() {
    var btn = $("sim"), q = params(), rr = Lab.rng(seed++), tp = 0, fp = 0, i;
    btn.disabled = true;
    setTimeout(function () {
      for (i = 0; i < N; i++) {
        var sick = rr() < q.p, pos = rr() < (sick ? q.se : q.fp);
        if (pos) { if (sick) tp++; else fp++; }
      }
      var exact = post(q.p, q.se, q.fp);
      $("simout").innerHTML = "Simulated <b>" + rnd(tp + fp) + "</b> positives: <b>" + rnd(tp) + "</b> real, <b>" + rnd(fp) + "</b> false alarms. Real share <b>" +
        (tp + fp ? Lab.pct(tp / (tp + fp), 2) : "n/a") + "</b> against the exact <b>" + fmtP(exact, 2) + "</b>. Run again for another seed.";
      btn.disabled = false;
    }, 30);
  }

  function setDials(b, s, f) {
    $("base").value = b; $("sens").value = s; $("fpr").value = f;
    ["base", "sens", "fpr"].forEach(function (id) { $(id)._upd(); });
    render();
  }
  function clearPressed() { Array.prototype.forEach.call(document.querySelectorAll("#presets .chip"), function (c) { c.setAttribute("aria-pressed", "false"); }); }

  function manual() { clearPressed(); $("notice-t").textContent = "Custom dials. Compare the big number with the dots."; render(); }
  Lab.slider("base", function (v) { var p = Math.pow(10, v); return p < 0.01 ? Lab.pct(p, 3) : Lab.pct(p, 1); }, manual);
  Lab.slider("sens", function (v) { return v.toFixed(1) + "%"; }, manual);
  Lab.slider("fpr", function (v) { return v.toFixed(1) + "%"; }, manual);

  Array.prototype.forEach.call(document.querySelectorAll("#presets .chip"), function (b) {
    b.addEventListener("click", function () {
      clearPressed(); b.setAttribute("aria-pressed", "true");
      setDials(b.getAttribute("data-b"), b.getAttribute("data-s"), b.getAttribute("data-f"));
      $("notice-t").textContent = b.getAttribute("data-n");
    });
  });
  $("sim").addEventListener("click", simulate);
  $("reset").addEventListener("click", function () { document.querySelector("#presets .chip").click(); $("simout").textContent = ""; });
  window.addEventListener("resize", render);
  document.querySelector("#presets .chip").click();
})();
