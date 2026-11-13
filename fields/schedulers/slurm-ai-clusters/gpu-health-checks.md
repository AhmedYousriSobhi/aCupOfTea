---
id: slurm-gpu-health-checks
title: "When a GPU Falls Off the Bus: Health Checks That Drain the Node"
sidebar_label: "4. GPU health checks"
order: 4
summary: A tested Slurm HealthCheckProgram that drains a node when a GPU disappears, the bug where it overwrote the admin's drain reason, what slurmd does on restart, and the per-GPU drain coming in 26.11.
level: intermediate
type: [concept, guide]
domains: [systems-and-hpc]
tags: [slurm, hpc, gpu, nvidia]
relations:
  related: [slurm-containers-pyxis, slurm-kill-task-failed, slurm-spool-dir-full]
---

# When a GPU Falls Off the Bus: Health Checks That Drain the Node

> **Part 4 of [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md)** GPUs fail in ways the scheduler can't see on its own. By the end you'll have a health check that takes a node with a missing GPU out of service within one interval, leaves running jobs alone, and doesn't trample a drain an admin set by hand.

- [The node that ate the queue](#the-node-that-ate-the-queue)
- [What Slurm does on its own](#what-slurm-does-on-its-own)
- [HealthCheckProgram in one paragraph](#healthcheckprogram-in-one-paragraph)
- [A GPU health check](#a-gpu-health-check)
- [Pulling a GPU out](#pulling-a-gpu-out)
- [The bug: it overwrote the admin's reason](#the-bug-it-overwrote-the-admins-reason)
- [What a real check should test](#what-a-real-check-should-test)
- [26.11: drain one GPU, not the node](#2611-drain-one-gpu-not-the-node)
- [Back to the queue](#back-to-the-queue)
- [References](#references)

---

## The node that ate the queue

One GPU in an 8-GPU node drops off the PCIe bus overnight. The driver now sees seven. Slurm still thinks there are eight, because it read `gres.conf` when `slurmd` started. Every job that lands there with `--gpus-per-node=8` dies in its first minute with a CUDA error. Each failure frees the node, so the scheduler gives it to the next job in the queue. By morning, forty jobs have failed on one node, and to the scheduler it looks like the healthiest node in the cluster, because it's always free.

Nothing checked the GPUs between job starts.

> [!NOTE]
> Lab: Slurm **23.11.4**, `gpu001` with four GPUs that are **fake device files** (`/dev/nvidia0`–`3`). "A GPU falls off" is simulated by deleting one device file. On a real node you'd count GPUs with `nvidia-smi`; the Slurm behaviour (drain, reasons, states) is the same and is what we tested.

---

## What Slurm does on its own

We tried the obvious thing first: delete `/dev/nvidia1`, restart `slurmd` on `gpu001`.

```text
error: Waiting for gres.conf file /dev/nvidia1
fatal: can't stat gres.conf file /dev/nvidia1: No such file or directory
```

`slurmd` refused to start, and the node showed `idle*` (not responding) until it would be marked `DOWN`. So Slurm notices a missing device **at `slurmd` start**. While `slurmd` keeps running, it doesn't look again. A GPU that disappears between restarts is invisible to it, which is the story above.

---

## HealthCheckProgram in one paragraph

`slurm.conf` can name a **`HealthCheckProgram`**: a script that `slurmd` runs as root, every `HealthCheckInterval` seconds, on every node that is responding. The script decides what "healthy" means and takes any action itself, usually `scontrol update ... state=drain`. From `slurm.conf(5)`: it runs at the same time on all nodes, it's killed if it doesn't finish within 60 seconds, and it also runs when `slurmd` starts, before the node registers. `HealthCheckNodeState` limits which node states run it; the default is `ANY`.

**Drain**, not down: a draining node finishes its running jobs and takes no new ones. Setting a node `DOWN` kills its jobs.

---

## A GPU health check

The check compares the GPUs Slurm expects with the GPUs the node can see:

```bash
#!/usr/bin/env bash
# gpu-health - Slurm HealthCheckProgram: drain this node if it sees fewer GPUs than Slurm expects.
node=$(hostname -s)
info=$(scontrol show node "$node")
want=$(grep -oP '\bGres=gpu:[^:]+:\K[0-9]+' <<<"$info")
[ -z "$want" ] && exit 0                                  # not a GPU node
grep -qP '\bState=\S*DRAIN' <<<"$info" && exit 0          # already drained: keep the existing reason
have=$(ls -d /dev/nvidia[0-9]* 2>/dev/null | wc -l)       # real nodes: nvidia-smi -L | wc -l
if [ "$have" -lt "$want" ]; then
  scontrol update nodename="$node" state=drain reason="gpu-health: $have/$want GPUs visible"
fi
exit 0
```

That's the second version. The first didn't have the `already drained` line, and the bug it caused is [below](#the-bug-it-overwrote-the-admins-reason).

Install it on **every** node, CPU nodes included (it exits at once when the node has no GPUs), then in `slurm.conf`:

```text
HealthCheckProgram=/usr/local/sbin/gpu-health
HealthCheckInterval=30
```

```text
$ scontrol show config | grep HealthCheck
HealthCheckInterval     = 30 sec
HealthCheckNodeState    = ANY
HealthCheckProgram      = /usr/local/sbin/gpu-health
```

30 seconds is a lab value to keep the test short. Production clusters usually check every few minutes; a check that runs `nvidia-smi` on 8 GPUs isn't free.

---

## Pulling a GPU out

Alice had a 1-GPU job running on `gpu001`. At 06:20:48 we deleted `/dev/nvidia2`:

```text
06:20:58 alloc|none
06:21:08 drng|gpu-health: 3/4 GPUs visible
```

Within one interval the node was **draining** (`drng`): alice's job kept running, and the reason says exactly what's wrong. A new 1-GPU job from bob waited:

```text
JOBID USER STATE NODELIST REASON
96 bob PENDING  Nodes required for job are DOWN, DRAINED or reserved for jobs in higher priority partitions
95 alice RUNNING gpu001 None
```

Then we put the device back. Forty seconds later the node was still `drng` with the same reason: the check drains, it never undrains. That's deliberate. A GPU that fell off once will fall off again; a person should look at it and run `scontrol update nodename=gpu001 state=resume`. After that, bob's job started.

Notice that bob asked for **one** GPU, and three healthy ones sat idle the whole time. Drain works on whole nodes. That's what 26.11 changes, [below](#2611-drain-one-gpu-not-the-node).

---

## The bug: it overwrote the admin's reason

Version 1 drained whenever GPUs were missing, whatever state the node was in. We drained `gpu001` by hand for planned work, then removed a GPU:

```bash
scontrol update nodename=gpu001 state=drain reason="CHG-2044 firmware update"
```

```text
drain|gpu-health: 3/4 GPUs visible|root(0)
```

The change ticket's reason was gone, replaced by the health check's. The next admin to look sees a hardware problem and opens a hardware ticket for a node that's down for planned firmware work. Worse, when the firmware work ends and someone resumes the node, nothing records that it was ever drained for a change.

Version 2 skips nodes that are already drained. Same test:

```text
drain|CHG-2044 firmware update|root(0)
```

The admin's reason survives. When the admin resumed the node with the GPU still missing, the next check drained it with `gpu-health: 3/4 GPUs visible`, which is the behaviour you want.

> [!TIP]
> If you run several checks (GPUs, disks, Pyxis, mounts), have one `HealthCheckProgram` call them all and drain once with the first failure as the reason. Several scripts racing to set a reason produce the same overwrite problem.

---

## What a real check should test

The device count catches "the GPU is gone". It doesn't catch a GPU that's present but broken. On real hardware, sites usually add (docs-only here, no GPUs in the lab):

| Check | Tool |
| --- | --- |
| Expected GPU count | `nvidia-smi -L \| wc -l` |
| Uncorrectable ECC errors, retired or remapped pages | `nvidia-smi -q -d ECC,PAGE_RETIREMENT` (fields vary by GPU generation) |
| A quick functional test | NVIDIA DCGM: `dcgmi diag -r 1` |
| Everything else (mounts, disk, daemons) | LBNL Node Health Check (NHC), a framework built for `HealthCheckProgram` |

Keep the periodic check short (it's killed after 60 seconds) and run the slow diagnostics from a prolog or epilog, or on demand.

---

## 26.11: drain one GPU, not the node

Docs-only: Slurm 26.11 was at rc1 when this was written, and these come from its release notes and man pages.

The 26.11 release notes list "per-device drain of GRES devices, CPUs, and memory with `scontrol update TresName=... Action=Drain`" and "the DEGRADED node state for nodes with drained TRES". From `scontrol(1)`:

```bash
scontrol update TresName=gres/gpu NodeName=tux1 Index=3 Action=Drain Reason=bad_gpu
scontrol show drainedtres
```

```text
NodeName=tux1 TresName=gres/gpu Index=0,2 Uuid=GPU-aaa,GPU-bbb Reason=ecc
```

What changes for the story above:

| | Through 26.05 | 26.11 |
| --- | --- | --- |
| One GPU bad | Drain the whole node | Drain that GPU; node becomes `DEGRADED` |
| Other GPUs on the node | Idle until resume | `sinfo(1)`: "The rest of the node stays schedulable" |
| A UUID-tracked GPU stops being reported | `slurmd` won't start (our test) | Its index is drained automatically, shown as `gpu(IDX:1)(gres/gpu:not_found)`. The node is also marked `INVAL` unless `SlurmctldParameters=drain_absent_gres` is set, which keeps it up |
| Return to service | `state=resume` | `TresName=... Action=Resume`; `state=RESUME_KEEP_TRES` returns the node but keeps drained GPUs drained |

`MaxDrainedTres` on a `NodeName` line drains the whole node once too many of its parts are drained. With these, the check above would drain the missing index instead of the node, and bob's 1-GPU job would have run on one of the three good GPUs.

---

## Back to the queue

With the check in place, the GPU falls off at 02:13, and at the next interval the node drains with `gpu-health: 7/8 GPUs visible`. The job running on it finishes or fails on its own; no new job lands there. The forty jobs that would have failed run elsewhere. In the morning there's one drained node with a precise reason, and a hardware ticket.

Nothing changed in the GPU. Slurm got told to look.

**Takeaway:** `slurmd` only checks GPU devices when it starts; a `HealthCheckProgram` that compares expected and visible GPUs and drains (never resumes, never overwrites an existing drain) keeps a broken node from eating the queue, and 26.11 can drain just the bad GPU.

**Next:** [Part 5, Metrics into VictoriaMetrics](/fields/schedulers/slurm-ai-clusters/metrics-openmetrics.md), puts drained nodes, idle CPUs and pending jobs on a graph.

---

## References

- [slurm.conf(5)](https://slurm.schedmd.com/slurm.conf.html#OPT_HealthCheckProgram): `HealthCheckProgram`, `HealthCheckInterval`, `HealthCheckNodeState`.
- [scontrol(1)](https://slurm.schedmd.com/scontrol.html): `update NodeName=... State=DRAIN|RESUME`, and in 26.11 `TresName=... Action=Drain`, `show drainedtres`, `RESUME_KEEP_TRES`.
- [gres.conf(5)](https://slurm.schedmd.com/gres.conf.html): `File=` device paths.
- [Slurm 26.11 release notes](https://github.com/SchedMD/slurm/blob/master/RELEASE_NOTES.md): per-device drain and the DEGRADED state.
- [LBNL Node Health Check](https://github.com/mej/nhc): a health-check framework for Slurm.
- [NVIDIA DCGM: diagnostics](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/dcgm-diagnostics.html): `dcgmi diag` run levels.
- [When jobs won't die](/fields/schedulers/slurm-cluster-operations/slurm-kill-task-failed.md) and [SlurmdSpoolDir is full](/fields/schedulers/slurm-cluster-operations/slurm-spool-dir-full.md): two other reasons nodes drain.
