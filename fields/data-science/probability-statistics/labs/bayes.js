(function () {
  "use strict";
  var $ = Lab.$, N = 100000, seed = 1;
  function params() {
    return { p: Math.pow(10, +$("base").value), se: +$("sens").value / 100, fp: +$("fpr").value / 100 };
  }
  function post(prior, se, fp) {
    var tp = se * prior, f = fp * (1 - prior);
    return tp + f === 0 ? NaN : tp / (tp + f);
  }
  function fmtP(x) { return isNaN(x) ? "n/a" : Lab.pct(x, 2); }
  function render() {
    var q = params();
    var sick = N * q.p, clean = N - sick, tp = sick * q.se, fn = sick - tp, fp = clean * q.fp, tn = clean - fp;
    var r = function (x) { return Math.round(x).toLocaleString("en"); };
    $("n-sick").textContent = r(sick); $("n-tp").textContent = r(tp); $("n-fp").textContent = r(fp);
    $("t-tp").textContent = r(tp); $("t-fn").textContent = r(fn); $("t-sick").textContent = r(sick);
    $("t-fp").textContent = r(fp); $("t-tn").textContent = r(tn); $("t-clean").textContent = r(clean);
    var p1 = post(q.p, q.se, q.fp), p2 = post(p1, q.se, q.fp);
    $("post").textContent = fmtP(p1); $("post2").textContent = fmtP(p2);
    var neg = fn + tn;
    $("postneg").textContent = neg ? Lab.pct(fn / neg, 4) : "n/a";
    $("cap").textContent = "Of " + r(tp + fp) + " positives, " + r(tp) + " are real and " + r(fp) + " are false alarms.";
    // stacked bar of positives
    var cv = $("cv"), P = Lab.prep(cv, 0.2), c = P.ctx, col = Lab.colors(), total = tp + fp;
    c.clearRect(0, 0, P.w, P.h);
    var x0 = 10, W = P.w - 20, y = P.h * 0.25, h = P.h * 0.5;
    var wt = total ? W * tp / total : 0;
    c.fillStyle = col.acc; c.fillRect(x0, y, wt, h);
    c.fillStyle = col.acc2; c.fillRect(x0 + wt, y, W - wt, h);
    c.font = "12px system-ui,sans-serif"; c.fillStyle = col.mut; c.textAlign = "left";
    c.fillText("real (green) vs false alarm (orange), all positives = 100% of the bar", x0, y - 6);
  }
  function simulate() {
    var q = params(), rr = Lab.rng(seed++), tp = 0, fp = 0;
    for (var i = 0; i < N; i++) {
      var sick = rr() < q.p, pos = rr() < (sick ? q.se : q.fp);
      if (pos) { if (sick) tp++; else fp++; }
    }
    var exact = post(q.p, q.se, q.fp);
    $("simout").textContent = "Simulated: " + tp + " true positives, " + fp + " false positives, share real = " +
      (tp + fp ? Lab.pct(tp / (tp + fp), 2) : "n/a") + " (exact " + fmtP(exact) + ").";
  }
  Lab.slider("base", function (v) { return Lab.pct(Math.pow(10, v), Math.pow(10, v) < 0.01 ? 3 : 2); }, render);
  Lab.slider("sens", function (v) { return v.toFixed(1) + "%"; }, render);
  Lab.slider("fpr", function (v) { return v.toFixed(1) + "%"; }, render);
  $("sim").addEventListener("click", simulate);
  $("reset").addEventListener("click", function () {
    $("base").value = -3; $("sens").value = 99; $("fpr").value = 1;
    ["base", "sens", "fpr"].forEach(function (id) { $(id).dispatchEvent(new Event("input")); });
  });
  Array.prototype.forEach.call(document.querySelectorAll("button[data-b]"), function (b) {
    b.addEventListener("click", function () {
      $("base").value = b.getAttribute("data-b"); $("sens").value = b.getAttribute("data-s"); $("fpr").value = b.getAttribute("data-f");
      ["base", "sens", "fpr"].forEach(function (id) { $(id).dispatchEvent(new Event("input")); });
    });
  });
  window.addEventListener("resize", render);
  render();
})();
