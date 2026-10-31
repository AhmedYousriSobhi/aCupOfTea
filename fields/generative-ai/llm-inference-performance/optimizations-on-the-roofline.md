---
id: llm-perf-optimizations
title: "Optimizations, Mapped to the Roofline"
sidebar_label: "4. Optimizations on the roofline"
order: 4
summary: Five proposals in one meeting, one roofline to judge them - batching, PagedAttention, quantization, tensor parallelism, FlashAttention, speculative decoding, disaggregation, and how to measure.
level: intermediate
type: concept
domains: [generative-ai, systems-and-hpc]
tags: [gpu, llm, nvidia, transformers]
relations:
  prerequisites: [llm-perf-sizing-70b]
---

# Optimizations, Mapped to the Roofline

> **Part 4 of the [LLM Inference Performance series](/fields/generative-ai/llm-inference-performance/README.md).** Every LLM serving optimization pulls one of five levers. Once you can name the lever, you can predict whether an idea will work before anyone spends a dollar on it. By the end of this page you'll judge five real proposals, meet three clever tricks nobody proposed, catch a dashboard lying to you, and give the 70B interview answer with reasons.

## Table of Contents
- [The meeting](#the-meeting)
- [The five levers](#the-five-levers)
- [Verdicts on the five proposals](#verdicts-on-the-five-proposals)
- [Three tricks nobody proposed](#three-tricks-nobody-proposed)
- [The dashboard that says 100%](#the-dashboard-that-says-100)
- [Myths, busted](#myths-busted)
- [The interview answer](#the-interview-answer)

---

## The meeting

Friday, 4 PM. The 70B chatbot from [part 3](/fields/generative-ai/llm-inference-performance/sizing-a-70b-model.md) is popular, and users say it's slow. Five people, five proposals:

1. **The manager:** "Next-gen GPUs have way more TFLOPS. Let's upgrade."
2. **The ML engineer:** "Switch our serving to vLLM."
3. **The researcher:** "Quantize the model to FP8."
4. **The infrastructure lead:** "Spread tensor parallelism across two servers, 16 GPUs instead of 8."
5. **The intern, quietly:** "Could we stop the long prompts from slowing everyone down?"

Everyone looks at you. You have a datasheet and a pencil.

☕ **Try it before you scroll.** Using parts 1 to 3, sort the five: likely to help, likely not to, or "it depends". Then compare with the verdicts below.

---

## The five levers

Decode speed is roughly *bytes per step ÷ bandwidth*, and batch size is capped by memory. That leaves exactly five things an optimization can do:

| Lever | What it does on the roofline | Helps |
|-------|------------------------------|-------|
| **Reuse each byte more** | Moves the work right, toward the ridge | Throughput |
| **Fetch fewer bytes** | Same work, less time on the slanted roof | Latency and throughput |
| **Add bandwidth** | Raises the slanted roof | Latency and throughput |
| **Fit more in memory** | Lets the batch grow, which then reuses bytes more | Throughput |
| **Separate the phases** | Stops compute-bound prefill from colliding with bandwidth-bound decode | Predictable latency |

Faster math isn't on the list for decode. Keep that in mind for proposal 1.

---

## Verdicts on the five proposals

### Proposal 1: "More TFLOPS" — doesn't help the complaint

Users complain about slow streaming. Streaming is decode. Decode is bandwidth-bound: in part 3 the math for a token took 0.02 ms and the fetching 5.2 ms. Making 0.02 ms faster changes nothing anyone can feel.

It's the overview story all over again: compute up 3.2×, streaming up 1.6×, because bandwidth went up 1.6×. **When comparing GPUs for decode, read the bandwidth row, not the TFLOPS row.** More TFLOPS *would* shorten the pause before long answers start (prefill), so it's not useless, just aimed at the wrong ticket.

### Proposal 2: "vLLM" — helps, by fitting more people on the bus

vLLM brings two things.

**Continuous batching.** At every decode step, finished requests leave and new ones join, so the batch stays full ([part 2](/fields/generative-ai/llm-inference-performance/llm-inference-on-the-roofline.md#batching-the-bus-instead-of-the-taxi)). Lever: *reuse each byte more*.

**PagedAttention.** Remember the villain from part 3: systems that reserved KV memory for the maximum possible conversation length, up front, for every request. Kwon et al. found that KV-cache memory was being badly wasted through fragmentation and reservation, which capped batch sizes. PagedAttention stores the KV cache in small fixed-size blocks that don't need to sit next to each other, the way an operating system pages virtual memory. Their paper reports near-zero KV-cache waste and **2-4× higher throughput** than earlier systems at the same latency. Lever: *fit more in memory*. Blocks can even be shared, for example a system prompt that every request starts with.

Notice what PagedAttention doesn't do: it doesn't make any single fetch faster. It lets more users fit, so each weight fetch serves more of them. **Verdict: helps throughput a lot. Each user's speed stays about the same.**

### Proposal 3: "Quantize to FP8" — helps everyone, with a quality check

Half the bytes per weight, half the fetching. Part 3's numbers: the one-user ceiling goes from about 190 to about 380 tokens/s, and 70 GB of memory frees up for KV cache. Quantize the KV cache too and you shrink the luggage that batching can never share.

Lever: *fetch fewer bytes*. One of the few optimizations that speeds up a single user, not just the crowd.

The catch is quality. Lower precision can hurt answers, and only your own evaluations can tell you by how much. Very low-bit formats (4-bit methods such as AWQ or GPTQ) also make the kernels unpack the weights, spending some of that idle compute. **Verdict: helps, if the evals agree.**

### Proposal 4: "16 GPUs across two servers" — probably hurts

Tensor parallelism inside one server pulls two levers at once: *capacity* and *bandwidth*. Eight GPUs gave 8× the single-user ceiling in part 3.

But it has a cost: in the Megatron-LM design, every layer ends with two all-reduce operations, so the GPUs exchange data **160 times per token** for an 80-layer model. Inside a server that happens over NVLink. Across two servers it goes over the network, which is much slower, and you pay it 160 times per token. The extra bandwidth from 8 more GPUs can easily be eaten by the waiting.

That's why tensor parallelism usually stops at the edge of one NVLink-connected server. To serve more users, run a **second copy** of the model on the second server and split traffic between them. **Verdict: replicate, don't stretch.**

### Proposal 5: the intern's — helps, and it's the cleverest one

The intern noticed the stutter from part 2: when someone pastes a giant document, its compute-bound prefill barges in between everyone else's bandwidth-bound decode steps, and every stream hiccups.

Two kinds of fix:

- **Split prefill into chunks** and interleave them with decode steps, so no single giant prompt blocks everyone.
- **Separate the phases entirely.** Systems such as **Splitwise** (Patel et al.) and **DistServe** (Zhong et al.) run prefill and decode on separate GPU pools and send the KV cache from one to the other. Each pool is sized for its own side of the roofline: compute for prefill, bandwidth and memory for decode.

Lever: *separate the phases*. Cost: moving KV caches between pools, and a smarter scheduler. **Verdict: helps latency predictability, especially with long prompts.** Give the intern a raise.

### The scorecard

| Proposal | Lever | Verdict |
|----------|-------|---------|
| 1. More TFLOPS | None for decode | Doesn't fix streaming; helps prefill |
| 2. vLLM | Reuse + capacity | Big throughput win |
| 3. FP8 | Fewer bytes | Faster for everyone, check quality |
| 4. TP across servers | Bandwidth, but network-bound | Replicate instead |
| 5. Tame long prompts | Separation | Smoother latency |

---

## Three tricks nobody proposed

### Grouped-query attention: luggage diet (chosen at training time)

Sharing each key/value head across several query heads shrinks the KV cache and raises attention's intensity by the group size. Llama 2 70B shares 8 KV heads among 64 query heads: an 8× lighter cache than classic attention ([part 3, question 2](/fields/generative-ai/llm-inference-performance/sizing-a-70b-model.md#question-2-how-much-does-each-conversation-cost)). You can't add it to a model after training, but you should check for it when choosing which model to serve.

### FlashAttention and kernel fusion: stop leaving the kitchen

Naive attention writes big intermediate tables out to HBM and reads them straight back. That's the teenager carrying a half-made pizza to the fridge and back between every step. **FlashAttention** (Dao et al.) is *IO-aware*: it computes attention in tiles that stay in fast on-chip memory, cutting trips to HBM. **Kernel fusion** does the same for chains of small operations. Lever: *fetch fewer bytes*. Biggest wins on long sequences and prefill.

### Speculative decoding: let the chefs guess ahead

Decode leaves the tensor cores idle. **Speculative decoding** (Leviathan et al.) puts them to work: a small, fast draft model guesses the next few tokens, and the big model checks all of them in *one* pass. Checking several tokens at once looks like a tiny prefill, so one walk through the library can produce several words. When the guesses are right, you get several tokens for one weight fetch, and the output matches what the big model would have produced alone.

Lever: *reuse each byte more*, for a **single user**, which batching can't do. Cost: the draft model's own work, and wasted checks when guesses miss. Shines when the draft guesses well and the server isn't already packed with users.

---

## The dashboard that says 100%

Monday. You've shipped vLLM and FP8. Someone posts a screenshot: **GPU utilization: 100%**. "We're maxed out. Time to buy more GPUs?"

Not so fast. The standard "GPU utilization" number (from `nvidia-smi`, and `DCGM_FI_DEV_GPU_UTIL` in dcgm-exporter) comes from NVML, which defines it as the percent of time during which **one or more kernels was executing**. It tells you the GPU was *busy*, not how much of it was working. A decode kernel waiting on memory shows 100% while the tensor cores twiddle their thumbs.

Two other metrics in dcgm-exporter's default counters tell you which side of the roofline you're on:

| Metric | Defined as |
|--------|-----------|
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | Ratio of cycles the tensor (HMMA) pipe is active |
| `DCGM_FI_PROF_DRAM_ACTIVE` | Ratio of cycles the device memory interface is active sending or receiving data |

Read them as a pair:

| Tensor active | Memory active | Diagnosis | Reach for |
|---------------|---------------|-----------|-----------|
| Low | High | Bandwidth-bound: typical decode | Fewer bytes, more reuse |
| High | Lower | Compute-bound: typical prefill | Faster math |
| Low | Low | Overhead-bound: tiny batches, launch gaps, waiting on communication | Bigger batches, fusion, fewer sync points |
| High | High | Balanced, near the ridge | You're in good shape |

For deeper digging: **Nsight Compute** draws each kernel on an actual roofline chart, **Nsight Systems** shows the timeline gaps, and your serving engine reports time to first token, time per output token and KV-cache usage. KV cache near full with requests queuing means you've hit the capacity wall.

> [!TIP]
> Compare real tokens/s with your part 3 ceiling. Hitting 50-70% of a bandwidth ceiling means the system is healthy and the next win needs a new lever. Hitting 10% means something outside the roofline (scheduling, communication, CPU) is eating your time.

---

## Myths, busted

| Myth | Reality |
|------|---------|
| "More TFLOPS, faster generation." | Generation follows **bandwidth**. The math for a token took 0.02 ms of a 5.2 ms step. |
| "Quantization increases memory bandwidth." | Bandwidth is fixed by the hardware. Quantization **cuts the bytes** you need. |
| "LLM inference is memory-bound." | **Decode** is. **Prefill** is compute-bound. |
| "Tensor parallelism is only to make the model fit." | It also multiplies bandwidth, so it speeds up one user even when the model already fits. |
| "Batch enough and decode becomes compute-bound." | Not at long contexts: KV luggage grows faster than useful work ([part 3](/fields/generative-ai/llm-inference-performance/sizing-a-70b-model.md#question-6-so-just-batch-more-until-its-compute-bound)). |
| "100% utilization means maxed out." | It means *a kernel was running*. Check tensor and memory activity. |

---

## The interview answer

> *"How would you serve a 70B model with high throughput and low latency?"*

> "Start with the physics. In 16-bit the weights are about 140 GB, so they don't fit on one 80 GB GPU. And generation is memory-bandwidth-bound: each token reads every weight and does about one FLOP per byte, while an H100 needs about 300 to keep its tensor cores busy. So I plan in bytes, not TFLOPS.
>
> I'd use tensor parallelism inside one 8-GPU NVLink server. That fits the model and multiplies bandwidth, for a single-user ceiling around 190 tokens per second. For throughput, an engine with continuous batching and PagedAttention, like vLLM, so each weight read serves many users and KV memory isn't wasted. At 64 users with 4K contexts that's a ceiling around 7,600 tokens per second. Then FP8 for weights and KV cache, which halves the bytes, after checking quality on our evals. To scale further I'd replicate across servers rather than stretch tensor parallelism over the network.
>
> I'd track time to first token and time per output token separately, because prefill is compute-bound and decode is bandwidth-bound. If long prompts hurt streaming, I'd chunk prefill or split it onto its own GPUs. And I'd verify on DCGM: high memory activity with low tensor activity confirms we're on the bandwidth side, so I know which optimizations can still help."

**Takeaway:** every serving optimization reuses bytes, fetches fewer bytes, adds bandwidth, frees memory or separates the phases, so name the lever before you spend the money, and check tensor activity against memory activity before you believe a utilization dashboard.

You walked in wondering why a 3× faster chip gave 1.6×. You can now predict it with a pencil. But one number on the datasheet is still unexplained: the H100's headline 1,979 TFLOPS, the one with the asterisk. What is "with sparsity," and can your models ever use it? That's [part 5](/fields/generative-ai/llm-inference-performance/structured-sparsity.md).

### References
- [Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention", SOSP 2023, arXiv:2309.06180](https://arxiv.org/abs/2309.06180)
- [Dao et al., "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness", arXiv:2205.14135](https://arxiv.org/abs/2205.14135)
- [Leviathan, Kalman, Matias, "Fast Inference from Transformers via Speculative Decoding", arXiv:2211.17192](https://arxiv.org/abs/2211.17192)
- [Patel et al., "Splitwise: Efficient Generative LLM Inference Using Phase Splitting", arXiv:2311.18677](https://arxiv.org/abs/2311.18677)
- [Zhong et al., "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving", arXiv:2401.09670](https://arxiv.org/abs/2401.09670)
- [Shoeybi et al., "Megatron-LM", arXiv:1909.08053](https://arxiv.org/abs/1909.08053)
- [Touvron et al., "Llama 2", arXiv:2307.09288](https://arxiv.org/abs/2307.09288)
- [dcgm-exporter `etc/default-counters.csv` (profiling metric definitions)](https://github.com/NVIDIA/dcgm-exporter/blob/main/etc/default-counters.csv)
- [NVML API reference: `nvmlUtilization_t`](https://docs.nvidia.com/deploy/nvml-api/structnvmlUtilization__t.html)
- [NVIDIA Nsight Compute Profiling Guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)
- [NVIDIA H100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/h100/)