# Schedulers: The Traffic Controller Nobody Thanks Until It Breaks

> **Directory index for `schedulers/`.** Everything in here assumes you already know *what* a scheduler is in the abstract — this is the "here's the actual landscape, here's how the pieces fit, here's what to read next" primer.

## Table of Contents
- [Schedulers: The Traffic Controller Nobody Thanks Until It Breaks](#schedulers-the-traffic-controller-nobody-thanks-until-it-breaks)
  - [Table of Contents](#table-of-contents)
  - [What a scheduler actually does](#what-a-scheduler-actually-does)
  - [Two very different meanings of "scheduler"](#two-very-different-meanings-of-scheduler)
  - [The job-scheduler landscape](#the-job-scheduler-landscape)
  - [The core concepts every scheduler shares](#the-core-concepts-every-scheduler-shares)
  - [Why Slurm, specifically](#why-slurm-specifically)
  - [The Slurm architecture, at a glance](#the-slurm-architecture-at-a-glance)
  - [Where to go from here](#where-to-go-from-here)

---

## What a scheduler actually does

Strip away the vendor-specific jargon and every scheduler — whether it's managing a single CPU or a 10,000-node cluster — is solving the same problem:

> **Given limited resources and competing demands for them, decide who runs, where, and when.**

That's it. Everything else — priority queues, fairshare, backfilling, cgroups, reservations — exists to answer that one question well, fairly, and without anyone having to babysit it manually.

## Two very different meanings of "scheduler"

This word gets overloaded constantly, and it's worth separating the two meanings cleanly before going further — because they operate at completely different timescales and solve completely different problems.

| | **OS Process Scheduler** | **HPC/Cluster Job Scheduler** |
|---|---|---|
| **Lives inside** | The Linux kernel (e.g. CFS — Completely Fair Scheduler) | A separate daemon layered on top of many machines (Slurm, PBS, LSF...) |
| **Decides** | Which thread runs on which CPU core, *right now*, for a few milliseconds at a time | Which multi-hour/multi-day job runs on which set of nodes, potentially hours or days from now |
| **Timescale** | Microseconds–milliseconds | Minutes–days |
| **Unit of work** | A thread or process | A job (which itself spawns many processes/threads) |
| **Visibility** | Invisible to the end user — it just happens | Extremely visible — users wait in a queue and watch it happen |

**This directory is about the second kind** — cluster/workload managers, with Slurm as the primary subject, since that's what the majority of production HPC and AI-training clusters run today. The OS-level scheduler still matters (it's *why* CPU affinity and NUMA binding are worth caring about — see the [parallel execution & affinity guide](../parallel-execution-affinity-blog.md) in the benchmarks series), but it's not what `schedulers/` is documenting.

---

## The job-scheduler landscape

Slurm isn't the only option, and it helps to know what else is out there — both to understand *why* Slurm won the default-choice war on most modern clusters, and because you'll inevitably run into the others on legacy systems, vendor documentation, or job-portability discussions.

| Scheduler | Origin | Where you'll still find it | Notable trait |
|---|---|---|---|
| **Slurm** | Open source, SchedMD | Most modern academic & national HPC centers, most GPU/AI training clusters | Plugin-based, scales to the largest systems on TOP500, the closest thing to a current default |
| **PBS / PBS Pro / OpenPBS** | Originally NASA-developed | Many legacy HPC centers, some commercial HPC | Mature, well-documented, still common in industry HPC (aerospace, oil & gas) |
| **LSF (Load Sharing Facility)** | IBM | Enterprise & pharma/life-sciences HPC | Strong commercial support, heavy enterprise integration features |
| **SGE / Grid Engine** (and descendants like UGE) | Sun Microsystems → various forks | Older academic clusters, some bioinformatics shops | Historically very common before Slurm's rise |
| **Kubernetes schedulers** (kube-scheduler, Volcano, Kueue) | Cloud-native ecosystem | Increasingly common for containerized ML training workloads | Built for elastic, container-first workloads rather than batch HPC jobs |
| **HTCondor** | University of Wisconsin–Madison | High-throughput (many small/independent jobs) computing, grid computing | Optimized for opportunistic, loosely-coupled workloads rather than tightly-coupled MPI jobs |

> [!TIP]
> If you're moving between sites or reading someone else's job scripts, the *concepts* below translate almost directly across all of these — only the command names and config file syntax change (`sbatch` ↔ `qsub` ↔ `bsub`, `squeue` ↔ `qstat` ↔ `bjobs`, and so on).

---

## The core concepts every scheduler shares

Regardless of which tool sits on top, these ideas show up everywhere — learn them once, and every scheduler's documentation gets easier to read:

- **Queue / Partition** — a logical pool of nodes with shared limits (max walltime, max job size, which users can submit). Slurm calls these *partitions*; PBS and others usually call them *queues*.
- **Job** — a request for resources (`N` nodes, `M` cores, `T` time) plus something to run once those resources are granted.
- **Priority & Fairshare** — the algorithm deciding *whose* queued job runs next. Fairshare specifically balances priority against how much of the cluster a user/group has already consumed recently, so heavy recent users don't perpetually crowd out lighter ones.
- **Backfill scheduling** — letting *smaller* jobs jump ahead in the queue and fill idle gaps, as long as doing so doesn't delay the start time already promised to a larger, higher-priority job waiting for enough nodes to free up. This is why a tiny job sometimes starts before a big one that's been queued longer — it's not favoritism, it's gap-filling.
- **Reservations** — blocking off nodes for a specific purpose (maintenance, a guaranteed-start job, a demo) ahead of time, bypassing normal queue ordering for that block.
- **Node health checking** — automated pre/post-job verification that a node is actually healthy (memory, GPUs, filesystem mounts, network) before the scheduler trusts it with real work. NHC is the common open-source tool for this on Slurm clusters.
- **Accounting / cgroup containment** — tracking and *enforcing* what a job actually consumes, not just what it requested — this is exactly the gap [`pam_slurm_adopt`](./slurm-pam-adopt-blog.md) closes for SSH sessions that would otherwise slip outside this accounting entirely.

---

## Why Slurm, specifically

A few reasons Slurm has become the default choice for new HPC and AI-training clusters, in rough order of practical impact:

1. **Open source, no licensing cost** — a real factor at scale, where commercial per-node licensing adds up fast.
2. **Plugin architecture** — cgroups, PAM integration, accounting backends (like `slurmdbd` + MariaDB), health checks, and GPU/topology-aware scheduling are all pluggable rather than bolted on.
3. **Proven at the largest scales** — it's what a large share of TOP500 systems run, which means the rough edges at extreme scale have mostly already been found and fixed by someone else.
4. **First-class GPU/accelerator awareness** — `--gres`, `--gpu-bind`, and topology-aware placement make it a natural fit for the GPU-dense clusters most new HPC and AI infrastructure is built around today.

---

## The Slurm architecture, at a glance

Every post in this directory assumes familiarity with this shape — worth internalizing once:

```
                    ┌─────────────────────┐
                    │      slurmdbd         │   ← accounting database daemon
                    │  (talks to MariaDB)   │      (fairshare history, job records)
                    └──────────┬────────────┘
                               │
                    ┌──────────▼────────────┐
                    │      slurmctld         │   ← the controller / brain
                    │  (scheduling decisions,│      one per cluster (+ optional
                    │   partition state)     │      backup controller)
                    └──────────┬────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
      ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
      │    slurmd       │ │    slurmd       │ │    slurmd       │   ← one per compute
      │  compute node 1 │ │  compute node 2 │ │  compute node N │      node; actually
      └───────────────┘ └───────────────┘ └───────────────┘      launches/contains jobs
```

- **`slurmctld`** — the decision-maker. Tracks partition/node state, runs the scheduling algorithm, decides what runs where and when.
- **`slurmdbd`** — the memory. Persists accounting data (who ran what, for how long, using how much) to a database, which is what fairshare calculations and usage reporting draw from.
- **`slurmd`** — the muscle. Runs on every compute node, actually launches job steps, and (with `task/cgroup` + `PrologFlags=contain` enabled) enforces resource containment — including adopting SSH sessions via `pam_slurm_adopt`.

Every operational task you'll do — a rolling reboot, a security hardening pass, a Slurm version upgrade — ultimately comes down to safely coordinating these three roles without letting them get out of sync with each other.

---

## Where to go from here

- New to Slurm entirely? Start with the [official Slurm quickstart](https://slurm.schedmd.com/quickstart.html) for the user-facing side (`sbatch`, `srun`, `squeue`) before diving into the admin-focused posts here.
- Already running a cluster and hardening it? Start with [`slurm-pam-adopt-blog.md`](./slurm-pam-adopt-blog.md) — it's a small config change that closes a real, commonly-overlooked gap.
- Planning your next maintenance window? [`slurm-reboot-order-blog.md`](./slurm-reboot-order-blog.md) is the checklist to have open in a second tab while you work.
- Wondering how scheduler decisions (rank placement, node allocation) connect to the performance numbers you actually measure? That's where this directory hands off to the [benchmarks series](../hpc-benchmarking-master-guide.md) — specifically the [parallel execution & affinity guide](../parallel-execution-affinity-blog.md), which picks up exactly where Slurm's node allocation leaves off.