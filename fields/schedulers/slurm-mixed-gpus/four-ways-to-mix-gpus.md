
# Four Ways to Ask Slurm for Mixed GPUs

<!-- related-block -->
<div class="reading-time">9 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read next:** [Why Mixed-GPU Training Disappoints](/fields/schedulers/slurm-mixed-gpus/why-mixed-training-disappoints.md)

</div>


> **Part 1 of the [Mixing GPU Types in Slurm series](/fields/schedulers/slurm-mixed-gpus/README.md).** Slurm doesn't have one way to give a job different GPUs. It has four, and they behave very differently. By the end of this page you'll know what each one allocates, which one to reach for, and why a single `|` in a constraint has quietly mixed GPU types on more clusters than any heterogeneous job ever has.

## Table of Contents
- [Four Ways to Ask Slurm for Mixed GPUs](#four-ways-to-ask-slurm-for-mixed-gpus)
  - [Table of Contents](#table-of-contents)
  - [The job that started fast and ran slow](#the-job-that-started-fast-and-ran-slow)
  - [First, how Slurm knows a GPU's type](#first-how-slurm-knows-a-gpus-type)
  - [Way 1: typed GRES, one kind per request](#way-1-typed-gres-one-kind-per-request)
  - [Way 2: constraints, and the trap in the bar](#way-2-constraints-and-the-trap-in-the-bar)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [Way 3: heterogeneous jobs, the real thing](#way-3-heterogeneous-jobs-the-real-thing)
  - [Way 4: heterogeneous steps, mixing inside one allocation](#way-4-heterogeneous-steps-mixing-inside-one-allocation)
  - [The four ways side by side](#the-four-ways-side-by-side)
    - [References](#references)

---

## The job that started fast and ran slow

A researcher needs 16 GPUs for a training run. The H100 partition has a two-day queue. The A100 nodes are busy too. So she gets clever and writes:

```bash
#SBATCH --nodes=4
#SBATCH --gres=gpu:4
#SBATCH --constraint="h100|a100"
```

"Either kind is fine," she thinks. The job starts in twenty minutes. She goes for lunch feeling smart.

When she comes back, the loss curve is crawling. `squeue` shows the job is running on two H100 nodes and two A100 nodes. Slurm did exactly what she asked: give me nodes that have H100s *or* A100s. It never promised they'd all be the same.

She didn't submit a "heterogeneous job." She doesn't know the term. She mixed GPU types with one character.

That's the first lesson of this series: **mixed allocations happen by accident far more often than on purpose.** To see why, start with how Slurm tells GPUs apart at all.

---

## First, how Slurm knows a GPU's type

Slurm describes GPUs as **GRES** (generic resources). An admin can give each GPU a **type**, either in `gres.conf` or by letting Slurm detect it through NVML. With autodetection, Slurm matches the type you configure against the GPU's reported name, and any substring works: the GRES docs show a GPU detected as `geforce_rtx_2060` that can be typed as `geforce`, `rtx` or `2060`.

Admins can also tag nodes with **features**, free-form labels like `h100` or `a100` that jobs match with `--constraint`.

So there are two separate labeling systems:

| Label | Lives on | Requested with | Answers |
|-------|----------|----------------|---------|
| GRES type | Each GPU | `--gres=gpu:h100:4`, `--gpus=h100:8` | "Which GPUs inside the node?" |
| Feature | Each node | `--constraint=h100` | "Which nodes?" |

Every way of mixing GPUs uses one or both. Here they are, from the most common to the most deliberate.

---

## Way 1: typed GRES, one kind per request

The everyday request names a type and a count:

```bash
#SBATCH --gres=gpu:h100:4     # 4 H100s on every node of the job
```

The GRES docs define the form as `name[:type:count]` for `--gres` and `[type]:count` for the `--gpu*` options. One detail matters a lot here: **`--gres` is per node.** It asks for the same thing on every node in the job.

That gives one legitimate way to get two types: a node that physically contains both. The GRES docs' own example configures nodes with `Gres=gpu:tesla:2,gpu:kepler:2`, two kinds of GPU in one chassis. On nodes like that, a job can ask for some of each. Data-center GPU servers are rarely built that way, so for A100-plus-H100 this is mostly a curiosity.

Another rule from the same docs: **typed and untyped requests must be consistent within a job.** If the allocation asked for `--gres=gpu:2`, a step can't then ask for `--gres=gpu:tesla:2`, and vice versa.

So a single, uniform per-node request can't say "H100s on these nodes, A100s on those." For that you need different nodes to be treated differently, which is where constraints come in.

---

## Way 2: constraints, and the trap in the bar

`--constraint` filters nodes by feature. The `sbatch` man page lists several operators, and the difference between two of them is the whole story of the researcher's lost afternoon.

| Operator | Example | Means |
|----------|---------|-------|
| AND | `--constraint="intel&gpu"` | Every node has both features |
| **OR** | `--constraint="h100\|a100"` | Every node has **at least one** of them. Different nodes can have different ones |
| **Matching OR** | `--constraint="[h100\|a100]"` | **All** nodes have the **same** one, but either is fine |
| Multiple counts | `--constraint="[h100*2&a100*2]"` | Exactly 2 nodes with `h100` and 2 with `a100` |

Read the second and third rows twice. They differ by a pair of square brackets.

- **Plain OR** is an *accidental mixer*. In a multi-node job it can hand you a blend. That's what happened to the researcher.
- **Matching OR** is what she meant: "give me whichever kind starts first, but don't mix." The man page's own example is `[rack1|rack2|rack3|rack4]`: all nodes on one rack, any rack.
- **Multiple counts** is a *deliberate mixer*. You say exactly how many nodes of each feature you want. Combined with an untyped GPU request like `--gres=gpu:4`, every node gets 4 GPUs, of whatever kind that node has.

A SchedMD engineer, discussing the feature-parsing code, described square-bracket counts as "essentially the same as a heterogeneous job." That's a good way to think of it: a lightweight version, where every node still gets the same per-node request.

> [!WARNING]
> **Audit your users' constraints.** On any cluster with more than one GPU generation, search job scripts for `--constraint` with a bare `|` and no brackets. Every multi-node job using it can land on mixed hardware, and the user probably doesn't know.

---

## Try it before you scroll

☕ Three requests. For each, could the job end up with both H100 and A100 nodes?

1. `--nodes=4 --gres=gpu:4 --constraint="[h100|a100]"`
2. `--nodes=4 --gres=gpu:h100:4`
3. `--nodes=4 --gres=gpu:4 --constraint="h100|a100"`

Answers: (1) no, matching OR keeps all nodes the same; (2) no, every node must have 4 H100s; (3) yes, plain OR allows a mix. If you got all three, you already understand constraints better than most job scripts on most clusters.

Now for the feature that was actually built for mixing.

---

## Way 3: heterogeneous jobs, the real thing

A **heterogeneous job** is a job made of several **components**, each with its own full set of options. Slurm's docs say each component has "virtually all job options available including partition, account and QOS." You separate components with `:` on the command line, or with `#SBATCH hetjob` lines in a script:

```bash
#!/bin/bash
#SBATCH --nodes=2 --gres=gpu:h100:8 --partition=h100
#SBATCH hetjob
#SBATCH --nodes=2 --gres=gpu:a100:8 --partition=a100

srun --het-group=0 ./trainer &
srun --het-group=1 ./rollout_worker &
wait
```

Here's what you get, all from the heterogeneous-jobs documentation:

- **Separate job IDs, one family.** Each component gets its own `job_id`; they share a `het_job_id` equal to the first component's ID. `squeue` shows them as `123+0`, `123+1`.
- **Started together.** Components are scheduled at the same time or not at all.
- **The script runs once,** on the first node of component 0.
- **`srun` launches on component 0 by default.** `--het-group` chooses others.
- **Per-component environment.** Variables get a `_HET_GROUP_<n>` suffix, like `SLURM_JOB_NODELIST_HET_GROUP_1`.
- **One MPI world, if you want it.** `srun prog0 : prog1` puts both components in a single `MPI_COMM_WORLD` with non-overlapping ranks. Separate `srun` calls give separate worlds.

The docs add two warnings about that last point, in capitals: running one application across components **doesn't work with all MPI implementations or Slurm MPI plugins**, and `mpirun` "would require substantial modification" to support it, with no such work known to SchedMD. Admins can switch cross-component steps off entirely with `SchedulerParameters=disable_hetjob_steps`.

So heterogeneous jobs really do allocate H100s and A100s to one job, cleanly, with each part sized independently. "Can't" is wrong. But notice the shape of the example: the H100s and A100s run **different programs**. Keep that in mind; it's the key to part 3.

---

## Way 4: heterogeneous steps, mixing inside one allocation

Since **Slurm 20.11**, you can also do the reverse: get one ordinary allocation, then launch a single step with different layouts on different nodes, using the same `:` syntax with `srun`. The docs' example takes two exclusive nodes with 10 GPUs and gives one step 4 tasks with 4 GPUs on one node and 1 task with 6 GPUs on the other.

Two limits from the docs: the step components **must run on unique nodes**, and you **can't request heterogeneous steps from within a heterogeneous job**.

Useful when the allocation is uniform but the work isn't, for example one process that wants a whole node's GPUs and several that want one each.

---

## The four ways side by side

| Way | Syntax | Mixes types? | On purpose? | Best for |
|-----|--------|-------------|-------------|----------|
| Typed GRES | `--gres=gpu:h100:4` | Only on nodes that contain both | Yes | Asking for one specific kind |
| Constraint, plain OR | `-C "h100\|a100"` | **Yes, possibly** | Usually **not** | Single-node jobs only |
| Constraint, matching OR | `-C "[h100\|a100]"` | No | Yes | "Either kind, whichever starts first" |
| Constraint, counts | `-C "[h100*2&a100*2]"` | Yes, exact node counts | Yes | Simple splits with the same per-node request |
| Heterogeneous job | `... : ...` / `#SBATCH hetjob` | Yes, fully independent parts | Yes | Different programs on different hardware |
| Heterogeneous step | `srun ... : ...` in one allocation | Layout only (same allocation) | Yes | Uneven work inside a uniform allocation |

**Takeaway:** Slurm can absolutely give one job H100s and A100s, deliberately with heterogeneous jobs or constraint counts, and accidentally with a bare `|`, so learn the brackets and audit for the bar.

So it works. Then why does everyone who tries to *train* across H100s and A100s come back disappointed? That's [part 2](/fields/schedulers/slurm-mixed-gpus/why-mixed-training-disappoints.md).

### References
- [Slurm: Heterogeneous Job Support](https://slurm.schedmd.com/heterogeneous_jobs.html)
- [Slurm: Generic Resource (GRES) Scheduling](https://slurm.schedmd.com/gres.html)
- [Slurm `sbatch` man page, `--constraint` operators (mirror of the official man page)](https://manpages.org/sbatch)
- [SchedMD ticket 12286: constraint operators and square-bracket counts](https://support.schedmd.com/show_bug.cgi?id=12286)