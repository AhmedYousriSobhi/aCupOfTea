---
id: dip-edges-sharpening
title: Edges and Sharpening
sidebar_label: 5. Edges and sharpening
order: 5
summary: Derivatives as differences between neighbours - gradient, Sobel, Laplacian and unsharp masking, plus a one-line example that shows exactly where sharpening halos come from.
level: beginner
type: concept
domains: [image-processing]
tags: [filtering, noise]
relations:
  prerequisites: [dip-spatial-filtering]
---

# Edges and Sharpening

> **Part 5 of the [Digital Image Processing series](/fields/digital-image-processing/README.md).** An edge is where neighbours disagree, and calculus is the tool for measuring disagreement. By the end you'll build Sobel and Laplacian kernels from first principles and explain why sharpening draws halos and amplifies noise.

## Table of Contents
- [Edges and Sharpening](#edges-and-sharpening)
  - [Table of Contents](#table-of-contents)
  - [The sharpen button that made things worse](#the-sharpen-button-that-made-things-worse)
  - [A derivative is a difference](#a-derivative-is-a-difference)
  - [Seeing it on one row](#seeing-it-on-one-row)
  - [The gradient: how strong, which way](#the-gradient-how-strong-which-way)
  - [Sobel: differentiate and smooth in one kernel](#sobel-differentiate-and-smooth-in-one-kernel)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [The Laplacian and sharpening](#the-laplacian-and-sharpening)
  - [Unsharp masking: the sharpening everyone actually uses](#unsharp-masking-the-sharpening-everyone-actually-uses)
  - [Back to the sharpen button](#back-to-the-sharpen-button)
    - [References](#references)

---

## The sharpen button that made things worse

A photo of a brick wall looks soft. You click "sharpen". The bricks pop. But the clear blue sky now looks like it has sand in it, and every dark edge has a faint bright outline, like it was cut out with scissors.

The software did exactly what it was told. To see what that was, we need to look at how a computer measures "this changes here".

---

## A derivative is a difference

In calculus, a derivative measures how fast something changes. In Pixel Town, the smallest step between citizens is one pixel, so the derivative becomes a plain **difference between neighbours**.

For a row of pixels f(x):

| Quantity | Formula (discrete) | In words |
|---|---|---|
| First derivative (forward) | f(x+1) − f(x) | Next minus this |
| First derivative (central) | (f(x+1) − f(x−1)) / 2 | Right neighbour minus left, halved |
| Second derivative | f(x+1) + f(x−1) − 2f(x) | How much I differ from the average of my neighbours, times two |

Flat region: all three are 0. Slope: first derivative is nonzero. Corner of a slope: second derivative is nonzero. That gives us a detector for each kind of change.

---

## Seeing it on one row

Take a perfect step edge, dark to bright:

```text
x:        0   1   2   3   4   5
f(x):    10  10  10  50  50  50
```

Compute the interior values (the border needs padding, so we skip it):

| x | 1st (central) | 2nd |
|---|---|---|
| 1 | 0 | 0 |
| 2 | (50 − 10)/2 = **20** | 50 + 10 − 20 = **+40** |
| 3 | (50 − 10)/2 = **20** | 50 + 10 − 100 = **−40** |
| 4 | 0 | 0 |

Two things to notice:

1. The **first derivative** is a plateau across the edge: its size says "strong edge here".
2. The **second derivative** goes positive then negative. The edge sits at the **zero crossing** between them. It also gives a double response, which is the root of the halos we'll meet later.

---

## The gradient: how strong, which way

In two dimensions there's an x-direction change and a y-direction change. Together they form the **gradient**:

$$\nabla f = \begin{bmatrix} G_x \\ G_y \end{bmatrix}$$

$$\|\nabla f\| = \sqrt{G_x^2 + G_y^2} \qquad \theta = \operatorname{atan2}(G_y,\, G_x)$$

The magnitude says how strong the edge is. The angle θ says which way the brightness climbs the fastest, which is **perpendicular to the edge line**.

A common cheaper approximation is |G_x| + |G_y|, which avoids the square root.

---

## Sobel: differentiate and smooth in one kernel

Differences are twitchy: one noisy pixel gives a huge difference. The **Sobel** kernel fixes this by averaging across the perpendicular direction while it differences:

$$G_x = \begin{bmatrix}-1&0&1\\-2&0&2\\-1&0&1\end{bmatrix} \qquad G_y = \begin{bmatrix}-1&-2&-1\\0&0&0\\1&2&1\end{bmatrix}$$

Look at G_x: the columns are [−1, 0, 1], which is a central difference, and the rows are weighted [1, 2, 1], which is a mild smoothing. It's a separable product:

$$\begin{bmatrix}1\\2\\1\end{bmatrix}\begin{bmatrix}-1&0&1\end{bmatrix}=\begin{bmatrix}-1&0&1\\-2&0&2\\-1&0&1\end{bmatrix}$$

Each Sobel kernel sums to **0** (the tip from [page 4](/fields/digital-image-processing/spatial-filtering.md)): flat regions give zero, edges give a response. Apply G_x and G_y as two filters, then combine with the magnitude formula to get an edge map. Full edge detectors such as Canny (1986) add thinning and thresholds on top of the same gradient.

---

## Try it before you scroll

☕ You slide the Sobel G_x kernel over a perfectly **flat** patch where every pixel is 100. **What is the output?** And what if the patch is all 200?

*Hint: add the kernel weights.*

**Answer:** **0** in both cases. The weights sum to 0, so any constant multiplied by the same total is 0. That's the point: a detector that stays silent when nothing changes. Replace the kernel with a box and the answer would be 100 and 200.

---

## The Laplacian and sharpening

The **Laplacian** adds the second derivatives in both directions into one isotropic (direction-independent) operator:

$$\nabla^2 f = f(x+1,y)+f(x-1,y)+f(x,y+1)+f(x,y-1)-4f(x,y)$$

As a kernel:

$$\begin{bmatrix}0&1&0\\1&-4&1\\0&1&0\end{bmatrix}$$

It responds to **neighbours disagreeing with me**: zero in flat regions, big at points and line ends, and positive-then-negative across edges, just like the 1-D example.

To sharpen with it, subtract the Laplacian from the image (we subtract because the centre weight is negative):

$$g = f - \nabla^2 f$$

Apply that to our step row. Using the second-derivative values from the table:

| x | f(x) | 2nd | g = f − 2nd |
|---|---|---|---|
| 1 | 10 | 0 | 10 |
| 2 | 10 | +40 | **−30** |
| 3 | 50 | −40 | **90** |
| 4 | 50 | 0 | 50 |

The dark side is pushed **even darker** (−30, below the original 10) and the bright side **even brighter** (90, above the original 50). The edge now looks steeper. That undershoot and overshoot is the halo you saw on the brick wall.

---

## Unsharp masking: the sharpening everyone actually uses

The name sounds like the opposite of what it does. The trick: take a blurred copy, subtract it from the original to isolate the **detail**, and add some of that detail back:

$$g = f + k\,\big(f - \text{blur}(f)\big)$$

| k | Name | Effect |
|---|---|---|
| 0 | none | Original image |
| 1 | Unsharp masking | Adds the detail once |
| greater than 1 | High-boost | Exaggerates the detail |

The difference f − blur(f) keeps only what the blur removed, which is the fine detail and edges. In the frequency picture of [page 6](/fields/digital-image-processing/fourier-transform-for-images.md) you've just **boosted the high frequencies**. Everything that sharpens an image, Laplacian or unsharp, boosts the same thing, and noise lives in the same place.

---

## Back to the sharpen button

Now the sand in the sky makes sense. A difference between neighbours **doesn't know** whether the difference is a brick edge or a speck of noise. Sharpening magnifies both. Flat sky had only a tiny random wobble, and the filter multiplied it until your eye noticed.

And the scissors halo is the overshoot from the table above: the filter makes dark sides darker and bright sides brighter so the edge looks steeper, and that outline is real data, drawn by the algorithm.

| Symptom | Cause | Fix |
|---|---|---|
| Grainy sky after sharpening | Noise lives in the high frequencies being boosted | Denoise or smooth first, lower k, mask flat regions |
| Bright/dark outlines at edges | Overshoot and undershoot of the second derivative | Reduce k, use a larger blur radius |
| Edge map full of tiny speckles | Raw differences amplify noise | Use Sobel (built-in smoothing) or blur first |

**Takeaway:** derivatives are neighbour differences; they find edges, and the same operation that sharpens also amplifies noise and draws halos.

**Next:** we keep saying "high frequencies". What are they, and can we filter them directly? [Part 6: The Fourier transform for images](/fields/digital-image-processing/fourier-transform-for-images.md), after an optional [interlude on the man behind it](/fields/digital-image-processing/meet-fourier.md).

### References

- R. C. Gonzalez and R. E. Woods, *Digital Image Processing*, 4th ed., Pearson, 2018: chapter 3 (sharpening spatial filters, Laplacian, unsharp masking, high-boost) and chapter 10 (edge detection).
- OpenCV documentation, [Image Gradients](https://docs.opencv.org/4.x/d5/d0f/tutorial_py_gradients.html): `Sobel`, `Laplacian`.
- J. Canny, "A Computational Approach to Edge Detection", *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 8(6), 679-698, 1986.
