---
id: slurm-cgroups-in-practice
title: "Slurm cgroups in Practice: What Gets Constrained, and Where the Numbers Lie"
order: 4
sidebar_label: Slurm cgroups in practice
summary: Which cgroup.conf switches actually fence a Slurm job, why every one of them defaults to off, how v1 and v2 differ, and why sacct's memory numbers are samples and not measurements.
level: intermediate
type: concept
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
  - gpu
relations:
  related:
    - slurm-pam-adopt-ssh-access
    - slurm-accounting-multi-tenancy
---

# Slurm cgroups in Practice: What Gets Constrained, and Where the Numbers Lie

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** The intro says `slurmd` "enforces resource containment" with `task/cgroup`. This page opens that sentence up: what exactly is fenced, what is not, and how to check which one you have. Commands and option names come from SchedMD's documentation for Slurm 26.05. They were not run on a live cluster for this page, so try them on a test node first.

## Table of Contents

- [Slurm cgroups in Practice: What Gets Constrained, and Where the Numbers Lie](#slurm-cgroups-in-practice-what-gets-constrained-and-where-the-numbers-lie)
  - [Table of Contents](#table-of-contents)
  - [The eight-GPU job that could see eight GPUs](#the-eight-gpu-job-that-could-see-eight-gpus)
  - [One switchboard, two files](#one-switchboard-two-files)
  - [cgroup v1 or v2: check before you debug](#cgroup-v1-or-v2-check-before-you-debug)
  - [Memory: two killers, pick one](#memory-two-killers-pick-one)
  - [Where the numbers lie](#where-the-numbers-lie)
  - [systemd and the scope nobody sees](#systemd-and-the-scope-nobody-sees)
  - [Verify it in ten minutes](#verify-it-in-ten-minutes)
  - [The mental model to keep](#the-mental-model-to-keep)
  - [References](#references)

* * *

## The eight-GPU job that could see eight GPUs

Picture a node with eight GPUs. A user submits a job with `--gres=gpu:2`. Slurm allocates two, sets `CUDA_VISIBLE_DEVICES` to match, and the training script behaves.

Then someone runs `nvidia-smi` inside the job and sees all eight. A more curious user unsets `CUDA_VISIBLE_DEVICES`, and PyTorch happily opens a GPU that belongs to someone else's job.

Nothing is misconfigured here, at least not by the usual definition. `CUDA_VISIBLE_DEVICES` is a request that the CUDA runtime politely honors. NVML tools such as `nvidia-smi` ignore it. What actually stops a process from touching a device file is the kernel, and the kernel only gets involved if Slurm asks it to. The setting that asks is `ConstrainDevices`, and its documented default is `no`.

That is the whole theme of this page. **Slurm's containment is a set of independent opt-in switches, and the shipped default for each one is off.** A cluster can run `task/cgroup` for years and still leak GPUs, cores or memory, because the plugin being loaded and the constraint being applied are two different things.

* * *

## One switchboard, two files

Two files cooperate. `slurm.conf` loads the plugins. `cgroup.conf` (same directory) decides what they enforce.

| Setting | File | What it does | Default |
|---|---|---|---|
| `ProctrackType=proctrack/cgroup` | `slurm.conf` | Tracks every process in a step, so a cancel reaches all of them | n/a |
| `TaskPlugin=task/cgroup,task/affinity` | `slurm.conf` | Loads the plugin that applies the `Constrain*` switches below | n/a |
| `PrologFlags=Contain` | `slurm.conf` | Creates the "extern" step that [`pam_slurm_adopt`](/fields/schedulers/slurm-pam-adopt-ssh-access.md) needs | off |
| `ConstrainCores` | `cgroup.conf` | Limits a job to its allocated cores (cpuset) | `no` |
| `ConstrainDevices` | `cgroup.conf` | Limits access to GRES devices, meaning GPUs | `no` |
| `ConstrainRAMSpace` | `cgroup.conf` | Sets soft and hard RAM limits from the allocation | `no` |
| `ConstrainSwapSpace` | `cgroup.conf` | Limits swap on top of RAM | `no` |
| `SignalChildrenProcesses` | `cgroup.conf` | Sends signals to all children, not just the parent process of a step | `no` |

Two small prerequisites trip people up:

- Memory constraints do nothing unless `slurm.conf` selects a memory-aware consumable resource mode (a `CR_*_Memory` value in `SelectTypeParameters`).
- SchedMD's example config pairs `task/cgroup` with `task/affinity`. The `ConstrainCores` entry notes that an old hwloc bug can make `task/affinity` necessary for cpuset binding to work properly.

SchedMD's own example `cgroup.conf` turns on cores, devices, RAM and swap together. If your file is shorter than that, it is worth asking which of the four you decided to leave out and why.

> [!NOTE]
> The same example config says nodes should either set `MemSpecLimit` or declare `RealMemory` below the physical total, so the OS and daemons always have memory the jobs cannot take. Compare your node definitions with the output of `slurmd -C`.

* * *

## cgroup v1 or v2: check before you debug

`CgroupPlugin` defaults to `autodetect`, so Slurm picks whichever the node has, and mixed v1/v2 fleets are supported. The v1 plugin is marked deprecated with no new features coming, so any cluster still on v1 has a migration waiting for it.

A quick way to see which one a node runs:

```bash
stat -fc %T /sys/fs/cgroup     # cgroup2fs  -> v2 (unified)
                               # tmpfs      -> v1 (legacy or hybrid)
cat /proc/self/cgroup          # a single line starting with 0:: -> v2
```

Differences that matter in practice:

- **Devices are enforced with eBPF on v2.** The device controller of cgroup v2 is eBPF-based, which is why Slurm's v2 documentation tells you to read up on eBPF before debugging odd GPU-access behavior.
- **Job paths changed in 26.05.** On v2 the job directories used to be named by job ID, as in `/sys/fs/cgroup/system.slice/slurmstepd.scope/job_123/`. In 26.05 they are named with an opaque ID unless you set `CgroupJobIdPaths=yes`. If you run exporters or scripts that find a job's cgroup by number, this is the first thing to check after an upgrade.
- **Resource specialization behaves differently.** With v1, the cores and memory you reserve for the system are also used by `slurmstepd`. With v2, `slurmstepd` is not constrained by that reservation. SchedMD's example is an MPI job whose PMI setup makes `slurmstepd` grow.
- **Debian and Ubuntu** historically ship without the memory and swap controllers enabled. The `cgroup.conf` man page still lists `cgroup_enable=memory swapaccount=1` on the kernel command line for those systems, so check your distro before assuming `ConstrainRAMSpace` is doing anything.

Moving a node from v1 to v2 is a boot-parameter change (the docs list `systemd.unified_cgroup_hierarchy=1 systemd.legacy_systemd_cgroup_controller=0 cgroup_no_v1=all`), but plan it like a maintenance task: it touches every job on the node.

* * *

## Memory: two killers, pick one

Slurm has two separate mechanisms that can kill a job for using too much memory, and they behave very differently.

| | `ConstrainRAMSpace` (cgroup) | `OverMemoryKill` (`JobAcctGatherParams`) |
|---|---|---|
| Who kills | The kernel OOM killer | Slurm, after polling usage |
| What dies | One or more processes in the step | The whole step |
| When | As soon as the cgroup limit is hit | At the next sample |
| Step afterwards | Marked OOM, but may keep running | Killed or cancelled |

Per the man page, with cgroup enforcement the step is flagged as OOM but keeps running, and other processes in it may carry on. For a single-process job that is invisible. For a multi-rank job it can mean one rank dies while the rest sit waiting for it. Whether that shows up as a hang or a clean failure depends on your launcher, so check what your own stack does before the first big run.

There is a middle option for exactly this problem. `TaskPluginParam=OOMKillStep` in `slurm.conf` makes Slurm kill the whole step, on all nodes, when an OOM event hits any task in it. It does not apply to the extern step, and a user can override it. It requires the `task/cgroup` plugin, cgroup v2 and a kernel newer than 4.19. I found it in the Niflheim site documentation, which cites SchedMD ticket 25478, so read the current `slurm.conf` page for the exact wording before enabling it.

SchedMD's release notes and support replies treat the two mechanisms as incompatible: since 18.08 the default is to enforce memory with neither, and the advice is not to combine cgroup enforcement with `OverMemoryKill`. Pick one deliberately.

Three details from the man page that save an afternoon:

- **Soft and hard limits.** `ConstrainRAMSpace` sets the soft limit at the allocation and the hard limit at the allocation times `AllowedRAMSpace` (default 100%). Setting it above 100 can cause system-wide OOM events, because jobs may then take more than the node has.
- **`AllowedSwapSpace=0` does not forbid swapping.** It limits RAM plus swap to the RAM limit. How eagerly the kernel swaps is a separate knob, and `MemorySwappiness` applies only to v1.
- **There is a throughput cost.** The docs warn that `ConstrainRAMSpace` can noticeably reduce per-node job throughput, so high-throughput sites have a real trade-off to weigh.

When an OOM kill does happen, the kernel logs it. `dmesg` or the journal on the node will say so, and `sacct` should report the state as `OUT_OF_MEMORY`.

* * *

## Where the numbers lie

After a job dies of memory, the natural next step is `sacct -o JobID,State,ReqMem,MaxRSS`. Sometimes `MaxRSS` is far below `ReqMem`, and the job still says `OUT_OF_MEMORY`. Believe the state, not the number.

`MaxRSS` is a **sample**. The task-level gather plugin polls on a timer, and the default `JobAcctGatherFrequency` is 30 seconds. A process that allocates fast, spikes and dies between two polls leaves no trace in the accounting data. SchedMD staff say exactly this when users ask why a fast-growing task is under-reported.

More ways the number can mislead:

- **The plugin decides what "RSS" means.** `jobacct_gather/linux` reads RSS from `/proc`, with `UsePSS` and `NoShare` options that change the calculation. Two clusters with different settings can report different `MaxRSS` for the same job.
- **`jobacct_gather/cgroup` on v2 has no virtual memory.** The `sstat` man page notes that combination reports 0 for the virtual-memory fields, because of what the kernel exposes.
- **Sampling can be switched off.** With the task interval set to 0 (as in `JobAcctGatherFrequency=task=0`), data is collected only when the job ends.
- **Gathering costs something.** SchedMD's large-cluster guidance calls `jobacct_gather/none` the best choice for throughput and, if you need job accounting, says to tune the sampling interval.

If you want a number you can trust, read it from the kernel while the job is alive. On cgroup v2 each job's cgroup has `memory.events` (look for `oom_kill`) and, on newer kernels, `memory.peak`. The cgroup is removed when the job ends, so this is a live-debugging tool, not a post-mortem one:

```bash
# on the compute node, while the job runs
# the job directory name depends on your version and CgroupJobIdPaths, so look first
ls /sys/fs/cgroup/system.slice/slurmstepd.scope/
cat /sys/fs/cgroup/system.slice/slurmstepd.scope/<job-dir>/memory.events
cat /sys/fs/cgroup/system.slice/slurmstepd.scope/<job-dir>/memory.peak
```

* * *

## systemd and the scope nobody sees

On cgroup v2, Slurm cannot just build a directory tree and walk away, because systemd owns the hierarchy and will tidy up anything it did not create. Slurm's answer is a dedicated scope, `slurmstepd.scope`, delegated to Slurm. Step processes live there rather than under the `slurmd` service, so restarting `slurmd` does not take running jobs with it. A small `slurmstepd infinity` process sits in the scope to keep it alive.

Knobs worth knowing:

- **`CgroupSlice`** moves the scope out of the default `system.slice`.
- **`SystemdTimeout`** is how long Slurm waits for the scope at `slurmd` start. It defaults to 1000 ms, which can be too short on a busy or virtualized node.
- **`IgnoreSystemd`** exists for development. The docs call it dangerous on a systemd machine, because systemd may modify the cgroups under running jobs.
- **`EnableControllers`** is for old kernels and old systemd (RHEL8 is the documented example) where not every controller is enabled down the tree.

This is also where [`pam_slurm_adopt`](/fields/schedulers/slurm-pam-adopt-ssh-access.md) plugs in. The `cgroup.conf` example says sites should configure it so users cannot escape the cgroups through `ssh`, and the cgroup v2 guide has its own section on running it there.

* * *

## Verify it in ten minutes

On a test node, with a test account:

```bash
# 1. What is Slurm configured to do?
scontrol show config | grep -E 'ProctrackType|TaskPlugin|JobAcctGather|PrologFlags|SelectTypeParameters'
cat /etc/slurm/cgroup.conf

# 2. GPUs: should list exactly the GPUs you asked for
srun --gres=gpu:1 nvidia-smi -L

# 3. Cores: affinity should match the allocation
srun --cpus-per-task=2 bash -c 'nproc; taskset -cp $$'

# 4. Memory: should die and be reported as OUT_OF_MEMORY
srun --mem=500M python3 -c "x = bytearray(2 * 1024**3); print('survived')"
sacct -j <jobid> -o JobID,State,ReqMem,MaxRSS
```

Read the results like this:

| Result | Meaning |
|---|---|
| `nvidia-smi -L` lists every GPU on the node | `ConstrainDevices` is off, or the GPU device files are not known to Slurm |
| `nproc` shows more cores than requested | `ConstrainCores` is off, or affinity binding is not working |
| The Python line prints `survived` | Memory is not being constrained (check `ConstrainRAMSpace`, `CR_*_Memory` and the memory controller) |
| `MaxRSS` is tiny but the state says OOM | Sampling missed the spike; the state is the truth |

> [!TIP]
> Run test 2 before and after switching on `ConstrainDevices`. Seeing eight GPUs shrink to one is the clearest way to explain this page to a colleague.

* * *

## The mental model to keep

```
slurm.conf  : loads the plugins     (task/cgroup, proctrack/cgroup, PrologFlags=Contain)
cgroup.conf : switches on the fences (cores, devices, RAM, swap) -> all default OFF

            slurmstepd.scope           (v2: delegated to Slurm by systemd)
            └── job
                ├── extern step        <- pam_slurm_adopt sessions land here
                ├── batch step
                └── step 0, 1, ...     <- cpuset, devices, memory limits apply here

accounting numbers (MaxRSS ...) = periodic samples; the kernel's OOM log = the truth
```

Loading `task/cgroup` is not the same as constraining anything, and `sacct` is a sampled summary, not a flight recorder.

* * *

## References

- [Slurm: cgroup.conf man page](https://slurm.schedmd.com/cgroup.conf.html)
- [Slurm: Control Group in Slurm](https://slurm.schedmd.com/cgroups.html)
- [Slurm: Control Group v2 plugin](https://slurm.schedmd.com/cgroup_v2.html)
- [slurm-users: accounting sampling and fast-growing tasks](https://lists.schedmd.com/pipermail/slurm-users/2023-November/010597.html)
- [slurm-users: memory enforcement mechanisms and OverMemoryKill](https://lists.schedmd.com/pipermail/slurm-users/2019-October/004260.html)
- [SchedMD ticket 10538: how MaxRSS is calculated per plugin](https://support.schedmd.com/show_bug.cgi?id=10538)
- [sstat man page: jobacct_gather/cgroup on v2 and virtual memory](https://dokk.org/manpages/debian/13/slurm-client/sstat.1.en)