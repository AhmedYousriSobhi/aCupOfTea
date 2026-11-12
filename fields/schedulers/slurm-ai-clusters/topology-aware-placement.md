---
id: slurm-topology-placement
title: "Keep the Job on One Switch: Topology-Aware Placement in Slurm"
sidebar_label: "1. Keep the job on one switch"
order: 1
summary: How Slurm places multi-node jobs with and without a topology plugin - topology/tree, --switches, topology/block that refuses to straddle, the 25.05 topology.yaml, and a fatal block config.
level: intermediate
type: [concept, guide]
domains: [systems-and-hpc]
tags: [slurm, hpc, distributed-training]
relations:
  related: [slurm-distributed-training, slurm-backfill-tuning]
---

# Keep the Job on One Switch: Topology-Aware Placement in Slurm

> **Part 1 of [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md)** A multi-node training job is only as fast as the slowest link between its nodes. By the end you'll know where Slurm puts a job when it knows nothing about your network, how to tell it, and the difference between "prefer one switch" and "never leave the block".

- [The Tuesday slowdown](#the-tuesday-slowdown)
- [Where Slurm puts a job by default](#where-slurm-puts-a-job-by-default)
- [topology/tree: prefer one switch](#topologytree-prefer-one-switch)
- [--switches: wait for one switch](#--switches-wait-for-one-switch)
- [topology/block: never straddle](#topologyblock-never-straddle)
- [Two topologies in one cluster (25.05+)](#two-topologies-in-one-cluster-2505)
- [Which one to use](#which-one-to-use)
- [Back to Tuesday](#back-to-tuesday)
- [References](#references)

---

## The Tuesday slowdown

A team runs the same 2-node fine-tuning job every night. Most nights it takes four hours. Some nights it takes five and a half, with the same code, the same data and the same GPU model. Nobody can find a pattern, until someone lists the node pairs: the slow nights are the ones where the two nodes sit under different leaf switches, and every gradient all-reduce crosses the spine.

Slurm picked those nodes. It had no idea the switches existed, because nobody told it.

> [!NOTE]
> Lab: Slurm **23.11.4**, four CPU nodes `cn001`–`cn004` with 2 CPUs each, plus `gpu001`. The "network" is invented: we declare `cn[001-002]` under one leaf and `cn[003-004]` under another. Containers share one real network, so these tests show **placement**, not speed. Slurm **26.05.6** on `s26a`–`s26c` for `topology.yaml`.

---

## Where Slurm puts a job by default

With no topology plugin, the scheduler treats nodes as a flat list. We filled `cn001` with a 2-CPU job, then asked for two nodes:

```bash
sbatch -p cpu -w cn001 -n2 --wrap 'sleep 300'     # make cn001 busy
sbatch -p cpu -N2 --wrap 'sleep 30'
squeue -o '%i %j %N'
```

```text
TopologyPlugin=topology/default  job two -> cn[002-003] RUNNING None
```

`cn002` and `cn003`: the first two free nodes in order. On our invented network, that's one node under each leaf. Exactly the slow nights.

---

## topology/tree: prefer one switch

**`topology/tree`** reads a switch hierarchy from `topology.conf` and tries to fit each job under the lowest common switch. In `slurm.conf`:

```text
TopologyPlugin=topology/tree
```

And `/etc/slurm/topology.conf`, on the controller and every node:

```text
SwitchName=leaf1 Nodes=cn[001-002]
SwitchName=leaf2 Nodes=cn[003-004]
SwitchName=leaf3 Nodes=gpu001
SwitchName=spine Switches=leaf[1-3]
```

After restarting `slurmctld` and the `slurmd`s, Slurm shows what it understood:

```text
$ scontrol show topology
SwitchName=leaf1 Level=0 LinkSpeed=1 Nodes=cn[001-002]
SwitchName=leaf2 Level=0 LinkSpeed=1 Nodes=cn[003-004]
SwitchName=leaf3 Level=0 LinkSpeed=1 Nodes=gpu001
SwitchName=spine Level=1 LinkSpeed=1 Nodes=cn[001-004],gpu001 Switches=leaf[1-3]
```

Same test, same busy `cn001`:

```text
TopologyPlugin=topology/tree  job two -> cn[003-004] RUNNING None
```

Both nodes under `leaf2`. That's the whole fix for the Tuesday slowdown, as long as one leaf has room.

When no single leaf has room, `tree` still starts the job, spread across leaves. The docs say a job that can't fit under one leaf "will be spread across as many leaf switches as possible". It *prefers* one switch, it doesn't insist.

> [!WARNING]
> Nodes on switches with **no common parent** never share a job (unless `TopologyParam=TopoOptional`). Forget the `spine` line and no job can ever span `leaf1` and `leaf2`. That's sometimes useful, usually a typo. And the docs note that node `Weight` overrides topology-based selection.

---

## --switches: wait for one switch

A user who'd rather wait than straddle can say so:

```bash
sbatch -p cpu -N2 --switches=1@00:01:00 --wrap 'sleep 30'
```

`--switches=count@max-time`: at most one leaf switch, and wait up to one minute for that. We made one node busy under each leaf (`cn001` and `cn003`), so the only free pair, `cn002` and `cn004`, straddled:

```text
+10s PENDING|Resources|
...
+90s PENDING|Resources|
+100s RUNNING|None|cn[002,004]
SubmitTime=2026-11-12T04:41:28 StartTime=2026-11-12T04:43:06 Switches=1@00:01:00
```

It waited, then gave up and took the straddling pair, 98 seconds after submission (69 seconds in an earlier run). The wait is checked on scheduling passes, so it runs over the limit by however long the next pass takes.

Without a time, the wait is capped by the cluster-wide `max_switch_wait` in `SchedulerParameters` (default 300 seconds, per `slurm.conf(5)`).

---

## topology/block: never straddle

**`topology/block`** is the stricter model, built for systems like NVLink racks where a job either fits inside a block of nodes or performs badly. `topology.conf`:

```text
BlockName=nvl1 Nodes=cn[001-002]
BlockName=nvl2 Nodes=cn[003-004]
```

```text
$ scontrol show topology
BlockName=nvl1 BlockIndex=0 Nodes=cn[001-002]
BlockName=nvl2 BlockIndex=1 Nodes=cn[003-004]
```

With `cn001` busy, the 2-node job went to `cn[003-004]`, like `tree`. The difference shows when no block has room. One busy node per block, then a 2-node and a 3-node job:

```text
after 90s:
JOBI   NAME ST     REASON NODELIST
 142    two PD  Resources
 143  three PD   Priority
 140  busy1  R       None cn001
 141  busy3  R       None cn003
after freeing cn003:
JOBI   NAME ST     REASON NODELIST
 143  three PD  Resources
 142    two  R       None cn[003-004]
 140  busy1  R       None cn001
```

Two free nodes sat idle for 90 seconds, and the job waited rather than straddle. When `cn003` freed up, it started inside `nvl2`. That's the trade: perfect placement, paid for in idle nodes and queue time.

Two things bit us while setting it up:

| What we did | What happened |
| --- | --- |
| Added `BlockName=nvl3 Nodes=gpu001`: a block of 1 next to blocks of 2 | `slurmctld` exited: `fatal: Block configuration (nvl3) children count no equal bblock_node_cnt`. Every block at a level must be the same size |
| Left `gpu001` out of every block | `warning: blocks lack access to 1 nodes: gpu001` in the controller log. Jobs in the `gpu` partition still ran on `gpu001` |

The first one takes the controller down, so test a new `topology.conf` on a lab controller before production.

The docs list more limits of `block`: `-w/--nodelist` can conflict with block placement and leave the job unallocated, and node-count ranges (`-N 2-8`) make the scheduler evaluate every value.

`--segment=<size>`, which builds a block job's allocation out of segments of that many nodes, isn't in 23.11 (`sbatch: unrecognized option '--segment=2'`). The 26.11 docs describe it for `block` and add a per-partition default, `DefSegmentSize`.

---

## Two topologies in one cluster (25.05+)

One cluster often has both: a switch tree for most nodes, and NVLink blocks for a few racks. Before 25.05 you had to pick one plugin. Since 25.05, **`topology.yaml`** defines several topologies and each partition chooses one with `Topology=`. On the 26.05 lab:

```yaml
# /opt/slurm26/etc/topology.yaml
- topology: fabric
  cluster_default: true
  tree:
    switches:
      - switch: leaf1
        nodes: s26a,s26b
      - switch: leaf2
        nodes: s26c
      - switch: spine
        children: leaf1,leaf2
- topology: nvl
  block:
    block_sizes: [2]
    blocks:
      - block: rack1
        nodes: s26a,s26b
```

```text
PartitionName=all Nodes=s26a,s26b,s26c Default=YES State=UP
PartitionName=nvl Nodes=s26a,s26b Topology=nvl State=UP
```

`scontrol show topology` lists the default tree; `scontrol show topology nvl` names the other:

```text
BlockName=rack1 BlockIndex=0 Nodes=s26a,s26b BlockSize=2
```

A `-p nvl -N2` job ran on `s26a,s26b`. Same nodes, two placement policies, chosen by partition. Our 26.05 `slurm.conf` had no `TopologyPlugin` line at all. The file sits next to `slurm.conf`, and the docs say that when `topology.yaml` exists, `topology.conf` is ignored.

---

## Which one to use

| Your network | Use | Users get |
| --- | --- | --- |
| Fat tree, small oversubscription | `tree` | Best effort, no extra waiting |
| Tree with heavy oversubscription at the spine | `tree`, and teach `--switches=1@<time>` for big jobs | A choice: wait, or run slower |
| NVLink domains, or racks where crossing hurts a lot | `block` | Fast placement or no placement |
| Both (25.05+) | `topology.yaml`, one topology per partition | The right policy per partition |

Generate the switch list from the fabric rather than by hand. The Slurm docs point at community tools such as `slurmibtopology` for InfiniBand.

---

## Back to Tuesday

With `topology/tree` and a `topology.conf` that matches the real switches, the nightly job lands under one leaf whenever one leaf has room, which on that cluster is almost every night. For the few nights it doesn't, the team added `--switches=1@01:00:00` to the job: wait up to an hour for one switch, then run anyway. A one-hour wait beats a ninety-minute slowdown.

The slow nights didn't come from the GPUs. Slurm didn't know where the cables went.

**Takeaway:** without a topology plugin Slurm picks nodes in list order; `topology/tree` prefers one switch, `--switches` makes a job wait for one, `topology/block` refuses to straddle at all, and since 25.05 each partition can pick its own.

**Next:** [Part 2, Launching Distributed Training](/fields/schedulers/slurm-ai-clusters/launching-distributed-training.md), gets every rank started on the nodes this page picked.

---

## References

- [Slurm: Topology Guide](https://slurm.schedmd.com/topology.html): `tree`, `block`, `BlockSizes`, block limitations, `topology.yaml`, `--segment`, configuration generators.
- [topology.conf(5)](https://slurm.schedmd.com/topology.conf.html) and [topology.yaml(5)](https://slurm.schedmd.com/topology.yaml.html): file formats.
- [sbatch(1): --switches](https://slurm.schedmd.com/sbatch.html#OPT_switches): `count@max-time`.
- [slurm.conf(5): SchedulerParameters](https://slurm.schedmd.com/slurm.conf.html#OPT_SchedulerParameters): `max_switch_wait`; `TopologyParam=TopoOptional`.
- [Slurm 26.11 release notes](https://github.com/SchedMD/slurm/blob/master/RELEASE_NOTES.md): `DefSegmentSize`.
