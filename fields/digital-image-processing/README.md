---
id: digital-image-processing-overview
title: Digital Image Processing - Overview
sidebar_label: Overview
sidebar_group: Digital Image Processing
summary: The math of digital image processing, made friendly - a nine-part series from pixels as matrices to filters, Fourier, restoration, geometry and wavelets, for anyone coming back to the subject.
level: beginner
type: concept
domains: [image-processing]
tags: [convolution, fourier-transform]
---

# Digital Image Processing - Overview

> A nine-part series for people returning to digital image processing (DIP) who want the **why** behind the formulas before going back to the textbook. By the end you'll read `s = c·r^γ`, `F(u,v)` and `H(u,v)G(u,v)` without flinching, and know which one to reach for when a real image misbehaves.

## Table of Contents
- [Digital Image Processing - Overview](#digital-image-processing---overview)
  - [Table of Contents](#table-of-contents)
  - [Welcome to Pixel Town](#welcome-to-pixel-town)
  - [The route](#the-route)
  - [Who this is for](#who-this-is-for)
  - [Conventions used in the series](#conventions-used-in-the-series)
  - [Contents](#contents)
  - [Related reading in this repo](#related-reading-in-this-repo)

---

## Welcome to Pixel Town

Picture a town laid out as a perfect grid. Every citizen stands on one square and holds up a card with a single number: how bright they are. That's an image.

Everything in this series is about what you can do to that town. Change what the cards say (**page 2**). Let neighbours vote on each other's numbers (**page 3, 4**). Stop looking at who stands where and listen to the town as a choir instead (**page 5, 6**). Work out what the town looked like before someone sneezed on the camera (**page 7**). Move the whole town to a new map without losing a citizen (**page 8**).

Look at the town at several zoom levels at once (**page 9**).

Same town, nine points of view. The math is only the language we use to describe them.

---

## The route

| # | Page | The question it answers |
|---|------|-------------------------|
| 1 | [Images are just matrices](/fields/digital-image-processing/images-are-just-matrices.md) | Why does my 16-bit image look black, and what is a pixel anyway? |
| 2 | [Intensity transforms and histograms](/fields/digital-image-processing/intensity-transforms-and-histograms.md) | How do you rescue an image that's too dark, with one formula? |
| 3 | [Spatial filtering](/fields/digital-image-processing/spatial-filtering.md) | What is a kernel, and why is blurring "a vote"? |
| 4 | [Edges and sharpening](/fields/digital-image-processing/edges-and-sharpening.md) | Why does sharpening make noise louder? |
| 5 | [The Fourier transform for images](/fields/digital-image-processing/fourier-transform-for-images.md) | What does an image sound like? |
| 6 | [Frequency filtering and aliasing](/fields/digital-image-processing/frequency-filtering-and-aliasing.md) | Why do striped shirts shimmer on video? |
| 7 | [Noise and restoration](/fields/digital-image-processing/noise-and-restoration.md) | Why does "un-blurring" a photo explode into static? |
| 8 | [Geometric transforms and interpolation](/fields/digital-image-processing/geometric-transforms-and-interpolation.md) | Why does a rotated scan come out jagged? |
| 9 | [Wavelets and multiresolution processing](/fields/digital-image-processing/wavelets-and-multiresolution-processing.md) | Where in the picture is the scratch, and at what scale? |

Each page ends with the question the next one answers. Read them in order the first time; later, jump straight to the formula you need.

---

## Who this is for

You took a DIP course (or half of one), the formulas are fuzzy, and the textbook looks heavier than you remember. You don't need a signal-processing background. You do need to be comfortable with sums, a little matrix notation, and the idea of a function.

The pages follow the order of the course's main reference, R. C. Gonzalez and R. E. Woods, *Digital Image Processing*, 4th ed. (Pearson, 2018), and each one cites the chapter to open next. This is a **starter**, not a replacement. It trades completeness for intuition so that the reference book becomes readable again.

---

## Conventions used in the series

| Item | Convention |
|------|------------|
| Image | f(x, y) is the input, g(x, y) the output |
| Origin | Top-left corner; x runs along the column, y runs down the row |
| Gray levels | L = 2^k levels, from 0 (black) to L−1 (white), unless a page says normalized [0, 1] |
| Sources | Gonzalez and Woods, *Digital Image Processing*, 4th ed.; library behaviour from the OpenCV and NumPy docs |
| Code | Short snippets are **not executed** by the author; worked numbers are computed by hand and checkable with a calculator |

> [!NOTE]
> Textbooks and libraries disagree on small conventions (which axis is first, where a 1/N factor goes). Each page names the convention it uses and where libraries differ.

## Contents

| File | Description |
|------|-------------|
| [images-are-just-matrices](/fields/digital-image-processing/images-are-just-matrices.md) | Sampling, quantization, bit depth, coordinates and neighbours |
| [intensity-transforms-and-histograms](/fields/digital-image-processing/intensity-transforms-and-histograms.md) | Negative, log, gamma and histogram equalization |
| [spatial-filtering](/fields/digital-image-processing/spatial-filtering.md) | Kernels, correlation vs convolution, padding, separability |
| [edges-and-sharpening](/fields/digital-image-processing/edges-and-sharpening.md) | Gradient, Sobel, Laplacian and unsharp masking |
| [fourier-transform-for-images](/fields/digital-image-processing/fourier-transform-for-images.md) | The 2D DFT, magnitude vs phase, the convolution theorem |
| [frequency-filtering-and-aliasing](/fields/digital-image-processing/frequency-filtering-and-aliasing.md) | Low-pass, high-pass and notch filters; sampling and aliasing |
| [noise-and-restoration](/fields/digital-image-processing/noise-and-restoration.md) | Noise models, inverse and Wiener filtering, PSNR |
| [geometric-transforms-and-interpolation](/fields/digital-image-processing/geometric-transforms-and-interpolation.md) | Affine transforms, inverse mapping, bilinear and bicubic interpolation |
| [wavelets-and-multiresolution-processing](/fields/digital-image-processing/wavelets-and-multiresolution-processing.md) | Pyramids, the Haar transform, subbands, wavelet denoising |

## Related reading in this repo

- [Deep Learning - Concepts - Convolution](/fields/deep-learning/concepts/convolution.md): the same sliding-window idea, as used in CNNs.
