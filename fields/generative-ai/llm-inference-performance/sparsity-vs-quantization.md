
# Sparsity vs Quantization: Who Pays, and Who Wins

<!-- related-block -->
<div class="reading-time">10 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [2:4 Sparsity: Half the Weights, Not Half the Time](/fields/generative-ai/llm-inference-performance/structured-sparsity.md)

</div>


> **Part 6 of the [LLM Inference Performance series](/fields/generative-ai/llm-inference-performance/README.md), the last one.** [Part 5](/fields/generative-ai/llm-inference-performance/structured-sparsity.md) showed what 2:4 sparsity does once a model is pruned. This page is about getting there: what pruning costs, what it does to accuracy, and how it stacks up against the cheaper-looking alternative, quantization. By the end you'll know which lever to pull first, and how to split the work between the research team and the infrastructure team.

## Table of Contents
- [Sparsity vs Quantization: Who Pays, and Who Wins](#sparsity-vs-quantization-who-pays-and-who-wins)
  - [Table of Contents](#table-of-contents)
  - ["Can't you just turn it on?"](#cant-you-just-turn-it-on)
  - [Two ways to prune](#two-ways-to-prune)
    - [The original recipe: prune, then retrain](#the-original-recipe-prune-then-retrain)
    - [The LLM shortcut: one-shot pruning](#the-llm-shortcut-one-shot-pruning)
  - [What it does to accuracy](#what-it-does-to-accuracy)
  - [Two diets for the same model](#two-diets-for-the-same-model)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [Quantize first, sparsify second](#quantize-first-sparsify-second)
  - [Who owns what](#who-owns-what)
  - [The interview answer](#the-interview-answer)
    - [References](#references)

---

## "Can't you just turn it on?"

The infrastructure lead has just read part 5. She walks over to the research team, excited. "The H100s have 2× sparse math. We're leaving half the chip on the table. Can you just turn on sparsity?"

The research lead puts down her coffee. "Sure. Which half of the model would you like me to delete?"

That's the conversation in one line. 2:4 sparsity isn't a switch on the GPU. It's a change to the **model**: half of every weight matrix becomes zero. Somebody has to choose which half, make sure the model still works afterwards, and prove it. That somebody is rarely the person who wanted the speedup.

---

## Two ways to prune

### The original recipe: prune, then retrain

NVIDIA's paper describes a simple workflow: take a trained dense model, zero out the two smallest-magnitude weights in each group of four, then **retrain** with the same settings as the original training. The authors report that it eliminated accuracy loss across many standard networks in vision, translation and language. PyTorch's 2:4 tutorial summarizes the same finding: prune once, retrain, and accuracy ends up nearly identical.

For a vision model or a BERT, that retraining is affordable. For a 70B LLM, "repeat the original training" can mean a large slice of the original compute budget. That's the catch.

### The LLM shortcut: one-shot pruning

Researchers built methods that prune large language models **without retraining**:

- **SparseGPT** (Frantar and Alistarh, ICML 2023) prunes layer by layer, adjusting the remaining weights so each layer's outputs stay close to the original. It was the first accurate one-shot method for 10-100+ billion parameter models, and it supports the 2:4 and 4:8 patterns. The authors ran it on 175B-parameter models in under 4.5 hours.
- **Wanda** (Sun et al., 2023) is even simpler: it scores each weight by its size times the size of the activations flowing into it, and prunes the lowest scores, again with no retraining.

One-shot pruning turns a training project into a post-processing step. But "no retraining" also means "no chance to win back what was lost." Which raises the real question.

---

## What it does to accuracy

SparseGPT's results on OPT-175B, one of the largest open models at the time, make the trade visible. Accuracy on the ARC-Challenge benchmark:

| Model | ARC-Challenge accuracy |
|-------|------------------------|
| Dense | 43.94 |
| 50% sparse, **unstructured** (SparseGPT) | 41.30 |
| 50% sparse, **2:4** (SparseGPT) | 38.99 |
| 50% sparse, naive magnitude pruning | 25.60 |

Three lessons in four rows:

- **Pruning method matters enormously.** Naive magnitude pruning at 50% wrecked the model. A careful method kept most of the accuracy.
- **The 2:4 rule costs extra.** Same 50% of weights removed, but forcing the hardware-friendly pattern lost more than letting the pruner choose freely. That's the price of a pattern the silicon can read.
- **Size helps.** The SparseGPT paper's broader finding is that larger models are more compressible: they lose less accuracy at a given sparsity.

The authors also showed that sparsity stacks with quantization: 50% sparsity combined with 4-bit weights gave a negligible increase in perplexity on OPT-175B.

> [!WARNING]
> Benchmarks like these are averages over public test sets. Your model, your tasks and your users can lose more, or less. Every pruned model needs to pass the same evaluation gate as any other model change before it serves traffic.

---

## Two diets for the same model

Sparsity and quantization both put the model on a diet. Different diets:

- **Quantization** keeps every weight, but stores each with fewer bits. Like keeping every page of a book but printing it in smaller type.
- **2:4 sparsity** keeps half the weights at full width, and adds a tag saying where each one sat. Like tearing out half the words on every line, and adding a tiny marker so you know where the gaps were.

Here's how they compare against a 16-bit dense baseline, on an H100:

| Lever | Weight bytes saved | Peak matmul math | Changes model structure? | Typical preparation |
|-------|-------------------|------------------|--------------------------|---------------------|
| **FP8** (weights and activations) | 50% | 2× (989 → 1,979 TFLOPS dense) | No | Post-training calibration, sometimes fine-tuning |
| **4-bit weights** (GPTQ, AWQ) | About 75%, minus scale factors | No gain: weights are unpacked for 16-bit math | No | One-shot post-training, calibration data |
| **2:4 sparsity, 16-bit** | ~44% | 2× for sparse matmuls | **Yes**: half the weights are zero | Pruning, ideally plus fine-tuning |
| **FP8 + 2:4** | ~69% | 4× (up to 3,958 TFLOPS) | Yes | Both of the above |

(GPTQ and AWQ are both one-shot weight-only quantization methods for LLMs, from Frantar et al. 2022 and Lin et al. 2023.)

Now map that onto the roofline from [part 1](/fields/generative-ai/llm-inference-performance/compute-bound-vs-memory-bound.md):

- **Decode** (bandwidth-bound) wants **fewer bytes**. 4-bit weights win, FP8 next, 2:4 at 16-bit last.
- **Prefill** (compute-bound) wants **more math**. FP8 and 2:4 both double it; together they quadruple the peak. 4-bit weight-only doesn't help here.

---

## Try it before you scroll

☕ Three workloads. Which lever would you reach for first?

1. A chatbot where users complain the answers stream slowly.
2. A batch job that scores millions of long documents with a model, producing one short label each.
3. A team that's already on FP8 and has a research budget for fine-tuning.

Answers: (1) quantization, ideally 4-bit weights or FP8: decode wants bytes; (2) FP8, then consider 2:4: it's almost all prefill, which wants math, and both levers double it; (3) 2:4 on top of FP8: they stack, and the team can afford the pruning and fine-tuning to protect accuracy.

---

## Quantize first, sparsify second

The recommendation, with the reasoning behind it:

> **Quantize first. Add 2:4 sparsity when quantization is done and the workload or the budget justifies the model surgery.**

Why quantization first:

- **More bytes saved for decode.** FP8 saves 50% of weight bytes and 4-bit about 75%, against 2:4's 44%. Decode is usually what users feel.
- **No structural change.** Every weight stays. Quality risk is easier to reason about and usually easier to recover.
- **Cheaper to prepare.** Post-training quantization is typically a calibration pass, not a pruning-plus-retraining project.

When 2:4 earns its place:

- **Prefill-heavy workloads**: long prompts, retrieval-augmented generation with big contexts, batch scoring, embedding generation. That's where doubled math shows up.
- **Stacking**: once you're on FP8, 2:4 is the next ~38% of bytes and the next 2× of math, the only path to the datasheet's 3,958.
- **Large models**: they tolerate pruning better, per SparseGPT's findings.
- **A research team with budget** to prune carefully and fine-tune.

The trade-off, stated plainly: 2:4 is the only lever that raises the **compute** ceiling without a lower-precision number format, but it's also the only one that changes what the model *is*. That's a research decision with infrastructure benefits, not the other way round.

---

## Who owns what

| Task | Research team | Infrastructure team |
|------|---------------|--------------------|
| Choose the pruning method (retrain, SparseGPT, Wanda) | Owns | Advises on budget |
| Decide which layers stay dense | Owns | Reports which layers dominate runtime |
| Fine-tune to recover accuracy | Owns | Provides the compute |
| Evaluation gate before serving | Co-owns | Co-owns: blocks deploys that fail it |
| Hardware support (Ampere or later; 2:4 needs Sparse Tensor Cores, compute capability 8.0+) | Informed | Owns |
| Engine support: does your serving stack have fast 2:4 kernels for your precision and batch sizes? | Informed | Owns |
| Benchmark **prefill and decode separately**, dense vs sparse | Informed | Owns |
| Keep the dense model as a fallback | Agrees | Owns the rollout and rollback |

The infrastructure lead from the opening story should leave the conversation with this split, not with "please turn it on."

---

## The interview answer

> *"How does 2:4 structured sparsity help with serving large models, and how does it compare with quantization?"*

> "2:4 sparsity means at least two of every four adjacent weights are zero. The model is compressed ahead of time to the non-zero values plus a 2-bit position index each, and Ampere and Hopper Sparse Tensor Cores skip the zeros, doubling peak matmul throughput.
>
> On the roofline it gives two different things. Doubled math helps prefill, which is compute-bound. Decode is bandwidth-bound, so it only feels the byte savings, and because of the metadata that's about 44% at 16-bit, not 50%. End-to-end gains are smaller than 2× because attention and other non-matmul work don't speed up.
>
> The real cost is on the research side: someone has to prune the model and recover accuracy, either by retraining or with one-shot methods like SparseGPT. The 2:4 pattern loses more accuracy than unstructured pruning, though large models tolerate it better.
>
> So I'd quantize first: FP8 or 4-bit weights save more bytes for decode without changing the model's structure. Then I'd add 2:4 on top for prefill-heavy workloads or to stack with FP8, which is the only way to reach the H100's 3,958 TFLOPS sparse FP8 figure, gated on our evals and benchmarked separately for prefill and decode."

**Takeaway:** quantization shrinks every weight and 2:4 sparsity deletes half of them; for decode, fewer bytes wins, so quantize first and add sparsity when prefill speed or stacking justifies the pruning and the accuracy work.

That's the series. You started with a 3× faster chip that gave 1.6×, and you're finishing with the asterisk on its datasheet explained. Back to the [overview](/fields/generative-ai/llm-inference-performance/README.md).

### References
- [Mishra et al., "Accelerating Sparse Deep Neural Networks", arXiv:2104.08378 (NVIDIA)](https://arxiv.org/abs/2104.08378)
- [Frantar and Alistarh, "SparseGPT: Massive Language Models Can Be Accurately Pruned in One-Shot", ICML 2023](https://proceedings.mlr.press/v202/frantar23a.html)
- [Sun et al., "A Simple and Effective Pruning Approach for Large Language Models" (Wanda), arXiv:2306.11695](https://arxiv.org/abs/2306.11695)
- [Frantar et al., "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers", arXiv:2210.17323](https://arxiv.org/abs/2210.17323)
- [Lin et al., "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration", arXiv:2306.00978](https://arxiv.org/abs/2306.00978)
- [PyTorch tutorial: Accelerating BERT with semi-structured (2:4) sparsity](https://pytorch.org/tutorials/prototype/semi_structured_sparse.html)
- [NVIDIA H100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/h100/)