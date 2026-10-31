---
id: llm-perf-structured-sparsity
title: "2:4 Sparsity: Half the Weights, Not Half the Time"
sidebar_label: "5. 2:4 structured sparsity"
order: 5
summary: How NVIDIA's 2:4 structured sparsity works, what it really saves (44% of weight bytes, not 50%), and why its doubled TFLOPS help prefill while decode only feels the byte savings.
level: intermediate
type: concept
domains: [generative-ai, systems-and-hpc]
tags: [gpu, llm, nvidia, transformers]
relations:
  prerequisites: [llm-perf-optimizations]
---

# 2:4 Sparsity: Half the Weights, Not Half the Time

> **Part 5 of the [LLM Inference Performance series](/fields/generative-ai/llm-inference-performance/README.md).** Remember the asterisk from [part 1](/fields/generative-ai/llm-inference-performance/compute-bound-vs-memory-bound.md#the-asterisk-that-doubles-your-mistake)? The H100's headline 1,979 TFLOPS is "with sparsity." This page is about that asterisk: what 2:4 structured sparsity is, what the hardware actually does with it, and what it buys you on the roofline. By the end you'll be able to fact-check every common claim about it, including a few that sound right and aren't.

## Table of Contents
- [2:4 Sparsity: Half the Weights, Not Half the Time](#24-sparsity-half-the-weights-not-half-the-time)
  - [Table of Contents](#table-of-contents)
  - [The slide with the big number](#the-slide-with-the-big-number)
  - [The pattern: two of every four](#the-pattern-two-of-every-four)
  - [What the hardware actually does](#what-the-hardware-actually-does)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [The metadata tax: 44%, not 50%](#the-metadata-tax-44-not-50)
  - [Sparsity on the roofline: two different gifts](#sparsity-on-the-roofline-two-different-gifts)
  - [The 70B model, pruned](#the-70b-model-pruned)
  - [Fact-checking the usual pitch](#fact-checking-the-usual-pitch)
    - [References](#references)

---

## The slide with the big number

A procurement meeting. The vendor's slide shows the H100 at **3,958 TFLOPS** of FP8. Someone does quick math: "Our current model runs at 989-ish BF16. So this is four times faster?"

The room nods. Nobody reads the footnote. The footnote says *with sparsity*.

Six weeks later, the deployed model, dense as the day it was trained, runs at the speed the dense numbers predict. Not one TFLOP of the "sparsity" half ever showed up. It couldn't. The model had no sparsity to use.

That's not a scam. It's a real hardware feature with a real price tag, paid by the research team, not the infrastructure team. Let's see what it is.

---

## The pattern: two of every four

Take any weight matrix. Walk along each row in groups of four neighboring values. **2:4 structured sparsity** requires that in every group, **at least two values are zero**.

```text
dense row:     0.8  -0.1   0.3   0.05 |  -0.6   0.2   0.01  0.9
2:4 pruned:    0.8   0     0.3   0    |  -0.6   0     0     0.9
               └── keep 2 of 4 ──┘       └── keep 2 of 4 ──┘
```

Exactly half the weights are gone. But *which* half is constrained: you can't zero out a whole row and keep another row dense. Every group of four keeps two.

Why such a fussy rule? Because it's a compromise between two extremes:

| Kind of sparsity | Accuracy after pruning | Hardware speedup |
|------------------|----------------------|------------------|
| **Unstructured** (zero any weights you like) | Best: the pruner has full freedom | Hard: irregular zeros are difficult for hardware to skip efficiently |
| **Coarse structured** (remove whole rows, channels, heads) | Worst: big chunks vanish | Easy: the matrix just gets smaller |
| **2:4 fine-grained structured** | In between | Built into the Tensor Cores |

NVIDIA's paper introducing it (Mishra et al., 2021) makes the same trade explicit: networks pruned with unstructured sparsity tend to keep more accuracy, but rarely use the hardware well. 2:4 is regular enough for silicon and fine-grained enough that accuracy can usually be recovered.

---

## What the hardware actually does

Three steps, and it's worth knowing which ones happen where.

**1. Prune (research side, before deployment).** Someone zeroes two of every four weights and, usually, fine-tunes the model to win back accuracy. Part 6 covers this.

**2. Compress (software, ahead of time).** The pruned matrix is packed into a compressed format: only the non-zero values, plus a small **metadata** index per value saying which of the four slots it came from. With four possible positions, each index needs 2 bits. Libraries do this before inference: NVIDIA's cuSPARSELt library exposes pruning and compression functions, and inference stacks like TensorRT do it when building the engine. The Tensor Cores don't compress anything on the fly; they consume the already-compressed format.

**3. Multiply (Sparse Tensor Cores).** Introduced with the Ampere architecture (A100), **Sparse Tensor Cores** use the metadata to pick out only the matching values from the other matrix and skip the zeros entirely. The paper's wording: they double math throughput for matrix multiplies **when the first argument is a compressed 2:4 sparse matrix**.

Note that last condition. One operand is sparse: the **weights**. The activations flowing through the model, and the KV cache, stay dense.

---

## Try it before you scroll

☕ A 2:4-compressed matrix stores half the values. Does it take half the memory?

Think about what else has to be stored. Then scroll.

---

## The metadata tax: 44%, not 50%

Half the values are gone, but every surviving value carries a 2-bit position tag. Count the bits for one group of four weights:

| Format | Dense group of 4 | 2:4 compressed group | Compressed size | Saving |
|--------|------------------|---------------------|-----------------|--------|
| 16-bit (FP16/BF16) | 4 × 16 = 64 bits | 2 × 16 + 2 × 2 = 36 bits | 56% | **~44%** |
| 8-bit (FP8/INT8) | 4 × 8 = 32 bits | 2 × 8 + 2 × 2 = 20 bits | 62.5% | **~38%** |

These match the storage savings NVIDIA's paper reports: about 44% for 16-bit and 38% for 8-bit operands.

Notice the trend: the smaller each value, the bigger the metadata's share. At 8 bits, the tags are a fifth of the compressed storage. That matters when you combine sparsity with quantization in part 6.

So "2:4 halves memory and bandwidth" is close but wrong. It cuts weight bytes by a bit less than half, and only for the weight matrices that were actually pruned.

---

## Sparsity on the roofline: two different gifts

Here's where the [roofline](/fields/generative-ai/llm-inference-performance/compute-bound-vs-memory-bound.md) earns its keep. 2:4 sparsity gives you **two separate things**, and each one helps a different phase:

| Gift | Size | Helps | Because |
|------|------|-------|---------|
| **Double peak math** for sparse matrix multiplies | Up to 2× | **Prefill** | Prefill is compute-bound ([part 2](/fields/generative-ai/llm-inference-performance/llm-inference-on-the-roofline.md#reading-the-prompt-the-dumpling-phase)): the flat roof matters |
| **Fewer weight bytes** to fetch | ~44% less at 16-bit | **Decode** | Decode is bandwidth-bound: the slanted roof matters |

This is the single most important point on the page. **The headline feature, doubled TFLOPS, does almost nothing for decode.** Generating tokens was already leaving the tensor cores ~99% idle in [part 3](/fields/generative-ai/llm-inference-performance/sizing-a-70b-model.md#question-4-how-fast-for-one-user). Doubling the speed of idle hardware changes nothing. What decode feels is the smaller weights: fewer bytes per token, the same lever as quantization.

So when someone says "sparsity lets us finally reach peak TFLOPS," ask: *for which phase?* For prefill, maybe. For streaming tokens, the TFLOPS were never the bottleneck.

And even for prefill, 2× only applies to the matrix multiplies. Attention over the KV cache, normalization, activations and communication don't get faster. The PyTorch tutorial that prunes BERT to 2:4 reports an end-to-end inference speedup of **1.3×**, not 2×. That's Amdahl's law in action: speed up part of the work, and the rest sets the ceiling.

---

## The 70B model, pruned

Back to Llama 2 70B on 8×H100 from [part 3](/fields/generative-ai/llm-inference-performance/sizing-a-70b-model.md). Suppose every weight matrix were pruned to 2:4 (in practice some layers are often left dense, so treat these as best cases). Same method: weight bytes ÷ 26.8 TB/s.

| Format | Weight memory | One-user decode ceiling | Room for KV cache (of 576 GB usable) |
|--------|---------------|------------------------|--------------------------------------|
| BF16 dense | 140 GB | ~190 tokens/s | ~436 GB |
| **BF16, 2:4 sparse** | ~79 GB | **~340 tokens/s** | ~497 GB |
| FP8 dense | 70 GB | ~380 tokens/s | ~506 GB |
| **FP8, 2:4 sparse** | ~44 GB | **~610 tokens/s** | ~532 GB |

Two surprises in that table:

- **FP8 dense beats BF16 sparse** for decode. Halving every value's width saves more bytes than deleting half the values and tagging the rest. And FP8 doesn't require changing the model's structure.
- **They stack.** FP8 plus 2:4 gets weights down to under a third of BF16 dense. On the datasheet, that's also where the 3,958 TFLOPS lives: FP8 *and* sparse.

For prefill, sparse matrix multiplies at up to double speed would bring the 2,000-token prompt's matmul time from about 35 ms toward about 18 ms, as a ceiling, with the non-matmul work unchanged.

> [!NOTE]
> These are ceilings from datasheet bandwidth, as everywhere in this series. Whether a serving engine has fast 2:4 kernels for your precision and batch sizes, especially the small batches of decode, is something to benchmark, not assume.

---

## Fact-checking the usual pitch

Here's a typical summary of 2:4 sparsity, checked line by line:

| Claim | Verdict |
|-------|---------|
| "Two out of every four adjacent weights must be zero." | **Correct.** At least two of every group of four. |
| "The Tensor Cores compress the matrix." | **Not quite.** Compression is a software step done ahead of time (cuSPARSELt, TensorRT). Tensor Cores consume the compressed format. |
| "Stores non-zeros plus a 2-bit index for each." | **Correct.** |
| "The silicon skips the math for the zeros, doubling TFLOPS." | **Correct for the matmul itself** (sparse first operand). End-to-end speedups are smaller: 1.3× in PyTorch's BERT example. |
| "It halves the bandwidth needed to fetch weights." | **Close.** About 44% at 16-bit, 38% at 8-bit, because of metadata. |
| "It doubles inference speed." | **Wrong.** Decode is bandwidth-bound and gains from the byte savings, not the TFLOPS. Prefill gains up to 2× on matmuls only. |
| "You can't run a dense model and get the boost." | **Correct**, and the most important line. |
| "It frees VRAM for larger batches." | **Correct.** About 44% of weight memory at 16-bit. The KV cache isn't affected. |

**Takeaway:** 2:4 sparsity gives two gifts, double matmul math (which helps compute-bound prefill) and ~44% fewer weight bytes (which helps bandwidth-bound decode), and neither shows up until someone prunes the model.

That "until someone prunes the model" is doing a lot of work. What does pruning cost, how much accuracy goes with it, and is it a better deal than quantization? That's [part 6](/fields/generative-ai/llm-inference-performance/sparsity-vs-quantization.md).

### References
- [Mishra et al., "Accelerating Sparse Deep Neural Networks", arXiv:2104.08378 (NVIDIA)](https://arxiv.org/abs/2104.08378)
- [NVIDIA cuSPARSE and cuSPARSELt (2:4 structured sparsity, pruning and compression APIs)](https://developer.nvidia.com/cusparse)
- [PyTorch tutorial: Accelerating BERT with semi-structured (2:4) sparsity](https://pytorch.org/tutorials/prototype/semi_structured_sparse.html)
- [NVIDIA H100 Tensor Core GPU datasheet (sparsity figures)](https://www.nvidia.com/en-us/data-center/h100/)
- [NVIDIA A100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/a100/)