// Shared image maths for the image-processing labs (vanilla JS, no libraries; runs under Node too, so the numbers can be checked).
(function (g) {
  "use strict";
  var N = 128; // the labs work on a 128 x 128 picture drawn in code

  function rng(seed) { // mulberry32, the same generator as lab-core.js
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function normal(r) { var u = 0; while (u === 0) u = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r()); }
  function clamp(v) { return v < 0 ? 0 : v > 255 ? 255 : v; }

  // A made-up scene with a ramp, a disc, a framed box, a diagonal line, stripes and a few bars: smooth areas, edges and texture.
  function scene() {
    var a = new Float32Array(N * N), x, y, dx, dy;
    for (y = 0; y < N; y++) for (x = 0; x < N; x++) {
      var v = 45 + 70 * x / N + 18 * Math.sin(2 * Math.PI * y / N);
      dx = x - 40; dy = y - 42;
      if (dx * dx + dy * dy < 484) v = 205 - 20 * (dx * dx + dy * dy) / 484;
      if (x >= 72 && x < 112 && y >= 14 && y < 46) v = 28;
      if (x >= 82 && x < 102 && y >= 22 && y < 38) v = 170;
      if (Math.abs(x - y - 30) < 2 && y > 56 && y < 122) v = 235;
      if (x >= 12 && x < 64 && y >= 78 && y < 118) v = (Math.floor(x / 4) % 2) ? 70 : 195;
      a[y * N + x] = Math.round(v);
    }
    [[76, 84, 3, 12], [81, 84, 3, 12], [86, 90, 8, 3], [86, 100, 8, 3], [98, 84, 3, 12], [104, 84, 3, 12], [98, 100, 9, 3], [78, 104, 12, 3], [94, 106, 3, 10], [100, 104, 10, 3]].forEach(function (b) {
      for (var yy = b[1]; yy < b[1] + b[3] && yy < N; yy++) for (var xx = b[0]; xx < b[0] + b[2] && xx < N; xx++) a[yy * N + xx] = 225;
    });
    return a;
  }

  // Drawing: gray levels onto a canvas of n x n pixels (CSS scales it up without smoothing).
  function draw(cv, arr, n, mapf) {
    n = n || N; cv.width = n; cv.height = n;
    var c = cv.getContext("2d"), im = c.createImageData(n, n), i, v;
    for (i = 0; i < n * n; i++) { v = clamp(mapf ? mapf(arr[i], i) : arr[i]); im.data[4 * i] = im.data[4 * i + 1] = im.data[4 * i + 2] = v; im.data[4 * i + 3] = 255; }
    c.putImageData(im, 0, 0);
  }
  function counts(arr) { var h = new Array(256).fill(0), i; for (i = 0; i < arr.length; i++) h[Math.round(clamp(arr[i]))]++; return h; }
  function drawHist(cv, h, color, bins) { // 256 levels folded into `bins` bars
    bins = bins || 64; cv.width = 256; cv.height = 110;
    var c = cv.getContext("2d"), f = new Array(bins).fill(0), i, m = 1, w = 256 / bins, per = 256 / bins;
    for (i = 0; i < 256; i++) f[Math.floor(i / per)] += h[i];
    for (i = 0; i < bins; i++) if (f[i] > m) m = f[i];
    c.clearRect(0, 0, 256, 110); c.fillStyle = color;
    for (i = 0; i < bins; i++) { var bh = Math.round(104 * f[i] / m); c.fillRect(i * w, 110 - bh, Math.max(1, w - 1), bh); }
  }
  function mse(a, b) { var s = 0, i, d; for (i = 0; i < a.length; i++) { d = a[i] - b[i]; s += d * d; } return s / a.length; }
  function psnr(a, b) { var m = mse(a, b); return m < 1e-9 ? 99 : 10 * Math.log10(255 * 255 / m); }
  function psnrRect(a, b, x0, y0, w, h) { // PSNR inside a w x h patch of the N x N picture
    var s = 0, x, y, d; for (y = y0; y < y0 + h; y++) for (x = x0; x < x0 + w; x++) { d = a[y * N + x] - b[y * N + x]; s += d * d; }
    s /= w * h; return s < 1e-9 ? 99 : 10 * Math.log10(255 * 255 / s);
  }

  // Noise
  function gaussNoise(img, sigma, seed) { var r = rng(seed), o = new Float32Array(img.length), i; for (i = 0; i < img.length; i++) o[i] = clamp(img[i] + sigma * normal(r)); return o; }
  function impulseNoise(img, p, seed) { // a share p of the pixels: half pepper (0), half salt (255)
    var r = rng(seed), o = new Float32Array(img.length), i, u;
    for (i = 0; i < img.length; i++) { u = r(); o[i] = u < p / 2 ? 0 : u < p ? 255 : img[i]; }
    return o;
  }

  // Spatial filters. Border handling: "zero", "replicate" or "reflect" (mirror without repeating the edge row, OpenCV's default).
  function at(img, n, x, y, mode) {
    if (x < 0 || x >= n || y < 0 || y >= n) {
      if (mode === "zero") return 0;
      if (mode === "reflect") { x = x < 0 ? -x : x >= n ? 2 * n - 2 - x : x; y = y < 0 ? -y : y >= n ? 2 * n - 2 - y : y; }
      else { x = x < 0 ? 0 : x >= n ? n - 1 : x; y = y < 0 ? 0 : y >= n ? n - 1 : y; }
    }
    return img[y * n + x];
  }
  function convolve(img, k, m, mode) { // k: m*m weights, applied as a weighted vote (correlation)
    var r = m >> 1, o = new Float32Array(N * N), x, y, s, t, acc;
    for (y = 0; y < N; y++) for (x = 0; x < N; x++) { acc = 0; for (t = -r; t <= r; t++) for (s = -r; s <= r; s++) acc += k[(t + r) * m + s + r] * at(img, N, x + s, y + t, mode); o[y * N + x] = acc; }
    return o;
  }
  function medianFilter(img, m, mode) {
    var r = m >> 1, o = new Float32Array(N * N), w = new Array(m * m), x, y, s, t, k;
    for (y = 0; y < N; y++) for (x = 0; x < N; x++) { k = 0; for (t = -r; t <= r; t++) for (s = -r; s <= r; s++) w[k++] = at(img, N, x + s, y + t, mode); w.sort(function (p, q) { return p - q; }); o[y * N + x] = w[(m * m) >> 1]; }
    return o;
  }
  function boxKernel(m) { return new Array(m * m).fill(1 / (m * m)); }
  function binomialKernel(m) { // 1 2 1 or 1 4 6 4 1, outer product, sums to 1
    var row = m === 3 ? [1, 2, 1] : [1, 4, 6, 4, 1], s = row.reduce(function (a, b) { return a + b; }, 0), k = [], i, j;
    for (i = 0; i < m; i++) for (j = 0; j < m; j++) k.push(row[i] * row[j] / (s * s));
    return k;
  }

  // Fourier: radix-2 FFT, in place; the inverse divides by n, so a 2-D round trip is exact.
  function fft1(re, im, inv) {
    var n = re.length, i, j = 0, k, t, len, bit;
    for (i = 1; i < n; i++) { bit = n >> 1; for (; j & bit; bit >>= 1) j ^= bit; j ^= bit; if (i < j) { t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; } }
    for (len = 2; len <= n; len <<= 1) {
      var ang = 2 * Math.PI / len * (inv ? 1 : -1), wr = Math.cos(ang), wi = Math.sin(ang), h = len >> 1;
      for (i = 0; i < n; i += len) {
        var cr = 1, ci = 0;
        for (k = 0; k < h; k++) {
          var a = i + k, b = a + h, vr = re[b] * cr - im[b] * ci, vi = re[b] * ci + im[b] * cr;
          re[b] = re[a] - vr; im[b] = im[a] - vi; re[a] += vr; im[a] += vi;
          var nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr;
        }
      }
    }
    if (inv) for (i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
  }
  function fft2(re, im, n, inv) {
    var r = new Float64Array(n), m = new Float64Array(n), y, x;
    for (y = 0; y < n; y++) { for (x = 0; x < n; x++) { r[x] = re[y * n + x]; m[x] = im[y * n + x]; } fft1(r, m, inv); for (x = 0; x < n; x++) { re[y * n + x] = r[x]; im[y * n + x] = m[x]; } }
    for (x = 0; x < n; x++) { for (y = 0; y < n; y++) { r[y] = re[y * n + x]; m[y] = im[y * n + x]; } fft1(r, m, inv); for (y = 0; y < n; y++) { re[y * n + x] = r[y]; im[y * n + x] = m[y]; } }
  }

  // A frequency mask at distance D from the centre of the spectrum, cut-off d0 (Butterworth order n).
  function mask(type, d, d0, n) { return type === "ideal" ? (d <= d0 ? 1 : 0) : type === "butter" ? 1 / (1 + Math.pow(d / d0, 2 * n)) : Math.exp(-d * d / (2 * d0 * d0)); }
  // Filter a picture in the frequency domain: pad to 256 x 256 with zeros, centre the spectrum, multiply, invert, crop.
  function freqFilter(img, type, highpass, d0, order) {
    var P = 2 * N, re = new Float64Array(P * P), im = new Float64Array(P * P), x, y, i;
    for (y = 0; y < N; y++) for (x = 0; x < N; x++) re[y * P + x] = img[y * N + x] * (((x + y) & 1) ? -1 : 1);
    fft2(re, im, P, false);
    var spec = new Float32Array(P * P), top = 0, H = new Float32Array(P * P);
    for (i = 0; i < P * P; i++) { spec[i] = Math.log(1 + Math.hypot(re[i], im[i])); if (spec[i] > top) top = spec[i]; }
    for (y = 0; y < P; y++) for (x = 0; x < P; x++) {
      var h = mask(type, Math.hypot(x - P / 2, y - P / 2), d0, order); if (highpass) h = 1 - h;
      H[y * P + x] = h; re[y * P + x] *= h; im[y * P + x] *= h;
    }
    fft2(re, im, P, true);
    var out = new Float32Array(N * N);
    for (y = 0; y < N; y++) for (x = 0; x < N; x++) out[y * N + x] = re[y * P + x] * (((x + y) & 1) ? -1 : 1);
    return { spec: spec, top: top, H: H, out: out, P: P };
  }
  // Ringing, measured on a 1-D bright pulse (0 / 255 / 0, 256 samples) through a low-pass of the same kind: overshoot above 255 and undershoot below 0, in percent of 255.
  function ring1d(type, d0, order) {
    var n = 256, re = new Float64Array(n), im = new Float64Array(n), k;
    for (k = 64; k < 192; k++) re[k] = 255;
    fft1(re, im, false);
    for (k = 0; k < n; k++) { var f = Math.min(k, n - k), h = mask(type, f, d0, order); re[k] *= h; im[k] *= h; }
    fft1(re, im, true);
    var hi = -1e9, lo = 1e9; for (k = 0; k < n; k++) { if (re[k] > hi) hi = re[k]; if (re[k] < lo) lo = re[k]; }
    return { signal: re, over: Math.max(0, hi - 255) / 255 * 100, under: Math.max(0, -lo) / 255 * 100 };
  }
  function alias(f, fs) { return Math.abs(f - Math.round(f / fs) * fs); } // where a wave of frequency f lands when sampled at fs

  // Periodic noise: a sine of `cycles` cycles across the picture along x. In the centred spectrum it is two bright dots at x = N/2 +- cycles.
  function stripes(img, amp, cycles) { var o = new Float32Array(img.length), x, y; for (y = 0; y < N; y++) for (x = 0; x < N; x++) o[y * N + x] = img[y * N + x] + amp * Math.sin(2 * Math.PI * cycles * x / N); return o; }
  // Notch filter on the N x N spectrum (no padding: the stripes fit the picture exactly). holes: [[x, y], ...] in spectrum pixels (the centre is N/2, N/2), radius r.
  function notchFilter(img, holes, r) {
    var re = new Float64Array(N * N), im = new Float64Array(N * N), x, y, i, k;
    for (y = 0; y < N; y++) for (x = 0; x < N; x++) re[y * N + x] = img[y * N + x] * (((x + y) & 1) ? -1 : 1);
    fft2(re, im, N, false);
    var mag = new Float32Array(N * N), top = 0;
    for (i = 0; i < N * N; i++) { mag[i] = Math.hypot(re[i], im[i]); }
    for (i = 0; i < N * N; i++) { var l = Math.log(1 + mag[i]); if (l > top) top = l; }
    var spec = new Float32Array(N * N); for (i = 0; i < N * N; i++) spec[i] = Math.log(1 + mag[i]);
    for (k = 0; k < holes.length; k++) for (y = 0; y < N; y++) for (x = 0; x < N; x++) if (Math.hypot(x - holes[k][0], y - holes[k][1]) <= r) { re[y * N + x] = 0; im[y * N + x] = 0; }
    fft2(re, im, N, true);
    var out = new Float32Array(N * N); for (y = 0; y < N; y++) for (x = 0; x < N; x++) out[y * N + x] = re[y * N + x] * (((x + y) & 1) ? -1 : 1);
    return { out: out, spec: spec, top: top, mag: mag };
  }
  function strongestPeak(mag, skip) { // brightest spectrum point in the right half-plane, away from the centre
    var best = -1, bx = 0, by = 0, x, y; for (y = 0; y < N; y++) for (x = N / 2; x < N; x++) { if (Math.hypot(x - N / 2, y - N / 2) < skip) continue; if (mag[y * N + x] > best) { best = mag[y * N + x]; bx = x; by = y; } }
    return [bx, by];
  }

  // Restoration: blur the picture along x with a box of length a, add Gaussian noise, then undo the blur two ways.
  function degrade(img, a, sigma, seed) {
    var n2 = N * N, re = new Float64Array(img), im = new Float64Array(n2), hr = new Float64Array(n2), hi = new Float64Array(n2), i, x;
    fft2(re, im, N, false);
    for (x = 0; x < a; x++) hr[x] = 1 / a;
    fft2(hr, hi, N, false);
    var gr = new Float64Array(n2), gi = new Float64Array(n2);
    for (i = 0; i < n2; i++) { gr[i] = re[i] * hr[i] - im[i] * hi[i]; gi[i] = re[i] * hi[i] + im[i] * hr[i]; }
    fft2(gr, gi, N, true);
    var rn = rng(seed), g = new Float32Array(n2);
    for (i = 0; i < n2; i++) g[i] = gr[i] + sigma * normal(rn); // the observed picture, not clipped: the blur and the noise as the model has them
    return { g: g, hr: hr, hi: hi };
  }
  function restore(g, hr, hi, kind, K) { // kind: "inverse" or "wiener"
    var n2 = N * N, gr = new Float64Array(g), gi = new Float64Array(n2), R = new Float64Array(n2), I = new Float64Array(n2), i, h2;
    fft2(gr, gi, N, false);
    for (i = 0; i < n2; i++) {
      h2 = hr[i] * hr[i] + hi[i] * hi[i];
      if (kind === "wiener") { R[i] = (hr[i] * gr[i] + hi[i] * gi[i]) / (h2 + K); I[i] = (hr[i] * gi[i] - hi[i] * gr[i]) / (h2 + K); }
      else if (h2 < 1e-12) { R[i] = 0; I[i] = 0; } // exactly erased by the blur: nothing to divide by
      else { R[i] = (gr[i] * hr[i] + gi[i] * hi[i]) / h2; I[i] = (gi[i] * hr[i] - gr[i] * hi[i]) / h2; }
    }
    fft2(R, I, N, true);
    var o = new Float32Array(n2); for (i = 0; i < n2; i++) o[i] = clamp(R[i]);
    return o;
  }

  // Wavelets. The row transform is the page's: average and half-difference. The image transform is orthonormal Haar (divide by sqrt 2).
  function haarRow(row) { // returns {out, levels:[{avg, det}]}; length a power of two
    var cur = row.slice(), out = [], levels = [], i;
    while (cur.length > 1) {
      var avg = [], det = [];
      for (i = 0; i < cur.length; i += 2) { avg.push((cur[i] + cur[i + 1]) / 2); det.push((cur[i] - cur[i + 1]) / 2); }
      levels.push({ avg: avg, det: det }); out = det.concat(out); cur = avg;
    }
    return { out: cur.concat(out), levels: levels };
  }
  function haarLine(a, off, st, s, inv, t) {
    var h = s >> 1, i, r = Math.SQRT1_2, p, q;
    if (!inv) for (i = 0; i < h; i++) { p = a[off + 2 * i * st]; q = a[off + (2 * i + 1) * st]; t[i] = (p + q) * r; t[h + i] = (p - q) * r; }
    else for (i = 0; i < h; i++) { p = a[off + i * st]; q = a[off + (h + i) * st]; t[2 * i] = (p + q) * r; t[2 * i + 1] = (p - q) * r; }
    for (i = 0; i < s; i++) a[off + i * st] = t[i];
  }
  function haar2(a, L, inv) { // in place on an N x N Float64Array, L levels
    var t = new Float64Array(N), s, l, y, x;
    if (!inv) { s = N; for (l = 0; l < L; l++) { for (y = 0; y < s; y++) haarLine(a, y * N, 1, s, false, t); for (x = 0; x < s; x++) haarLine(a, x, N, s, false, t); s >>= 1; } }
    else { s = N >> (L - 1); for (l = 0; l < L; l++) { for (x = 0; x < s; x++) haarLine(a, x, N, s, true, t); for (y = 0; y < s; y++) haarLine(a, y * N, 1, s, true, t); s <<= 1; } }
  }

  // Equalisation as a lookup table: s_k = round((L-1) * cumulative share up to k).
  function equalizeLut(c, L) {
    var total = 0, run = 0, lut = [], k; for (k = 0; k < L; k++) total += c[k];
    for (k = 0; k < L; k++) { run += c[k]; lut.push(total ? Math.round((L - 1) * run / total) : 0); }
    return lut;
  }

  g.Img = { N: N, rng: rng, normal: normal, clamp: clamp, scene: scene, draw: draw, counts: counts, drawHist: drawHist, mse: mse, psnr: psnr, psnrRect: psnrRect,
    gaussNoise: gaussNoise, impulseNoise: impulseNoise, convolve: convolve, medianFilter: medianFilter, boxKernel: boxKernel, binomialKernel: binomialKernel,
    fft1: fft1, fft2: fft2, mask: mask, freqFilter: freqFilter, ring1d: ring1d, alias: alias, stripes: stripes, notchFilter: notchFilter, strongestPeak: strongestPeak, degrade: degrade, restore: restore,
    haarRow: haarRow, haar2: haar2, equalizeLut: equalizeLut };
})(typeof window !== "undefined" ? window : globalThis);
