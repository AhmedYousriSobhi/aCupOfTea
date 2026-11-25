
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/digital-image-processing/">Digital Image Processing</a></nav>

# Pick and Check an Image-Processing Step

<!-- related-block -->
<div class="reading-time">Intermediate · Guide · 6 min read · Updated 25 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/filtering">filtering</a> <a class="chip" href="#/.docs/generated/explore/tags/quick">quick</a></div>


> **Quick guide for** [Intensity transforms](/fields/digital-image-processing/intensity-transforms-and-histograms.md) (part 3), [Spatial filtering](/fields/digital-image-processing/spatial-filtering.md) (part 4), [Frequency filtering and aliasing](/fields/digital-image-processing/frequency-filtering-and-aliasing.md) (part 7), [Noise and restoration](/fields/digital-image-processing/noise-and-restoration.md) (part 8) and [Wavelets](/fields/digital-image-processing/wavelets-and-multiresolution-processing.md) (part 9).
> Use it when an image misbehaves and you need to choose the step and check one number by hand. The five labs at the end let you move the dials.

## 3. Image too dark or washed out

1. Measure first: `h(r_k) = n_k`, `p(r_k) = n_k / MN`. **Expect:** bars squeezed against one wall.
2. Pick the transform:

| Transform | Formula | Reach for it when |
|---|---|---|
| Negative | `s = (L-1) - r` | White-on-dark detail in a dark region |
| Log | `s = c * log(1 + r)` | A huge range crushed into a few bright values |
| Gamma | `s = c * r^γ` | γ < 1 brightens darks, γ > 1 darkens, γ = 1 does nothing |

3. Or equalize: `s_k = (L-1) * sum(p(r_j))`. **Check:** 8 x 8 pixels, L = 8, 24 pixels at level 0 gives `7 * 24 / 64 = 2.625`, so level 0 becomes 3. **Expect:** the counts still add up to 64.

> [!WARNING]
> Equalization merges levels (information is lost) and amplifies noise in large flat regions. CLAHE limits that: `createCLAHE` in OpenCV.

## 4. One bad pixel, or noise everywhere

1. Box filter: every weight `1/9` in a 3 x 3 window. Median: sort the nine values, take the middle one.
2. **Check:** eight 10s and one 90 give a mean of `170 / 9 ≈ 18.9` and a median of 10.
3. Pick by noise: the mean for Gaussian-like noise (it blurs edges), the median for salt-and-pepper (it is nonlinear and keeps edges better).
4. Set the border: zero (dark halo), replicate (neutral, smeary) or reflect (smooth, the usual default). OpenCV's `filter2D` uses `BORDER_REFLECT_101`. **Expect:** with padding the output keeps the input size; without it a k x k kernel shrinks N to `N - k + 1`.
5. For a big blur use a separable kernel, two 1-D passes: k = 3, 5, 11 cost 9, 25, 121 multiplies as one pass and 6, 10, 22 as two.

Weights that sum to 1 keep brightness; weights that sum to 0 respond only to change.

## 7. Filter by frequency, then sample

1. Recipe: FFT, multiply by the mask `H(u,v)`, inverse FFT: `G(u,v) = H(u,v) F(u,v)`. Pad with zeros to at least the image size plus the kernel size, filter, crop. **If not:** the left edge bleeds in from the right (wraparound).
2. Choose the mask:

| Filter | `H(u,v)` | Note |
|---|---|---|
| Ideal | 1 if `D ≤ D₀`, else 0 | Rings |
| Butterworth | `1 / (1 + (D/D₀)^(2n))` | Larger n is steeper and rings more |
| Gaussian | `exp(-D² / (2·D₀²))` | No ringing: use it unless you have a reason not to |

3. High-pass is `1 - H_lp`. A notch removes one frequency or a symmetric pair: the tool for periodic noise.
4. Sample at `f_s > 2 * f_max`. **Check:** a 9 Hz wave sampled 10 times per second appears at `|9 - 10| = 1` Hz; the general rule is `|f - k * f_s|`.
5. Shrinking an image: blur, then downsample. In OpenCV, `INTER_AREA` for `resize`.

> [!WARNING]
> Once aliasing has happened it cannot be undone. Fix it before sampling.

## 8. Un-blur and de-noise

1. Write the damage: `g = h * f + η`, in frequency `G = H F + N`.
2. Match the filter to the noise: Gaussian, mean or Gaussian blur; salt-and-pepper, median; periodic stripes, notch; several frames of a still scene, average them (the noise standard deviation falls by about `√n`).
3. Do not divide by the blur: `F̂ = G / H = F + N / H`. **Check:** H = 0.01 and N ≈ 1 make the noise about 100 times bigger.
4. Use Wiener: `F̂ = [H* / (|H|² + K)] G`. **Check:** H = 0.01, K = 0.01 give a gain of `0.01 / 0.0101 ≈ 0.99`. Tune K by eye: too small and the noise creeps back, too big and it stays blurry.
5. Score with `PSNR = 10 * log10(MAX² / MSE)`. **Check:** MSE = 100 and MAX = 255 give about 28.1 dB; every 3 dB is about half the MSE.

> [!WARNING]
> PSNR only loosely matches how a person judges quality. The `√n` rule needs noise that is independent and zero-mean across frames; a fixed pattern does not average out.

## 9. See the picture at several scales

1. One level of the Haar step: replace each pair with its average and its half-difference. **Check:** `[9, 7, 3, 5]` gives averages `[8, 4]` and details `[1, -1]`; again on the averages gives `[6 | 2 | 1, -1]`.
2. Undo it: first = average + detail, second = average − detail.
3. For an image, do rows then columns: four subbands (approximation, horizontal, vertical, diagonal detail), then repeat on the approximation. PyWavelets returns them in that order; other books name them differently.
4. Denoise: shrink or zero every detail coefficient below a threshold, then invert. **Check:** `[10, 10, 10, 50, 50, 50, 50, 50]` has finest details `[0, -20, 0, 0]`.

The orthonormal Haar transform divides by `√2` instead; the structure is the same.

## Symptoms

| What you see | Likely cause | Fix |
|---|---|---|
| Every value between 0 and about 60 | A dark image | Gamma below 1, or equalization |
| A white speck still leaves a smudge | A mean on impulse noise | Median |
| Faint bands beside every edge | An ideal low-pass | Gaussian mask |
| Crunchy thumbnails, shimmering stripes | Aliasing from sampling too coarsely | Blur, then downsample |
| "Restored" photo is static | Dividing by a near-zero H | Wiener with a K |
| Denoising smears the edges | A mean blurs edges with the noise | Wavelet threshold |

## Try it

### Intensity transforms lab

[Intensity transforms lab](/fields/digital-image-processing/labs/intensity-transforms.html#embed ':ignore')

### Spatial filters lab

[Spatial filters lab](/fields/digital-image-processing/labs/spatial-filters.html#embed ':ignore')

### Frequency filters lab

[Frequency filters lab](/fields/digital-image-processing/labs/frequency-filters.html#embed ':ignore')

### Restoration lab

[Restoration lab](/fields/digital-image-processing/labs/restoration.html#embed ':ignore')

### Wavelets lab

[Wavelets lab](/fields/digital-image-processing/labs/wavelets.html#embed ':ignore')

**Why it works:** the five story pages above. Back to the [series overview](/fields/digital-image-processing/README.md).

<!-- related-block -->
<div class="see-also">

**See also**

- [One Bad Pixel: Spatial Filtering](/fields/digital-image-processing/spatial-filtering.md) — Kernels, correlation versus convolution, padding and separability - blurring explained as a neighbourhood vote, with the mean and median compared on one noisy pixel.
- [The Photo That Turned to Static: Noise and Restoration](/fields/digital-image-processing/noise-and-restoration.md) — The degradation model g = h*f + n, common noise types, why inverse filtering explodes, and how the Wiener filter gives up gracefully - with PSNR to score the result.
- [The Shirt That Shimmers: Frequency Filtering and Aliasing](/fields/digital-image-processing/frequency-filtering-and-aliasing.md) — Low-pass, high-pass and notch filters as masks on the spectrum, why the ideal filter rings, and how sampling too coarsely creates moire - with the Nyquist rule worked on one number.
- [The Unreadable X-ray: Intensity Transforms and Histograms](/fields/digital-image-processing/intensity-transforms-and-histograms.md) — Rescue a dark image with one formula - negatives, log, gamma and histogram equalization, with the CDF worked out by hand on a tiny image.
- [Wavelets and Multiresolution Processing](/fields/digital-image-processing/wavelets-and-multiresolution-processing.md) — Seeing an image at several scales at once - pyramids, a Haar wavelet transform by hand, the four 2D subbands, and why mostly-zero detail makes denoising and compression work.

</div>
