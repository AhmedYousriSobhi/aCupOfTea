
# Images Are Just Matrices

<!-- related-block -->
<div class="reading-time">7 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read next:** [Geometric Transforms and Interpolation](/fields/digital-image-processing/geometric-transforms-and-interpolation.md), [Intensity Transforms and Histograms](/fields/digital-image-processing/intensity-transforms-and-histograms.md)

</div>


> **Part 1 of the [Digital Image Processing series](/fields/digital-image-processing/README.md).** An image is a grid of numbers and nothing more mysterious. By the end you'll know what sampling and quantization do to a scene, how to count the bytes in an image, and why adding two pixels can make them darker.

## Table of Contents
- [Images Are Just Matrices](#images-are-just-matrices)
  - [Table of Contents](#table-of-contents)
  - [The black rectangle](#the-black-rectangle)
  - [From a scene to a grid](#from-a-scene-to-a-grid)
  - [Sampling: how many citizens?](#sampling-how-many-citizens)
  - [Quantization: how many shades per card?](#quantization-how-many-shades-per-card)
  - [Counting bytes](#counting-bytes)
  - [Rows, columns and the upside-down y](#rows-columns-and-the-upside-down-y)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [Neighbours and distances](#neighbours-and-distances)
  - [Back to the black rectangle](#back-to-the-black-rectangle)
    - [References](#references)

---

## The black rectangle

A colleague sends you a medical scan. "It's a 16-bit PNG," they say. "Open it in anything."

You open it. A black rectangle. You check the file size: fine. You check the dimensions: fine. You squint at the screen: still black.

Nothing is broken. The file is correct, and so is your viewer. They just disagree about what the number **4095** means. Hold that thought; we'll solve it at the end of the page. First we need to know what a pixel is.

---

## From a scene to a grid

Welcome to **Pixel Town**: a town on a perfect grid, one citizen per square, each holding a card with one number for how bright they are.

The real world is continuous. Light varies smoothly across space and has infinitely many intensities. A camera turns that into a town in two steps, and each step throws something away on purpose:

```mermaid
flowchart LR
    A["Continuous scene"] --> B["Sampling<br/>choose the grid"]
    B --> C["Quantization<br/>round each value"]
    C --> D["Digital image<br/>matrix of integers"]
```

*Sampling decides where we look. Quantization decides how precisely we write down what we see.*

Mathematically, the result is a function f(x, y) that returns an integer for each grid position, which is the same thing as a matrix with M rows and N columns:

$$f = \begin{bmatrix} f(0,0) & f(0,1) & \cdots & f(0,N-1) \\ \vdots & & & \vdots \\ f(M-1,0) & f(M-1,1) & \cdots & f(M-1,N-1) \end{bmatrix}$$

That's the whole object. Every algorithm in this series is "do something to this matrix".

---

## Sampling: how many citizens?

**Sampling** picks the grid size. More squares means finer detail, up to the limit of the optics.

Too few squares and small things fall between citizens and vanish, or worse, turn into patterns that were never there. That second failure is called **aliasing**, and it deserves its own page ([page 7](/fields/digital-image-processing/frequency-filtering-and-aliasing.md)).

Spatial resolution is simply how many samples you take per unit of the scene. "12 megapixels" means roughly twelve million citizens. It says nothing about how good each card is, which brings us to the other half.

---

## Quantization: how many shades per card?

**Quantization** rounds each brightness into one of L allowed levels. With k bits per pixel:

$$L = 2^k$$

| Bits per pixel (k) | Levels (L) | Typical use |
|---|---|---|
| 1 | 2 | Scanned text, masks |
| 8 | 256 | Ordinary photos and screens, `uint8` |
| 12 | 4096 | Many medical and camera-raw sensors |
| 16 | 65,536 | Containers for deep sensors, `uint16` |

Use too few levels and smooth gradients break into visible steps called **false contouring**. Eight bits is enough for most screens; deeper data matters when you plan to stretch the contrast later.

---

## Counting bytes

Storage for an uncompressed grayscale image is just the number of squares times the bits on each card:

$$\text{bits} = M \times N \times k$$

A 1024 × 768 image at 8 bits: 1024 × 768 = 786,432 pixels, times 8 bits is 6,291,456 bits, which is **786,432 bytes** (768 KiB). A colour image with three channels (red, green, blue) triples that. Compression changes the file size, never the matrix once it is decoded.

---

## Rows, columns and the upside-down y

Two conventions trip up everyone at least once.

| | Math / textbook | Matrix / NumPy / OpenCV |
|---|---|---|
| First index | x (horizontal) | row (vertical) |
| Order | f(x, y) | `img[row, col]` = `img[y, x]` |
| Origin | Often top-left in DIP books | Top-left |
| y direction | Down the image | Down the image |

So `img[y, x]` is the pixel at column x, row y. If your result looks transposed, you swapped the two. And because y grows **downward**, a "counter-clockwise" rotation in the usual math formula looks clockwise on screen (we'll meet that again on [page 2](/fields/digital-image-processing/geometric-transforms-and-interpolation.md)).

> [!NOTE]
> OpenCV also stores colour channels in BGR order, not RGB. Show a BGR array with an RGB viewer and every face turns blue.

---

## Try it before you scroll

☕ In a `uint8` image, a pixel holds 250. Your code adds 10 to it. **What is the new value?**

*Hint: 8 bits can't hold 260.*

**Answer:** it depends on who does the adding, and that is the trap.

| Operation | 250 + 10 | 200 + 100 |
|---|---|---|
| NumPy `uint8` array addition | wraps modulo 256: **4** | wraps: **44** |
| OpenCV `cv2.add` | saturates at the ceiling: **255** | saturates: **255** |

A bright pixel becoming almost black is the classic "why is there a dark speckle where the sky was?" bug. NumPy wraps; OpenCV's `add` saturates (clips). Convert to a wider type first (`float32`) if you want arithmetic that behaves.

---

## Neighbours and distances

Almost every operation in later pages looks at a pixel **and the pixels around it**, so we need words for "around".

- **4-neighbours** of (x, y): the four squares that share an edge, up, down, left, right.
- **8-neighbours**: those four plus the four diagonals.

Distance between two pixels p = (x₁, y₁) and q = (x₂, y₂) depends on which moves you allow:

| Name | Formula | Moves allowed | Shape of "all points within r" |
|---|---|---|---|
| Euclidean | √((x₁−x₂)² + (y₁−y₂)²) | Straight line | Circle |
| City-block (D4) | \|x₁−x₂\| + \|y₁−y₂\| | 4-neighbour steps | Diamond |
| Chessboard (D8) | max(\|x₁−x₂\|, \|y₁−y₂\|) | 8-neighbour steps | Square |

The names come from taxis on a street grid versus a chess king. You'll meet D4 and D8 again whenever someone asks "which pixels are connected?".

---

## Back to the black rectangle

Your scan is stored in a 16-bit container (values 0 to 65,535), but the sensor only produces 12 bits (0 to 4095). The brightest possible pixel is 4095, and the viewer maps 65,535 to white:

$$\frac{4095}{65535} \approx 0.0625$$

The brightest pixel in the picture is shown at about **6%** of full brightness. To a human eye, that's a black rectangle with extra steps. The data is fine; it needs its contrast stretched, which is exactly what the next page does.

**Takeaway:** an image is a matrix of integers with a finite number of levels, and most "mystery" bugs are the wrong type, the wrong axis or the wrong range.

**Next:** every rotation, zoom and shift sends a citizen to a square that doesn't exist. What number do you write on the squares left behind? [Part 2: Geometric transforms and interpolation](/fields/digital-image-processing/geometric-transforms-and-interpolation.md).

### References

- R. C. Gonzalez and R. E. Woods, *Digital Image Processing*, 4th ed., Pearson, 2018: chapter 2, "Digital Image Fundamentals" (sampling, quantization, neighbours, distance measures).
- OpenCV documentation, [Arithmetic operations on images](https://docs.opencv.org/4.x/d0/d86/tutorial_py_image_arithmetics.html): `cv2.add` saturation versus NumPy modulo arithmetic.
- NumPy documentation, [Data types](https://numpy.org/doc/stable/user/basics.types.html): fixed-size integer overflow.
