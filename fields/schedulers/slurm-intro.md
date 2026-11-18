<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/schedulers/">Schedulers</a></nav>

# Schedulers: The Traffic Controller Nobody Thanks Until It Breaks

<!-- related-block -->
<div class="reading-time">Beginner · Concept · 10 min read · Updated 17 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/hpc">hpc</a> <a class="chip" href="#/.docs/generated/explore/tags/slurm">slurm</a></div>
<!-- related-block -->
<div class="related-strip">

**Read next:** [The Tale of a Slurm Job Script: Submission Is a Commitment, Not a Promise](/fields/schedulers/slurm-inside-a-job/slurm-job-script-tale.md)

</div>


> **Directory index for `schedulers/`.** Everything in here assumes you already know *what* a scheduler is in the abstract — this is the "here's the actual landscape, here's how the pieces fit, here's what to read next" primer.


## What a scheduler actually does

Strip away the vendor-specific jargon and every scheduler — whether it's managing a single [CPU](/references/glossary?id=cpu "Central Processing Unit") or a 10,000-node cluster — is solving the same problem:

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

**This directory is about the second kind** — cluster/workload managers, with Slurm as the primary subject, since that's what the majority of production [HPC](/references/glossary?id=hpc "High-Performance Computing") and AI-training clusters run today. The OS-level scheduler still matters (it's *why* CPU affinity and [NUMA](/references/glossary?id=numa "Non-Uniform Memory Access") binding are worth caring about — see the [parallel execution & affinity guide](/fields/benchmarks/parallel-execution-affinity-master-guide.md) in the benchmarks series), but it's not what `schedulers/` is documenting.

---

## The job-scheduler landscape

Slurm isn't the only option, and it helps to know what else is out there — both to understand *why* Slurm won the default-choice war on most modern clusters, and because you'll inevitably run into the others on legacy systems, vendor documentation, or job-portability discussions.

| Scheduler | Origin | Where you'll still find it | Notable trait |
|---|---|---|---|
| **Slurm** | Open source, SchedMD | Most modern academic & national HPC centers, most GPU/AI training clusters | Plugin-based, scales to the largest systems on TOP500, the closest thing to a current default |
| **PBS / PBS Pro / OpenPBS** | Originally NASA-developed | Many legacy HPC centers, some commercial HPC | Mature, well-documented, still common in industry HPC (aerospace, oil & gas) |
| **LSF (Load Sharing Facility)** | IBM | Enterprise & pharma/life-sciences HPC | Strong commercial support, heavy enterprise integration features |
| **SGE / Grid Engine** (and descendants like UGE) | Sun Microsystems → various forks | Older academic clusters, some bioinformatics shops | Historically very common before Slurm's rise |
| **Kubernetes schedulers** (kube-scheduler, Volcano, Kueue) | Cloud-native ecosystem | Increasingly common for containerized ML training workloads | Built for elastic, container-first workloads rather than batch HPC jobs — see [isolating GPU workloads](/fields/devops/kubernetes/isolating-gpu-workloads.md) for how the two compare |
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
- **Preemption** — letting an urgent job evict a running, lower-priority one: the victim is cancelled, suspended, or put back in the queue (*requeued*) to start again later. It is off by default in Slurm. [Dying Politely](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md) covers what the victim must do to survive it.
- **Reservations** — blocking off nodes for a specific purpose (maintenance, a guaranteed-start job, a demo) ahead of time, bypassing normal queue ordering for that block. [Calling Dibs on Nodes](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md) shows how it works in Slurm, including what happens to jobs that are running when the window opens.
- **Node health checking** — automated pre/post-job verification that a node is actually healthy (memory, GPUs, filesystem mounts, network) before the scheduler trusts it with real work. [NHC](/references/glossary?id=nhc "Node Health Check") is the common open-source tool for this on Slurm clusters.
- **Accounting / cgroup containment** — tracking and *enforcing* what a job actually consumes, not just what it requested — this is exactly the gap [`pam_slurm_adopt`](/fields/schedulers/slurm-cluster-operations/slurm-pam-adopt-ssh-access.md) closes for [SSH](/references/glossary?id=ssh "Secure Shell") sessions that would otherwise slip outside this accounting entirely.

---

## Why Slurm, specifically

A few reasons Slurm has become the default choice for new HPC and AI-training clusters, in rough order of practical impact:

1. **Open source, no licensing cost** — a real factor at scale, where commercial per-node licensing adds up fast.
2. **Plugin architecture** — cgroups, PAM integration, accounting backends (like `slurmdbd` + MariaDB), health checks, and [GPU](/references/glossary?id=gpu "Graphics Processing Unit")/topology-aware scheduling are all pluggable rather than bolted on.
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

- **`slurmctld`** — the decision-maker. Tracks partition/node state, runs the scheduling algorithm, decides what runs where and when — and *enforces* account limits, when `AccountingStorageEnforce` tells it to.
- **`slurmdbd`** — the memory. Persists accounting data (who ran what, for how long, using how much) plus accounts, limits and QOS definitions to a database, which is what fairshare calculations and usage reporting draw from.
- **`slurmd`** — the muscle. Runs on every compute node, actually launches job steps, and (with `task/cgroup` + `PrologFlags=contain` enabled) enforces resource containment — including adopting SSH sessions via `pam_slurm_adopt` (which also needs `pam_systemd` out of the way).
- **`sacctmgr`** and friends (`sacct`, `sreport`) — not daemons, but command-line clients that read and write accounting data *through* `slurmdbd`. All of this traffic is authenticated with **MUNGE**.

Every operational task you'll do — a rolling reboot, a security hardening pass, a Slurm version upgrade — ultimately comes down to safely coordinating these roles without letting them get out of sync with each other.

> [!NOTE]
> "`slurmdbd` stores the limits" and "`slurmdbd` enforces the limits" are different claims, and only the first is true. See [Slurm multi-tenancy: who stores the rules, who enforces them](/fields/schedulers/slurm-accounting-multi-tenancy.md).

---

## Where to go from here

- New to Slurm entirely? Start with the [official Slurm quickstart](https://slurm.schedmd.com/quickstart.html) for the user-facing side (`sbatch`, `srun`, `squeue`) before diving into the admin-focused posts here.
- Sharing a cluster between teams? [Slurm multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md) covers associations, limits, QOS and fairshare — and the one missing `slurm.conf` line that makes limits do nothing.
- Running more than one GPU generation? [Mixing GPU types in Slurm](/fields/schedulers/slurm-mixed-gpus/README.md) explains heterogeneous jobs, the bare-`|` constraint trap, and why mixed training disappoints.
- Users asking why their job won't start? [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md) reads the reason column, opens up the priority number, and finds the limits that make jobs wait forever.
- Running GPU training? [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md) covers topology-aware placement, launching PyTorch across nodes, containers with Pyxis, GPU health checks and metrics, with a [lab cheatsheet](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md) to build your own test cluster.
- Already running a cluster and hardening it? Start with [pam_slurm_adopt](/fields/schedulers/slurm-cluster-operations/slurm-pam-adopt-ssh-access.md) — it's a small config change that closes a real, commonly-overlooked gap.
- Planning your next maintenance window? [the reboot order](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md) is the checklist to have open in a second tab while you work.
- Want urgent jobs to bump low-priority ones, and the bumped ones to restart? [The Guest List](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md) sets up QOS preemption, [The Receptionist Who Rewrites Your Badge](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) adds a Lua submit script that routes jobs for you, and [Who Gets Told What](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md) lists every signal a job receives and who hears it.
- Planning to upgrade from an older Slurm? [The Changelog Nobody Reads](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md) collects what changed between 23.11 and 26.05, with the security-fix timeline.
- Want to know the cluster still works after a change? [Slurm Smoke Tests](/fields/schedulers/slurm-smoke-tests/README.md) is a six-part series of tested checks for the control plane, config changes, upgrades, policy and nodes.
- A job vanished and nobody knows why? [Autopsy of a Job](/fields/schedulers/slurm-sacct-job-forensics.md) reads the record `sacct` keeps of how it ended.
- Curious what a single job actually goes through? [The job-script tale](/fields/schedulers/slurm-inside-a-job/slurm-job-script-tale.md) follows one script from `sbatch` to exit, and [slurmstepd](/fields/schedulers/slurm-inside-a-job/slurm-slurmstepd.md) explains the process that babysits it on the node.
- Wondering how scheduler decisions (rank placement, node allocation) connect to the performance numbers you actually measure? That's where this directory hands off to the [benchmarks series](/fields/benchmarks/benchmarking-guide.md) — specifically the [parallel execution & affinity guide](/fields/benchmarks/parallel-execution-affinity-master-guide.md), which picks up exactly where Slurm's node allocation leaves off.

---

## References

- [Slurm Quick Start User Guide](https://slurm.schedmd.com/quickstart.html): commands and the daemon architecture.
- [Slurm Quick Start Administrator Guide](https://slurm.schedmd.com/quickstart_admin.html): slurmctld, slurmd, slurmdbd and how they're configured.
- [Slurm overview](https://slurm.schedmd.com/overview.html): what Slurm does and its plugin design.
- [Slurm accounting](https://slurm.schedmd.com/accounting.html): slurmdbd, sacctmgr and `AccountingStorageEnforce`.
- [MUNGE](https://github.com/dun/munge): the authentication service the daemons use.

<!-- related-block -->
<div class="see-also">

**See also**

- [slurmstepd: The Small Daemon That Actually Runs Your Job](/fields/schedulers/slurm-inside-a-job/slurm-slurmstepd.md) — slurmstepd (1/step/node) bridges slurmd's fork and task start. Jobs survive slurmd restarts via SlurmdSpoolDir sockets. Covers how to find, count, and read stepds on busy nodes.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Autopsy of a Job: Reading sacct Like a Coroner](/fields/schedulers/slurm-sacct-job-forensics.md) — How to find out what happened to a job that has gone, with sacct states, exit codes (exit:signal), requeued runs, useful fields, and the neighbors scontrol, sstat and sreport.
- [Backfill Tuning: The Planner That Can Only See One Day Ahead](/fields/schedulers/slurm-backfill-tuning.md) — Slurm backfill relies on accurate time limits. A 1-day bf_window hides 7-day jobs, causing squeue drift. Use sdiag to tune bf_window, bf_resolution, bf_max_job_test, and bf_max_time.
- [Calling Dibs on Nodes: Reservations, Maintenance Windows and the Job That Fit](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md) — How to block nodes ahead of time with scontrol reservations, what happens to jobs that fit before the window and jobs that do not, and what users see while it is open.
- [Core AI Infrastructure Concepts: A Map](/business/hpc-industry/ai-infrastructure-core-concepts.md) — Six concepts every AI-infrastructure engineer gets asked about, each fact-checked with a 30-second answer and a pointer to where to go deeper.
- [Dying Politely: Preemption, Requeue and the Signals Your Training Job Ignores](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md) — How Slurm preemption modes differ, what GraceTime and --signal send and to whom, why a bash trap never fires while the trainer runs, and a requeue-safe checkpoint wrapper that cannot loop.
- [Kill Task Failed: A Murder Mystery With No Body (and One Drained Node)](/fields/schedulers/slurm-cluster-operations/slurm-kill-task-failed.md) — Slurm job death (SIGTERM, KillWait, SIGKILL) fails on uninterruptible sleep, draining nodes. Raising timeouts rarely helps. Debug these with UnkillableStepProgram.
- [Slurm cgroups in Practice: What Gets Constrained, and Where the Numbers Lie](/fields/schedulers/slurm-inside-a-job/slurm-cgroups-in-practice.md) — Which cgroup.conf switches actually fence a Slurm job, why every one of them defaults to off, how v1 and v2 differ, and why sacct's memory numbers are samples and not measurements.
- [Slurm Multi-Tenancy: Who Stores the Rules, Who Enforces Them](/fields/schedulers/slurm-accounting-multi-tenancy.md) — How slurmctld, slurmd, slurmdbd and sacctmgr split the work of multi-tenant accounting, why limits you set can silently do nothing, and how associations, TRES limits, QOS and fairshare fit together.
- and 9 more

</div>
