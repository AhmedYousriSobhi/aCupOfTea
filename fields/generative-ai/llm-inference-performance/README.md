---
id: llm-inference-performance-overview
title: LLM Inference Performance - Overview
sidebar_label: Overview
summary: Why a GPU with 3x the TFLOPS can make your chatbot only 1.6x faster - a four-part series on the roofline, LLM inference and the optimizations that actually work.
level: intermediate
type: concept
domains: [generative-ai, systems-and-hpc]
tags: [gpu, llm, nvidia, transformers]
---

# LLM Inference Performance - Overview

> A four-part series on the most expensive misunderstanding in AI infrastructure: buying compute when you're short of bandwidth. By the end you'll be able to predict a model's speed on any GPU with a pencil, and explain why vLLM, quantization and tensor parallelism work instead of just naming them.

## Table of Contents
- [LLM Inference Performance - Overview](#llm-inference-performance---overview)
  - [Table of Contents](#table-of-contents)
  - [The upgrade that didn't upgrade](#the-upgrade-that-didnt-upgrade)
  - [The route](#the-route)
  - [Who this is for](#who-this-is-for)
  - [The numbers we'll use](#the-numbers-well-use)
  - [Contents](#contents)
  - [Related reading in this repo](#related-reading-in-this-repo)

---

## The upgrade that didn't upgrade

A team runs their chatbot on A100s. Leadership approves the upgrade to H100s. The slide says it all: dense BF16 compute goes from 312 to 989 TFLOPS. **Three times faster.**

Migration weekend. New hardware, same model. Monday morning, someone runs the benchmark.

Prompt processing: close to 3× faster. Great.

The answers streaming back to users: about **1.6× faster**. Not great.

Nothing is broken. No bug, no misconfiguration. The datasheet told them exactly what would happen. They just read the wrong line. The answer was two rows down, next to "GPU memory bandwidth": 2,039 GB/s on the A100, 3.35 TB/s on the H100. **1.6×.**

This series explains why the second number decided their week, and why it decides most of LLM serving.

---

## The route

| # | Page | The question it answers |
|---|------|-------------------------|
| 1 | [Compute-bound vs memory-bandwidth-bound](/fields/generative-ai/llm-inference-performance/compute-bound-vs-memory-bound.md) | Why does a 3× faster chip sometimes give you 1.6×? |
| 2 | [LLM inference on the roofline](/fields/generative-ai/llm-inference-performance/llm-inference-on-the-roofline.md) | Why does the answer start fast but stream slowly? |
| 3 | [Sizing a 70B model with a pencil](/fields/generative-ai/llm-inference-performance/sizing-a-70b-model.md) | Can you predict a model's speed in an interview, live, on a whiteboard? |
| 4 | [Optimizations, mapped to the roofline](/fields/generative-ai/llm-inference-performance/optimizations-on-the-roofline.md) | Which of the five "fixes" proposed in the meeting will actually work? |

Each page ends with the question the next one answers. Page 3 is the one to rehearse: doing the arithmetic live is what wins the room.

---

## Who this is for

Infrastructure and platform engineers who run GPUs for AI and keep getting asked "why is it slow?" and "what should we buy?". You don't need to write CUDA. You need to be happy multiplying big numbers and dividing them by other big numbers.

And if you're preparing for the interview question *"How would you serve a 70B model?"*, this series is the long version of a great answer.

---

## The numbers we'll use

All hardware figures from NVIDIA datasheets; the model from the Llama 2 paper and its published configuration.

| Item | Value |
|------|-------|
| H100 SXM | 989 TFLOPS dense BF16 (the datasheet's 1,979 is *with sparsity*), 80 GB HBM3 at 3.35 TB/s |
| A100 80GB SXM | 312 TFLOPS dense BF16 (624 with sparsity), 80 GB HBM2e at 2,039 GB/s |
| Llama 2 70B | 80 layers, hidden size 8192, 64 query heads, 8 key/value heads |

> [!NOTE]
> Every speed in this series is a **ceiling**: what the hardware allows at 100% of datasheet numbers. Real systems land below. Ceilings are still the right tool. They tell you which resource you've run out of, and they catch vendor claims that break physics.

## Contents

| File | Description |
|------|-------------|
| [compute-bound-vs-memory-bound](/fields/generative-ai/llm-inference-performance/compute-bound-vs-memory-bound.md) | Arithmetic intensity, the roofline model and ridge points |
| [llm-inference-on-the-roofline](/fields/generative-ai/llm-inference-performance/llm-inference-on-the-roofline.md) | Prefill vs decode, batching and the KV cache |
| [sizing-a-70b-model](/fields/generative-ai/llm-inference-performance/sizing-a-70b-model.md) | Worked example: Llama 2 70B on 8×H100 |
| [optimizations-on-the-roofline](/fields/generative-ai/llm-inference-performance/optimizations-on-the-roofline.md) | What each optimization moves, how to measure, interview answer |

## Related reading in this repo

- [Predicting GPU Node Failures](/fields/system-administration/gpu-failure-prediction/README.md): the same GPUs, the same telemetry, the reliability side of the story.