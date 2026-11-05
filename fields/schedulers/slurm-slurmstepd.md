---
id: slurm-slurmstepd
title: "slurmstepd: The Small Daemon That Actually Runs Your Job"
order: 3
sidebar_label: slurmstepd
summary: slurmstepd (1/step/node) bridges slurmd's fork and task start. Jobs survive slurmd restarts via SlurmdSpoolDir sockets. Covers how to find, count, and read stepds on busy nodes.
level: intermediate
type: concept
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  related:
    - slurm-kill-task-failed
    - slurm-cgroups-in-practice
    - slurm-spool-dir-full
---

# slurmstepd: The Small Daemon That Actually Runs Your Job

> **Part of the [schedulers](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-intro.md) directory.** The intro draws `slurmctld` and `slurmd` and then waves at "the job". This page is about the process that sits between `slurmd` and your code. Facts come from SchedMD's Job Launch Design Guide, support tickets, slurmd man pages and the Slurm source as I read it. Nothing was run on a live cluster for this page, and some details (such as socket handling) are from source files of different versions, so they are marked where it matters.

## Table of Contents

- [slurmstepd: The Small Daemon That Actually Runs Your Job](#slurmstepd-the-small-daemon-that-actually-runs-your-job)
  - [Table of Contents](#table-of-contents)
  - [The middle manager nobody draws](#the-middle-manager-nobody-draws)
  - [One stepd per step per node](#one-stepd-per-step-per-node)
  - [What it does before your code runs](#what-it-does-before-your-code-runs)
  - [Why restarting slurmd does not kill jobs](#why-restarting-slurmd-does-not-kill-jobs)
  - [The socket in the spool directory](#the-socket-in-the-spool-directory)
  - [Who actually kills the job](#who-actually-kills-the-job)
  - [The stepd has a memory footprint too](#the-stepd-has-a-memory-footprint-too)
  - [The step manager: stepd with a promotion](#the-step-manager-stepd-with-a-promotion)
  - [Field guide: find it, count it, read it](#field-guide-find-it-count-it-read-it)
  - [Cheat sheet](#cheat-sheet)
  - [References](#references)

* * *

## The middle manager nobody draws

Every architecture diagram of Slurm has the same three boxes: the controller, the compute-node daemon and the job. It is a clean picture, and it skips the part where the work happens.

A better org chart looks like this:

| Role | Process | What it does |
|---|---|---|
| Executive | `slurmctld` | Decides who gets what and when. Deliberately kept out of task launch to protect itself from load |
| Receptionist | `slurmd` | Accepts requests, validates credentials, and **forks** a stepd for each step |
| Middle manager | `slurmstepd` | Runs one step, start to finish, on one node |
| Staff | Your tasks | The reason anyone showed up |

The Job Launch Design Guide says it in one dry sentence: each `slurmstepd` program executes a single job step. That sentence has consequences, and the rest of this page unpacks them.

* * *

## One stepd per step per node

Per the guide, `slurmd` tests that the job was not cancelled since the credential was issued, then spawns a `slurmstepd` to manage the step. Every step type works this way:

| Step | Runs where | What it runs |
|---|---|---|
| **extern** | Every node of the job, if `PrologFlags=contain` is set | Nothing of yours. It exists to hold processes started outside Slurm, like `ssh` sessions adopted by [`pam_slurm_adopt`](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-pam-adopt-ssh-access.md) |
| **batch** | The first node of an `sbatch` job | Your batch script |
| **interactive** | The node with your shell, for `salloc` with `LaunchParameters=use_interactive_step` | The shell or command |
| **normal** | Every node of each `srun` inside the job, shown in `sacct` as `jobid.stepid` | The command given to `srun` |

A normal step has **one stepd per node** in that step, and each stepd can run several tasks.

An invented but typical case: a two-node `sbatch` job that calls `srun` twice. On the first node you can expect an extern stepd, a batch stepd and one stepd for each of the two `srun` steps. On the second node you can expect the extern stepd and the two step stepds. That makes four stepds on the first node and three on the second, seven small processes for one job, none of them yours.

That count matters when you hear a story about a node with a job count of 40 and a process list that looks like a small town.

* * *

## What it does before your code runs

The guide lists the stepd's functions in order. Between the fork and your first instruction, it:

1. Performs MPI setup, using the appropriate plugin
2. Calls the `switch` plugin to do any network configuration
3. Creates a container for the step using a `proctrack` plugin
4. **Changes user ID** to that of the user
5. Configures I/O for the tasks, either with files or with a socket connection back to `srun`
6. Sets up environment variables, including many task-specific ones
7. Forks and execs the tasks

And in between, it runs several SPANK plugin hooks at various points.

Three observations that explain things people find odd:

- **The stepd is why your job runs as you.** `slurmd` runs as root. The step changes to your UID in step 4, before any task starts. A root-owned `slurmd` never runs your code directly.
- **The stepd owns the container.** Process tracking (and, with the cgroup plugins, the resource limits described on the [cgroups page](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-cgroups-in-practice.md)) is set up here, which is how "kill the job" later reaches every process.
- **Output does not travel through `slurmd`.** The stepd sets up the I/O path itself, either writing to files or connecting back to `srun`.

* * *

## Why restarting slurmd does not kill jobs

An old SchedMD ticket answers a question every new admin eventually asks: can I restart the daemons while jobs run? The reply is worth quoting in spirit. The controller keeps its state in the `StateSaveLocation` directory and the job information in the `SlurmdSpoolDir`, so as long as those directories exist, the information needed to restore state is there. And each job is administered by its stepd, which is forked from `slurmd` and responsible for monitoring the job and collecting its resource data. **The stepd is unaffected by a `slurmd` restart**, so restarting `slurmd` does not affect the job.

The reply adds a caveat in the same breath: lose the stepd and you lose the job. It also says that in practice this almost never happens, because the stepd is small and stable. The ticket dates from 2014, so treat the folklore with some age in mind, but the design has not changed in shape.

This is why [the upgrade page](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-upgrade-order.md) can say that running jobs survive a `slurmd` upgrade, and why the same page warns that a job started before the upgrade keeps running with the old stepd.

* * *

## The socket in the spool directory

How does a freshly restarted `slurmd` find a stepd it did not start? Through the filesystem. In the source I read, each stepd creates a Unix domain socket in `SlurmdSpoolDir` with a name built from the node name, job ID and step ID:

```
<SlurmdSpoolDir>/<nodename>_<jobid>.<stepid>
```

Other tools use the same naming to talk to a running step. The stepd API describes scanning a directory for sockets whose names begin with the node name as the way to find running step daemons, and the request types on that socket include signalling tasks, asking for state and info, attaching, and listing PIDs in the container. The older source I read creates the socket world-accessible and enforces who may do what inside the request handler, which checks for root or `SlurmUser` on privileged requests.

Two details from the source that matter in practice:

- **A stale socket is cleaned up with some patience.** If a connection to a socket is refused (nothing is listening), the client treats it as stray, and in the version I read it removes the socket if it is at least ten minutes old.
- **A step cannot be created twice.** If a socket with the same name already exists, the stepd logs that the socket already exists and fails to start the step.

The practical rule that follows is a simple one, and the [spool directory page](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-spool-dir-full.md) builds on it: **do not clean up `SlurmdSpoolDir` by hand while jobs are running.** The directory is where `slurmd` and its stepds find each other. That rule is my inference from the design rather than a sentence in the docs, so check with `ls` and a test node before you improvise.

* * *

## Who actually kills the job

A subtle point from the Job Launch Design Guide. When a job is cancelled or hits its limit, the termination sequence is described as work done by **`slurmd`**:

1. Send `SIGCONT` and `SIGTERM` to user tasks
2. Wait `KillWait` seconds if tasks remain
3. Send `SIGKILL`
4. Wait for all tasks to complete
5. Run the `Epilog`
6. Send an `epilog_complete` RPC to `slurmctld`

The stepd is the one holding the container that makes step 3 reach every process, and it is the one that reports when tasks exit. When step 4 never finishes, you get the drained node described in [Kill Task Failed](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-kill-task-failed.md). One log line from a support ticket on that failure reads "STEPD TERMINATED ON <node> ... DUE TO JOB NOT ENDING WITH SIGNALS", which is the stepd's side of the same story.

* * *

## The stepd has a memory footprint too

The stepd is small, but on a busy node there are a lot of them, and some jobs make theirs grow. Slurm's documentation makes a few separate points:

- **Reserving memory for the daemons.** `MemSpecLimit` reserves memory for system use. The `slurm.conf` description says that, with `task/cgroup` and `ConstrainRAMSpace=yes`, the compute node daemons (`slurmd` plus `slurmstepd`) are allocated that limit, and the OOM killer is disabled for the daemons' memory cgroup.
- **A version caveat.** The cgroups guide says that under cgroup v1 the reserved resources are also used by `slurmstepd`, while under cgroup v2 `slurmstepd` is **not** constrained by resource specialization. Its example is an MPI job whose PMI setup makes `slurmstepd` use a lot of memory. If those two statements seem to disagree on your version, trust a test over my summary.
- **Pinning it in memory.** `slurmd -M` locks `slurmd` into memory, and the man page suggests setting `LaunchParameters=slurmstepd_memlock` in `slurm.conf` along with it. That helps on nodes that get marked DOWN during heavy swap activity.
- **Limits are inherited.** The stepds, and so your tasks, run under the limits of the `slurmd` systemd service (`LimitNOFILE`, `LimitMEMLOCK`, `LimitSTACK`, `LimitCORE`), not the ones in `/etc/security/limits.conf`. Check them with `cat /proc/$(pgrep -u 0 slurmd)/limits`.

A note from Niflheim's documentation adds a multiplication that is easy to forget: `LimitNOFILE` applies per job step, so a node running N jobs needs the kernel's `fs.file-max` to allow N times that value.

* * *

## The step manager: stepd with a promotion

Newer Slurm releases changed who creates steps. Traditionally `srun` asks `slurmctld` for a step, and the controller does the work. SchedMD's SLUG 2024 slides describe a **step manager (stepmgr)** design that reduces RPC congestion and locking on the controller: one stepd of the job (the batch, extern or interactive one) is designated as the step manager, the job allocation tells clients which `slurmd` hosts it, and `srun` sends its step-create request there instead. The slides also say that `scontrol show steps` without a job ID lists the steps managed by the controller, including the extern, batch and interactive ones.

I have only read the slides, not the release notes, so check your version's release notes for how it is enabled and which commands behave differently.

* * *

## Field guide: find it, count it, read it

**Find stepds on a node.** Their process titles carry the step ID in brackets, such as `[12345.batch]`, `[12345.extern]` and `[12345.0]`:

```bash
ps -eo pid,ppid,etime,args | grep '[s]lurmstepd'
```

To see the independence for yourself on a test node, note a stepd's PID and parent PID, restart `slurmd`, and look again. The stepd keeps running with its PID unchanged. That is a test, not a documented guarantee, so try it before you rely on it.

**Count steps per job.**

```bash
ps -eo args | grep -o '\[[0-9]*\.[a-z0-9]*\]' | sort | uniq -c | sort -rn | head
```

**See the job's processes.** `scontrol listpids <jobid>` on the node lists the PIDs Slurm tracks for the job. If your process is running on the node and missing from that list, it escaped containment.

**Look at the sockets.**

```bash
scontrol show config | grep SlurmdSpoolDir
ls -l <that directory> | head
```

**Read the logs.** Step messages land in the node's `slurmd` log, prefixed with the step in brackets, as in `[91099.batch] error: ...`. `SlurmdDebug=debug2` gives more detail on the node while you test. Typical lines from support tickets include "Abandoning IO 60 secs after job shutdown initiated" and "done with job".

* * *

## Cheat sheet

```
slurmctld  decides       slurmd  receives, validates, forks       slurmstepd  runs ONE step on ONE node

stepd types:  extern (PrologFlags=contain) | batch | interactive | normal (jobid.stepid)
before tasks: MPI setup -> switch plugin -> proctrack container -> setuid -> I/O -> env -> fork/exec
survives:     slurmd restarts (it is not slurmd's child in any way that matters)
rendezvous:   <SlurmdSpoolDir>/<nodename>_<jobid>.<stepid>   (unix socket)
dies how:     slurmd sends signals; the stepd holds the container; a stuck process leaves the stepd waiting
```

The middle manager is small, quiet, and holds the keys. Most of what is strange about Slurm on a compute node becomes less strange once you ask which stepd it belongs to.

* * *

## References

- [Slurm: Job Launch Design Guide](https://slurm.schedmd.com/job_launch.html)
- [SchedMD ticket 689: advice for running in production (restarting daemons and stepds)](https://support.schedmd.com/show_bug.cgi?id=689)
- [SchedMD ticket 11103: unkillable step log lines](https://support.schedmd.com/show_bug.cgi?id=11103)
- [SchedMD ticket 22425: STEPD TERMINATED ... DUE TO JOB NOT ENDING WITH SIGNALS](https://support.schedmd.com/show_bug.cgi?id=22425)
- [Slurm: slurmd man page (-M, `slurmstepd_memlock`)](https://www.mankier.com/8/slurmd)
- [Slurm: Control Group in Slurm](https://slurm.schedmd.com/cgroups.html)
- [Slurm source: stepd_api.c (socket naming and stale-socket cleanup)](https://third-party-mirror.googlesource.com/SchedMD/slurm/+/refs/heads/slurm-2.5/src/common/stepd_api.c)
- [SchedMD SLUG 2024: Step Management slides](https://slurm.schedmd.com/SLUG24/Step-Management.pdf)
- [Niflheim: Slurm configuration (slurmd systemd limits)](https://niflheim-system.readthedocs.io/en/latest/Slurm_configuration.html)