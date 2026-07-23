# Benchmarks - STREAM

## Table of Contents
- [Benchmarks - STREAM](#benchmarks---stream)
  - [Table of Contents](#table-of-contents)
  - [Motivation](#motivation)
  - [1. STREAM CPU](#1-stream-cpu)
  - [2. BABEL STREAM](#2-babel-stream)
  - [3. STREAM GPU](#3-stream-gpu)

## Motivation
Feature|jeffhammond/STREAM|stream-gpu-test|BabelStream
|-|-|-|-|
Main Target|CPUs (Multi-core)|NVIDIA GPUs (and Grace CPU)|Cross-platform GPUs & CPUs
Code Availability|Open Source (C / Fortran)|Closed Source (Pre-compiled Binary)|Open Source (C++ Multi-backend)
Memory Allocation|Static/Global (Compile-time)|Native CUDA Device Memory|Dynamic Heap (Runtime)
Main Use Case|Baseline x86/ARM CPU architecture validation.|"Strict vendor-provided validation testing for high-end NVIDIA GPU nodes (e.g. H100/H200)."|"Evaluating performance portability across vendors (e.g., NVIDIA vs. AMD MI300X) or models (e.g., CUDA vs. SYCL)."

## 1. STREAM CPU
## 2. BABEL STREAM
Defining the correct `arraysize` used in the code. This variable is not used to calculate the theoretical bandwidth. Instead, it determines how much data is processed so that:
1. The arrays fit in GPU memory.
2. The benchmark is large enough to avoid cache effects and timing noise.
3. The kernel runs long enough to measure bandwidth accurately.

**What does arraysize mean?**</br>
An example: arraysize = 2048*1024*1024</br>
means: N = 2,147,483,648 elements.</br>
For double precision: sizeof(double) = 8 bytes.</br>
Each array consumes: N×8=17,179,869,184 bytes = 16 GB.</br>

**How many arrays does BabelStream allocate?**</br>
Most implementation allocates three vectors: {a[N], b[N], c[N]}</br>
Total Memory:</br> 3 x N x 8 per GPU.</br>
From previous example: then total memory= 3x16=48 GB per GPU.

**How to choose the arraysize?**</br>
A common rule is to use around 50%-80% of GPU memory.</br>
In H200 Node, it has 140.4 GB usable.</br>
Setting target to 80%: 140.4 x 80% = 112.32 GB</br>
Available for the three arrays: N=(112.32 x 2^30)/(3 x 8) = 5.025 x 10^9</br>
So the reasonable H200-size test would be: 5000000000</br>

**Power-of-two example:**</br>
5000000000 = (4792.32 x 1024 x 1024)</br>
As it should be multiple of 1024, then we could use: (4098 x 1024 x 1024) = 4,294,967,296</br>
This gives around ~96 GB total array storage per GPU.</br>
If you want to maximize memory occupancy, you could increase toward roughly 5×10^9 elements, but the extra size usually doesn't improve the measured bandwidth once you've exceeded the cache hierarchy by a large margin.

## 3. STREAM GPU
Based on `stream-gpu-test` script from `nvcr.io/nvidia/hpc-benchmarks_26.02.sif`
