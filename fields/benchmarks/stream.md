# STREAM & BabelStream: Measuring the Thing Everyone Forgets to Measure

> **TL;DR** — Compute (HPL) gets all the glory. Communication (OSU/NCCL) gets all the debugging attention. Memory bandwidth quietly decides how fast *everything else* actually runs, and almost nobody benchmarks it first.

## Table of Contents
- [STREAM \& BabelStream: Measuring the Thing Everyone Forgets to Measure](#stream--babelstream-measuring-the-thing-everyone-forgets-to-measure)
  - [Table of Contents](#table-of-contents)
  - [Why this benchmark exists](#why-this-benchmark-exists)
  - [Picking your flavor of STREAM](#picking-your-flavor-of-stream)
  - [1. Classic STREAM (CPU)](#1-classic-stream-cpu)
  - [2. BabelStream (the GPU workhorse)](#2-babelstream-the-gpu-workhorse)
    - [Walking through the math](#walking-through-the-math)
    - [Choosing arraysize on an H200](#choosing-arraysize-on-an-h200)
  - [3. STREAM-GPU (the vendor-strict version)](#3-stream-gpu-the-vendor-strict-version)
  - [Quick-reference cheat sheet](#quick-reference-cheat-sheet)

---

## Why this benchmark exists

Every compute unit — CPU core or GPU SM — is only as fast as the data it can pull out of memory. A GPU with monster TFLOPS but a starved memory pipe will sit idle waiting for bytes. STREAM-family benchmarks exist to answer one unglamorous but critical question:

> **"How many bytes per second can I actually move between memory and compute — before I even start doing math on them?"**

Think of it as measuring the width of the pipe *before* you turn on the faucet (HPL) or open both ends at once (OSU/NCCL).

---

## Picking your flavor of STREAM

There isn't just one STREAM anymore — there are three, and picking the wrong one for your hardware wastes a benchmarking cycle. Here's the decision table:

| | [jeffhammond/STREAM](https://github.com/jeffhammond/STREAM) | `stream-gpu-test` | [BabelStream](https://github.com/UoB-HPC/BabelStream) |
|---|---|---|---|
| 🎯 **Target** | CPUs (multi-core) | NVIDIA GPUs (+ Grace CPU) | Cross-platform GPUs & CPUs |
| 📦 **Source** | Open (C / Fortran) | Closed — precompiled vendor binary | Open (C++, multi-backend) |
| 🧠 **Memory model** | Static/global, compile-time sized | Native CUDA device memory | Dynamic heap, runtime sized |
| ✅ **Best for** | Baseline x86/ARM CPU validation | Strict vendor-grade NVIDIA node validation (H100/H200) | Cross-vendor comparisons — NVIDIA vs AMD MI300X, CUDA vs SYCL |

**Rule of thumb:** if you're validating a shiny new H200 node against NVIDIA's own numbers, use `stream-gpu-test`. If you're comparing your GPU choice across vendors or backends, use BabelStream. If you just want a CPU sanity check, grab the original STREAM.

---

## 1. Classic STREAM (CPU)

This is the original — four dead-simple kernels (`Copy`, `Scale`, `Add`, `Triad`) running over large statically-sized arrays, timed and converted into GB/s. No GPUs, no fancy memory allocators — just raw "how fast can this CPU socket move data" numbers. It's the benchmark every other memory-bandwidth tool is compared against, and it's the right first move before you ever touch HPL numbers on a new CPU node — a memory-starved node will cap your HPL efficiency no matter how good your BLAS library is.

---

## 2. BabelStream (the GPU workhorse)

BabelStream's whole personality hinges on one setting: **`arraysize`**. Get this wrong and your "benchmark" is secretly measuring your cache instead of your HBM.

> [!IMPORTANT]
> `arraysize` does **not** feed into the theoretical bandwidth formula. It exists purely to make sure:
> 1. The arrays actually fit in GPU memory.
> 2. The dataset is big enough to blow past cache effects and timing noise.
> 3. The kernel runs *long enough* to get a clean, stable measurement.

### Walking through the math

Say you set:

```
arraysize = 2048 * 1024 * 1024   → N = 2,147,483,648 elements
```

For double precision (`sizeof(double) = 8 bytes`):

$$\text{Each array} = N \times 8 = 17{,}179{,}869{,}184 \text{ bytes} \approx 16\ \text{GB}$$

BabelStream allocates **three** vectors — `a[N]`, `b[N]`, `c[N]` — so:

$$\text{Total memory} = 3 \times N \times 8 = 3 \times 16 = 48\ \text{GB per GPU}$$

### Choosing arraysize on an H200

Common wisdom: target **50–80% of usable GPU memory**, no more (you need headroom for the runtime, CUDA context, and driver overhead).

For an H200 with 140.4 GB usable, aiming at 80%:

$$140.4 \times 0.80 = 112.32\ \text{GB available for the three arrays}$$

$$N = \frac{112.32 \times 2^{30}}{3 \times 8} \approx 5.025 \times 10^9 \text{ elements}$$

So a reasonable H200-sized test lands around:

```
arraysize ≈ 5,000,000,000
```

**Power-of-two cleanup:** since 5,000,000,000 ≈ 4792.32 × 1024², round to a clean multiple of 1024:

```
4098 × 1024 × 1024 = 4,294,967,296 elements  →  ~96 GB total array storage per GPU
```

> [!TIP]
> Pushing toward the full 5×10⁹ elements is fine if you want maximum memory occupancy, but once you're comfortably past the cache hierarchy, extra size mostly just burns runtime without moving the measured bandwidth needle.

---

## 3. STREAM-GPU (the vendor-strict version)

This one's based on NVIDIA's own `stream-gpu-test` script, shipped inside `nvcr.io/nvidia/hpc-benchmarks_26.02.sif`. Unlike BabelStream (which you tune yourself), this is the closed, pre-tuned binary NVIDIA uses for their own acceptance testing — use it when you specifically need numbers comparable to vendor-published specs, not when you want flexibility.

---

## Quick-reference cheat sheet

```text
Need a CPU baseline?             → jeffhammond/STREAM
Need cross-vendor GPU numbers?   → BabelStream (tune arraysize to ~80% mem)
Need NVIDIA-official H100/H200
numbers to match a spec sheet?   → stream-gpu-test (vendor binary)
```

**One-line memory-bandwidth formula for BabelStream:**

$$N = \frac{(\text{usable GPU memory}) \times \text{target\%} \times 2^{30}}{3 \times \text{bytes per element}}$$

Run this before your compute-bound benchmarks (HPL) so you know, going in, whether a low GFLOPS number is a compute problem or a memory-starved GPU problem.