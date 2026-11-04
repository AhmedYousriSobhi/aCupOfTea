
# Why Mixed-GPU Training Disappoints

<!-- related-block -->
<div class="reading-time">9 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Four Ways to Ask Slurm for Mixed GPUs](/fields/schedulers/slurm-mixed-gpus/four-ways-to-mix-gpus.md)  ·  **Read next:** [Where Heterogeneous Jobs Shine](/fields/schedulers/slurm-mixed-gpus/where-hetjobs-shine.md)

</div>


> **Part 2 of the [Mixing GPU Types in Slurm series](/fields/schedulers/slurm-mixed-gpus/README.md).** [Part 1](/fields/schedulers/slurm-mixed-gpus/four-ways-to-mix-gpus.md) showed that Slurm can allocate H100s and A100s to one job. This page is about what happens next. By the end you'll be able to explain, with datasheet numbers, why a mixed training run is slower than it looks, and list the scheduling costs heterogeneous jobs carry even when the workload is perfect.

## Table of Contents
- [Why Mixed-GPU Training Disappoints](#why-mixed-gpu-training-disappoints)
  - [Table of Contents](#table-of-contents)
  - [Doing it properly this time](#doing-it-properly-this-time)
  - [The rowing boat rule](#the-rowing-boat-rule)
  - [The numbers: how much the fast GPUs wait](#the-numbers-how-much-the-fast-gpus-wait)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [The features the A100s switch off](#the-features-the-a100s-switch-off)
  - [Can you rebalance the work?](#can-you-rebalance-the-work)
  - [The queue tax: what co-scheduling costs](#the-queue-tax-what-co-scheduling-costs)
  - [So is it "not functional"?](#so-is-it-not-functional)
    - [References](#references)

---

## Doing it properly this time

After the accidental mix in part 1, our researcher reads the docs. She learns about heterogeneous jobs and does it properly: component 0 is two nodes of 4 H100s, component 1 is two nodes of 4 A100s. One `srun` across both groups, one distributed training run over 16 GPUs.

It schedules. It launches. It trains.

And it runs at almost exactly the speed it would have on 16 A100s. Her eight H100s, the most expensive hardware in the building, spend most of every training step doing nothing.

Nothing is broken. Slurm delivered precisely the allocation she asked for. The problem is the shape of the workload, and it has a name.

---

## The rowing boat rule

Picture a rowing boat with eight rowers. Four are Olympic athletes. Four are enthusiastic amateurs. The boat moves as one: every stroke starts together, and the next stroke can't start until everyone has finished this one.

How fast does the boat go? The athletes finish each stroke early, then sit with oars raised, waiting. The boat moves at the **amateurs' pace**. The athletes add almost nothing.

Standard **data-parallel training** is that boat. Every GPU processes its share of the batch, then all GPUs exchange gradients (an **all-reduce**, on NVIDIA GPUs usually performed by the NCCL library) before anyone can take the next step. That exchange is a meeting point: nobody leaves until everybody arrives.

So the rule is:

> **A synchronous job runs at the speed of its slowest participant.**

Every faster GPU in the job finishes early and waits at the all-reduce. The waiting doesn't show up as an error. It shows up as a GPU that's "allocated" and "busy" on your dashboards while doing no useful work.

---

## The numbers: how much the fast GPUs wait

Here's how far apart the two generations are, from NVIDIA's datasheets (80 GB SXM versions):

| | A100 | H100 | H100 ÷ A100 |
|---|---|---|---|
| Dense BF16 Tensor Core | 312 TFLOPS | 989 TFLOPS | ~3.2× |
| HBM bandwidth | 2,039 GB/s | 3.35 TB/s | ~1.6× |
| NVLink per GPU | 600 GB/s | 900 GB/s | 1.5× |
| Memory | 80 GB | 80 GB | 1× |

Take the simplest case: each GPU gets the same share of the batch, and the step is limited by math, as large training steps usually are. An H100 finishes its share in about 1/3.2 of the time an A100 takes. Then it waits.

$$\text{H100 idle fraction} \approx 1 - \frac{312}{989} \approx 68\%$$

Roughly **two-thirds of every H100's time is spent waiting** for the A100s. Throughput is set by 16 GPUs moving at A100 pace: you've built a 16-A100 job that happens to cost H100 hours.

If the step is limited by memory bandwidth instead, the gap is smaller (about 1.6×) and the H100s wait about 40% of the time. Either way, the fast GPUs pay for the slow ones.

> [!NOTE]
> These are ceiling-based ratios from datasheets, not measurements. Real training steps mix math, memory and communication, so the exact waiting share will differ. The direction never does: in a synchronous job, the faster GPUs always wait.

---

## Try it before you scroll

☕ A team has 8 H100s free and 8 A100s free. Option A: one 16-GPU mixed job. Option B: run on the 8 H100s alone. For a compute-bound training run with perfect scaling, which finishes sooner?

Work it out in "A100-equivalents." Option A: 16 GPUs at A100 pace = **16** A100-equivalents. Option B: 8 H100s at about 3.2× each = about **25** A100-equivalents.

**The 8 H100s alone beat all 16 GPUs together**, on these ceiling numbers. Adding the A100s didn't just fail to help; it made the job slower. And it tied up eight A100s that another team could have used for their own job.

That's the counterintuitive heart of this page: **adding slower GPUs to a synchronous job can reduce its speed.**

---

## The features the A100s switch off

Speed isn't the only mismatch. The two generations don't support the same things.

**FP8.** The H100 datasheet lists FP8 Tensor Core performance (1,979 TFLOPS dense). The A100 datasheet has no FP8 row at all; its lowest floating-point Tensor Core formats are BF16 and FP16. Training recipes that use FP8 on Hopper can't use it on Ampere. A single run spanning both has to drop to a format both support, giving up the H100's biggest speed lever.

**Interconnect inside the node.** A100 systems use NVLink at 600 GB/s per GPU, H100 systems 900 GB/s. Collective operations that span both kinds of node run at the pace of the slower links, plus whatever network connects the two groups.

**Memory size, if the models differ.** Both GPUs in the table have 80 GB, so that pairing is fine. Mix an 80 GB H100 with a 40 GB A100 and the smaller memory caps the per-GPU batch for everyone, or crashes the ranks that run out first.

**Software paths.** Kernels, libraries and container images are often built and tuned per architecture. A mixed job needs one software stack that runs correctly, and ideally fast, on both. That's more testing for every upgrade, forever.

---

## Can you rebalance the work?

The obvious fix: give the H100s more of the batch, about 3× as many samples per step, so everyone finishes together.

It's possible. It's also your problem to build and maintain:

- The data loading has to hand out uneven shares and keep them balanced as speeds drift.
- Gradients from uneven shares must be weighted correctly, or the training math changes.
- The right ratio depends on the model, sequence length and precision, so it has to be measured, not guessed.
- Memory limits still apply: a larger share on the H100s must still fit in 80 GB.

Teams that try this usually discover that the engineering time costs more than the A100s were worth to the job. Rebalancing is a research project, not a scheduler setting.

---

## The queue tax: what co-scheduling costs

Even with a perfect workload, heterogeneous jobs pay a price in the queue. Every item below is from Slurm's heterogeneous-jobs documentation.

**All components start together, or none do.** Each component might be able to start at a different time on its own. A heterogeneous job waits until **every** component can start at once. The more components, and the busier each partition, the longer that wait.

**Only the backfill scheduler can start them.** The docs say the more frequently executed main scheduling logic works first-in, first-out and can't schedule all components together, so heterogeneous jobs are left entirely to the backfill scheduler. Their pending reason isn't even set until a backfill pass has looked at them.

**Backfill makes simplifying assumptions.** It typically needs to be able to place each component on a different node to begin the allocation, even if components could actually share a node.

**You can starve yourself.** With overlapping partitions, an early component can grab nodes that a later component needed. The docs give an example: partition `p1` has 10 nodes and `p2` uses 5 of the same nodes. Ask for 5 nodes in each, and the scheduler may hand some `p2` nodes to the first component, leaving a job that can never start.

**Limits count every component.** Each component counts as a "job" for resource limits. The docs' example: a user limited to 2 running jobs submits a 3-component heterogeneous job, which "will have an adverse effect upon scheduling other jobs."

**Some features don't come along.** From the limitations list:

| Not available | Detail |
|---------------|--------|
| Job arrays | Arrays of heterogeneous jobs aren't supported |
| Licenses on later components | License requests only on the first component |
| Gang scheduling | Not supported |
| Moving between federated clusters | The whole job runs on the submitting cluster |
| Magnetic reservations | Won't attract a heterogeneous job unless it names the reservation |
| Cancelling one pending component | Only the whole job can be cancelled while pending |
| Requeue, suspend, resume per component | Leader only, applies to all |

None of this means the feature is broken. It means co-scheduling is a hard problem, and Slurm makes you pay for it in queue time and flexibility.

---

## So is it "not functional"?

Here's the honest scorecard:

| Claim | Verdict |
|-------|---------|
| "Slurm can't allocate H100s and A100s to one job." | **False.** Heterogeneous jobs, constraint counts, and even a stray `\|` all do it |
| "The heterogeneous-jobs feature doesn't work." | **False.** It schedules and launches as documented, with documented limits |
| "One synchronous training run across H100s and A100s is a bad deal." | **True, usually.** It runs at A100 pace and loses H100-only features |
| "Heterogeneous jobs cost extra queue time and flexibility." | **True.** Co-scheduling, backfill only, no arrays, limits per component |

So the precise way to say it: **Slurm's mixed allocation is functional; tightly coupled training on mixed GPUs usually isn't worth it.** The feature works. The rowing boat doesn't.

**Takeaway:** in a synchronous job every GPU waits for the slowest one, so 8 H100s plus 8 A100s train like 16 A100s, often slower than the 8 H100s alone, and co-scheduling adds a queue tax on top.

So if mixing H100s and A100s in one training run is usually a bad idea, why did SchedMD build heterogeneous jobs at all? Because the boat was never the point. [Part 3](/fields/schedulers/slurm-mixed-gpus/where-hetjobs-shine.md) shows the workloads where different hardware for different parts is exactly right.

### References
- [Slurm: Heterogeneous Job Support (limitations, scheduling, system administrator information)](https://slurm.schedmd.com/heterogeneous_jobs.html)
- [NVIDIA H100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/h100/)
- [NVIDIA A100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/a100/)