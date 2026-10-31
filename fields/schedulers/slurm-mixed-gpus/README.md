---
id: slurm-mixed-gpus-overview
title: Mixing GPU Types in Slurm - Overview
sidebar_label: Overview
summary: Slurm can allocate H100s and A100s in one job - four different ways. A three-part series on what each actually gives you, why mixed training disappoints, and where it shines.
level: intermediate
type: concept
domains: [systems-and-hpc]
tags: [slurm, gpu, hpc, nvidia]
---

# Mixing GPU Types in Slurm - Overview

> A three-part series on a question that sounds simple: *can one Slurm job get H100s and A100s at the same time?* Short answer: yes, in four different ways. Long answer: the scheduler part works fine; what usually breaks is the job you put on top of it. By the end you'll know which way to use, which to avoid, and how to explain the difference.

## Table of Contents
- [Mixing GPU Types in Slurm - Overview](#mixing-gpu-types-in-slurm---overview)
  - [Table of Contents](#table-of-contents)
  - [The myth, the correction, and the real answer](#the-myth-the-correction-and-the-real-answer)
  - [The route](#the-route)
  - [Who this is for](#who-this-is-for)
  - [What this series is based on](#what-this-series-is-based-on)
  - [Contents](#contents)
  - [Related reading in this repo](#related-reading-in-this-repo)

---

## The myth, the correction, and the real answer

There are three stages most people go through with this question.

**Stage 1, the myth:** "Slurm can't give one job two kinds of GPU. A job gets one kind of node."

**Stage 2, the correction:** "Oh, it can. There's a thing called heterogeneous jobs. But it doesn't really work."

**Stage 3, the real answer:** Slurm has supported **heterogeneous jobs** since version 17.11, and there are three other ways to end up with mixed GPUs besides. The scheduling works as documented. What "doesn't work" is something else: putting one tightly synchronized training run across GPUs of different speeds, and paying the scheduling costs that co-scheduling brings. Those are real, but they're about the *workload* and the *queue*, not a broken feature.

The difference matters. "Slurm can't" ends the conversation. "Slurm can, here's when it's worth it" is what a senior engineer says.

---

## The route

| # | Page | The question it answers |
|---|------|-------------------------|
| 1 | [Four ways to ask for mixed GPUs](/fields/schedulers/slurm-mixed-gpus/four-ways-to-mix-gpus.md) | What exactly can Slurm do, and which innocent-looking option mixes GPUs by accident? |
| 2 | [Why mixed training disappoints](/fields/schedulers/slurm-mixed-gpus/why-mixed-training-disappoints.md) | Why does a 16-GPU job with 8 H100s run like 16 A100s, and what does co-scheduling cost in the queue? |
| 3 | [Where heterogeneous jobs shine](/fields/schedulers/slurm-mixed-gpus/where-hetjobs-shine.md) | Which workloads actually benefit, how should admins set up the cluster, and what's the interview answer? |

---

## Who this is for

HPC and AI platform engineers running Slurm on clusters that grew over time: a rack of A100s from two years ago, a row of H100s from last quarter, maybe something newer on order. Also anyone preparing for a scheduler question in an AI-infrastructure interview.

---

## What this series is based on

| Source | Used for |
|--------|----------|
| Slurm documentation (version 26.05): *Heterogeneous Job Support*, *Generic Resource (GRES) Scheduling*, the `sbatch` man page | Every Slurm behavior and limitation described |
| NVIDIA A100 and H100 datasheets | Every GPU speed comparison |

> [!IMPORTANT]
> The Slurm commands in this series are taken from SchedMD's documentation and weren't run on a live cluster while writing. Try them on a test partition first. Behavior can differ between Slurm versions; the pages note the version a feature arrived in where it matters.

## Contents

| File | Description |
|------|-------------|
| [four-ways-to-mix-gpus](/fields/schedulers/slurm-mixed-gpus/four-ways-to-mix-gpus.md) | Typed GRES, constraints, heterogeneous jobs and heterogeneous steps |
| [why-mixed-training-disappoints](/fields/schedulers/slurm-mixed-gpus/why-mixed-training-disappoints.md) | Slowest-rank math, feature gaps, and the scheduling costs of co-scheduling |
| [where-hetjobs-shine](/fields/schedulers/slurm-mixed-gpus/where-hetjobs-shine.md) | Good use cases, admin setup, decision table, interview answer |

## Related reading in this repo

- [LLM Inference Performance](/fields/generative-ai/llm-inference-performance/README.md): where the A100-vs-H100 speed ratios in part 2 come from.
- [Predicting GPU Node Failures](/fields/system-administration/gpu-failure-prediction/README.md): the same Slurm drains, from the reliability side.