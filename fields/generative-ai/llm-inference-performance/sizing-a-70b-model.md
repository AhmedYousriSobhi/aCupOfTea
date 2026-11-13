
# Sizing a 70B Model with a Pencil

<!-- related-block -->
<div class="reading-time">9 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [LLM Inference on the Roofline](/fields/generative-ai/llm-inference-performance/llm-inference-on-the-roofline.md)  ·  **Read next:** [Optimizations, Mapped to the Roofline](/fields/generative-ai/llm-inference-performance/optimizations-on-the-roofline.md)

</div>


> **Part 3 of the [LLM Inference Performance series](/fields/generative-ai/llm-inference-performance/README.md).** This page is a whiteboard session. One real model, one real server, seven questions an interviewer could ask, and the arithmetic to answer each one live. By the end you'll be able to size any model on any GPU in about five minutes, and you'll have caught the batching myth red-handed.

## Table of Contents
- [Sizing a 70B Model with a Pencil](#sizing-a-70b-model-with-a-pencil)
  - [Table of Contents](#table-of-contents)
  - [The marker is in your hand](#the-marker-is-in-your-hand)
  - [Question 1: "Does it fit?"](#question-1-does-it-fit)
  - [Question 2: "How much does each conversation cost?"](#question-2-how-much-does-each-conversation-cost)
  - [Question 3: "How many users can we hold?"](#question-3-how-many-users-can-we-hold)
  - [Question 4: "How fast for one user?"](#question-4-how-fast-for-one-user)
  - [Question 5: "And with 64 users?"](#question-5-and-with-64-users)
  - [Question 6: "So just batch more until it's compute-bound?"](#question-6-so-just-batch-more-until-its-compute-bound)
  - [Question 7: "What about the prompt?"](#question-7-what-about-the-prompt)
  - [Bonus round: FP8](#bonus-round-fp8)
  - [The five-line cheat sheet](#the-five-line-cheat-sheet)
    - [References](#references)

---

## The marker is in your hand

Interview room. Whiteboard. The interviewer leans back.

*"We want to serve Llama 2 70B on one server with eight H100s. Talk me through it. How fast can it go?"*

Most candidates start listing tools: vLLM, quantization, tensor parallelism. The interviewer nods politely. They've heard it forty times.

You pick up the marker and write the inputs instead.

| Input | Value |
|-------|-------|
| Model | Llama 2 70B: 80 layers, hidden size 8192, 64 query heads, **8 KV heads**, head dim 128 (8192 ÷ 64), context up to 4,096 tokens |
| Precision | 16-bit: 2 bytes per weight and per cached value |
| One H100 SXM | 80 GB HBM3, **3.35 TB/s**, 989 TFLOPS dense BF16 |
| Eight of them | **640 GB, 26.8 TB/s, ~7.9 PFLOPS** |

*"Everything I compute is a ceiling: 100% of datasheet numbers, no overheads. Real systems land below. But ceilings tell us which resource we'll run out of first."*

The interviewer sits up a little. Let's go.

---

## Question 1: "Does it fit?"

$$70 \times 10^9 \times 2 \text{ bytes} \approx 140 \text{ GB}$$

One H100 holds 80 GB. **It doesn't fit.** That's a *capacity* problem, and it's the first reason for **tensor parallelism**: slice every weight matrix across the GPUs. Eight GPUs, about 17.5 GB of weights each.

Now say the subtle bit out loud: *"Two GPUs would hold the weights. We're using eight for bandwidth and for room to store conversations."* That sentence sets up everything that follows.

---

## Question 2: "How much does each conversation cost?"

Every token in every conversation leaves luggage in the KV cache ([part 2](/fields/generative-ai/llm-inference-performance/llm-inference-on-the-roofline.md#the-kv-cache-the-luggage-that-doesnt-share)):

$$2 \times 80 \text{ layers} \times 8 \text{ KV heads} \times 128 \times 2 \text{ bytes} = 327{,}680 \text{ bytes} \approx 0.33 \text{ MB per token}$$

A full 4,096-token conversation:

$$4{,}096 \times 0.33 \text{ MB} \approx 1.34 \text{ GB}$$

Now the flourish that makes interviewers smile. *"This is cheap because Llama 2 70B uses grouped-query attention. With classic multi-head attention, all 64 heads would store their own keys and values: 8× more, about 2.6 MB per token, 10.7 GB per conversation. Seven long chats would weigh more than the model."*

---

## Question 3: "How many users can we hold?"

Keep some memory back for activations and runtime buffers. Engines expose this as a setting; assume 10% headroom.

| | GB |
|---|---|
| Eight GPUs | 640 |
| Usable at 90% | 576 |
| Minus the weights | −140 |
| **Left for KV cache** | **~436** |

$$\frac{436}{1.34} \approx 325 \text{ full-length conversations}$$

That's if every conversation runs to the full 4,096 tokens. Most are shorter, so more fit... but only if you don't **reserve** the full 4,096 for every request up front. Older systems did exactly that and wasted most of the space on tokens nobody ever generated. File that away; it's the villain PagedAttention defeats in part 4.

---

## Question 4: "How fast for one user?"

One user means decode at batch 1: every weight read once per token.

$$\frac{140 \text{ GB}}{26.8 \text{ TB/s}} \approx 5.2 \text{ ms per token} \quad\Rightarrow\quad \text{at most } \sim 190 \text{ tokens/s}$$

Now compute how long the *math* takes for that token: 2 × 70×10⁹ ≈ 1.4×10¹¹ FLOPs, at 7.9 PFLOPS, about **0.02 ms**.

Write both numbers side by side on the board. **5.2 ms of fetching, 0.02 ms of thinking.** The tensor cores spend 99.7% of the time waiting. That's part 2's "300× below the ridge," made physical.

One more line for depth: *"If the model somehow fit on one H100, the ceiling would be 140 GB ÷ 3.35 TB/s, about 24 tokens per second. Eight GPUs give 8× the single-user speed because they add bandwidth, not because they add compute."*

> [!NOTE]
> Real numbers land below 190. Tensor parallelism also has to *talk*: in the standard Megatron-LM design, each layer needs two all-reduce operations across the GPUs. That's 160 small messages per token for 80 layers, over NVLink. At batch 1 those messages are tiny, so their cost is latency, not bandwidth. It's a third roof the simple model doesn't draw.

---

## Question 5: "And with 64 users?"

Sixty-four conversations, each with a full 4,096-token history, each getting its next token in the same step.

| Bytes read per step | GB |
|---------------------|-----|
| Weights, read once and shared by all 64 | 140 |
| KV caches, 64 × 1.34 GB, **not shared** | ~86 |
| **Total** | **~226** |

$$\frac{226 \text{ GB}}{26.8 \text{ TB/s}} \approx 8.4 \text{ ms per step}$$

And each step now produces 64 tokens. Put it in a table, because this table is the punchline of the whole page:

| | 1 user | 64 users |
|---|---|---|
| Time per step | 5.2 ms | 8.4 ms |
| Tokens per step | 1 | 64 |
| **Server throughput ceiling** | ~190 tokens/s | **~7,600 tokens/s** |
| **Each user's speed ceiling** | ~190 tokens/s | **~120 tokens/s** |

Throughput up about **40×**. Each user slowed by about a third. That's the bus from part 2, in numbers.

Quick compute check: 64 × 1.4×10¹¹ ≈ 9×10¹² FLOPs, about 1.1 ms. Still seven times less than the fetching. *"Even at batch 64, we're bandwidth-bound by about 7×."*

---

## Question 6: "So just batch more until it's compute-bound?"

The interviewer is testing you now. The tempting answer: weight intensity ≈ batch size, ridge ≈ 295, so batch 295 and you're compute-bound.

☕ **Try it before you scroll.** You've got every number you need. Does it work?

...

Here's the board at batch 295, full 4,096-token contexts:

| | Value |
|---|---|
| Bytes per step | 140 GB of weights + 295 × 1.34 GB of KV ≈ **535 GB** |
| FLOPs per step | weights: 295 × 1.4×10¹¹ ≈ 4.1×10¹³; attention: about 0.3×10¹³ more |
| Intensity | 4.4×10¹³ ÷ 5.35×10¹¹ ≈ **83 FLOP/byte** |

Eighty-three. Not 295. Not even close.

The luggage won. By batch 295, the KV caches weigh almost three times as much as the model, and they run at about 8 FLOP/byte no matter what. Every passenger you add brings more luggage than useful work. And from Question 3, only about 325 such conversations fit in memory anyway.

Say it plainly: *"With long contexts, decode is bandwidth-bound at every batch size that fits in memory. Short contexts get closer to the ridge, because then the weights are most of the bytes. So context length isn't a detail; it's a capacity-planning input."*

That's the moment the interviewer stops checking their phone.

---

## Question 7: "What about the prompt?"

Flip to prefill. A 2,000-token prompt:

| | Value |
|---|---|
| FLOPs | 2 × 70×10⁹ × 2,000 ≈ 2.8×10¹⁴ |
| Time for the math at 7.9 PFLOPS | **≈ 35 ms** |
| Time to read the weights once | ≈ 5.2 ms |

Now the math is the slow part, by about 7×. **Compute-bound**, just as part 2 predicted. Roughly 35 ms is the ceiling on time to first token for this prompt, and more bandwidth wouldn't move it. More compute would.

Same model, same server, opposite bottleneck. Two tickets, two physics.

---

## Bonus round: FP8

*"What if we quantize to 8-bit?"* H100 tensor cores support FP8. The bytes halve:

| | 16-bit | FP8 weights |
|---|---|---|
| Weight memory | 140 GB | 70 GB |
| One-user ceiling | ~190 tokens/s | **~380 tokens/s** |
| Room for KV cache (of 576 GB usable) | ~436 GB | ~506 GB |

The bandwidth didn't change. The model just needs half the bytes per token. Quantize the KV cache to 8 bits as well and the luggage halves too: more users fit *and* every step reads less.

The careful closing line: *"Those are ceilings. Whether quality holds at 8 bits is something we'd measure on our own evals. The roofline can't tell us that."*

---

## The five-line cheat sheet

That whole session, for any model on any GPU:

| Question | Formula |
|----------|---------|
| Does it fit? | parameters × bytes per weight |
| Cost per token of context | 2 × layers × KV heads × head dim × bytes per value |
| How many users? | (usable memory − weights) ÷ (KV per token × context length) |
| How fast per step? | (weights + users × KV per user) ÷ total bandwidth |
| Which wall? | FLOPs ÷ bytes, compared with peak FLOPS ÷ bandwidth |

**Takeaway:** for Llama 2 70B on 8×H100, the weights take 140 GB, each long conversation 1.34 GB more, one user tops out near 190 tokens/s, and even 64 users stay about 7× bandwidth-bound, so plan capacity in bytes, not FLOPs.

Then the interviewer smiles and asks the follow-up: *"Great. So, my team proposed five optimizations last week. Which ones would actually help?"* That's [part 4](/fields/generative-ai/llm-inference-performance/optimizations-on-the-roofline.md).

### References
- [Touvron et al., "Llama 2: Open Foundation and Fine-Tuned Chat Models", arXiv:2307.09288](https://arxiv.org/abs/2307.09288)
- [Llama 2 70B configuration (published `config.json`, mirrored)](https://huggingface.co/galqiwi/llama2-70b-hf/blob/10a97a0a7de3926c2d03eba4e9c216501e00beba/config.json)
- [NVIDIA H100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/h100/)
- [Shoeybi et al., "Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism", arXiv:1909.08053](https://arxiv.org/abs/1909.08053)
- [Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention", arXiv:2309.06180](https://arxiv.org/abs/2309.06180)