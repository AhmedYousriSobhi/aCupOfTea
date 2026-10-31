---
id: slurm-mixed-gpus-where-shine
title: "Where Heterogeneous Jobs Shine"
sidebar_label: "3. Where hetjobs shine"
order: 3
summary: The workloads where mixing GPU types in one Slurm job is exactly right, how admins should label and guard a multi-generation cluster, a decision table, and the interview answer.
level: intermediate
type: concept
domains: [systems-and-hpc]
tags: [slurm, gpu, hpc, nvidia]
relations:
  prerequisites: [slurm-mixed-gpus-why-disappoints]
---

# Where Heterogeneous Jobs Shine

> **Part 3 of the [Mixing GPU Types in Slurm series](/fields/schedulers/slurm-mixed-gpus/README.md), the last one.** [Part 2](/fields/schedulers/slurm-mixed-gpus/why-mixed-training-disappoints.md) showed why one synchronous training run across H100s and A100s is usually a bad deal. This page is the other half: the jobs where different hardware for different parts is exactly the right design. By the end you'll have the rule that separates the two, a setup guide for admins, and an answer that turns "Slurm can't do that" into a strong interview moment.

## Table of Contents
- [Where Heterogeneous Jobs Shine](#where-heterogeneous-jobs-shine)
  - [Table of Contents](#table-of-contents)
  - [The restaurant, not the rowing boat](#the-restaurant-not-the-rowing-boat)
  - [The rule: mix across roles, not within a role](#the-rule-mix-across-roles-not-within-a-role)
  - [Pattern 1: trainer and rollout workers](#pattern-1-trainer-and-rollout-workers)
  - [Pattern 2: server and clients](#pattern-2-server-and-clients)
  - [Pattern 3: "either kind, never both"](#pattern-3-either-kind-never-both)
  - [Pattern 4: uneven layouts in one allocation](#pattern-4-uneven-layouts-in-one-allocation)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [For admins: setting up a multi-generation cluster](#for-admins-setting-up-a-multi-generation-cluster)
    - [Label GPUs and nodes the same way](#label-gpus-and-nodes-the-same-way)
    - [Decide how partitions map to generations](#decide-how-partitions-map-to-generations)
    - [Guard against the accidental mix](#guard-against-the-accidental-mix)
    - [Tune the controls heterogeneous jobs care about](#tune-the-controls-heterogeneous-jobs-care-about)
    - [Teach users the three lines](#teach-users-the-three-lines)
  - [The decision table](#the-decision-table)
  - [The interview answer](#the-interview-answer)
    - [References](#references)

---

## The restaurant, not the rowing boat

A rowing boat needs identical rowers because everyone does the same job at the same moment. A restaurant is different. It has a head chef, line cooks, a dishwasher and waiters. Nobody expects the dishwasher to be as fast at cooking as the head chef. They do *different jobs*, connected by queues: orders go in, plates come out. If the dishwasher is slower, a stack of plates builds up, but the kitchen keeps cooking.

That's what heterogeneous jobs were designed for. Look at the example in Slurm's own documentation: one node with lots of memory running a program called `server`, and 32 other nodes running a program called `client`. Different programs, different hardware, each sized for its role.

Nobody in that example is rowing in sync.

---

## The rule: mix across roles, not within a role

Part 2's problem was that every GPU did the **same job**, in **lockstep**. Take either of those away and mixing makes sense.

> **Mix hardware across roles, not within a role.**

| Question | If yes | If no |
|----------|--------|-------|
| Do the GPU types run *different programs* or roles? | Mixing can fit | Same role on different speeds: the rowing boat |
| Are the parts connected by queues or occasional messages, rather than a per-step barrier? | Each part runs at its own pace | Everyone waits for the slowest |
| Does each part have needs that suit one kind of hardware? | Put each part where it fits best | No reason to mix |

Three yeses is a heterogeneous job. Here are the patterns that pass.

---

## Pattern 1: trainer and rollout workers

Reinforcement learning on language models often has two roles:

- A **trainer** that updates the model's weights: big matrix math, compute-heavy, benefits from the fastest GPUs.
- **Rollout workers** that run the current model to generate samples: mostly inference, and as the [LLM inference series](/fields/generative-ai/llm-inference-performance/llm-inference-on-the-roofline.md) explains, text generation is limited by memory bandwidth far more than by compute.

The roles are connected by a queue of samples going one way and occasional weight updates going the other. They don't meet at every step.

That's a natural heterogeneous job: component 0 on H100s for the trainer, component 1 on A100s for the workers. Each runs at its own pace. The A100s do useful work instead of slowing anyone down.

```bash
#!/bin/bash
#SBATCH --nodes=1 --gres=gpu:h100:8 --partition=h100
#SBATCH hetjob
#SBATCH --nodes=2 --gres=gpu:a100:8 --partition=a100

srun --het-group=0 ./trainer &
srun --het-group=1 ./rollout_worker &
wait
```

Two `srun` calls, two separate worlds, one allocation that starts and ends together. The trainer can find its workers through the per-component variables such as `SLURM_JOB_NODELIST_HET_GROUP_1`.

---

## Pattern 2: server and clients

The documentation's own pattern, generalized: one component is a coordinator, a parameter store, a database or an inference endpoint; the other is a fleet of workers that talk to it. The coordinator might want a big-memory node; the workers want GPUs. Or the coordinator wants one H100 node and the workers are happy on older GPUs.

Slurm gives each its own size, partition, account and QOS, and guarantees they start together, so workers never come up before the thing they connect to.

---

## Pattern 3: "either kind, never both"

Sometimes the honest need isn't mixing at all. It's flexibility: "I can run on H100s or A100s; give me whichever is free first." That's **matching OR** from [part 1](/fields/schedulers/slurm-mixed-gpus/four-ways-to-mix-gpus.md#way-2-constraints-and-the-trap-in-the-bar):

```bash
#SBATCH --nodes=4
#SBATCH --gres=gpu:4
#SBATCH --constraint="[h100|a100]"
```

All four nodes are the same kind, so the rowing boat stays matched. The job just starts sooner. For most researchers who think they want "mixed GPUs," this is the request they actually need.

Make sure the job adapts to whichever kind it gets: for example, enable FP8 only when it lands on H100s.

---

## Pattern 4: uneven layouts in one allocation

When the allocation is uniform but the work inside it isn't, a **heterogeneous step** (Slurm 20.11 and later) lets one `srun` give different nodes different layouts. The docs' example splits a 10-GPU, 2-node allocation into one node with 4 tasks on 4 GPUs and another with 1 task on 6 GPUs. No co-scheduling of separate jobs, so none of the queue tax from part 2.

---

## Try it before you scroll

☕ Four requests from users. Heterogeneous job, matching OR, or "please don't"?

1. "I want to fine-tune on 8 H100s plus the 4 idle A100s to go faster."
2. "My evaluation harness runs a judge model next to my training job, and I want them to start together."
3. "I don't care which GPUs, I just want to start today."
4. "My simulation runs on CPU nodes and streams data to a GPU model."

Answers: (1) please don't: same role in lockstep, the rowing boat; (2) heterogeneous job: different roles, loosely connected; (3) matching OR; (4) heterogeneous job: CPU and GPU components, connected by a stream.

---

## For admins: setting up a multi-generation cluster

The configuration below uses standard `slurm.conf` and `gres.conf` parameters described in Slurm's GRES documentation and man pages. Adapt names to your site and try it on a test partition first.

### Label GPUs and nodes the same way

Give every node both a **GRES type** (for `--gres`/`--gpus`) and a **feature** (for `--constraint`), using the same short names so users only learn one vocabulary:

```text
# slurm.conf (excerpt)
GresTypes=gpu
NodeName=gpu-a[001-016] Gres=gpu:a100:8 Features=a100,ampere
NodeName=gpu-h[001-032] Gres=gpu:h100:8 Features=h100,hopper
```

With `AutoDetect=nvml` in `gres.conf`, Slurm reads the GPUs from the driver, and the type in `slurm.conf` only needs to be a substring of the detected name. Check what a node reports with `slurmd -C` before choosing names.

### Decide how partitions map to generations

| Layout | Upside | Downside |
|--------|--------|----------|
| One partition per generation | Simple; plain OR can't mix across partitions by accident | Users must pick; idle capacity in one isn't visible from the other |
| One shared GPU partition, features to choose | Flexible; matching OR lets jobs take whichever is free | A bare `\|` can mix generations in multi-node jobs |

If you choose the shared partition, guard it.

### Guard against the accidental mix

Slurm's docs note the job submit plugin runs **independently for each component** of a heterogeneous job, and it sees every regular job too. That's the place to enforce site policy, for example: flag or reject multi-node GPU jobs whose constraint uses a bare `|` without brackets, with a message pointing users to matching OR.

### Tune the controls heterogeneous jobs care about

| Setting | What it does, per the docs |
|---------|---------------------------|
| `SchedulerParameters=disable_hetjob_steps` | Disables steps that span more than one component cluster-wide (useful if your MPI stack can't handle them) |
| `SchedulerParameters=whole_hetjob` | Makes cancel, hold and release on any component apply to the whole job |
| Per-user running-job limits | Remember every component counts as a job; a low limit can block multi-component jobs |

### Teach users the three lines

Most mixing problems are vocabulary problems. Put this in your user docs:

| You want | Write |
|----------|-------|
| A specific kind | `--gres=gpu:h100:4` |
| Either kind, all the same | `--constraint="[h100\|a100]"` |
| Different hardware for different programs | A heterogeneous job (`#SBATCH hetjob`) |

---

## The decision table

| Your situation | Use | Why |
|----------------|-----|-----|
| One training run, same role on every GPU | **One GPU type** | Synchronous jobs run at the slowest GPU's pace |
| Flexible about the type, but not mixing | **Matching OR** `[h100\|a100]` | Faster start, matched hardware |
| Different programs that start together and talk loosely | **Heterogeneous job** | Each part sized for its role |
| Uniform allocation, uneven work inside | **Heterogeneous step** | No co-scheduling cost |
| Need job arrays, gang scheduling or migration between federated clusters | **Not a heterogeneous job** | Unsupported for heterogeneous jobs |
| Fixed node split, same per-node request | **Constraint counts** `[h100*2&a100*2]` | Lightweight, but you're mixing: be sure the workload tolerates it |

---

## The interview answer

> *"Can Slurm allocate different GPU types, say H100s and A100s, to one job?"*

> "Yes. Since 17.11 it supports heterogeneous jobs: several components, each with its own resources, partition and QOS, scheduled together. You can also get a fixed split with constraint counts, or mix by accident with a plain OR constraint, which is why I'd use matching OR, the bracketed form, when users just want either type.
>
> The real question is whether you should. For one synchronous training run, no: every step waits at the all-reduce for the slowest GPU, so eight H100s plus eight A100s train at A100 pace, and on datasheet numbers the eight H100s alone would be faster. You also lose H100-only features like FP8. Heterogeneous jobs also pay a queue cost: all components must start together, only the backfill scheduler places them, and they don't support job arrays.
>
> Where they shine is different roles on different hardware: a trainer on H100s with rollout or inference workers on A100s, or a server with a fleet of clients. The rule I use is: mix hardware across roles, not within a role."

**Takeaway:** heterogeneous jobs are for restaurants, not rowing boats, so give different roles different hardware, give one synchronous role one kind of GPU, and give flexible users matching OR.

That's the series. You started with "Slurm can't" and "it doesn't really work." You're leaving with "it works, here's exactly when to use it." Back to the [overview](/fields/schedulers/slurm-mixed-gpus/README.md).

### References
- [Slurm: Heterogeneous Job Support (examples, heterogeneous steps, system administrator information)](https://slurm.schedmd.com/heterogeneous_jobs.html)
- [Slurm: Generic Resource (GRES) Scheduling (GPU types, AutoDetect, `slurmd -C`)](https://slurm.schedmd.com/gres.html)
- [Slurm `sbatch` man page, `--constraint` operators (mirror of the official man page)](https://manpages.org/sbatch)
- [NVIDIA H100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/h100/)
- [NVIDIA A100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/a100/)