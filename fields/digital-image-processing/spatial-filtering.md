---
id: dip-spatial-filtering
title: "One Bad Pixel: Spatial Filtering"
sidebar_label: 4. Spatial filtering
order: 4
summary: Kernels, correlation versus convolution, padding and separability - blurring explained as a neighbourhood vote, with the mean and median compared on one noisy pixel.
level: beginner
type: concept
domains: [image-processing, deep-learning]
tags: [convolution, filtering, noise]
relations:
  prerequisites: [dip-intensity-transforms-histograms]
  related: [dip-fourier-transform-images]
---

# One Bad Pixel: Spatial Filtering

> **Part 4 of the [Digital Image Processing series](/fields/digital-image-processing/README.md).** *Mira, Ravi and the facilities team are invented; the maths and numbers are real.*

On Wednesday Mira will be asked to clean a single white speck off a photo of a gray wall. She will remove it three different ways and each will be the right answer for something. One of them will have been about to erase the thin lines of 200 floor plans.

**By the end of this page you will be able to:**

- Compute a filtered pixel by hand.
- Explain why convolution flips the kernel, and why CNN libraries quietly don't.
- Pick the mean or the median by the kind of noise.
- Choose what to put outside the picture at the border.
- Explain why a big Gaussian blur costs far less than it looks.

---

## One citizen shouts

The facilities team photographs a wall for a survey, and the scanner leaves a single white speck in the middle of a gray patch. Every neighbour says 10. One citizen shouts 90.

The team lead wants it gone before the report goes out. Ravi says: "Average it with the neighbours. Done." Mira has a nagging feeling that someone once told her to take the middle value instead.

Her first reading is the obvious one: it is one bad pixel, so **any smoothing will fix it**.

---

## Three ways to quiet a loud pixel

**Attempt 1: average it.** She applies a 3 × 3 box filter. The speck is much fainter, and it has left a smudge where it used to be.

**Attempt 2: average over a bigger window.** If a small window leaves a smudge, a bigger one will dilute it more. The smudge gets wider and fainter, and the wall's real edges start going soft with it.

**Attempt 3: take the middle value, everywhere.** She remembers the median, and it removes the speck completely. Pleased, she queues the median filter over the facilities team's whole folder, which includes 200 scanned floor plans. Ravi stops the job and holds one up: the thin walls have vanished from half the drawings.

So far:

- Averaging leaves a smudge, and a bigger window only spreads it.
- The median removed the speck cleanly.
- The same median erased thin lines it should have kept.

That leaves one question: **what does each filter actually compute from nine numbers, and when is each one right?**

---

## Nine numbers, two ways to vote

### The neighbourhood vote

A **spatial filter** computes each output pixel from a small window of input pixels around it. The window of weights is called a **kernel** (or mask, or filter), usually 3 × 3, 5 × 5, or another odd size so it has a centre.

```mermaid
flowchart LR
    A["Place kernel<br/>on a pixel"] --> B["Multiply each weight<br/>by the pixel under it"]
    B --> C["Add everything up"]
    C --> D["Write the sum to<br/>the output pixel"]
    D --> E["Slide one step<br/>and repeat"]
```

*The whole algorithm. Every "filter" in the next three pages is a different kernel in this loop.*

With a kernel w of size (2a+1) × (2b+1), the output is:

$$g(x,y) = \sum_{s=-a}^{a}\sum_{t=-b}^{b} w(s,t)\, f(x+s,\, y+t)$$

That is a weighted vote: each neighbour gets a weight, and the sum is the result. For a **box** (mean) filter every weight is 1/9 in a 3 × 3 window, so the pixel becomes the plain average of itself and its eight neighbours.

> [!TIP]
> Weights that sum to **1** keep overall brightness. Weights that sum to **0** (edge detectors, page 5) give zero on flat regions and a response only where things change.

### Correlation and convolution

The formula above is technically **correlation**. True **convolution** flips the kernel by 180° (both axes) before sliding it:

$$g(x,y) = \sum_{s=-a}^{a}\sum_{t=-b}^{b} w(s,t)\, f(x-s,\, y-t)$$

Only the sign inside f changed, and that sign decides whether you read the kernel forwards or backwards.

If the kernel is symmetric (box, Gaussian, Laplacian), flipping changes nothing and the two are the same. They differ only for asymmetric kernels such as a Sobel edge detector, where the flip reverses the direction of the response.

Why does the flip exist at all? Because convolution has clean algebra: it is commutative and associative, and, as [page 6](/fields/digital-image-processing/fourier-transform-for-images.md) shows, it turns into plain multiplication in the frequency domain. Correlation is the "what matches this pattern?" operation and is what you reach for when you slide a template over a picture.

### Try it before you scroll

☕ You apply a 3 × 3 box filter (all weights 1/9) to the neighbourhood below. **What does the centre pixel become?**

```text
10  10  10
10  90  10
10  10  10
```

*Hint: eight 10s and one 90.*

**Answer:** (8 × 10 + 90) / 9 = 170 / 9 ≈ **18.9**. The speck dropped from 90 to 19, but it didn't disappear. It also **bled** into all eight neighbours: each of them now gets a share of that 90 in its own average. The wall has a smudge where the speck used to be.

### Mean versus median

The median filter takes the same nine values, sorts them, and picks the middle one:

```text
sorted: 10 10 10 10 10 10 10 10 90   ->   median = 10
```

The speck vanishes completely and nothing bleeds. A single outlier can never be the median of nine numbers unless five others agree with it.

| | Mean (box) | Median |
|---|---|---|
| Is it a kernel (weighted sum)? | Yes, linear | No, it sorts, so it is **nonlinear** |
| Good against | Gaussian-like noise spread over every pixel | Salt-and-pepper (isolated extreme pixels) |
| Side effect | Blurs edges | Preserves edges better, can erase thin lines |

So the manager and the other engineer were both right. They were treating different noise: Pixel Town's whisper campaign versus one loudmouth. More on telling them apart on [page 8](/fields/digital-image-processing/noise-and-restoration.md).

> ☕ **Try it live.** Edit the nine numbers under the window, then add noise to a picture and compare the mean, the median and the three borders.

[Spatial filters lab](/fields/digital-image-processing/labs/spatial-filters.html#embed ':ignore')

### The edge of the map

At the border, a 3 × 3 window hangs off the image. Something has to fill the missing neighbours. Common choices:

| Padding | Fills the outside with | Effect |
|---|---|---|
| Zero | 0 | Dark halo around the border |
| Replicate | The nearest edge pixel, repeated | Neutral, a bit smeary |
| Reflect | The image mirrored across the border | Smooth, the usual default |

With p pixels of padding on every side the output keeps the input size ("same"). With no padding ("valid") a k × k kernel shrinks an N-wide image to N − k + 1. OpenCV's `filter2D` uses a reflected border by default (`BORDER_REFLECT_101`).

### Gaussian blur and the separability trick

A box gives every neighbour the same vote. A **Gaussian** gives close neighbours more say:

$$G(x,y) = \frac{1}{2\pi\sigma^2}\, e^{-\frac{x^2+y^2}{2\sigma^2}}$$

The parameter σ sets how far the influence reaches. A bigger σ means a bigger, softer blur.

The cheap trick: the 2-D Gaussian is the **product of two 1-D Gaussians**, one in x and one in y. Any kernel that factors this way is **separable**: instead of one k × k pass you do a row pass then a column pass.

A small example is the binomial kernel, which approximates a Gaussian:

$$\frac{1}{4}\begin{bmatrix}1\\2\\1\end{bmatrix}\cdot\frac{1}{4}\begin{bmatrix}1&2&1\end{bmatrix}=\frac{1}{16}\begin{bmatrix}1&2&1\\2&4&2\\1&2&1\end{bmatrix}$$

The saving per output pixel:

| Kernel size k | 2-D multiplies (k²) | Separable (2k) |
|---|---|---|
| 3 | 9 | 6 |
| 5 | 25 | 10 |
| 11 | 121 | 22 |

The bigger the kernel, the bigger the win. That's why libraries blur with two 1-D passes.

### The CNN connection

A convolutional layer in a neural network is this exact loop with one change of attitude: **the kernel values are learned instead of designed**. Box, Gaussian and Sobel are hand-picked weights; a CNN lets training find its own.

One naming quirk: deep learning frameworks such as PyTorch compute **cross-correlation** (no flip) and call it convolution. PyTorch's `Conv2d` documentation says so. Since the weights are learned anyway, flipping them would change nothing, so nobody bothers. See [Deep Learning - Concepts - Convolution](/fields/deep-learning/concepts/convolution.md) for the network side of the story.

---

## Back to the bad pixel

Mira lays the nine numbers side by side. The box filter's answer for the middle is 18.9; the median's is 10. They are different questions: a vote lets the loud citizen speak a little, a sort lets the crowd outvote it.

The mean turned a loud speck into a quiet smudge. The median erased it. Neither knew what the speck *was*; each just applied a rule to nine numbers.

Notice also what both did to a real edge between a dark wall and a bright door: the mean blurred it, the median mostly kept it. A kernel that **averages** removes differences. What if we built a kernel that does the opposite and **celebrates** differences?

For the wall photo she uses the median. For the floor plans she leaves the pixels alone, because a thin line can look to a median like a pixel that disagrees with its neighbours. The manager and Ravi were both right: they were just treating different noise.

---

## Never again: which filter, which border

| Situation | Reach for |
|---|---|
| Gaussian-like noise on every pixel | A mean, or a Gaussian blur (it blurs edges) |
| Isolated extreme pixels (salt-and-pepper) | The median, which is nonlinear and keeps edges better |
| Thin lines you must keep | Not the median: it can erase them |
| A blur that must not change brightness | Weights that sum to 1 (a box is all `1/9` in 3 × 3) |
| Responding only where things change | Weights that sum to 0 (edge detectors, next page) |
| The border | Zero (dark halo), replicate (smeary), reflect (the usual default; OpenCV `filter2D` uses `BORDER_REFLECT_101`) |
| A big blur | A separable kernel: two 1-D passes (9, 25, 121 multiplies become 6, 10, 22) |

**Takeaway:** a filter is a sliding weighted vote; linear ones are kernels, the median is the nonlinear exception, and separable kernels make big blurs cheap.

**Next:** how do you find an edge by asking neighbours to disagree? [Part 5: Edges and sharpening](/fields/digital-image-processing/edges-and-sharpening.md).

---

## 📜 The Scroll (keep this)

```text
Symptom:  One loud pixel (90 among 10s)
Mean:     (8 x 10 + 90) / 9 = 18.9: smudge, and it bleeds into neighbours
Median:   sorted 10 10 10 10 10 10 10 10 90 -> 10: gone, nothing bleeds
Pick:     mean/Gaussian for Gaussian-like noise; median for salt-and-pepper
Do not:   median thin lines; forget the border rule
Cost:     separable kernels: k = 3, 5, 11 -> 6, 10, 22 multiplies
```


### References

- R. C. Gonzalez and R. E. Woods, *Digital Image Processing*, 4th ed., Pearson, 2018: chapter 3 (spatial filtering, correlation and convolution, smoothing, order-statistic filters).
- OpenCV documentation, [Image Filtering](https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html): `filter2D`, `GaussianBlur`, `medianBlur` and border types.
- PyTorch documentation, [torch.nn.Conv2d](https://pytorch.org/docs/stable/generated/torch.nn.Conv2d.html): the operation is cross-correlation.
