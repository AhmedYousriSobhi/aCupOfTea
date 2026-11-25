<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/digital-image-processing/">Digital Image Processing</a></nav>

# The Shirt That Shimmers: Frequency Filtering and Aliasing

<!-- related-block -->
<div class="reading-time">Intermediate · Concept · 10 min read · Updated 25 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/convolution">convolution</a> <a class="chip" href="#/.docs/generated/explore/tags/filtering">filtering</a> <a class="chip" href="#/.docs/generated/explore/tags/fourier-transform">fourier-transform</a> <a class="chip" href="#/.docs/generated/explore/tags/sampling">sampling</a></div>
<!-- related-block -->
<div class="lab-line">Interactive lab: <a href="#/fields/digital-image-processing/frequency-filtering-and-aliasing?id=try-it-the-shirt-that-shimmers-filter-the-spectrum-then-sample-it">The shirt that shimmers, filter the spectrum, then sample it</a></div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [The Fourier Transform for Images](/fields/digital-image-processing/fourier-transform-for-images.md)  ·  **Read next:** [The Photo That Turned to Static: Noise and Restoration](/fields/digital-image-processing/noise-and-restoration.md)

</div>


> **Part 7 of the [Digital Image Processing series](/fields/digital-image-processing/README.md).** Give the choir a volume knob for every singer, then find out what happens when the town is too small to hear the fast ones. *Kofi and the broadcast team are invented; the maths and numbers are real.* By the end you can design a filter as a mask on the spectrum and compute an alias by hand.

```text
T-40:00   segment confirmed, anchor in the striped shirt
T-25:00   moire noticed on camera two
T-12:00   you draft a very sharp low-pass filter
```

---

## The shirt that crawls

The anchor wears a fine striped shirt. On camera, the stripes crawl and shimmer in slow rainbow bands that aren't on the shirt at all. The producers have a name for it: moiré. The viewers have another name for it: "why is his shirt doing that?".

You're the broadcast engineer, Kofi is the producer's voice in your ear, and the segment is live in forty minutes. Your first reading is the obvious one: **the footage has a pattern in it that should be filtered out.**

---

## One very sharp filter

You build a low-pass filter with a perfectly sharp wall to remove everything above a cutoff, and put it on the live feed with twelve minutes to spare. Nobody reviews it.

On the monitor, the slow bands are still there, and now there is a faint ripple around the anchor's collar and every edge on the set. The producer notices at T-00:10 and asks what happened to the picture. You take the filter out.

The filter softened the picture, left the slow bands alone and added ripples of its own. The stripes are the problem, and filtering after the camera did nothing to them. Where do the stripes come from? First, you need to see what a filter actually does to the spectrum.

---

## The recipe: transform, multiply, transform back

Thanks to the convolution theorem, filtering in the frequency domain is a three-step recipe:

$$G(u,v) = H(u,v)\,F(u,v)$$

```mermaid
flowchart LR
    A["Image f"] --> B["FFT"]
    B --> C["Multiply by<br/>filter H(u,v)"]
    C --> D["Inverse FFT"]
    D --> E["Filtered image g"]
```

*H is a mask the same size as the spectrum. Values near 1 keep a frequency, values near 0 remove it.*

Think of the choir from the last page: every singer is a frequency, and H is a volume knob for each one. Let D(u,v) be the distance of a frequency from the centre of the (shifted) spectrum, and D₀ the **cutoff**. Everything below is a different way to design H. So how do you turn the high singers down?

---

## Three ways to turn the highs down

A **low-pass** filter keeps low frequencies (smooth shading) and removes high ones (edges, texture, noise). It blurs.

| Filter | H(u,v) | Character |
|---|---|---|
| Ideal | 1 if D ≤ D₀, else 0 | Sharp cutoff, **rings** (next section) |
| Butterworth (order n) | 1 / (1 + (D/D₀)^(2n)) | Smooth cutoff; larger n is steeper and rings more |
| Gaussian | exp(−D² / (2·D₀²)) | Smoothest; **no ringing** |

The Gaussian has a bonus: its inverse transform is also a Gaussian. A Gaussian mask in frequency matches a Gaussian kernel in space, so it's the same blur as page 4, just designed from the other side.

> [!TIP]
> Recommendation: use the Gaussian unless you have a reason not to. It's the only one of the three with no artifacts. Pick the Ideal filter only to see the artifact once, for the lesson.

You picked the first row, the Ideal one, with twelve minutes to spare. So where did the ripples around the collar come from?

---

## Why the sharp wall rings

An ideal low-pass is a perfect circle of 1s with a hard wall. Its equivalent spatial kernel, via the inverse transform, is not a gentle blob. It's a **sinc**-like function: a central peak with endless decaying ripples around it.

Convolve a sharp edge with ripples and you get ripples next to the edge: faint bands that follow every edge, like the echo after a shout in a stairwell. It's the same overshoot and undershoot as page 5's sharpening, now caused by cutting frequencies too abruptly.

The rule: **a sharp edge in one domain becomes ripples in the other.** A softer cutoff means fewer ripples. That's why Gaussian wins.

Turn the knob the other way and you get a **high-pass** filter: H_hp = 1 − H_lp. It removes smooth shading and keeps edges, which is another way to see the sharpening of page 5: unsharp masking is "the original plus some high-pass".

A **notch** filter removes one specific frequency, or a symmetric pair, and leaves everything else alone. It's the right tool for **periodic noise**, such as the regular line pattern from a scanner or a screen-captured halftone. In the spectrum that noise shows up as a few isolated bright dots, and you mask just those dots. No spatial kernel can do that as cleanly.

| Goal | Filter | Mask looks like |
|---|---|---|
| Blur, remove noise | Low-pass | Bright disc in the centre |
| Find edges, sharpen | High-pass | Dark disc in the centre |
| Remove a repeating pattern | Notch | Everything on except small holes at the bright dots |

A notch looks like the right tool for stripes, doesn't it? It isn't, and the reason is the stripes aren't in the footage the way a scanner's lines are. Try this first.

☕ **Try it before you scroll.** A signal contains a pure 9 Hz wave. You sample it **10 times per second**. When you look at the samples, what frequency do they appear to have? *Hint: 10 samples per second can describe at most 5 Hz honestly.*

---

## A grid that cannot hear every singer

**Answer:** **1 Hz.** Here's why.

To capture a wave faithfully you must sample it more than **twice per cycle**. The **Nyquist–Shannon sampling theorem** says: if the highest frequency in the signal is f_max, you need

$$f_s > 2\, f_{\max}$$

samples per unit length (per second, or per millimetre across a scene) to be able to reconstruct it. Half the sampling rate, f_s / 2, is the **Nyquist frequency**: the fastest wave the grid can honestly describe.

Anything faster doesn't vanish. It **folds back** into the range the grid can see. A wave at frequency f above the Nyquist limit appears at |f − k·f_s| for the integer k that lands it inside the range. For our case: |9 − 10| = **1 Hz**.

That's **aliasing**: a fast wave pretending to be a slow one. Now look at the shirt again.

---

## The shirt, the screen and the wheel

The stripes are too fine for the camera's pixel grid. The sensor reports a much coarser stripe pattern that isn't on the shirt: moiré.

The same effect appears in three places you've met:

| Where | What happens |
|---|---|
| Camera or scanner | Fine patterns (shirts, screens, brick, halftone) make moiré |
| Shrinking an image | Picking every second pixel drops fine detail into false jagged patterns |
| Wheel on video | The wheel appears to turn slowly or backward (temporal aliasing, same math) |

The **fix is applied before sampling**: remove the frequencies the grid can't carry, by blurring with a low-pass filter, then sample. Optical cameras use an anti-aliasing filter on the sensor for exactly this. In software, **blur, then downsample**. Shrinking without blurring first is the standard cause of "my thumbnails look crunchy". OpenCV's `INTER_AREA` option for `resize` exists for this reason, and its docs recommend it for shrinking.

Once aliasing has happened it can't be undone: the information about the true frequency is gone, and the 1 Hz you see could just as well have come from a real 1 Hz wave.

There's one more trap in the recipe, and it bites at the edges of the picture.

---

## The wallpaper trap

One trap from [page 6](/fields/digital-image-processing/fourier-transform-for-images.md): multiplying DFTs corresponds to **circular** convolution, as if the image repeated like wallpaper. Filter without care and the left edge's content bleeds in from the right edge.

The fix is to **pad** the image with zeros (to at least the image size plus the kernel size) before transforming, filter, and crop afterwards.

Now you know enough to go back to the live feed.

---

## Back to the shirt

You compare the stripe spacing with the camera grid. The stripes are finer than the grid can describe, so the camera reports different, coarser stripes that were never there.

The anchor's shirt had stripes finer than the Nyquist limit of the camera, so they folded down into slow bands: moiré. You can't fix it after the fact. You fix it before: change the shirt, move the camera, or blur optically.

And the choir picture holds: each singer is a frequency, the grid can only hear up to half its sampling rate, and any singer above that is mistaken for a lower one.

### Try it: The shirt that shimmers, filter the spectrum, then sample it

> **What it shows:** Filtering in frequency is three steps: transform, multiply by a mask, transform back. Cut too sharply and it rings; sample too coarsely and it aliases.  
> **Start with:** the preset *Gaussian low-pass* (No ringing at all: its twin in space is a Gaussian too. PSNR 21.8 dB at D₀ = 30).

[Frequency filters lab](/fields/digital-image-processing/labs/frequency-filters.html#embed ':ignore')

---

## Never again: filter by frequency, sample with care

| Do | Because |
|---|---|
| Use a Gaussian mask unless you have a reason not to | It is the only one of the three with no artifacts; the ideal filter rings; Butterworth rings more as `n` grows |
| Build high-pass as `1 − H_lp` | It keeps edges and removes smooth shading |
| Use a notch for periodic noise | It removes one frequency (or a symmetric pair) and nothing else |
| Pad before you transform | Zero-pad to at least the image size plus the kernel size, filter, then crop; otherwise the left edge bleeds in from the right |
| Check `f_s > 2 f_max` before you sample | The Nyquist frequency `f_s / 2` is the fastest wave the grid describes honestly |
| Blur first, then downsample | Aliasing cannot be undone afterwards (`INTER_AREA` in OpenCV for shrinking) |

**Takeaway:** a frequency filter is a mask on the spectrum (Gaussian is the safe choice), and sampling below twice the highest frequency creates aliases that can't be undone.

**Next:** real images arrive damaged by noise and blur. Can you undo the damage by dividing it out? [Part 8: Noise and restoration](/fields/digital-image-processing/noise-and-restoration.md).

---

## 📜 The Scroll (keep this)

```text
Symptom:  Shimmering bands that are not on the object (moire); crunchy thumbnails
Cause:    Detail finer than the grid folds back: |f - k*fs|; 9 Hz at 10/s -> 1 Hz
Check:    fs > 2 * fmax ? Nyquist = fs/2
Do not:   Filter after sampling and expect it back; use an ideal low-pass (rings)
Fix:      Blur before sampling or shrinking; Gaussian mask; notch for stripes
Pad:      Zero-pad before the FFT, crop after (wraparound)
```


### References

- R. C. Gonzalez and R. E. Woods, *Digital Image Processing*, 4th ed., Pearson, 2018: chapter 4 (sampling and the Fourier transform of sampled functions, aliasing, lowpass, highpass and notch filters).
- C. E. Shannon, "Communication in the Presence of Noise", *Proceedings of the IRE*, 37(1), 10-21, 1949.
- OpenCV documentation, [Geometric Image Transformations](https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html): `resize` and `INTER_AREA`.

<!-- related-block -->
<div class="see-also">

**See also**

- [Pick and Check an Image-Processing Step](/fields/digital-image-processing/quick-guide.md) — A cheat sheet for parts 3, 4, 7, 8 and 9 - which transform or filter to pick, the number to check by hand, and five labs to try.
- [The Jagged Scan: Geometric Transforms and Interpolation](/fields/digital-image-processing/geometric-transforms-and-interpolation.md) — Moving the whole map - affine transforms in homogeneous coordinates, why you must map backwards, and nearest, bilinear and bicubic interpolation with a bilinear example worked by hand.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Meet Fourier](/fields/digital-image-processing/meet-fourier.md) — The story of Joseph Fourier, the prefect who drained swamps and studied heat, and why his idea that heat spreads as a sum of sine waves ended up inside every image filter.
- [Pick and Check an Image-Processing Step](/fields/digital-image-processing/quick-guide.md) — A cheat sheet for parts 3, 4, 7, 8 and 9 - which transform or filter to pick, the number to check by hand, and five labs to try.
- [The Fourier Transform for Images](/fields/digital-image-processing/fourier-transform-for-images.md) — What the 2D DFT really says - an image as a sum of waves, magnitude versus phase, a 4-point DFT done by hand, and the convolution theorem that turns sliding windows into multiplication.
- [The Jagged Scan: Geometric Transforms and Interpolation](/fields/digital-image-processing/geometric-transforms-and-interpolation.md) — Moving the whole map - affine transforms in homogeneous coordinates, why you must map backwards, and nearest, bilinear and bicubic interpolation with a bilinear example worked by hand.
- [The Scan That Opened Black: Images Are Just Matrices](/fields/digital-image-processing/images-are-just-matrices.md) — A pixel is a number in a grid - sampling, quantization, bit depth, coordinates and neighbours, and why 200 + 100 can equal 44.

</div>
